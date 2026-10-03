"""Reading page of the v2 GUI, drawn on a canvas so that Viktor can show through the panels.

Tk widgets cannot be translucent, so the page is a canvas: a pre-composited background image
(Viktor, large and faint, under dark semi-transparent panels) and transparent canvas text on top.
Only the inputs and buttons stay real widgets, placed on the canvas.
"""
import random
import tkinter as tk
from pathlib import Path

import reading
from widgets import ALERT, BG, GOOD, MUTED, PANEL, TEXT, WARM, NumberField

VIKTOR_IMAGE = Path(__file__).resolve().parent / "viktor" / "viktor_boule.png"
VIKTOR_ALPHA = 0.60   # opacity of Viktor under the panels
VIKTOR_HEIGHT = 1.25  # Viktor's height relative to the page: head to waist visible, the rest zoomed out of frame
VIKTOR_MIN_SPAN = 1.12  # at least this many panel widths wide, so that he crosses the gaps between the panels
PANEL_ALPHA = 0.74    # opacity of the dark panels over the picture (lower = more Viktor)
MARGIN, GAP = 14, 12


class CanvasText:
    """A transparent canvas text with a tk.Label-like config(text=, fg=)."""

    def __init__(self, canvas: tk.Canvas, font, fill: str, justify: str = "center", min_lines: int = 0, gap: int = 4):
        self.canvas, self.font, self.min_lines, self.gap = canvas, font, min_lines, gap
        self.id = canvas.create_text(0, 0, text="", font=font, fill=fill, anchor="n", justify=justify)

    def config(self, text: str | None = None, fg: str | None = None) -> None:
        if text is not None:
            self.canvas.itemconfigure(self.id, text=text)
        if fg is not None:
            self.canvas.itemconfigure(self.id, fill=fg)

    @property
    def shown(self) -> bool:
        return bool(self.canvas.itemcget(self.id, "text"))

    def place(self, x: float, y: float, width: int, anchor: str = "n") -> int:
        """Position the text and return its height."""
        self.canvas.itemconfigure(self.id, width=max(60, width), state="normal", anchor=anchor)
        self.canvas.coords(self.id, x, y)
        box = self.canvas.bbox(self.id)
        height = box[3] - box[1] if box else 0
        return max(height, self.min_lines * self.font.metrics("linespace"))

    def hide(self) -> None:
        self.canvas.itemconfigure(self.id, state="hidden")


class CanvasWindow:
    """A real widget placed on the canvas."""

    def __init__(self, canvas: tk.Canvas, widget: tk.Widget, gap: int = 6):
        self.canvas, self.widget, self.gap, self.shown = canvas, widget, gap, True
        self.id = canvas.create_window(0, 0, window=widget, anchor="n")

    def place(self, x: float, y: float, anchor: str = "n") -> int:
        self.canvas.itemconfigure(self.id, state="normal", anchor=anchor)
        self.canvas.coords(self.id, x, y)
        self.widget.update_idletasks()
        return self.widget.winfo_reqheight()

    def hide(self) -> None:
        self.canvas.itemconfigure(self.id, state="hidden")


