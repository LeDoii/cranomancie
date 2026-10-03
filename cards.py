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
