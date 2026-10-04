"""Cranomancie v2: stream-friendly GUI to read a bald skull, palmistry style (Oswald Bald).

Run: python app.py
Viktor enters one /roll 1-20 per axis; each result designates a sign. A manual per-axis
polarity roll (done by the UI: even = favorable, odd = unfavorable) picks its definition.
Single resizable window (opens maximized) with two views: Lecture and Signes.
"""
import ctypes
import random
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import font as tkfont

import reading
import updater
from library import SignsView
from reading_view import AxisPanel, ReadingView
from widgets import ALERT, BG, GOOD, MUTED, PANEL, TEXT, WARM

FONTS = Path(__file__).resolve().parent / "fonts"
# Font sizes at scale 1.0 (window around 1500x1000); everything scales with the window.
BASE_SIZES = {"title": 40, "title_s": 20, "body": 17, "small": 13, "label": 12, "label_s": 10, "entry": 16, "emoji": 12, "big": 30}


def load_private_fonts() -> None:
    """Register the project fonts for this process only (Windows)."""
    if sys.platform != "win32":
        return
    for name in ("Italiana-Regular.ttf", "CrimsonPro.ttf", "GeistMono.ttf"):
        ctypes.windll.gdi32.AddFontResourceExW(str(FONTS / name), 0x10, 0)


def pick_family(candidates: list[str], fallback: str) -> str:
    available = set(tkfont.families())
    return next((c for c in candidates if c in available), fallback)


