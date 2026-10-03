"""Library of the 60 signs (search + side drawer) for the Cranomancie v2 GUI."""
import tkinter as tk
import unicodedata

import reading

BG = "#1B1A18"
PANEL = "#26241F"
TEXT = "#E7E0D1"
MUTED = "#948B78"
WARM = "#D9803A"
GOOD = "#8DBF6A"
BAD = "#E0705A"


def _norm(text: str) -> str:
    """Lowercase without accents, for forgiving search."""
    return "".join(c for c in unicodedata.normalize("NFD", text.lower()) if unicodedata.category(c) != "Mn")


def matches(axis: dict, sign: dict, query: str) -> bool:
    """Every word must match: a number (15 = sign n°15) or a text fragment of the axis/sign/definitions."""
    haystack = _norm(" ".join([axis["label"], sign["sign"], sign["fav"], sign["unf"]]))
    for word in _norm(query).split():
        ok = int(word) == sign["n"] if word.isdigit() else word in haystack
        if not ok:
            return False
    return True


class DetailPanel(tk.Frame):
    """Side drawer: both definitions of a sign and the phrases Viktor would say."""

    def __init__(self, parent: tk.Widget, app, view: "SignsView") -> None:
        super().__init__(parent, bg=PANEL)
        f = app.fonts
        bar = tk.Frame(self, bg=PANEL)
        bar.pack(fill="x", padx=12, pady=(10, 0))
        self.title = tk.Label(bar, font=f["body"], bg=PANEL, fg=TEXT, anchor="w", wraplength=360, justify="left")
        self.title.pack(side="left", fill="x", expand=True)
        tk.Button(bar, text="Fermer ✕", font=f["label_s"], bg=BG, fg=TEXT, activebackground=WARM,
                  relief="flat", padx=8, pady=2, command=view.close_detail).pack(side="right")
        body = tk.Frame(self, bg=PANEL)
        body.pack(fill="both", expand=True, padx=12, pady=8)
        scroll = tk.Scrollbar(body, orient="vertical")
        self.text = tk.Text(body, bg=PANEL, fg=TEXT, relief="flat", wrap="word", font=f["small"],
                            highlightthickness=0, cursor="arrow", padx=2, pady=4, yscrollcommand=scroll.set)
        scroll.config(command=self.text.yview)
        scroll.pack(side="right", fill="y")
        self.text.pack(side="left", fill="both", expand=True)
        self.text.tag_configure("h", font=f["label"], foreground=WARM, spacing1=12, spacing3=3)
        self.text.tag_configure("good", font=f["label"], foreground=GOOD, spacing1=12, spacing3=3)
        self.text.tag_configure("bad", font=f["label"], foreground=BAD, spacing1=12, spacing3=3)
        self.text.tag_configure("m", font=f["label_s"], foreground=MUTED)

    def show(self, axis_index: int, roll: int) -> None:
        axis = reading.AXES[axis_index]
        sign = reading.get_sign(axis_index, roll)
        self.title.config(text=f"{axis['label']} n°{roll} : {sign['sign']}")
        t = self.text
        t.config(state="normal")
        t.delete("1.0", "end")
        t.insert("end", f"{axis['label'].upper()} · {axis['nom']}\n", "h")
        t.insert("end", f"{axis['observe']}.\n", "m")
        for favorable in (True, False):
            tag = "good" if favorable else "bad"
            t.insert("end", "FAVORABLE (jet de polarité pair)\n" if favorable else "DÉFAVORABLE (jet de polarité impair)\n", tag)
            t.insert("end", (sign["fav"] if favorable else sign["unf"]) + "\n")
            result = reading.read_axis(axis_index, roll, favorable)
            t.insert("end", "Phrase : ", "m")
            t.insert("end", result["phrase"] + "\n")
            t.insert("end", "/me : ", "m")
            t.insert("end", result["me_phrase"] + "\n")
        t.insert("end", "\nDéfinitions inventées (Cranomancie d'Oswald Bald).", "m")
        t.config(state="disabled")
        t.yview_moveto(0)


