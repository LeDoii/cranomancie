"""Shared colours and small widgets of the Cranomancie v2 GUI."""
import random
import tkinter as tk

BG = "#1B1A18"
PANEL = "#26241F"
TEXT = "#E7E0D1"
MUTED = "#948B78"
WARM = "#D9803A"
ALERT = "#E0705A"
GOOD = "#8DBF6A"


class NumberField(tk.Frame):
    """Roll entry with a double arrow (click to step), arrow keys / wheel and a dice button."""

    def __init__(self, parent: tk.Widget, app, var: tk.StringVar, caption: str, lo: int, hi: int):
        super().__init__(parent, bg=PANEL)
        self.app, self.var, self.lo, self.hi = app, var, lo, hi
        f = app.fonts
        tk.Label(self, text=caption, font=f["label_s"], bg=PANEL, fg=MUTED).pack()
        row = tk.Frame(self, bg=PANEL)
        row.pack()
        self.entry = tk.Entry(row, textvariable=var, width=4, justify="center", font=f["entry"], bg=BG, fg=TEXT,
                              insertbackground=TEXT, relief="flat", highlightthickness=1,
                              highlightbackground=MUTED, highlightcolor=WARM)
        self.entry.pack(side="left")
        arrows = tk.Frame(row, bg=PANEL)
        arrows.pack(side="left", padx=(2, 0))
        for symbol, step in (("▲", 1), ("▼", -1)):
            tk.Button(arrows, text=symbol, font=f["label_s"], bg=BG, fg=TEXT, activebackground=WARM,
                      relief="flat", padx=3, pady=0, bd=0, command=lambda s=step: self.step(s)).pack(fill="x")
        tk.Button(row, text="🎲", font=f["emoji"], bg=PANEL, fg=TEXT, activebackground=WARM, relief="flat",
                  bd=0, padx=4, command=self.roll).pack(side="left", padx=(4, 0))
        for keys, step in (("<Up> <Right>", 1), ("<Down> <Left>", -1)):
            for key in keys.split():
                self.entry.bind(key, lambda _e, s=step: self._key(s))
        self.entry.bind("<MouseWheel>", lambda e: self._key(1 if e.delta > 0 else -1))
        self.entry.bind("<KeyRelease>", lambda _e: app.refresh())

    def _key(self, step: int) -> str:
        self.step(step)
        return "break"  # keep the caret still

    def step(self, delta: int) -> None:
        """+1/-1 within [lo, hi]; an empty or invalid field starts at the matching bound."""
        try:
            value = int(self.var.get().strip())
        except ValueError:
            value = self.lo - 1 if delta > 0 else self.hi + 1
        self.var.set(str(max(self.lo, min(self.hi, value + delta))))
        self.app.refresh()

    def roll(self) -> None:
        self.var.set(str(random.randint(self.lo, self.hi)))
        self.app.refresh()
