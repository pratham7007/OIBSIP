"""Tkinter BMI tracker with named users, SQLite history, and trend chart."""

from __future__ import annotations

import sqlite3
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk

DB_PATH = Path(__file__).with_name("bmi_history.sqlite3")


def category(bmi: float) -> tuple[str, str]:
    if bmi < 18.5:
        return "Underweight", "#2878b5"
    if bmi < 25:
        return "Normal", "#238636"
    if bmi < 30:
        return "Overweight", "#d29922"
    return "Obese", "#cf222e"


class BmiApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("BMI Tracker")
        self.geometry("520x440")
        self.resizable(False, False)
        self._create_database()
        self._build_ui()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(DB_PATH, timeout=5)

    def _create_database(self) -> None:
        try:
            with self._connect() as connection:
                connection.execute(
                    """CREATE TABLE IF NOT EXISTS bmi_records (
                        id INTEGER PRIMARY KEY,
                        user TEXT NOT NULL,
                        weight_kg REAL NOT NULL,
                        height_m REAL NOT NULL,
                        bmi REAL NOT NULL,
                        recorded_at TEXT NOT NULL
                    )"""
                )
        except sqlite3.Error as exc:
            messagebox.showerror("Database error", f"Could not initialize BMI history: {exc}")
            raise

    def _build_ui(self) -> None:
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="BMI Tracker", font=("Segoe UI", 22, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 15))
        self.user = tk.StringVar()
        self.weight = tk.StringVar()
        self.height = tk.StringVar()
        for row, label, variable in (
            (1, "Name", self.user),
            (2, "Weight (kg)", self.weight),
            (3, "Height (m)", self.height),
        ):
            ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", pady=6)
            ttk.Entry(frame, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=6)
        frame.columnconfigure(1, weight=1)
        ttk.Button(frame, text="Calculate and save", command=self.calculate).grid(row=4, column=0, columnspan=2, sticky="ew", pady=12)
        self.result = ttk.Label(frame, text="Enter your details to calculate BMI.", font=("Segoe UI", 13))
        self.result.grid(row=5, column=0, columnspan=2, sticky="w", pady=8)
        ttk.Button(frame, text="Show my BMI trend", command=self.show_trend).grid(row=6, column=0, sticky="ew", pady=10)
        ttk.Button(frame, text="View history", command=self.show_history).grid(row=6, column=1, sticky="ew", padx=(8, 0), pady=10)
        ttk.Label(frame, text="BMI is a screening measure, not a medical diagnosis.", wraplength=460).grid(row=7, column=0, columnspan=2, sticky="w", pady=10)

    def calculate(self) -> None:
        name = self.user.get().strip()
        try:
            weight, height = float(self.weight.get()), float(self.height.get())
            if not name or not (0 < weight <= 500) or not (0 < height <= 3):
                raise ValueError
        except ValueError:
            messagebox.showerror("Check your entries", "Enter a name, weight in (0, 500] kg, and height in (0, 3] m.")
            return
        bmi = weight / height**2
        label, color = category(bmi)
        self.result.configure(text=f"BMI: {bmi:.2f} — {label}", foreground=color)
        try:
            with self._connect() as connection:
                connection.execute(
                    "INSERT INTO bmi_records (user, weight_kg, height_m, bmi, recorded_at) VALUES (?, ?, ?, ?, ?)",
                    (name, weight, height, bmi, datetime.now().isoformat(timespec="seconds")),
                )
        except sqlite3.Error as exc:
            messagebox.showerror("Save failed", f"BMI was calculated but history could not be saved: {exc}")

    def _records(self) -> list[tuple[str, float]]:
        name = self.user.get().strip()
        if not name:
            messagebox.showinfo("Name required", "Enter the same name used when saving records.")
            return []
        try:
            with self._connect() as connection:
                return connection.execute(
                    "SELECT recorded_at, bmi FROM bmi_records WHERE user = ? ORDER BY recorded_at",
                    (name,),
                ).fetchall()
        except sqlite3.Error as exc:
            messagebox.showerror("Database error", f"Could not read BMI history: {exc}")
            return []

    def show_history(self) -> None:
        records = self._records()
        if not records:
            messagebox.showinfo("No history", "No records found for this name.")
            return
        window = tk.Toplevel(self)
        window.title("BMI History")
        box = tk.Text(window, width=48, height=14)
        box.pack(padx=12, pady=12)
        box.insert("end", "\n".join(f"{date}: BMI {bmi:.2f} ({category(bmi)[0]})" for date, bmi in records))
        box.configure(state="disabled")

    def show_trend(self) -> None:
        records = self._records()
        if len(records) < 2:
            messagebox.showinfo("Not enough data", "Save at least two measurements to see a trend.")
            return
        try:
            import matplotlib.dates as mdates
            import matplotlib.pyplot as plt
        except ImportError:
            messagebox.showerror("Chart unavailable", "Install matplotlib with: python -m pip install matplotlib")
            return
        dates = [datetime.fromisoformat(date) for date, _ in records]
        values = [bmi for _, bmi in records]
        figure, axis = plt.subplots(figsize=(8, 4))
        axis.plot(dates, values, marker="o", color="#176b87")
        axis.set(title=f"BMI trend for {self.user.get().strip()}", ylabel="BMI")
        axis.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        figure.autofmt_xdate()
        axis.grid(alpha=0.25)
        plt.show()


if __name__ == "__main__":
    import argparse

    argparse.ArgumentParser(description=__doc__).parse_args()
    BmiApp().mainloop()