class SignsView(tk.Frame):
    """Search bar + the three axes side by side + optional side drawer."""

    def __init__(self, parent: tk.Widget, app) -> None:
        super().__init__(parent, bg=BG)
        self.app = app
        f = app.fonts
        self.selected: tuple[int, int] | None = None
        self.drawer_width = 460
        self.rows: dict[tuple[int, int], tk.Label] = {}

        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=16, pady=(10, 4))
        tk.Label(top, text="Rechercher", font=f["label_s"], bg=BG, fg=MUTED).pack(side="left")
        self.query = tk.StringVar()
        entry = tk.Entry(top, textvariable=self.query, font=f["entry"], bg=PANEL, fg=TEXT, insertbackground=TEXT,
                         relief="flat", highlightthickness=1, highlightbackground=MUTED, highlightcolor=WARM)
        entry.pack(side="left", padx=10, fill="x", expand=True)
        entry.bind("<KeyRelease>", lambda _e: self.populate())
        self.count = tk.Label(top, font=f["label_s"], bg=BG, fg=MUTED)
        self.count.pack(side="left")
        tk.Label(self, text="Numéro (15), signe, mot-clé ou définition. Clic sur un signe : détail ; Échap : fermer.",
                 font=f["small"], bg=BG, fg=MUTED).pack(anchor="w", padx=16)

        self.main = tk.Frame(self, bg=BG)
        self.main.pack(fill="both", expand=True, padx=8, pady=6)
        self.main.grid_rowconfigure(0, weight=1)
        self.main.grid_columnconfigure(0, weight=1)
        left = tk.Frame(self.main, bg=BG)
        left.grid(row=0, column=0, sticky="nsew")
        self.canvas = tk.Canvas(left, bg=BG, highlightthickness=0)
        scroll = tk.Scrollbar(left, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.grid_frame = tk.Frame(self.canvas, bg=BG)
        window = self.canvas.create_window((0, 0), window=self.grid_frame, anchor="nw")
        self.grid_frame.bind("<Configure>", lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(window, width=e.width))
        self.canvas.bind("<Enter>", lambda _e: self.canvas.bind_all("<MouseWheel>", self._wheel))
        self.canvas.bind("<Leave>", lambda _e: self.canvas.unbind_all("<MouseWheel>"))
        for i in range(3):
            self.grid_frame.grid_columnconfigure(i, weight=1, uniform="axes")

        self.detail = DetailPanel(self.main, app, self)
        app.root.bind("<Escape>", lambda _e: self.close_detail() if getattr(app, "current_view", "") == "signs" else None,
                      add="+")
        self.populate()

    def _wheel(self, event: tk.Event) -> None:
        self.canvas.yview_scroll(-1 * (event.delta // 120), "units")

    def show_detail(self, axis_index: int, roll: int) -> None:
        self.selected = (axis_index, roll)
        self.detail.grid(row=0, column=1, sticky="ns", padx=(8, 0))
        self.detail.config(width=self.drawer_width)
        self.detail.pack_propagate(False)
        self.detail.show(axis_index, roll)
        self._highlight()

    def close_detail(self) -> None:
        self.selected = None
        self.detail.grid_remove()
        self._highlight()

    def open_sign(self, axis_index: int, roll: int) -> None:
        """Jump here from the reading page: clear the search so the sign is listed, then open it."""
        if self.query.get():
            self.query.set("")
            self.populate()
        self.show_detail(axis_index, roll)

    def rescale(self) -> None:
        self.drawer_width = int(max(340, min(self.app.root.winfo_width() * 0.30, 620)))
        if self.selected is not None:
            self.detail.config(width=self.drawer_width)
            self.detail.title.config(wraplength=self.drawer_width - 120)
        self.populate(keep_scroll=True)

    def _highlight(self) -> None:
        for key, label in self.rows.items():
            label.config(bg=WARM if key == self.selected else PANEL, fg=BG if key == self.selected else TEXT)

    def populate(self, keep_scroll: bool = False) -> None:
        position = self.canvas.yview()[0] if keep_scroll else 0
        for child in self.grid_frame.winfo_children():
            child.destroy()
        self.rows = {}
        total = 0
        for col, axis in enumerate(reading.AXES):
            column = tk.Frame(self.grid_frame, bg=BG)
            column.grid(row=0, column=col, sticky="new", padx=6)
            tk.Label(column, text=f"{axis['label'].upper()} · {axis['nom']}", font=self.app.fonts["label"],
                     bg=BG, fg=WARM, anchor="w").pack(fill="x", pady=(2, 6))
            for sign in axis["signs"]:
                if not matches(axis, sign, self.query.get()):
                    continue
                total += 1
                label = tk.Label(column, text=f"{sign['n']:>2}  {sign['sign']}", font=self.app.fonts["small"],
                                 bg=PANEL, fg=TEXT, anchor="w", padx=8, pady=5, cursor="hand2",
                                 wraplength=300, justify="left")
                label.pack(fill="x", pady=2)
                label.bind("<Button-1>", lambda _e, a=col, n=sign["n"]: self.show_detail(a, n))
                self.rows[(col, sign["n"])] = label
        self.count.config(text=f"{total} / 60")
        self._highlight()
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(position)
