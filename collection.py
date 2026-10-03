"""Card collection view (search + side drawer detail) for the Cranomancie GUI."""
import re
import tkinter as tk
import unicodedata

from PIL import ImageTk

import reading
from cards import render_card

BG = "#1B1A18"
PANEL = "#26241F"
TEXT = "#E7E0D1"
MUTED = "#948B78"
WARM = "#D9803A"
CARD_RATIO = 0.6  # width / height of a card

ROMAN = re.compile(r"^[ivx]+$")


def _norm(text: str) -> str:
    """Lowercase without accents, for forgiving search."""
    return "".join(c for c in unicodedata.normalize("NFD", text.lower())
                   if unicodedata.category(c) != "Mn")


def _haystack(arcane: dict) -> str:
    return _norm(" ".join([arcane["name"], arcane["up"], arcane["rev"], arcane["anchor"]]))


def matches(arcane: dict, query: str) -> bool:
    """Every word must match: a number (11 = XI), a Roman numeral, or a text fragment."""
    for word in _norm(query).split():
        if word.isdigit():
            ok = int(word) == arcane["n"]
        elif ROMAN.match(word):
            ok = word == arcane["numeral"].lower() or (len(word) >= 3 and word in _haystack(arcane))
        else:
            ok = word in _haystack(arcane)
        if not ok:
            return False
    return True


