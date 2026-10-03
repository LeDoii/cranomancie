"""Script-drawn tarot cards (placeholder art: numeral, name, geometric sigil).

Final illustrations will follow the lore references given by the user.
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

_LOCAL_FONTS = Path(__file__).resolve().parent / "fonts"
# Standalone copy first (published app); the shared project folder is the fallback in the dev tree.
FONTS = _LOCAL_FONTS if _LOCAL_FONTS.exists() else Path(__file__).resolve().parents[2] / "Bindrune" / "_fonts"
PAPER = "#E7E0D1"
INK = "#20201E"
WARM = "#A4551F"
GREY = "#948B78"

SCALE = 2  # drawn at 2x then downsampled for smooth lines

# Arcane number -> house emblems from the wiki lore page (emblems/ folder; sigil used when a file is missing).
EMBLEMS_DIR = Path(__file__).resolve().parent / "emblems"
EMBLEMS = {
    3: ["felora"],                                    # III L'Impératrice: Athénaïs, founder of Felora
    4: ["azuralys"],                                  # IV L'Empereur: Hazelyonn, founder of Azuralys
    5: ["wendelhart_blason"],                         # V Le Mentor: Académie Wendelhart
    10: ["azuralys", "felora", "ferrox", "oragonn"],  # X La Roue de Fortune: the four houses around the wheel
    8: ["ferrox"],                                    # VIII La Justice: the Garde of Velorn (Ferrox)
}


# Arcane number -> (file in illustrations/, crop box) for framed artworks (fan art provided by the user).
ILLUSTRATIONS_DIR = Path(__file__).resolve().parent / "illustrations"
ILLUSTRATIONS = {
    20: ("morzhul.png", (225, 0, 1137, 912)),  # XX Le Jugement: Morzhul, emissary of death (fan art)
}


def _load_chosen() -> None:
    """Add the validated generated illustrations (illustrations/chosen.json: {"13": "13_sans_nom_v1_s2.png"})."""
    path = ILLUSTRATIONS_DIR / "chosen.json"
    if not path.exists():
        return
    import json
    for number, name in json.loads(path.read_text(encoding="utf-8")).items():
        ILLUSTRATIONS[int(number)] = (f"chosen/{name}", None)  # None = the whole (square) image


_load_chosen()


def _paste_illustration(img: Image.Image, d: ImageDraw.ImageDraw, n: int, cx: float, cy: float, span: float) -> bool:
    """Paste a square crop of the artwork, with an ink frame; False when absent."""
    entry = ILLUSTRATIONS.get(n)
    if not entry or not (ILLUSTRATIONS_DIR / entry[0]).exists():
        return False
    art = Image.open(ILLUSTRATIONS_DIR / entry[0]).convert("RGB")
    if entry[1]:
        art = art.crop(entry[1])
    art = art.resize((int(span), int(span)), Image.LANCZOS)
    x, y = int(cx - span / 2), int(cy - span / 2)
    img.paste(art, (x, y))
    d.rectangle([x, y, x + int(span), y + int(span)], outline=INK, width=SCALE * 2)
    return True


def _paste_emblems(img: Image.Image, n: int, cx: float, cy: float, span: float) -> bool:
    """Paste the emblem(s) of arcane n centred on (cx, cy); False when nothing could be drawn."""
    names = EMBLEMS.get(n, [])
    files = [EMBLEMS_DIR / f"{name}.png" for name in names]
    if not files or not all(f.exists() for f in files):
        return False
    side = span if len(files) == 1 else span / 2
    for i, path in enumerate(files):
        emblem = Image.open(path).convert("RGBA").resize((int(side), int(side)), Image.LANCZOS)
        if len(files) == 1:
            x, y = cx - side / 2, cy - side / 2
        else:
            x = cx - side + (i % 2) * side
            y = cy - side + (i // 2) * side
        img.paste(emblem, (int(x), int(y)), emblem)
    return True


def _font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTS / name), size * SCALE)


def _sigil(d: ImageDraw.ImageDraw, cx: float, cy: float, r: float, n: int) -> None:
    """Deterministic star polygon + rings, different for each arcane."""
    w = SCALE * 2
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=INK, width=w)
    d.ellipse([cx - r * 0.82, cy - r * 0.82, cx + r * 0.82, cy + r * 0.82], outline=GREY, width=SCALE)
    points = 5 + n % 6
    step = 2 + n // 8
    pts = [(cx + r * 0.78 * math.sin(2 * math.pi * i / points),
            cy - r * 0.78 * math.cos(2 * math.pi * i / points)) for i in range(points)]
    for i in range(points):
        d.line([pts[i], pts[(i + step) % points]], fill=WARM, width=w)
    for i in range(n % 7 + 1):
        a = 2 * math.pi * i / (n % 7 + 1)
        x, y = cx + r * math.sin(a), cy - r * math.cos(a)
        d.ellipse([x - 5 * SCALE, y - 5 * SCALE, x + 5 * SCALE, y + 5 * SCALE], fill=INK)
    d.ellipse([cx - 6 * SCALE, cy - 6 * SCALE, cx + 6 * SCALE, cy + 6 * SCALE], fill=WARM)


def render_card(arcane: dict, reversed_: bool, size: tuple[int, int] = (240, 400)) -> Image.Image:
    final_size = size
    size = (240, 400)  # all offsets below are laid out for this canvas
    w, h = size[0] * SCALE, size[1] * SCALE
    img = Image.new("RGB", (w, h), PAPER)
    d = ImageDraw.Draw(img)
    m = 10 * SCALE
    d.rectangle([m, m, w - m, h - m], outline=INK, width=SCALE * 3)
    d.rectangle([m * 2, m * 2, w - m * 2, h - m * 2], outline=GREY, width=SCALE)

    numeral_font = _font("Italiana-Regular.ttf", 34)
    d.text((w / 2, 62 * SCALE), arcane["numeral"], font=numeral_font, fill=INK, anchor="mm")

    drawn = (_paste_illustration(img, d, arcane["n"], w / 2, h * 0.46, w * 0.80)
             or _paste_emblems(img, arcane["n"], w / 2, h * 0.46, w * 0.74))
    if not drawn:
        _sigil(d, w / 2, h * 0.46, w * 0.30, arcane["n"])

    name_font = _font("Italiana-Regular.ttf", 26)
    name = arcane["name"]
    words = name.split()
    lines = [name] if d.textlength(name, font=name_font) < w - 60 * SCALE else \
        [" ".join(words[:len(words) // 2 or 1]), " ".join(words[len(words) // 2 or 1:])]
    y = h - (70 if len(lines) == 1 else 88) * SCALE
    for line in lines:
        d.text((w / 2, y), line, font=name_font, fill=INK, anchor="mm")
        y += 34 * SCALE

    img = img.resize(final_size, Image.LANCZOS)
    return img.rotate(180) if reversed_ else img


if __name__ == "__main__":
    import json
    data = json.loads((Path(__file__).parent / "data.json").read_text(encoding="utf-8"))
    sheet = Image.new("RGB", (240 * 11, 400 * 2), "#3a3630")
    for i, arc in enumerate(data["arcanes"]):
        sheet.paste(render_card(arc, False), ((i % 11) * 240, (i // 11) * 400))
    sheet.resize((sheet.width // 3, sheet.height // 3)).save(Path(__file__).parent / "cards_contact.png")
    print("cards_contact.png written")