class AxisPanel:
    """d20 input, observed sign, polarity roll and reading of one axis (drawn on the canvas)."""

    def __init__(self, app, view: "ReadingView", index: int):
        self.app, self.view, self.index = app, view, index
        axis = reading.AXES[index]
        canvas, f = view.canvas, app.fonts
        self.items: list = []  # layout order, top to bottom

        def text(font, fill, gap=4, optional=False, **kw) -> CanvasText:
            item = CanvasText(canvas, font, fill, gap=gap, **kw)
            item.optional = optional  # dropped when the window is too small for everything
            self.items.append(item)
            return item

        def window(widget, gap=6) -> CanvasWindow:
            item = CanvasWindow(canvas, widget, gap)
            self.items.append(item)
            return item

        text(f["label"], WARM, gap=0).config(text=axis["label"].upper())
        text(f["title_s"], TEXT, gap=2).config(text=axis["nom"])
        text(f["small"], MUTED, gap=2, min_lines=2, optional=True).config(text=axis["question"])

        self.var = tk.StringVar()
        self.field = NumberField(canvas, app, self.var, "Jet (1-20)", 1, 20)
        window(self.field, gap=6)

        self.sign_label = text(f["title_s"], TEXT, gap=14)
        canvas.tag_bind(self.sign_label.id, "<Button-1>", lambda _e: self.open_detail())
        canvas.tag_bind(self.sign_label.id, "<Enter>", lambda _e: canvas.config(cursor="hand2"))
        canvas.tag_bind(self.sign_label.id, "<Leave>", lambda _e: canvas.config(cursor=""))
        self.observe = text(f["small"], MUTED, gap=4, optional=True)

        self.pol_box = tk.Frame(canvas, bg=PANEL)
        self.polarity_btn = tk.Button(self.pol_box, text="🎲 Lancer la polarité", font=f["label_s"], bg=BG, fg=TEXT,
                                      activebackground=WARM, relief="flat", padx=12, pady=6, state="disabled",
                                      command=lambda: app.roll_polarity(self))
        self.pol_var = tk.StringVar()
        self.pol_field = NumberField(self.pol_box, app, self.pol_var, "Polarité (/roll 1-20 du 2e joueur)", 1, 20)
        self._show_polarity_input()
        window(self.pol_box, gap=14)
        self.polarity_label = text(f["label"], MUTED, gap=4)

        self.phrase = text(f["body"], TEXT, gap=8, justify="left")

        self.btns = tk.Frame(canvas, bg=PANEL)
        self.copy_btn = tk.Button(self.btns, text="Copier la phrase", font=f["label_s"], bg=BG, fg=TEXT,
                                  activebackground=WARM, relief="flat", padx=10, pady=4, command=self.copy,
                                  state="disabled")
        self.copy_btn.pack(side="left", padx=4)
        tk.Button(self.btns, text="Aléatoire", font=f["label_s"], bg=BG, fg=TEXT, activebackground=WARM,
                  relief="flat", padx=10, pady=4,
                  command=lambda: (self.randomize_full(), app.refresh())).pack(side="left", padx=4)
        window(self.btns, gap=8)
        self.error = text(f["small"], ALERT, gap=4)

        self.roll = None        # validated d20 result
        self.polarity = None    # None until rolled, else (ui roll, favorable)
        self.result = None      # full reading once the polarity is rolled

    # --- layout -----------------------------------------------------------
    def layout(self, x: float, width: float, y: float, compact: bool = False) -> float:
        """Stack the visible items from y; returns the bottom. Compact: halve the gaps, drop optional lines."""
        cx = x + width / 2
        for item in self.items:
            if isinstance(item, CanvasText):
                if (not item.shown and not item.min_lines) or (compact and item.optional):
                    item.hide()
                    continue
                y += item.gap // 2 if compact else item.gap
                y += item.place(cx, y, int(width - 36))
            else:
                y += item.gap // 2 if compact else item.gap
                y += item.place(cx, y)
        return y

    # --- logic (same behaviour as before) ----------------------------------
    def _show_polarity_input(self) -> None:
        """Button (UI rolls the polarity) or entry field (the second player rolls it in game)."""
        manual = self.app.manual_polarity.get()
        self.polarity_btn.pack_forget()
        self.pol_field.pack_forget()
        (self.pol_field if manual else self.polarity_btn).pack()

    def randomize_full(self) -> None:
        """Random d20 and random polarity roll for this axis."""
        self.roll = random.randint(1, 20)  # set first so update() keeps the polarity below
        self.var.set(str(self.roll))
        self.polarity = reading.roll_polarity()
        if self.app.manual_polarity.get():
            self.pol_var.set(str(self.polarity[0]))  # show the rolled value in the entry

    def open_detail(self) -> None:
        if self.roll:
            self.app.open_sign(self.index, self.roll)

    def display_text(self) -> str:
        """Spoken sentence, or the /me preview exactly as the chat will show it."""
        if self.app.me_prefix.get():
            return "l'individu " + self.result["me_phrase"]
        return self.result["phrase"]

    def update(self) -> None:
        text = self.var.get().strip()
        self.error.config(text="")
        if not text:
            return self.clear()
        try:
            roll = reading.parse_roll(text)
        except ValueError as exc:
            return self.clear(str(exc))
        if roll != self.roll:  # a new d20 invalidates the previous polarity roll
            self.polarity = None
            self.pol_var.set("")
        self.roll = roll
        self._show_polarity_input()
        if self.app.manual_polarity.get():  # polarity typed by the user: the second player's /roll 1-20
            pol_text = self.pol_var.get().strip()
            self.polarity = None
            if pol_text:
                try:
                    value = reading.parse_roll(pol_text)
                except ValueError as exc:
                    self.error.config(text=str(exc).replace("Jet", "Polarité"))
                else:
                    self.polarity = (value, value % 2 == 0)
        sign = reading.get_sign(self.index, roll)
        self.sign_label.config(text=sign["sign"])
        self.observe.config(text=reading.AXES[self.index]["observe"])
        if self.polarity is None:
            self.result = None
            self.polarity_btn.config(state="normal", text="🎲 Lancer la polarité")
            self.polarity_label.config(text="", fg=MUTED)
            self.phrase.config(text="")
            self.copy_btn.config(state="disabled")
            return
        value, favorable = self.polarity
        self.result = reading.read_axis(self.index, roll, favorable, value)
        self.polarity_btn.config(state="normal", text="🎲 Relancer la polarité")
        self.polarity_label.config(
            text=f"Polarité : {value} ({'pair' if favorable else 'impair'}) → "
                 f"{'FAVORABLE' if favorable else 'DÉFAVORABLE'}",
            fg=GOOD if favorable else ALERT)
        self.phrase.config(text=self.display_text())
        self.copy_btn.config(state="normal")

    def clear(self, message: str = "") -> None:
        self.roll = None
        self.polarity = None
        self.pol_var.set("")
        self.result = None
        self.sign_label.config(text="")
        self.observe.config(text="")
        self.polarity_btn.config(state="disabled", text="🎲 Lancer la polarité")
        self.polarity_label.config(text="")
        self.phrase.config(text="")
        self.copy_btn.config(state="disabled")
        self.error.config(text=message)

    def copy(self) -> None:
        if self.result:
            self.app.copy_text(self.result["phrase"], self.result["me_phrase"])