class DetailPanel(tk.Frame):
    """Side drawer: big card, both senses, lore anchor, axis readings."""

    def __init__(self, parent: tk.Widget, app, view: "CollectionView") -> None:
        super().__init__(parent, bg=PANEL)
        self.app, self.view = app, view
        f = app.fonts
        self.arcane = None
        self.reversed = False
        self._photo = None

        bar = tk.Frame(self, bg=PANEL)
        bar.pack(fill="x", padx=12, pady=(10, 0))
        self.title = tk.Label(bar, font=f["title_s"], bg=PANEL, fg=TEXT, anchor="w")
        self.title.pack(side="left", fill="x", expand=True)
        tk.Button(bar, text="Fermer ✕", font=f["label_s"], bg=BG, fg=TEXT, activebackground=WARM,
                  relief="flat", padx=8, pady=2, command=view.close_detail).pack(side="right")

        body = tk.Frame(self, bg=PANEL)
        body.pack(fill="both", expand=True, padx=12, pady=8)
        scroll = tk.Scrollbar(body, orient="vertical")
        self.text = tk.Text(body, bg=PANEL, fg=TEXT, relief="flat", wrap="word", font=f["small"],
                            highlightthickness=0, cursor="arrow", padx=2, pady=4,
                            yscrollcommand=scroll.set)
        scroll.config(command=self.text.yview)
        scroll.pack(side="right", fill="y")
        self.text.pack(side="left", fill="both", expand=True)
        self.text.tag_configure("h", font=f["label"], foreground=WARM, spacing1=12, spacing3=3)
        self.text.tag_configure("m", font=f["label_s"], foreground=MUTED)
        self.text.tag_configure("center", justify="center", spacing1=6, spacing3=6)

    def set_arcane(self, arcane: dict) -> None:
        self.arcane = arcane
        self.reversed = False
        self.title.config(text=f"{arcane['numeral']} — {arcane['name']}")
        self._fill()
        self.rescale()

    def _fill(self) -> None:
        a = self.arcane
        t = self.text
        t.config(state="normal")
        t.delete("1.0", "end")
        # Card and flip button are part of the scrolled content.
        self.image = tk.Label(t, bg=PANEL)
        self.flip_btn = tk.Button(t, font=self.app.fonts["label_s"], bg=BG, fg=TEXT, activebackground=WARM,
                                  relief="flat", padx=10, pady=4, command=self.flip)
        for widget in (self.image, self.flip_btn):
            widget.bind("<MouseWheel>", self._wheel)
        t.window_create("end", window=self.image)
        t.insert("end", "\n", "center")
        t.window_create("end", window=self.flip_btn)
        t.insert("end", "\n", "center")
        t.tag_add("center", "1.0", "end")
        t.insert("end", "SENS À L'ENDROIT\n", "h")
        t.insert("end", a["up"] + "\n")
        t.insert("end", "SENS À L'ENVERS\n", "h")
        t.insert("end", a["rev"] + "\n")
        t.insert("end", "ANCRAGE LORE (source)\n", "h")
        t.insert("end", a["anchor"] + "\n")
        for reversed_ in (False, True):
            t.insert("end", "LECTURE " + ("À L'ENVERS" if reversed_ else "À L'ENDROIT") + "\n", "h")
            for index, axis in enumerate(reading.AXES):
                t.insert("end", axis["label"].upper() + "  ", "m")
                t.insert("end", reading.read_axis(index, a["n"], reversed_)["phrase"] + "\n")
        t.insert("end", "\nSens et lectures inventés (Cranomancie d'Oswald Bald) ; ancrages sourcés.", "m")
        t.config(state="disabled")
        t.yview_moveto(0)

    def _wheel(self, event: tk.Event) -> str:
        self.text.yview_scroll(-1 * (event.delta // 120), "units")
        return "break"

    def rescale(self) -> None:
        """Re-render the big card to fit the current drawer size."""
        if not self.arcane:
            return
        height = int(max(180, min(self.app.root.winfo_height() * 0.36, 460)))
        width = int(height * CARD_RATIO)
        avail = self.view.drawer_width - 40
        if width > avail:
            width, height = avail, int(avail / CARD_RATIO)
        self._photo = ImageTk.PhotoImage(render_card(self.arcane, self.reversed, (width, height)))
        self.image.config(image=self._photo)
        self.flip_btn.config(text="Voir à l'endroit" if self.reversed else "Voir à l'envers")

    def flip(self) -> None:
        self.reversed = not self.reversed
        self.rescale()


class CollectionView(tk.Frame):
    """Search bar + responsive card grid + optional side drawer."""

    def __init__(self, parent: tk.Widget, app) -> None:
        super().__init__(parent, bg=BG)
        self.app = app
        f = app.fonts
        self.selected = None
        self.drawer_width = 460
        self._thumbs: dict[tuple[int, int], ImageTk.PhotoImage] = {}
        self._cols = 0
        self.found: list[dict] = []
        self.cells: dict[int, tk.Frame] = {}

        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=16, pady=(10, 4))
        tk.Label(top, text="Rechercher", font=f["label_s"], bg=BG, fg=MUTED).pack(side="left")
        self.query = tk.StringVar()
        entry = tk.Entry(top, textvariable=self.query, font=f["entry"], bg=PANEL, fg=TEXT,
                         insertbackground=TEXT, relief="flat", highlightthickness=1,
                         highlightbackground=MUTED, highlightcolor=WARM)
        entry.pack(side="left", padx=10, fill="x", expand=True)
        entry.bind("<KeyRelease>", self._on_search_key)
        for key, (dx, dy) in {"<Left>": (-1, 0), "<Right>": (1, 0), "<Up>": (0, -1), "<Down>": (0, 1)}.items():
            app.root.bind(key, lambda _e, d=(dx, dy): self._arrow(*d), add="+")
            entry.bind(key, lambda _e, d=(dx, dy): self._arrow(*d))  # keep the caret from moving
        app.root.bind("<Escape>", lambda _e: self.close_detail() if self._active() else None, add="+")
        self.count = tk.Label(top, font=f["label_s"], bg=BG, fg=MUTED)
        self.count.pack(side="left")
        tk.Label(self, text="Nom, numéro (11 ou XI), mot-clé ou lieu du lore. Clic ou flèches : détail ; Échap : fermer.",
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
        self.canvas.create_window((0, 0), window=self.grid_frame, anchor="nw")
        self.grid_frame.bind("<Configure>",
                             lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda _e: self.relayout())
        self.canvas.bind("<Enter>", lambda _e: self.canvas.bind_all("<MouseWheel>", self._wheel))
        self.canvas.bind("<Leave>", lambda _e: self.canvas.unbind_all("<MouseWheel>"))

        self.detail = DetailPanel(self.main, app, self)  # shown on demand in column 1
        self.populate()

    def _on_search_key(self, event: tk.Event) -> None:
        if event.keysym not in ("Left", "Right", "Up", "Down", "Escape"):
            self.populate()

    def _active(self) -> bool:
        return getattr(self.app, "current_view", "") == "collection"

    def _arrow(self, dx: int, dy: int) -> str | None:
        """Move the selection with the four arrow keys (only while the collection is shown)."""
        if not self._active() or not self.found:
            return None
        order = [a["n"] for a in self.found]
        if self.selected in order:
            index = order.index(self.selected) + dx + dy * self._cols
        else:
            index = 0
        self.show_detail(self.found[max(0, min(len(order) - 1, index))])
        return "break"

    def _highlight(self) -> None:
        for n, cell in self.cells.items():
            cell.config(bg=WARM if n == self.selected else BG)

    def _see(self, cell: tk.Frame) -> None:
        """Scroll the grid so the selected card is fully visible."""
        self.canvas.update_idletasks()
        total = max(1, self.grid_frame.winfo_height())
        top = self.canvas.yview()[0] * total
        view = self.canvas.winfo_height()
        y0, y1 = cell.winfo_y(), cell.winfo_y() + cell.winfo_height()
        if y0 < top:
            self.canvas.yview_moveto(max(0, (y0 - 8) / total))
        elif y1 > top + view:
            self.canvas.yview_moveto(min(1, (y1 + 8 - view) / total))

    def _wheel(self, event: tk.Event) -> None:
        self.canvas.yview_scroll(-1 * (event.delta // 120), "units")

    # --- drawer -----------------------------------------------------------
    def show_detail(self, arcane: dict) -> None:
        self.selected = arcane["n"]
        self.detail.grid(row=0, column=1, sticky="ns", padx=(8, 0))
        self.detail.config(width=self.drawer_width)
        self.detail.pack_propagate(False)
        self.detail.set_arcane(arcane)
        self._highlight()
        if arcane["n"] in self.cells:
            self.after(30, lambda: self._see(self.cells[arcane["n"]]))

    def close_detail(self) -> None:
        self.selected = None
        self.detail.grid_remove()
        self._highlight()

    # --- grid -------------------------------------------------------------
    def _thumb(self, arcane: dict, size: tuple[int, int]) -> ImageTk.PhotoImage:
        key = (arcane["n"], size[0])
        if key not in self._thumbs:
            self._thumbs[key] = ImageTk.PhotoImage(render_card(arcane, False, size))
        return self._thumbs[key]

    def _thumb_size(self) -> tuple[int, int]:
        width = int(120 * self.app.scale)
        return width, int(width / CARD_RATIO)

    def rescale(self) -> None:
        self.drawer_width = int(max(340, min(self.app.root.winfo_width() * 0.30, 620)))
        if self.selected is not None:
            self.detail.config(width=self.drawer_width)
            self.detail.rescale()
        self._thumbs.clear()
        self.populate(keep_scroll=True)

    def relayout(self) -> None:
        """Re-flow only when the number of columns changed."""
        if self._columns() != self._cols:
            self.populate(keep_scroll=True)

    def _columns(self) -> int:
        cell = self._thumb_size()[0] + 28
        return max(1, self.canvas.winfo_width() // cell)

    def populate(self, keep_scroll: bool = False) -> None:
        position = self.canvas.yview()[0] if keep_scroll else 0
        for child in self.grid_frame.winfo_children():
            child.destroy()
        found = [a for a in reading.ARCANES if matches(a, self.query.get())]
        self.count.config(text=f"{len(found)} / {len(reading.ARCANES)}")
        self.found = found
        self.cells = {}
        self._cols = self._columns()
        size = self._thumb_size()
        for i, arcane in enumerate(found):
            chosen = arcane["n"] == self.selected
            cell = tk.Frame(self.grid_frame, bg=WARM if chosen else BG, padx=2, pady=2, cursor="hand2")
            cell.grid(row=i // self._cols, column=i % self._cols, padx=8, pady=8)
            self.cells[arcane["n"]] = cell
            image = tk.Label(cell, image=self._thumb(arcane, size), bg=BG)
            image.pack()
            name = tk.Label(cell, text=arcane["name"], font=self.app.fonts["small"], bg=BG, fg=TEXT)
            name.pack()
            for widget in (cell, image, name):
                widget.bind("<Button-1>", lambda _e, a=arcane: self.show_detail(a))
        if not found:
            tk.Label(self.grid_frame, text="Aucune carte ne correspond.", font=self.app.fonts["body"],
                     bg=BG, fg=MUTED).grid(padx=20, pady=20)
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(position)
