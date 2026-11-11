"""Privacy-conscious voice assistant with text fallback and opt-in integrations."""

from __future__ import annotations

import json
import os
import re
import smtplib
import threading
import time
import webbrowser
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from urllib.parse import quote

try:
    import requests
except ImportError:
    requests = None

CONFIG = Path(__file__).with_name("commands.json")
DEFAULT_COMMANDS = {
    "help": "Say hello, ask for the time or date, search the web, set a reminder, or ask for weather.",
    "hello": "Hello! How can I help?",
}


def load_commands() -> dict[str, str]:
    if not CONFIG.exists():
        CONFIG.write_text(json.dumps(DEFAULT_COMMANDS, indent=2), encoding="utf-8")
    try:
        commands = json.loads(CONFIG.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Could not read {CONFIG.name}: {exc}") from exc
    if not isinstance(commands, dict) or not all(
        isinstance(k, str) and isinstance(v, str) for k, v in commands.items()
    ):
        raise ValueError("commands.json must contain a JSON object of string responses.")
    return {k.casefold(): v for k, v in commands.items()}


class Assistant:
    def __init__(self) -> None:
        self.commands = load_commands()
        self.speaker = None
        try:
            import pyttsx3

            self.speaker = pyttsx3.init()
        except (ImportError, RuntimeError):
            pass

    def say(self, text: str) -> None:
        print(f"Assistant: {text}")
        if self.speaker:
            self.speaker.say(text)
            self.speaker.runAndWait()

    def handle(self, utterance: str) -> bool:
        text = utterance.strip()
        normalized = text.casefold()
        if not text:
            self.say("I didn't catch that. Please try again.")
            return True
        for trigger, response in self.commands.items():
            if normalized == trigger or normalized.startswith(trigger + " "):
                self.say(response)
                return True
        if normalized in {"quit", "exit", "goodbye", "stop assistant"}:
            self.say("Goodbye.")
            return False
        if "time" in normalized:
            self.say(datetime.now().strftime("It is %I:%M %p."))
        elif "date" in normalized or "day is it" in normalized:
            self.say(datetime.now().strftime("Today is %A, %B %d, %Y."))
        elif normalized.startswith(("search ", "google ")):
            query = re.sub(r"^(search|google)\s+(for\s+)?", "", text, flags=re.I).strip()
            if query:
                webbrowser.open("https://www.google.com/search?q=" + quote(query))
                self.say(f"Searching the web for {query}.")
            else:
                self.say("Tell me what you would like to search for.")
        elif normalized.startswith("remind me in "):
            match = re.match(r"remind me in (\d+)\s*(seconds?|minutes?|hours?)\s*(?:to\s+)?(.+)", normalized)
            if not match:
                self.say("Use: remind me in 5 minutes to take a break.")
            else:
                amount, unit, reminder = match.groups()
                seconds = int(amount) * (3600 if unit.startswith("hour") else 60 if unit.startswith("minute") else 1)
                if seconds > 7 * 24 * 3600:
                    self.say("Please set a reminder no more than seven days ahead.")
                else:
                    threading.Timer(seconds, self.say, args=(f"Reminder: {reminder}",)).start()
                    self.say(f"Reminder set for {amount} {unit}.")
        elif normalized.startswith("weather in "):
            city = text[len("weather in "):].strip()
            self.weather(city)
        elif normalized.startswith("ask "):
            self.answer_question(text[4:].strip())
        elif normalized.startswith("email "):
            self.send_email(text[6:].strip())
        else:
            self.say("I didn't understand that. Say help to hear example commands.")
        return True

    def weather(self, city: str) -> None:
        key = os.getenv("OPENWEATHER_API_KEY")
        if not key:
            self.say("Weather needs an OPENWEATHER_API_KEY environment variable.")
            return
        if not requests:
            self.say("Install the requests package to use live weather.")
            return
        try:
            response = requests.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={"q": city, "appid": key, "units": "metric"},
                timeout=8,
            )
            response.raise_for_status()
            data = response.json()
            self.say(f"{city}: {data['weather'][0]['description']}, {data['main']['temp']:.1f} degrees Celsius.")
        except (requests.RequestException, KeyError, ValueError) as exc:
            self.say(f"Weather is unavailable: {exc}")

    def answer_question(self, question: str) -> None:
        if not requests or not question:
            self.say("Ask a non-empty question, and install requests for knowledge lookup.")
            return
        try:
            response = requests.get(
                "https://en.wikipedia.org/api/rest_v1/page/summary/" + quote(question.replace(" ", "_")),
                timeout=8,
                headers={"User-Agent": "OasisInternshipAssistant/1.0"},
            )
            response.raise_for_status()
            self.say(response.json().get("extract", "I could not find a summary for that topic.")[:700])
        except (requests.RequestException, ValueError) as exc:
            self.say(f"Knowledge lookup is unavailable: {exc}")

    def send_email(self, instruction: str) -> None:
        """Send only after explicit confirmation; credentials are read from environment."""
        match = re.fullmatch(r"to\s+(\S+@\S+)\s+subject\s+(.+?)\s+body\s+(.+)", instruction, re.I)
        if not match:
            self.say("Use: email to name@example.com subject Hello body Message text.")
            return
        recipient, subject, body = match.groups()
        if input(f"Send this email to {recipient}? Type SEND to confirm: ").strip() != "SEND":
            self.say("Email cancelled.")
            return
        required = ("SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD", "SMTP_FROM")
        missing = [name for name in required if not os.getenv(name)]
        if missing:
            self.say("Email is not configured. Missing: " + ", ".join(missing))
            return
        message = EmailMessage()
        message["From"], message["To"], message["Subject"] = os.environ["SMTP_FROM"], recipient, subject
        message.set_content(body)
        try:
            with smtplib.SMTP_SSL(os.environ["SMTP_HOST"], int(os.environ["SMTP_PORT"]), timeout=10) as server:
                server.login(os.environ["SMTP_USERNAME"], os.environ["SMTP_PASSWORD"])
                server.send_message(message)
            self.say("Email sent.")
        except (OSError, smtplib.SMTPException, ValueError) as exc:
            self.say(f"Email could not be sent: {exc}")


def listen() -> str | None:
    try:
        import speech_recognition as sr
    except ImportError:
        return None
    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            print("Listening... (Ctrl+C to cancel)")
            recognizer.adjust_for_ambient_noise(source, duration=0.4)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=12)
        return recognizer.recognize_google(audio)
    except (OSError, AttributeError, sr.WaitTimeoutError, sr.UnknownValueError, sr.RequestError) as exc:
        print(f"Voice input unavailable or unclear ({exc}). Use text input instead.")
        return None


def main() -> None:
    assistant = Assistant()
    assistant.say("Assistant ready. Type a command, or enter /voice to use the microphone.")
    while True:
        try:
            raw = input("You: ").strip()
            utterance = listen() if raw == "/voice" else raw
            if not assistant.handle(utterance or ""):
                break
        except (EOFError, KeyboardInterrupt):
            print()
            assistant.say("Goodbye.")
            break
        time.sleep(0.05)


if __name__ == "__main__":
    main()
