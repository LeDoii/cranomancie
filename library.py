"""Library of the 60 signs (search + side drawer) for the Cranomancie v2 GUI."""
import tkinter as tk
import unicodedata
from tkinter import messagebox

import reading
from signs_text import with_article

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
        self.view, self.fonts = view, f
        self.key: tuple[int, int] | None = None
        self.editing = False
        self.form = None
        bar = tk.Frame(self, bg=PANEL)
        self.bar = bar
        bar.pack(fill="x", padx=12, pady=(10, 0))
        self.title = tk.Label(bar, font=f["body"], bg=PANEL, fg=TEXT, anchor="w", wraplength=360, justify="left")
        self.title.pack(side="left", fill="x", expand=True)
        tk.Button(bar, text="Fermer ✕", font=f["label_s"], bg=BG, fg=TEXT, activebackground=WARM,
                  relief="flat", padx=8, pady=2, command=view.close_detail).pack(side="right")
        self.actions = tk.Frame(self, bg=PANEL)
        self.actions.pack(fill="x", padx=12, pady=(6, 0))
        self.edit_btn = tk.Button(self.actions, text="✎ Modifier", font=f["label_s"], bg=BG, fg=TEXT,
                                  activebackground=WARM, relief="flat", padx=10, pady=3, command=self.start_edit)
        self.reset_btn = tk.Button(self.actions, text="↺ Réinitialiser", font=f["label_s"], bg=BG, fg=TEXT,
                                   activebackground=WARM, relief="flat", padx=10, pady=3, command=self.reset)
        body = tk.Frame(self, bg=PANEL)
        self.body = body
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
        if self.editing:
            self._leave_edit()
        self.key = (axis_index, roll)
        axis = reading.AXES[axis_index]
        sign = reading.get_sign(axis_index, roll)
        custom = reading.is_customized(axis_index, roll)
        self.title.config(text=f"{axis['label']} n°{roll} : {sign['sign']}" + ("  ✎ personnalisé" if custom else ""))
        self.edit_btn.pack_forget()
        self.reset_btn.pack_forget()
        self.edit_btn.pack(side="left")
        if custom:  # the reset button only exists for a signs that differs from the shipped one
            self.reset_btn.pack(side="left", padx=6)
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
        t.insert("end", "\nDéfinitions inventées (Cranomancie d'Oswald Bald)."
                 + (" Ce signe a été modifié par vous." if custom else ""), "m")
        t.config(state="disabled")
        t.yview_moveto(0)

    # --- editing ---------------------------------------------------------------------------------
    def start_edit(self) -> None:
        """Replace the preview with a form: name, form used in the sentence, both definitions."""
        if self.key is None or self.editing:
            return
        self.editing = True
        self.actions.pack_forget()
        self.body.pack_forget()
        f = self.fonts
        sign = reading.get_sign(*self.key)
        form = self.form = tk.Frame(self, bg=PANEL)
        form.pack(fill="both", expand=True, padx=12, pady=8)

        def caption(text: str, hint: str = "") -> None:
            tk.Label(form, text=text, font=f["label"], bg=PANEL, fg=WARM, anchor="w").pack(fill="x", pady=(8, 0))
            if hint:
                tk.Label(form, text=hint, font=f["label_s"], bg=PANEL, fg=MUTED, anchor="w", justify="left",
                         wraplength=self.view.drawer_width - 50).pack(fill="x")

        def entry(value: str) -> tk.Entry:
            widget = tk.Entry(form, font=f["small"], bg=BG, fg=TEXT, insertbackground=TEXT, relief="flat",
                              highlightthickness=1, highlightbackground=MUTED, highlightcolor=WARM)
            widget.insert(0, value)
            widget.pack(fill="x", pady=2)
            return widget

        def box(value: str) -> tk.Text:
            widget = tk.Text(form, font=f["small"], bg=BG, fg=TEXT, insertbackground=TEXT, relief="flat", height=3,
                             wrap="word", highlightthickness=1, highlightbackground=MUTED, highlightcolor=WARM)
            widget.insert("1.0", value)
            widget.pack(fill="x", pady=2)
            return widget

        caption("NOM DU SIGNE")
        self.name_entry = entry(sign["sign"])
        caption("DANS LA PHRASE (« je vois … »)", "Se remplit tout seul si vous changez le nom et laissez ce champ tel quel.")
        self.article_entry = entry(sign["sign_art"])
        caption("FAVORABLE (jet de polarité pair)")
        self.fav_box = box(sign["fav"])
        caption("DÉFAVORABLE (jet de polarité impair)")
        self.unf_box = box(sign["unf"])
        row = tk.Frame(form, bg=PANEL)
        row.pack(fill="x", pady=(12, 0))
        tk.Button(row, text="Enregistrer", font=f["label_s"], bg=WARM, fg=BG, activebackground=WARM, relief="flat",
                  padx=12, pady=4, command=self.save).pack(side="left")
        tk.Button(row, text="Annuler", font=f["label_s"], bg=BG, fg=TEXT, activebackground=WARM, relief="flat",
                  padx=12, pady=4, command=self.cancel_edit).pack(side="left", padx=8)
        self.name_entry.focus_set()

    def save(self) -> None:
        name = self.name_entry.get().strip()
        article = self.article_entry.get().strip()
        old = reading.get_sign(*self.key)
        if name != old["sign"] and article == old["sign_art"]:
            article = with_article(name, strict=False)  # the user renamed the sign: follow with its article
        try:
            reading.save_sign(*self.key, name, article, self.fav_box.get("1.0", "end"), self.unf_box.get("1.0", "end"))
        except (ValueError, OSError) as exc:
            messagebox.showwarning("Enregistrement impossible", str(exc), parent=self)
            return
        self._leave_edit()
        self.view.after_edit()

    def cancel_edit(self) -> None:
        self._leave_edit()
        if self.key is not None:
            self.show(*self.key)

    def _leave_edit(self) -> None:
        if self.form is not None:
            self.form.destroy()
            self.form = None
        self.editing = False
        self.actions.pack(fill="x", padx=12, pady=(6, 0), after=self.bar)
        self.body.pack(fill="both", expand=True, padx=12, pady=8, after=self.actions)

    def reset(self) -> None:
        if self.key is None:
            return
        if messagebox.askyesno("Réinitialiser", "Remettre ce signe à sa version d'origine ?\n"
                               "Vos modifications seront perdues.", parent=self):
            reading.reset_sign(*self.key)
            self.view.after_edit()


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
        tk.Label(self, text="Numéro (15), signe, mot-clé ou définition. Clic sur un signe : détail et modification (✎ = personnalisé) ; Échap : fermer.",
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
        app.root.bind("<Escape>", self._on_escape, add="+")
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

    def _on_escape(self, _event: tk.Event) -> None:
        if getattr(self.app, "current_view", "") == "signs":
            self.detail.cancel_edit() if self.detail.editing else self.close_detail()

    def after_edit(self) -> None:
        """A sign was saved or reset: refresh the list, the open preview and the reading page."""
        self.populate(keep_scroll=True)
        if self.selected is not None:
            self.detail.show(*self.selected)
        self.app.refresh()

    def close_detail(self) -> None:
        if self.detail.editing:
            self.detail.cancel_edit()
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
                mark = "  ✎" if reading.is_customized(col, sign["n"]) else ""
                label = tk.Label(column, text=f"{sign['n']:>2}  {sign['sign']}{mark}", font=self.app.fonts["small"],
                                 bg=PANEL, fg=TEXT, anchor="w", padx=8, pady=5, cursor="hand2",
                                 wraplength=300, justify="left")
                label.pack(fill="x", pady=2)
                label.bind("<Button-1>", lambda _e, a=col, n=sign["n"]: self.show_detail(a, n))
                self.rows[(col, sign["n"])] = label
        self.count.config(text=f"{total} / 60")
        self._highlight()
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(position)
