"""OpenWeatherMap desktop client with current conditions and 5-day forecast."""

from __future__ import annotations

import os
import threading
import tkinter as tk
from io import BytesIO
from datetime import datetime
from tkinter import ttk

import requests

BASE_URL = "https://api.openweathermap.org/data/2.5"


class WeatherApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Weather")
        self.geometry("620x650")
        self.minsize(480, 520)
        self.units = "metric"
        self.city = tk.StringVar()
        self.status = tk.StringVar(value="Enter a city to see current weather and forecast.")
        self._build_ui()

    def _build_ui(self) -> None:
        frame = ttk.Frame(self, padding=18)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Local Weather", font=("Segoe UI", 22, "bold")).pack(anchor="w")
        controls = ttk.Frame(frame)
        controls.pack(fill="x", pady=12)
        entry = ttk.Entry(controls, textvariable=self.city)
        entry.pack(side="left", fill="x", expand=True)
        entry.bind("<Return>", lambda _event: self.fetch())
        ttk.Button(controls, text="Get weather", command=self.fetch).pack(side="left", padx=8)
        ttk.Button(controls, text="°C / °F", command=self.toggle_units).pack(side="left")
        self.current = ttk.Label(frame, text="", font=("Segoe UI", 14), justify="left")
        self.current.pack(anchor="w", pady=6)
        self.icon_display = ttk.Label(frame, text="")
        self.icon_display.pack(anchor="w")
        self.icon_link = ttk.Label(frame, text="", foreground="#0969da")
        self.icon_link.pack(anchor="w")
        self.icon_link.bind("<Button-1>", self.open_icon)
        ttk.Label(frame, text="Next 6 hours", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(16, 3))
        self.hourly = tk.Listbox(frame, height=6)
        self.hourly.pack(fill="x")
        ttk.Label(frame, text="5-day outlook", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(12, 3))
        self.daily = tk.Listbox(frame, height=6)
        self.daily.pack(fill="both", expand=True)
        ttk.Label(frame, textvariable=self.status, wraplength=560).pack(anchor="w", pady=(8, 0))

    def toggle_units(self) -> None:
        self.units = "imperial" if self.units == "metric" else "metric"
        if self.city.get().strip():
            self.fetch()
        else:
            self.status.set(f"Units: {'Fahrenheit' if self.units == 'imperial' else 'Celsius'}.")

    def fetch(self) -> None:
        city = self.city.get().strip()
        if not city:
            self.status.set("Enter a city name.")
            return
        key = os.getenv("OPENWEATHER_API_KEY")
        if not key:
            self.status.set("Set the OPENWEATHER_API_KEY environment variable, then try again.")
            return
        self.status.set("Loading weather…")
        threading.Thread(target=self._load_weather, args=(city, key, self.units), daemon=True).start()

    def _load_weather(self, city: str, key: str, units: str) -> None:
        try:
            params = {"q": city, "appid": key, "units": units}
            current_response = requests.get(f"{BASE_URL}/weather", params=params, timeout=10)
            current_response.raise_for_status()
            forecast_response = requests.get(f"{BASE_URL}/forecast", params=params, timeout=10)
            forecast_response.raise_for_status()
            self.after(0, self._render_weather, city, units, current_response.json(), forecast_response.json())
        except requests.HTTPError as exc:
            message = "City not found." if exc.response is not None and exc.response.status_code == 404 else "Weather service rejected the request. Check the API key and quota."
            self.after(0, self.status.set, message)
        except requests.RequestException as exc:
            self.after(0, self.status.set, f"Network error: {exc}")
        except (ValueError, KeyError, TypeError) as exc:
            self.after(0, self.status.set, f"Unexpected weather response: {exc}")

    def _render_weather(self, city: str, units: str, current: dict, forecast: dict) -> None:
        suffix = "°F" if units == "imperial" else "°C"
        wind_suffix = "mph" if units == "imperial" else "m/s"
        weather = current["weather"][0]
        self.current.configure(
            text=f"{current['name']}, {current['sys']['country']}\n"
            f"{weather['description'].capitalize()} · {current['main']['temp']:.1f}{suffix}\n"
            f"Feels like {current['main']['feels_like']:.1f}{suffix} · "
            f"Humidity {current['main']['humidity']}% · Wind {current['wind']['speed']} {wind_suffix}"
        )
        self.icon_code = weather.get("icon", "")
        self.icon_link.configure(text=f"Weather icon: openweathermap.org/img/wn/{self.icon_code}@2x.png")
        if self.icon_code:
            threading.Thread(target=self._load_icon, args=(self.icon_code,), daemon=True).start()
        forecast_items = forecast.get("list", [])
        self.hourly.delete(0, "end")
        for item in forecast_items[:2]:
            time_label = datetime.fromtimestamp(item["dt"]).strftime("%a %I:%M %p")
            self.hourly.insert("end", f"{time_label}: {item['main']['temp']:.1f}{suffix}, {item['weather'][0]['description']}")
        by_day: dict[str, list[dict]] = {}
        for item in forecast_items:
            day = datetime.fromtimestamp(item["dt"]).strftime("%a, %b %d")
            by_day.setdefault(day, []).append(item)
        self.daily.delete(0, "end")
        for day, entries in list(by_day.items())[:5]:
            average = sum(item["main"]["temp"] for item in entries) / len(entries)
            descriptions = max(
                (item["weather"][0]["description"] for item in entries),
                key=lambda text: sum(x["weather"][0]["description"] == text for x in entries),
            )
            self.daily.insert("end", f"{day}: avg {average:.1f}{suffix}, {descriptions}")
        self.status.set(f"Updated for {city}. Forecasts use the provider's 3-hour data points.")

    def _load_icon(self, code: str) -> None:
        try:
            response = requests.get(f"https://openweathermap.org/img/wn/{code}@2x.png", timeout=8)
            response.raise_for_status()
            self.after(0, self._show_icon, response.content)
        except requests.RequestException as exc:
            self.after(0, self.status.set, f"Weather updated; condition icon could not be loaded: {exc}")

    def _show_icon(self, content: bytes) -> None:
        try:
            from PIL import Image, ImageTk

            with Image.open(BytesIO(content)) as source:
                image = ImageTk.PhotoImage(source.convert("RGBA").resize((96, 96)))
            self.weather_icon = image
            self.icon_display.configure(image=image, text="")
        except (ImportError, OSError) as exc:
            self.status.set(f"Weather updated; icon could not be displayed: {exc}")

    def open_icon(self, _event: tk.Event) -> None:
        import webbrowser

        if getattr(self, "icon_code", ""):
            webbrowser.open(f"https://openweathermap.org/img/wn/{self.icon_code}@2x.png")


if __name__ == "__main__":
    WeatherApp().mainloop()
