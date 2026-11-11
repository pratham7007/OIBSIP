"""Tkinter client for chat_server.py. Connects only to the local demo server."""

from __future__ import annotations

import json
import queue
import socket
import threading
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

HOST, PORT = "127.0.0.1", 8765
EMOJI = {":smile:": "😄", ":heart:": "❤️", ":thumbsup:": "👍", ":fire:": "🔥", ":laugh:": "😂"}


class ChatClient(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Oasis Local Chat")
        self.geometry("700x560")
        self.minsize(500, 400)
        self.sock: socket.socket | None = None
        self.send_lock = threading.Lock()
        self.events: queue.Queue[dict] = queue.Queue()
        self.username = tk.StringVar()
        self.password = tk.StringVar()
        self.room = tk.StringVar(value="general")
        self._build_login()
        self.after(100, self._process_events)
        self.protocol("WM_DELETE_WINDOW", self._close)

    def _build_login(self) -> None:
        self.login_frame = ttk.Frame(self, padding=36)
        self.login_frame.pack(fill="both", expand=True)
        ttk.Label(self.login_frame, text="Local Chat", font=("Segoe UI", 22, "bold")).pack(pady=(40, 20))
        ttk.Label(self.login_frame, text="Username").pack(anchor="w")
        ttk.Entry(self.login_frame, textvariable=self.username).pack(fill="x", pady=(2, 12))
        ttk.Label(self.login_frame, text="Password").pack(anchor="w")
        ttk.Entry(self.login_frame, textvariable=self.password, show="•").pack(fill="x", pady=(2, 16))
        buttons = ttk.Frame(self.login_frame)
        buttons.pack(fill="x")
        ttk.Button(buttons, text="Log in", command=lambda: self._authenticate("login")).pack(side="left", expand=True, fill="x")
        ttk.Button(buttons, text="Register", command=lambda: self._authenticate("register")).pack(side="left", expand=True, fill="x", padx=(8, 0))
        ttk.Label(self.login_frame, text="Demo is bound to localhost; credentials and messages are not encrypted in transit.", wraplength=440).pack(pady=18)

    def _authenticate(self, action: str) -> None:
        username, password = self.username.get().strip(), self.password.get()
        if not username or not password:
            messagebox.showerror("Required", "Enter a username and password.")
            return
        try:
            self.sock = socket.create_connection((HOST, PORT), timeout=5)
            self.sock.settimeout(None)
            threading.Thread(target=self._receive, daemon=True).start()
            self._send({"action": action, "username": username, "password": password})
        except OSError as exc:
            self._close_socket()
            messagebox.showerror("Connection failed", f"Start chat_server.py first.\n\n{exc}")

    def _send(self, payload: dict) -> None:
        if not self.sock:
            return
        data = (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")
        with self.send_lock:
            self.sock.sendall(data)

    def _receive(self) -> None:
        assert self.sock
        try:
            with self.sock.makefile("r", encoding="utf-8") as reader:
                for line in reader:
                    self.events.put(json.loads(line))
        except (OSError, ValueError, json.JSONDecodeError):
            pass
        self.events.put({"type": "disconnected"})

    def _process_events(self) -> None:
        while True:
            try:
                event = self.events.get_nowait()
            except queue.Empty:
                break
            event_type = event.get("type")
            if event_type == "authenticated":
                self._open_chat()
            elif event_type == "history":
                self.room.set(event["room"])
                self.chat.configure(state="normal")
                self.chat.delete("1.0", "end")
                for item in event["messages"]:
                    self._append_message(item["sent_at"], item["username"], item["text"])
                self.chat.configure(state="disabled")
            elif event_type == "message" and event.get("room") == self.room.get():
                self.chat.configure(state="normal")
                self._append_message(event["sent_at"], event["username"], event["text"])
                self.chat.configure(state="disabled")
                if event["username"] != self.username.get() and not self.focus_displayof():
                    self.bell()
            elif event_type == "system":
                self.chat.configure(state="normal")
                self.chat.insert("end", f"\n[{event.get('sent_at', '')}] {event['text']}\n")
                self.chat.configure(state="disabled")
            elif event_type == "error":
                messagebox.showerror("Chat", event["text"])
            elif event_type == "disconnected":
                if self.sock:
                    messagebox.showinfo("Chat", "Connection to the server closed.")
                    self._close_socket()
        self.after(100, self._process_events)

    def _open_chat(self) -> None:
        self.login_frame.destroy()
        frame = ttk.Frame(self, padding=12)
        frame.pack(fill="both", expand=True)
        controls = ttk.Frame(frame)
        controls.pack(fill="x", pady=(0, 8))
        ttk.Label(controls, text=f"Signed in as {self.username.get()}").pack(side="left")
        ttk.Entry(controls, textvariable=self.room, width=20).pack(side="right")
        ttk.Button(controls, text="Join / create room", command=self._join_room).pack(side="right", padx=6)
        self.chat = tk.Text(frame, state="disabled", wrap="word")
        self.chat.pack(fill="both", expand=True)
        send_row = ttk.Frame(frame)
        send_row.pack(fill="x", pady=(8, 0))
        self.message = tk.StringVar()
        entry = ttk.Entry(send_row, textvariable=self.message)
        entry.pack(side="left", fill="x", expand=True)
        entry.bind("<Return>", lambda _event: self._send_message())
        ttk.Button(send_row, text="Send", command=self._send_message).pack(side="right", padx=(8, 0))
        self._join_room()

    def _join_room(self) -> None:
        try:
            self._send({"action": "join", "room": self.room.get().strip()})
        except OSError as exc:
            messagebox.showerror("Send failed", str(exc))

    def _send_message(self) -> None:
        text = self.message.get().strip()
        if not text:
            return
        for shortcode, symbol in EMOJI.items():
            text = text.replace(shortcode, symbol)
        try:
            self._send({"action": "message", "room": self.room.get().strip(), "text": text})
            self.message.set("")
        except OSError as exc:
            messagebox.showerror("Send failed", str(exc))

    def _append_message(self, sent_at: str, username: str, text: str) -> None:
        try:
            time_label = datetime.fromisoformat(sent_at).astimezone().strftime("%H:%M")
        except ValueError:
            time_label = sent_at
        self.chat.insert("end", f"[{time_label}] {username}: {text}\n")
        self.chat.see("end")

    def _close_socket(self) -> None:
        sock, self.sock = self.sock, None
        if sock:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            sock.close()

    def _close(self) -> None:
        self._close_socket()
        self.destroy()


if __name__ == "__main__":
    import argparse

    argparse.ArgumentParser(description=__doc__).parse_args()
    ChatClient().mainloop()