class ReadingView(tk.Frame):
    """The three axes and the conclusion on one canvas, over the Viktor watermark."""

    def __init__(self, parent: tk.Widget, app) -> None:
        super().__init__(parent, bg=BG)
        self.app = app
        self.viktor_enabled = True
        f = app.fonts
        self.canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.bg_item = self.canvas.create_image(0, 0, anchor="nw")
        self._bg_key = None
        self._photo = None
        self._viktor_src = None
        self._viktor_cache: dict = {}
        try:
            from PIL import Image  # Pillow is optional: without it the page works with flat panels
            self._viktor_src = Image.open(VIKTOR_IMAGE).convert("RGBA")
        except Exception:
            self._viktor_src = None

        self.panels = [AxisPanel(app, self, i) for i in range(3)]

        # Conclusion: header, 4 rows (text + own Copy button), then the two general buttons.
        self.header = CanvasText(self.canvas, f["label"], WARM, justify="left")
        self.header.config(text="CONCLUSION")
        self.rows = []  # (CanvasText, copy Button, CanvasWindow)
        for _ in range(4):
            label = CanvasText(self.canvas, f["body"], TEXT, justify="left")
            button = tk.Button(self.canvas, text="Copier", font=f["label_s"], bg=BG, fg=TEXT, activebackground=WARM,
                               relief="flat", padx=10, pady=2)
            self.rows.append((label, button, CanvasWindow(self.canvas, button)))
        self.buttons = tk.Frame(self.canvas, bg=PANEL)
        self.copy_synth = tk.Button(self.buttons, text="Tout copier (une ligne)", font=f["label_s"], bg=BG, fg=TEXT,
                                    relief="flat", padx=10, pady=4, state="disabled", command=app.copy_synthesis)
        self.copy_synth.pack(side="left", padx=(0, 8))
        tk.Button(self.buttons, text="Nouvelle lecture", font=f["label_s"], bg=BG, fg=TEXT, relief="flat", padx=10,
                  pady=4, command=app.reset).pack(side="left")
        self.buttons_window = CanvasWindow(self.canvas, self.buttons)
        self._row_state = [False] * 4  # which rows are shown

        self._job = None
        self.canvas.bind("<Configure>", lambda _e: self.relayout_soon())

    # --- conclusion content -------------------------------------------------
    def show_placeholder(self, text: str) -> None:
        """Before the three readings are complete: one message, no copy button."""
        label = self.rows[0][0]
        label.config(text=text, fg=TEXT)
        self._row_state = [True, False, False, False]
        self._placeholder = True
        self.relayout_soon()

    def show_items(self, items: list[dict], me_mode: bool) -> None:
        """One row per conclusion line: green / red for the axes, its own Copy button."""
        self._placeholder = False
        for (label, button, _), item in zip(self.rows, items):
            text = "l'individu " + item["me"] if me_mode else item["display"]
            color = TEXT if item["favorable"] is None else (GOOD if item["favorable"] else ALERT)
            label.config(text=text, fg=color)
            button.config(command=lambda i=item: self.app.copy_text(i["spoken"], i["me"]))
        self._row_state = [True] * 4
        self.relayout_soon()

    # --- layout ---------------------------------------------------------------
    def relayout_soon(self) -> None:
        if self._job:
            self.after_cancel(self._job)
        self._job = self.after(30, self.relayout)

    def relayout(self) -> None:
        self._job = None
        W, H = self.canvas.winfo_width(), self.canvas.winfo_height()
        if W < 100 or H < 100:
            return
        col_w = (W - 2 * MARGIN - 2 * GAP) / 3
        left = MARGIN + 18
        inner_w = W - 2 * MARGIN - 36

        # conclusion height first (it sits at the bottom)
        btn_w = max(b.winfo_reqwidth() for _, b, _ in self.rows)
        text_w = inner_w - btn_w - 14
        heights = []
        for (label, button, win), shown in zip(self.rows, self._row_state):
            if shown:
                h = label.place(left, 0, text_w, anchor="nw")
                heights.append(max(h, button.winfo_reqheight()) + 4)
            else:
                heights.append(0)
        self.buttons.update_idletasks()
        placeholder = getattr(self, "_placeholder", True)
        buttons_h = 0 if placeholder else self.buttons.winfo_reqheight()
        header_h = self.header.place(left, 0, 400, anchor="nw")
        concl_h = 10 + header_h + sum(heights) + (buttons_h + 8 if buttons_h else 0) + 10
        concl_top = H - MARGIN - concl_h
        panel_top, panel_bottom = 6, concl_top - GAP

        # columns
        rects = []
        for compact in (False, True):  # second pass only when the first one overflows the panels
            rects = []
            bottoms = []
            for i, panel in enumerate(self.panels):
                x = MARGIN + i * (col_w + GAP)
                bottoms.append(panel.layout(x, col_w, panel_top + 10, compact))
                rects.append((int(x), panel_top, int(x + col_w), int(panel_bottom)))
            if max(bottoms) <= panel_bottom - 6:
                break
        rects.append((MARGIN, int(concl_top), W - MARGIN, H - MARGIN))

        # conclusion items
        y = concl_top + 10
        self.header.place(left, y, 400, anchor="nw")
        y += header_h
        for (label, button, win), shown, h in zip(self.rows, self._row_state, heights):
            if shown:
                label.place(left, y, text_w, anchor="nw")
                win.place(W - MARGIN - 18, y, anchor="ne")
                y += h
            else:
                label.hide()
                win.hide()
        if placeholder:
            self.buttons_window.hide()
        else:
            self.buttons_window.place(left, y + 8, anchor="nw")

        self._set_background(W, H, rects)
        self.canvas.tag_lower(self.bg_item)

    # --- background -----------------------------------------------------------
    def _set_background(self, W: int, H: int, rects: list[tuple[int, int, int, int]]) -> None:
        """Viktor under the panels, composited once per layout (cached)."""
        key = (W, H, tuple(rects), self.viktor_enabled)
        if key == self._bg_key:
            return
        self._bg_key = key
        try:
            from PIL import Image, ImageDraw, ImageTk
        except ImportError:
            self.canvas.itemconfigure(self.bg_item, image="")
            return
        base = Image.new("RGBA", (W, H), BG)
        if self.viktor_enabled and self._viktor_src is not None:
            ratio = self._viktor_src.width / self._viktor_src.height
            panel_w = rects[1][2] - rects[1][0]
            width = max(int(H * VIKTOR_HEIGHT * ratio), int(panel_w * VIKTOR_MIN_SPAN))
            height = int(width / ratio)
            cache_key = (width, height)
            if cache_key not in self._viktor_cache:
                self._viktor_cache = {cache_key: self._viktor_src.resize((width, height), Image.LANCZOS)}
            art = self._viktor_cache[cache_key].copy()
            art.putalpha(art.getchannel("A").point(lambda v: int(v * VIKTOR_ALPHA)))
            x, y = (W - width) // 2, int(H * 0.01)
            layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            layer.paste(art, (x, y), art)
            base.alpha_composite(layer)
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        for x0, y0, x1, y1 in rects:
            draw.rectangle([x0, y0, x1, y1], fill=(0x26, 0x24, 0x1F, int(255 * PANEL_ALPHA)))
        base.alpha_composite(overlay)
        self._photo = ImageTk.PhotoImage(base.convert("RGB"))
        self.canvas.itemconfigure(self.bg_item, image=self._photo)

    def set_viktor(self, enabled: bool) -> None:
        self.viktor_enabled = enabled
        self.relayout_soon()
