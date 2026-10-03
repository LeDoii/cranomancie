"""Cranomancie: stream-friendly GUI to read a bald skull (Oswald Bald).

Run: python app.py
Single resizable window (opens maximized) with two views: Lecture and Collection.
Viktor enters the /roll results; each axis is read as soon as its rolls are valid.
"""
import ctypes
import random
import sys
import tkinter as tk
from tkinter import font as tkfont

from PIL import ImageTk

import reading
import updater
from cards import FONTS, render_card
from collection import CARD_RATIO, CollectionView

BG = "#1B1A18"
PANEL = "#26241F"
TEXT = "#E7E0D1"
MUTED = "#948B78"
WARM = "#D9803A"
ALERT = "#E0705A"

# Font sizes at scale 1.0 (window around 1500x1000); everything scales with the window.
BASE_SIZES = {"title": 40, "title_s": 20, "body": 17, "small": 13, "label": 12, "label_s": 10, "entry": 16, "emoji": 12}


def load_private_fonts() -> None:
    """Register the project fonts for this process only (Windows)."""
    if sys.platform != "win32":
        return
    for name in ("Italiana-Regular.ttf", "CrimsonPro.ttf", "GeistMono.ttf"):
        ctypes.windll.gdi32.AddFontResourceExW(str(FONTS / name), 0x10, 0)


def pick_family(candidates: list[str], fallback: str) -> str:
    available = set(tkfont.families())
    return next((c for c in candidates if c in available), fallback)


class NumberField(tk.Frame):
    """Roll entry with a double arrow (click to step), arrow keys / wheel and a dice button."""

    def __init__(self, parent: tk.Widget, app: "App", var: tk.StringVar, caption: str, lo: int, hi: int):
        super().__init__(parent, bg=PANEL)
        self.app, self.var, self.lo, self.hi = app, var, lo, hi
        f = app.fonts
        tk.Label(self, text=caption, font=f["label_s"], bg=PANEL, fg=MUTED).pack()
        row = tk.Frame(self, bg=PANEL)
        row.pack()
        self.entry = tk.Entry(row, textvariable=var, width=4, justify="center", font=f["entry"],
                              bg=BG, fg=TEXT, insertbackground=TEXT, relief="flat",
                              highlightthickness=1, highlightbackground=MUTED, highlightcolor=WARM)
        self.entry.pack(side="left")
        arrows = tk.Frame(row, bg=PANEL)
        arrows.pack(side="left", padx=(2, 0))
        for symbol, step in (("▲", 1), ("▼", -1)):
            tk.Button(arrows, text=symbol, font=f["label_s"], bg=BG, fg=TEXT, activebackground=WARM,
                      relief="flat", padx=3, pady=0, bd=0,
                      command=lambda s=step: self.step(s)).pack(fill="x")
        tk.Button(row, text="🎲", font=f["emoji"], bg=PANEL, fg=TEXT, activebackground=WARM,
                  relief="flat", bd=0, padx=4, command=self.roll).pack(side="left", padx=(4, 0))
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


