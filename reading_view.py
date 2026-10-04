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

ROOM_IMAGE = Path(__file__).resolve().parent / "viktor" / "piece.jpg"  # the room: Viktor reading at his desk, his raven on his shoulder (old room: viktor/piece_v1_boule.jpg)
ROOM_DIM = 0.88       # brightness of the room picture
PANEL_ALPHA = 0.56    # opacity of the dark panels over the picture (lower = more of the room)
GAP_ALPHA = 0.10      # darkness of the strips between the panels
VEIL_ALPHA = 0.08     # dark veil over the whole page
MARGIN, GAP = 14, 12


class CanvasText:
    """A transparent canvas text with a tk.Label-like config(text=, fg=)."""

    def __init__(self, canvas: tk.Canvas, font, fill: str, justify: str = "center", min_lines: int = 0, gap: int = 4):
        self.canvas, self.font, self.min_lines, self.gap = canvas, font, min_lines, gap
        self.id = canvas.create_text(0, 0, text="", font=font, fill=fill, anchor="n", justify=justify,
                                     state="hidden")  # shown by place(), never at the (0, 0) corner

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
        self.id = canvas.create_window(0, 0, window=widget, anchor="n", state="hidden")

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
        f = app.fonts
        self.canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.bg_item = self.canvas.create_image(0, 0, anchor="nw")
        self._bg_key = None
        self._photo = None
        self._room_src = None
        self._layers: dict = {}  # processed background layers, per page size
        try:
            from PIL import Image  # Pillow is optional: without it the page works with flat panels
            self._room_src = Image.open(ROOM_IMAGE).convert("RGB")
        except Exception:
            pass

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

        # Enlarge: a button next to the header; the big view is a frame laid over the whole page (large type for a stream)
        self.big_button = tk.Button(self.canvas, text="⤢ Agrandir", font=f["label_s"], bg=BG, fg=TEXT,
                                    activebackground=WARM, relief="flat", padx=10, pady=2, command=self.open_big)
        self.big_window = CanvasWindow(self.canvas, self.big_button)
        self.big = tk.Frame(self, bg=PANEL)
        top = tk.Frame(self.big, bg=PANEL)
        top.pack(fill="x", padx=30, pady=(24, 8))
        tk.Label(top, text="CONCLUSION", font=f["label"], bg=PANEL, fg=WARM).pack(side="left")
        tk.Button(top, text="⤡ Réduire", font=f["label_s"], bg=BG, fg=TEXT, activebackground=WARM, relief="flat",
                  padx=12, pady=4, command=self.close_big).pack(side="right")
        self.big_rows = []  # (Label, Copy button) x4
        for _ in range(4):
            row = tk.Frame(self.big, bg=PANEL)
            row.pack(fill="x", padx=30, pady=10)
            btn = tk.Button(row, text="Copier", font=f["label_s"], bg=BG, fg=TEXT, activebackground=WARM,
                            relief="flat", padx=12, pady=4)
            btn.pack(side="right", padx=(16, 0))
            lab = tk.Label(row, text="", font=f["big"], bg=PANEL, fg=TEXT, justify="left", anchor="w", wraplength=1200)
            lab.pack(side="left", fill="x", expand=True)
            self.big_rows.append((lab, btn))
        self.big.bind("<Configure>", lambda e: [lab.config(wraplength=max(300, e.width - 220)) for lab, _ in self.big_rows])
        self.bind_all("<Escape>", lambda _e: self.close_big(), add="+")

        self._job = None
        self.canvas.bind("<Configure>", lambda _e: self.relayout_soon())

    # --- conclusion content -------------------------------------------------
    def open_big(self) -> None:
        if self._row_state[1:] != [True] * 3:  # nothing to enlarge before the three readings are complete
            return
        self.big.place(x=0, y=0, relwidth=1, relheight=1)
        self.big.lift()

    def close_big(self) -> None:
        self.big.place_forget()

    def show_placeholder(self, text: str) -> None:
        """Before the three readings are complete: one message, no copy button."""
        label = self.rows[0][0]
        label.config(text=text, fg=TEXT)
        self._row_state = [True, False, False, False]
        self._placeholder = True
        self.close_big()
        self.relayout_soon()

    def show_items(self, items: list[dict], me_mode: bool) -> None:
        """One row per conclusion line: green / red for the axes, its own Copy button."""
        self._placeholder = False
        for (label, button, _), item in zip(self.rows, items):
            text = "l'individu " + item["me"] if me_mode else item["display"]
            color = TEXT if item["favorable"] is None else (GOOD if item["favorable"] else ALERT)
            label.config(text=text, fg=color)
            button.config(command=lambda i=item: self.app.copy_text(i["spoken"], i["me"]))
        for (lab, btn), item in zip(self.big_rows, items):
            lab.config(text="l'individu " + item["me"] if me_mode else item["display"],
                       fg=TEXT if item["favorable"] is None else (GOOD if item["favorable"] else ALERT))
            btn.config(command=lambda i=item: self.app.copy_text(i["spoken"], i["me"]))
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
        hb = self.canvas.bbox(self.header.id)
        header_w = (hb[2] - hb[0]) if hb else 120
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
            self.big_window.hide()
        else:
            self.buttons_window.place(left, y + 8, anchor="nw")
            self.big_window.place(left + header_w + 24, concl_top + 5, anchor="nw")

        self._set_background(W, H, rects)
        self.canvas.tag_lower(self.bg_item)

    # --- background -----------------------------------------------------------
    def _cover(self, name: str, source, W: int, H: int, process, floor: int | None = None, scale: float | None = None):
        """`source` scaled to cover W x H (or by `scale`), its bottom (the floor) on `floor` (default H); cached."""
        from PIL import Image
        scale = scale if scale is not None else max(W / source.width, H / source.height)
        size = (int(source.width * scale), int(source.height * scale))
        key = (name, W, H)
        if key not in self._layers:
            self._layers = {k: v for k, v in self._layers.items() if k[0] != name}  # keep one size per layer
            self._layers[key] = process(source.resize(size, Image.LANCZOS))
        layer = self._layers[key]
        return layer, ((W - layer.width) // 2, (H if floor is None else floor) - layer.height)

    @staticmethod
    def _mirror_wide(image, width: int):
        """Extend the picture to `width` on very wide screens: the sides are a darkened, strongly blurred, stretched
        copy of the picture (an ambient glow), never a mirrored room; the sharp picture stays centred."""
        from PIL import Image, ImageEnhance, ImageFilter
        if image.width >= width:
            return image.convert("RGBA")
        side = image.resize((width, image.height), Image.BILINEAR).filter(ImageFilter.GaussianBlur(image.height * 0.05))
        side = ImageEnhance.Brightness(side).enhance(0.55)
        x = (width - image.width) // 2
        edge = max(8, int(image.width * 0.03))          # feather the join so the sharp picture melts into the glow
        mask = Image.new("L", image.size, 255)
        for i in range(edge):
            v = int(255 * i / edge)
            mask.paste(v, (i, 0, i + 1, image.height))
            mask.paste(v, (image.width - 1 - i, 0, image.width - i, image.height))
        side.paste(image, (x, 0), mask)
        return side.convert("RGBA")

    def _set_background(self, W: int, H: int, rects: list[tuple[int, int, int, int]]) -> None:
        """Room, then the scene (Viktor, ball, ZAZA), then the translucent panels; composited once per layout."""
        key = (W, H, tuple(rects))  # the picture itself only depends on W and H; the panels are re-drawn on top
        if key == self._bg_key:
            return
        self._bg_key = key
        try:
            from PIL import Image, ImageDraw, ImageEnhance, ImageTk
        except ImportError:
            self.canvas.itemconfigure(self.bg_item, image="")
            return
        base = Image.new("RGBA", (W, H), BG)
        if self._room_src is not None:
            # the whole room is shown (nobody is cropped): fitted to the height of the panels, its bottom (the
            # floor) on their bottom edge; the sides are completed with the mirrored room
            floor = H   # the picture covers the whole page and never depends on the conclusion height
            scale = floor / self._room_src.height
            room, (x, y) = self._cover("room", self._room_src, W, floor,
                                       lambda im: self._mirror_wide(ImageEnhance.Brightness(im).enhance(ROOM_DIM), W),
                                       floor, scale)
            base.paste(room, (x, y))
        overlay = Image.new("RGBA", (W, H), (0x1B, 0x1A, 0x18, int(255 * VEIL_ALPHA)))  # soft veil over everything
        draw = ImageDraw.Draw(overlay)
        columns = rects[:3]
        draw.rectangle([columns[0][0], columns[0][1], columns[2][2], columns[0][3]],
                       fill=(0x26, 0x24, 0x1F, int(255 * GAP_ALPHA)))  # the gaps between the panels are not bright strips
        for i, (x0, y0, x1, y1) in enumerate(rects):  # the conclusion (last rect) is more opaque: it is plain reading text
            draw.rectangle([x0, y0, x1, y1], fill=(0x26, 0x24, 0x1F, int(255 * (PANEL_ALPHA if i < 3 else 0.88))))
        base.alpha_composite(overlay)
        self._photo = ImageTk.PhotoImage(base.convert("RGB"))
        self.canvas.itemconfigure(self.bg_item, image=self._photo)