class App:
    def __init__(self) -> None:
        load_private_fonts()
        self.root = tk.Tk()
        self.root.title(f"CRANOMANTIE 2000 — Oswald Bald (v{updater.local_version()})")
        self.root.configure(bg=BG)
        self.root.minsize(900, 600)
        # Fixed window size: children must not shrink or grow the toplevel when fonts change.
        self.root.pack_propagate(False)
        self.root.geometry("1400x900+60+40")  # size used when the window is restored from maximized
        try:
            self.root.state("zoomed")  # always open maximized (Windows)
        except tk.TclError:
            pass  # non-Windows: stay at the default size

        serif = pick_family(["Crimson Pro"], "Georgia")
        display = pick_family(["Italiana"], serif)
        mono = pick_family(["Geist Mono"], "Consolas")
        families = {"title": display, "title_s": display, "body": serif, "small": serif, "label": mono,
                    "label_s": mono, "entry": mono, "emoji": "Segoe UI Emoji", "big": serif}
        self.fonts = {name: tkfont.Font(root=self.root, family=families[name], size=size,
                                        weight="bold" if name == "label" else "normal")
                      for name, size in BASE_SIZES.items()}
        self.scale = 1.0
        f = self.fonts
        meta = reading.DATA["meta"]

        self.update_bar = tk.Frame(self.root, bg=WARM)  # packed only when an update exists
        head = tk.Frame(self.root, bg=BG)
        self.head = head
        head.pack(pady=(4, 0))
        # Retro arcade title drawn with Pillow (re-rendered when the window scale changes); plain text without it.
        self.title_text = meta["title"]
        self._title_photo = None
        self._title_key = None
        self.title_label = tk.Label(head, text=self.title_text, font=f["title"], bg=BG, fg=TEXT)
        self.title_label.pack()
        tk.Label(head, text=meta["subtitle"], font=f["small"], bg=BG, fg=MUTED).pack(pady=(0, 2))

        bar = tk.Frame(self.root, bg=BG)
        bar.pack(pady=(2, 4))
        self.me_prefix = tk.BooleanVar(value=True)  # /me format by default
        tk.Checkbutton(bar, text="Format /me (le jeu ajoute « l'individu »)", variable=self.me_prefix,
                       font=f["label_s"], bg=BG, fg=TEXT, selectcolor=PANEL, activebackground=BG,
                       activeforeground=WARM, command=self.refresh).pack(side="left", padx=10)
        self.manual_polarity = tk.BooleanVar(value=False)
        tk.Checkbutton(bar, text="Polarité manuelle (jet fait par un autre joueur)", variable=self.manual_polarity,
                       font=f["label_s"], bg=BG, fg=TEXT, selectcolor=PANEL, activebackground=BG,
                       activeforeground=WARM, command=self.on_polarity_mode).pack(side="left", padx=10)
        tk.Button(bar, text="Tout tirer au hasard", font=f["label_s"], bg=PANEL, fg=TEXT, activebackground=WARM,
                  relief="flat", padx=10, pady=4, command=self.randomize_all).pack(side="left", padx=8)
        self.view_buttons = {}
        for name, label in (("reading", "Lecture"), ("signs", "Bibliothèque des signes")):
            btn = tk.Button(bar, text=label, font=f["label_s"], bg=PANEL, fg=TEXT, activebackground=WARM,
                            relief="flat", padx=10, pady=4, command=lambda n=name: self.show_view(n))
            btn.pack(side="left", padx=4)
            self.view_buttons[name] = btn

        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True)
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=1)
        self.reading_view = ReadingView(body, self)
        self.signs_view = SignsView(body, self)
        self.views = {"reading": self.reading_view, "signs": self.signs_view}
        for view in self.views.values():
            view.grid(row=0, column=0, sticky="nsew")
        self.panels = self.reading_view.panels
        self.copy_synth = self.reading_view.copy_synth

        self.synthesis_spoken = ""
        self._resize_job = None
        self.root.bind("<Configure>", self._on_configure)
        self.show_view("reading")
        self.refresh()
        self.root.update_idletasks()
        self.apply_scale()
        self._update_check: dict = {"done": False, "info": None}
        updater.check_async(self._update_check)
        self.root.after(1000, self._poll_update_check)

    # --- layout -----------------------------------------------------------
    def _on_configure(self, event: tk.Event) -> None:
        if event.widget is self.root:
            if self._resize_job:
                self.root.after_cancel(self._resize_job)
            self._resize_job = self.root.after(120, self.apply_scale)

    def apply_scale(self) -> None:
        """Scale fonts with the window size (debounced)."""
        self._resize_job = None
        w, h = self.root.winfo_width(), self.root.winfo_height()
        self.scale = max(0.65, min(1.6, min(h / 1000, w / 1500)))
        for name, size in BASE_SIZES.items():
            self.fonts[name].configure(size=max(7, int(size * self.scale)))
        self.signs_view.rescale()
        self.reading_view.relayout_soon()
        self.update_title()

    def update_title(self) -> None:
        """Pixelated amber title sized with the window; falls back to the plain text label."""
        height = max(60, int(120 * self.scale))
        if self._title_key == height:
            return
        try:
            from PIL import ImageTk
            from title_art import render_title
            image = render_title(self.title_text, height, (0x1B, 0x1A, 0x18))
        except Exception:
            return
        self._title_key = height
        self._title_photo = ImageTk.PhotoImage(image)
        self.title_label.config(image=self._title_photo, text="")

    def show_view(self, name: str) -> None:
        self.current_view = name
        self.views[name].tkraise()
        for key, btn in self.view_buttons.items():
            btn.config(bg=WARM if key == name else PANEL, fg=BG if key == name else TEXT)

    def open_sign(self, axis_index: int, roll: int) -> None:
        self.show_view("signs")
        self.signs_view.open_sign(axis_index, roll)

    # --- updates ----------------------------------------------------------
    def _poll_update_check(self) -> None:
        if not self._update_check["done"]:
            self.root.after(500, self._poll_update_check)
        elif self._update_check["info"]:
            self._show_update(self._update_check["info"])

    def _show_update(self, info: dict) -> None:
        f = self.fonts
        for child in self.update_bar.winfo_children():
            child.destroy()
        self.update_label = tk.Label(
            self.update_bar, bg=WARM, fg=BG, font=f["label_s"],
            text=f"Mise à jour disponible : v{info['version']} (actuelle : v{updater.local_version()})")
        self.update_label.pack(side="left", padx=12, pady=4)
        self.update_btn = tk.Button(self.update_bar, text="Mettre à jour", font=f["label_s"], bg=BG, fg=TEXT,
                                    relief="flat", padx=10, pady=2, command=lambda: self._run_update(info))
        self.update_btn.pack(side="right", padx=12, pady=4)
        self.update_bar.pack(fill="x", before=self.head)

    def _run_update(self, info: dict) -> None:
        self.update_btn.config(state="disabled")
        self.update_label.config(text="Téléchargement et installation en cours…")
        outcome: dict = {"done": False, "error": None}

        def work() -> None:
            try:
                updater.apply_update(info)
            except Exception as exc:  # reported in the bar, the app stays on the current version
                outcome["error"] = str(exc)
            outcome["done"] = True

        def poll() -> None:
            if not outcome["done"]:
                self.root.after(300, poll)
            elif outcome["error"]:
                self.update_label.config(text=f"Échec de la mise à jour : {outcome['error']}")
                self.update_btn.config(state="normal", text="Réessayer")
            else:
                self.update_label.config(text=f"v{info['version']} installée. Redémarrage…")
                self.root.after(800, self._restart)

        threading.Thread(target=work, daemon=True).start()
        poll()

    def _restart(self) -> None:
        updater.restart()
        self.root.destroy()

    # --- actions ----------------------------------------------------------
    def copy_text(self, spoken: str, me: str | None = None) -> None:
        """Copy the spoken sentence, or '/me ...' (the game adds "l'individu") in /me mode."""
        text = "/me " + me if self.me_prefix.get() and me is not None else spoken
        self.root.clipboard_clear()
        self.root.clipboard_append(text)

    def on_polarity_mode(self) -> None:
        """Switching between UI-rolled and manually entered polarity starts every axis' polarity afresh."""
        for panel in self.panels:
            panel.polarity = None
            panel.pol_var.set("")
            panel._show_polarity_input()
        self.refresh()

    def copy_synthesis(self) -> None:
        self.copy_text(self.synthesis_spoken, reading.synthesize_me(self.synthesis_spoken))

    def roll_polarity(self, panel: AxisPanel) -> None:
        """Polarity roll of one axis (button, can be rerolled): 1-20 by the UI, even = favorable."""
        if panel.roll:
            panel.polarity = reading.roll_polarity()
            self.refresh()

    def refresh(self) -> None:
        for panel in self.panels:
            panel.update()
        self.reading_view.relayout_soon()
        done = [p.result for p in self.panels if p.result]
        if len(done) == 3:
            self.synthesis_spoken = reading.synthesize(done)
            self.reading_view.show_items(reading.conclusion_items(done), self.me_prefix.get())
            self.copy_synth.config(state="normal")
        else:
            self.synthesis_spoken = ""
            self.reading_view.show_placeholder("Entrez les trois jets, puis lancez la polarité de chaque axe.")
            self.copy_synth.config(state="disabled")

    def randomize_all(self) -> None:
        """Full random reading: a d20 per axis and every polarity roll."""
        for panel in self.panels:
            panel.randomize_full()
        self.refresh()
        self.show_view("reading")

    def reset(self) -> None:
        for panel in self.panels:
            panel.var.set("")
            panel.polarity = None
        self.refresh()

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    # Launched with pythonw (no console): keep a crash log instead of a silent exit.
    try:
        updater.apply_pending()  # files of a previous update that were locked while the app was running
        App().run()
    except Exception:
        import traceback
        Path(__file__).with_name("crash.log").write_text(traceback.format_exc(), encoding="utf-8")
        raise