class AxisPanel:
    """Inputs, card and reading of one axis."""

    def __init__(self, app: "App", parent: tk.Widget, index: int):
        self.app, self.index = app, index
        axis = reading.AXES[index]
        self.frame = tk.Frame(parent, bg=PANEL, padx=14, pady=10)
        f = app.fonts
        tk.Label(self.frame, text=axis["label"].upper(), font=f["label"], bg=PANEL, fg=WARM).pack()
        tk.Label(self.frame, text=axis["nom"], font=f["title_s"], bg=PANEL, fg=TEXT).pack()
        self.question = tk.Label(self.frame, text=axis["question"], font=f["small"], bg=PANEL,
                                 fg=MUTED, wraplength=300, height=2)
        self.question.pack(pady=(0, 6))

        self.inputs = tk.Frame(self.frame, bg=PANEL)
        self.inputs.pack()
        self.vars = {k: tk.StringVar() for k in ("a", "card", "sense", "confirm")}
        self.entries = {}
        for key, caption, lo, hi in (("a", "Jet (1-44)", 1, 44), ("card", "Carte (1-20)", 1, 20),
                                     ("sense", "Sens (1-6)", 1, 6), ("confirm", "Confirm. (1-6)", 1, 6)):
            field = NumberField(self.inputs, app, self.vars[key], caption, lo, hi)
            self.entries[key] = (field, field.entry)

        self.card_label = tk.Label(self.frame, bg=PANEL)
        self.card_label.pack(pady=8)
        self.caption = tk.Label(self.frame, text="", font=f["title_s"], bg=PANEL, fg=TEXT)
        self.caption.pack()
        self.phrase = tk.Label(self.frame, text="", font=f["body"], bg=PANEL, fg=TEXT,
                               wraplength=330, justify="left")
        self.phrase.pack(pady=6, fill="x")
        btns = tk.Frame(self.frame, bg=PANEL)
        btns.pack()
        self.copy_btn = tk.Button(btns, text="Copier la phrase", font=f["label_s"], bg=BG, fg=TEXT,
                                  activebackground=WARM, relief="flat", padx=10, pady=4,
                                  command=self.copy, state="disabled")
        self.copy_btn.pack(side="left", padx=4)
        tk.Button(btns, text="Aléatoire", font=f["label_s"], bg=BG, fg=TEXT, activebackground=WARM,
                  relief="flat", padx=10, pady=4,
                  command=lambda: (self.randomize(app.mode.get()), app.refresh())).pack(side="left", padx=4)
        self.error = tk.Label(self.frame, text="", font=f["small"], bg=PANEL, fg=ALERT, wraplength=320)
        self.error.pack(pady=(4, 0))
        self.result = None
        self._photo = None
        self.frame.bind("<Configure>", self._on_resize)

    def _on_resize(self, event: tk.Event) -> None:
        wrap = max(180, event.width - 40)
        self.phrase.config(wraplength=wrap)
        self.question.config(wraplength=wrap)
        self.error.config(wraplength=wrap)

    def randomize(self, mode: str) -> None:
        """Fill the entries with random rolls valid for the current mode."""
        for var in self.vars.values():
            var.set("")
        if mode == reading.MODE_A:
            self.vars["a"].set(str(random.randint(1, 44)))
        else:
            card = random.randint(1, 20)
            self.vars["card"].set(str(card))
            self.vars["sense"].set(str(random.randint(1, 6)))
            if reading.needs_confirmation(str(card)):
                self.vars["confirm"].set(str(random.randint(1, 6)))

    def layout_inputs(self, mode: str) -> None:
        for cell, _ in self.entries.values():
            cell.pack_forget()
        keys = ["a"] if mode == reading.MODE_A else ["card", "sense"]
        if mode == reading.MODE_B and reading.needs_confirmation(self.vars["card"].get()):
            keys.append("confirm")
        for key in keys:
            self.entries[key][0].pack(side="left", padx=5)

    def update(self, mode: str) -> None:
        self.layout_inputs(mode)
        v = {k: var.get().strip() for k, var in self.vars.items()}
        self.error.config(text="")
        try:
            if mode == reading.MODE_A:
                if not v["a"]:
                    return self.clear()
                idx, rev = reading.resolve_a(v["a"])
            else:
                if not (v["card"] and v["sense"]):
                    return self.clear()
                if reading.needs_confirmation(v["card"]) and not v["confirm"]:
                    return self.clear("Jet de confirmation requis (1 ou 20).")
                idx, rev = reading.resolve_b(v["card"], v["sense"], v["confirm"])
        except ValueError as exc:
            return self.clear(str(exc))
        self.result = reading.read_axis(self.index, idx, rev)
        arcane = self.result["arcane"]
        sense_label = "à l'envers" if rev else "à l'endroit"
        self.caption.config(text=f"{arcane['name']} — {sense_label}")
        self.phrase.config(text=self.display_text())
        self.copy_btn.config(state="normal")
        self.render_card()

    def display_text(self) -> str:
        """Spoken sentence, or the /me preview exactly as the chat will show it."""
        if self.app.me_prefix.get():
            return "l'individu " + self.result["me_phrase"]
        return self.result["phrase"]

    def render_card(self) -> None:
        if not self.result:
            return
        self._photo = ImageTk.PhotoImage(
            render_card(self.result["arcane"], self.result["reversed"], self.app.card_size))
        self.card_label.config(image=self._photo)

    def clear(self, message: str = "") -> None:
        self.result = None
        self.card_label.config(image="")
        self._photo = None
        self.caption.config(text="")
        self.phrase.config(text="")
        self.copy_btn.config(state="disabled")
        self.error.config(text=message)

    def copy(self) -> None:
        if self.result:
            self.app.copy_text(self.result["phrase"], self.result["me_phrase"])


