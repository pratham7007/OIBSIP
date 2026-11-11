"""Cryptographically secure password generator; passwords are never saved."""

from __future__ import annotations

import secrets
import string
import tkinter as tk
from tkinter import messagebox, ttk

import pyperclip


def generate_password(length: int, groups: list[str], exclude_ambiguous: bool = True) -> str:
    if length < 8 or length > 256:
        raise ValueError("Choose a length from 8 to 256.")
    if exclude_ambiguous:
        groups = ["".join(c for c in group if c not in "0O1lI") for group in groups]
    groups = [group for group in groups if group]
    if len(groups) < 2:
        raise ValueError("Select at least two character types.")
    alphabet = "".join(groups)
    if not alphabet:
        raise ValueError("No characters remain after excluding ambiguous symbols.")
    if length < len(groups):
        raise ValueError("Length must be at least the number of selected character types.")
    password = [secrets.choice(group) for group in groups]
    password.extend(secrets.choice(alphabet) for _ in range(length - len(password)))
    secrets.SystemRandom().shuffle(password)
    return "".join(password)


class PasswordApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Secure Password Generator")
        self.geometry("520x570")
        self.minsize(480, 520)
        self.length = tk.IntVar(value=20)
        self.ambiguous = tk.BooleanVar(value=True)
        self.history: list[str] = []
        self.options = {
            "Uppercase (A-Z)": tk.BooleanVar(value=True),
            "Lowercase (a-z)": tk.BooleanVar(value=True),
            "Digits (0-9)": tk.BooleanVar(value=True),
            "Symbols": tk.BooleanVar(value=True),
        }
        self._build_ui()

    def _build_ui(self) -> None:
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Secure Password Generator", font=("Segoe UI", 18, "bold")).pack(anchor="w", pady=(0, 12))
        row = ttk.Frame(frame)
        row.pack(fill="x")
        ttk.Label(row, text="Length (8–256)").pack(side="left")
        ttk.Spinbox(row, from_=8, to=256, textvariable=self.length, width=7).pack(side="right")
        for label, variable in self.options.items():
            ttk.Checkbutton(frame, text=label, variable=variable).pack(anchor="w", pady=2)
        ttk.Checkbutton(frame, text="Exclude ambiguous characters (0, O, 1, l, I)", variable=self.ambiguous).pack(anchor="w", pady=4)
        ttk.Button(frame, text="Generate", command=self.generate).pack(fill="x", pady=8)
        output = ttk.Frame(frame)
        output.pack(fill="x")
        self.output = tk.StringVar()
        ttk.Entry(output, textvariable=self.output, font=("Consolas", 12), state="readonly").pack(side="left", fill="x", expand=True)
        ttk.Button(output, text="Copy", command=self.copy).pack(side="right", padx=(8, 0))
        strength_row = ttk.Frame(frame)
        strength_row.pack(fill="x", pady=(8, 0))
        self.strength = tk.StringVar(value="Strength: not generated")
        ttk.Label(strength_row, textvariable=self.strength).pack(side="left")
        self.strength_bar = ttk.Progressbar(strength_row, maximum=3, value=0, length=180)
        self.strength_bar.pack(side="right")
        ttk.Label(frame, text="Recent passwords (this session only)", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(12, 4))
        self.history_list = tk.Listbox(frame, height=5, font=("Consolas", 10), exportselection=False)
        self.history_list.pack(fill="x")
        ttk.Button(frame, text="Clear history", command=self.clear_history).pack(anchor="e", pady=(4, 0))
        ttk.Label(frame, text="Generation copies to the system clipboard. Clear clipboard and history when no longer needed.",
                  wraplength=470).pack(anchor="w", pady=10)

    def generate(self) -> None:
        groups = []
        if self.options["Uppercase (A-Z)"].get():
            groups.append(string.ascii_uppercase)
        if self.options["Lowercase (a-z)"].get():
            groups.append(string.ascii_lowercase)
        if self.options["Digits (0-9)"].get():
            groups.append(string.digits)
        if self.options["Symbols"].get():
            groups.append("!@#$%^&*()-_=+[]{}:,.?")
        try:
            password = generate_password(self.length.get(), groups, self.ambiguous.get())
            self.output.set(password)
            self.history.insert(0, password)
            del self.history[5:]
            self._render_history()
            diversity = len([group for group in groups if group])
            level = 1 if len(password) < 12 or diversity < 3 else 2 if len(password) < 16 or diversity < 4 else 3
            labels = {1: "Weak", 2: "Medium", 3: "Strong"}
            self.strength.set(f"Strength: {labels[level]} (length and character-set heuristic)")
            self.strength_bar.configure(value=level)
            try:
                pyperclip.copy(password)
            except pyperclip.PyperclipException as exc:
                self.strength.set(f"{labels[level]}; clipboard unavailable: {exc}")
        except (ValueError, tk.TclError) as exc:
            messagebox.showerror("Cannot generate password", str(exc))

    def copy(self) -> None:
        value = self.output.get()
        if not value:
            messagebox.showinfo("Nothing to copy", "Generate a password first.")
            return
        try:
            pyperclip.copy(value)
        except pyperclip.PyperclipException as exc:
            messagebox.showerror("Clipboard unavailable", f"Could not copy the password: {exc}")
            return
        messagebox.showinfo("Copied", "Password copied to the clipboard. Clear it when no longer needed.")

    def _render_history(self) -> None:
        self.history_list.delete(0, "end")
        for password in self.history:
            self.history_list.insert("end", password)

    def clear_history(self) -> None:
        self.history.clear()
        self._render_history()


if __name__ == "__main__":
    PasswordApp().mainloop()
