"""Threaded localhost chat server with accounts, rooms, and SQLite history."""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import socket
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HOST, PORT = "127.0.0.1", 8765
DB_PATH = Path(__file__).with_name("chat.sqlite3")
MAX_LINE = 16_384


def password_hash(password: str, salt: bytes | None = None) -> tuple[bytes, bytes]:
    salt = salt or secrets.token_bytes(16)
    return salt, hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 310_000)


def initialize_db() -> None:
    with sqlite3.connect(DB_PATH) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY COLLATE NOCASE,
            salt BLOB NOT NULL,
            password_hash BLOB NOT NULL
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY,
            room TEXT NOT NULL,
            username TEXT NOT NULL,
            text TEXT NOT NULL,
            sent_at TEXT NOT NULL
        )""")
        db.execute("CREATE INDEX IF NOT EXISTS messages_room_id ON messages(room, id)")


def send_json(client: socket.socket, payload: dict[str, Any], lock: threading.Lock) -> None:
    data = (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")
    with lock:
        client.sendall(data)


class ChatServer:
    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.clients: dict[socket.socket, dict[str, Any]] = {}

    def _reply(self, client: socket.socket, payload: dict[str, Any]) -> None:
        state = self.clients.get(client, {})
        send_json(client, payload, state.get("send_lock", threading.Lock()))

    def _auth(self, client: socket.socket, action: str, username: str, password: str) -> bool:
        if not (3 <= len(username) <= 24) or not username.replace("_", "").isalnum() or not (8 <= len(password) <= 128):
            self._reply(client, {"type": "error", "text": "Username must be 3–24 letters/numbers/underscores; password 8–128 characters."})
            return False
        with sqlite3.connect(DB_PATH) as db:
            row = db.execute("SELECT salt, password_hash FROM users WHERE username = ?", (username,)).fetchone()
            if action == "register":
                if row:
                    self._reply(client, {"type": "error", "text": "That username is already registered."})
                    return False
                salt, digest = password_hash(password)
                try:
                    db.execute("INSERT INTO users (username, salt, password_hash) VALUES (?, ?, ?)", (username, salt, digest))
                except sqlite3.IntegrityError:
                    self._reply(client, {"type": "error", "text": "That username is already registered."})
                    return False
            elif not row or not hmac.compare_digest(password_hash(password, row[0])[1], row[1]):
                self._reply(client, {"type": "error", "text": "Invalid username or password."})
                return False
        with self.lock:
            self.clients[client]["username"] = username
        self._reply(client, {"type": "authenticated", "username": username})
        return True

    def _join(self, client: socket.socket, room: str) -> None:
        room = room.strip()
        if not 1 <= len(room) <= 40 or any(ord(char) < 32 for char in room):
            self._reply(client, {"type": "error", "text": "Room names must be 1–40 characters."})
            return
        with self.lock:
            state = self.clients[client]
            state["rooms"].add(room)
        with sqlite3.connect(DB_PATH) as db:
            rows = db.execute(
                "SELECT username, text, sent_at FROM messages WHERE room = ? ORDER BY id DESC LIMIT 100",
                (room,),
            ).fetchall()
        self._reply(client, {"type": "history", "room": room, "messages": [
            {"username": name, "text": text, "sent_at": sent_at} for name, text, sent_at in reversed(rows)
        ]})

    def _message(self, client: socket.socket, room: str, text: str) -> None:
        text = text.strip()
        if not text or len(text) > 2000:
            self._reply(client, {"type": "error", "text": "Messages must contain 1–2000 characters."})
            return
        with self.lock:
            state = self.clients[client]
            if room not in state["rooms"]:
                self._reply(client, {"type": "error", "text": "Join the room before sending a message."})
                return
            username = state["username"]
        sent_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with sqlite3.connect(DB_PATH) as db:
            db.execute("INSERT INTO messages (room, username, text, sent_at) VALUES (?, ?, ?, ?)", (room, username, text, sent_at))
        payload = {"type": "message", "room": room, "username": username, "text": text, "sent_at": sent_at}
        with self.lock:
            recipients = [
                (sock, details["send_lock"]) for sock, details in self.clients.items()
                if room in details["rooms"]
            ]
        for sock, send_lock in recipients:
            try:
                send_json(sock, payload, send_lock)
            except OSError:
                self._disconnect(sock)

    def _disconnect(self, client: socket.socket) -> None:
        with self.lock:
            state = self.clients.pop(client, None)
            if not state:
                return
            rooms, username = state["rooms"], state.get("username", "A user")
        for room in rooms:
            payload = {"type": "system", "room": room, "text": f"{username} disconnected.", "sent_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
            with self.lock:
                recipients = [(sock, info["send_lock"]) for sock, info in self.clients.items() if room in info["rooms"]]
            for sock, send_lock in recipients:
                try:
                    send_json(sock, payload, send_lock)
                except OSError:
                    pass
        try:
            client.close()
        except OSError:
            pass

    def _handle(self, client: socket.socket) -> None:
        send_lock = threading.Lock()
        with self.lock:
            self.clients[client] = {"username": None, "rooms": set(), "send_lock": send_lock}
        try:
            reader = client.makefile("rb")
            for raw in reader:
                if len(raw) > MAX_LINE:
                    self._reply(client, {"type": "error", "text": "Request too large."})
                    break
                try:
                    request = json.loads(raw.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    self._reply(client, {"type": "error", "text": "Invalid request."})
                    continue
                if not isinstance(request, dict):
                    self._reply(client, {"type": "error", "text": "Invalid request."})
                    continue
                with self.lock:
                    authenticated = bool(self.clients.get(client, {}).get("username"))
                action = request.get("action")
                if not authenticated and action in {"register", "login"}:
                    if not all(isinstance(request.get(k), str) for k in ("username", "password")):
                        self._reply(client, {"type": "error", "text": "Username and password are required."})
                    else:
                        self._auth(client, action, request["username"], request["password"])
                elif not authenticated:
                    self._reply(client, {"type": "error", "text": "Please sign in first."})
                elif action == "join" and isinstance(request.get("room"), str):
                    self._join(client, request["room"])
                elif action == "message" and all(isinstance(request.get(k), str) for k in ("room", "text")):
                    self._message(client, request["room"], request["text"])
                else:
                    self._reply(client, {"type": "error", "text": "Unsupported request."})
        except (OSError, sqlite3.Error) as exc:
            print(f"Client disconnected after server error: {exc}")
        finally:
            self._disconnect(client)

    def serve(self) -> None:
        initialize_db()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((HOST, PORT))
            server.listen()
            print(f"Local chat server listening on {HOST}:{PORT} (Ctrl+C to stop)")
            while True:
                client, address = server.accept()
                print(f"Client connected from {address[0]}:{address[1]}")
                threading.Thread(target=self._handle, args=(client,), daemon=True).start()


if __name__ == "__main__":
    try:
        ChatServer().serve()
    except KeyboardInterrupt:
        print("\nServer stopped.")