class ReadingView(tk.Frame):
    """The three axes and the closing synthesis."""

    def __init__(self, parent: tk.Widget, app: "App") -> None:
        super().__init__(parent, bg=BG)
        f = app.fonts
        foot = tk.Frame(self, bg=PANEL, padx=18, pady=10)
        foot.pack(side="bottom", padx=21, pady=(4, 10), fill="x")
        tk.Label(foot, text="CONCLUSION", font=f["label"], bg=PANEL, fg=WARM).pack(anchor="w")
        self.synthesis = tk.Label(foot, text="", font=f["body"], bg=PANEL, fg=TEXT,
                                  wraplength=1180, justify="left", anchor="w")
        self.synthesis.pack(anchor="w", pady=4, fill="x")
        foot.bind("<Configure>", lambda e: self.synthesis.config(wraplength=max(300, e.width - 40)))
        buttons = tk.Frame(foot, bg=PANEL)
        buttons.pack(anchor="w")
        self.copy_synth = tk.Button(buttons, text="Copier la conclusion", font=f["label_s"], bg=BG, fg=TEXT,
                                    relief="flat", padx=10, pady=4, state="disabled",
                                    command=app.copy_synthesis)
        self.copy_synth.pack(side="left", padx=(0, 8))
        tk.Button(buttons, text="Nouvelle lecture", font=f["label_s"], bg=BG, fg=TEXT, relief="flat",
                  padx=10, pady=4, command=app.reset).pack(side="left")

        cols = tk.Frame(self, bg=BG)
        cols.pack(padx=14, pady=6, fill="both", expand=True)
        cols.grid_rowconfigure(0, weight=1)
        self.panels = []
        for i in range(3):
            panel = AxisPanel(app, cols, i)
            panel.frame.grid(row=0, column=i, padx=7, sticky="nsew")
            cols.grid_columnconfigure(i, weight=1, uniform="axes")
            self.panels.append(panel)


class App:
    def __init__(self) -> None:
        load_private_fonts()
        self.root = tk.Tk()
        self.root.title(f"Cranomancie — Oswald Bald (v{updater.local_version()})")
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
        families = {"title": display, "title_s": display, "body": serif, "small": serif,
                    "label": mono, "label_s": mono, "entry": mono,
                    "emoji": "Segoe UI Emoji"}
        self.fonts = {name: tkfont.Font(root=self.root, family=families[name], size=size,
                                        weight="bold" if name == "label" else "normal")
                      for name, size in BASE_SIZES.items()}
        self.scale = 1.0
        self.card_size = (150, 250)
        f = self.fonts
        meta = reading.DATA["meta"]

        self.update_bar = tk.Frame(self.root, bg=WARM)  # packed only when an update exists
        head = tk.Frame(self.root, bg=BG)
        self.head = head
        head.pack(pady=(10, 2))
        tk.Label(head, text=meta["title"], font=f["title"], bg=BG, fg=TEXT).pack()
        tk.Label(head, text=meta["subtitle"], font=f["small"], bg=BG, fg=MUTED).pack()

        bar = tk.Frame(self.root, bg=BG)
        bar.pack(pady=4)
        self.mode = tk.StringVar(value=reading.MODE_A)
        for value, label in ((reading.MODE_A, "Mode A : 1 jet par axe, /roll 1-44"),
                             (reading.MODE_B, "Mode B : /roll 1-20 puis /roll 1-6")):
            tk.Radiobutton(bar, text=label, value=value, variable=self.mode, font=f["label_s"],
                           bg=BG, fg=TEXT, selectcolor=PANEL, activebackground=BG,
                           activeforeground=WARM, command=self.refresh).pack(side="left", padx=10)
        self.me_prefix = tk.BooleanVar(value=False)
        tk.Checkbutton(bar, text="Format /me (le jeu ajoute « l'individu »)", variable=self.me_prefix,
                       font=f["label_s"], bg=BG, fg=TEXT, selectcolor=PANEL, activebackground=BG,
                       activeforeground=WARM, command=self.refresh).pack(side="left", padx=10)
        tk.Button(bar, text="Tout tirer au hasard", font=f["label_s"], bg=PANEL, fg=TEXT,
                  activebackground=WARM, relief="flat", padx=10, pady=4,
                  command=self.randomize_all).pack(side="left", padx=8)
        self.view_buttons = {}
        for name, label in (("reading", "Lecture"), ("collection", "Collection des cartes")):
            btn = tk.Button(bar, text=label, font=f["label_s"], bg=PANEL, fg=TEXT, activebackground=WARM,
                            relief="flat", padx=10, pady=4, command=lambda n=name: self.show_view(n))
            btn.pack(side="left", padx=4)
            self.view_buttons[name] = btn

        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True)
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=1)
        self.reading_view = ReadingView(body, self)
        self.collection_view = CollectionView(body, self)
        self.views = {"reading": self.reading_view, "collection": self.collection_view}
        for view in self.views.values():
            view.grid(row=0, column=0, sticky="nsew")
        self.panels = self.reading_view.panels
        self.synthesis = self.reading_view.synthesis
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
        """Scale fonts and cards with the window size (debounced)."""
        self._resize_job = None
        w, h = self.root.winfo_width(), self.root.winfo_height()
        self.scale = max(0.65, min(1.6, min(h / 1000, w / 1500)))
        for name, size in BASE_SIZES.items():
            self.fonts[name].configure(size=max(7, int(size * self.scale)))
        card_h = int(max(100, min(0.42 * h - 190, 560)))
        col_w = w / 3 - 70
        card_w = int(min(card_h * CARD_RATIO, col_w))
        self.card_size = (card_w, int(card_w / CARD_RATIO))
        for panel in self.panels:
            panel.render_card()
        self.collection_view.rescale()

    def show_view(self, name: str) -> None:
        self.current_view = name
        self.views[name].tkraise()
        for key, btn in self.view_buttons.items():
            btn.config(bg=WARM if key == name else PANEL, fg=BG if key == name else TEXT)

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
        self.update_btn = tk.Button(self.update_bar, text="Mettre à jour", font=f["label_s"], bg=BG,
                                    fg=TEXT, relief="flat", padx=10, pady=2,
                                    command=lambda: self._run_update(info))
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

        import threading
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

    def copy_synthesis(self) -> None:
        self.copy_text(self.synthesis_spoken, reading.synthesize_me(self.synthesis_spoken))

    def refresh(self) -> None:
        mode = self.mode.get()
        for panel in self.panels:
            panel.update(mode)
        done = [p.result for p in self.panels if p.result]
        if len(done) == 3:
            self.synthesis_spoken = reading.synthesize(done)
            shown = ("l'individu " + reading.synthesize_me(self.synthesis_spoken)
                     if self.me_prefix.get() else self.synthesis_spoken)
            self.synthesis.config(text=shown)
            self.copy_synth.config(state="normal")
        else:
            self.synthesis_spoken = ""
            self.synthesis.config(text="Entrez les jets des trois axes.")
            self.copy_synth.config(state="disabled")

    def randomize_all(self) -> None:
        for panel in self.panels:
            panel.randomize(self.mode.get())
        self.refresh()
        self.show_view("reading")

    def reset(self) -> None:
        for panel in self.panels:
            for var in panel.vars.values():
                var.set("")
        self.refresh()

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    # Launched with pythonw (no console): keep a crash log instead of a silent exit.
    try:
        App().run()
    except Exception:
        import traceback
        from pathlib import Path
        Path(__file__).with_name("crash.log").write_text(traceback.format_exc(), encoding="utf-8")
        raise
