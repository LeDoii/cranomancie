"""Retro arcade title: pixelated bold monospace, amber CRT glow and scanlines (drawn with Pillow)."""
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
AMBER = (255, 190, 70)
AMBER_GLOW = (180, 90, 0)


def _font(size: int) -> ImageFont.FreeTypeFont:
    """Consolas Bold when installed (Windows), else the bundled Geist Mono."""
    for path in (Path("C:/Windows/Fonts/consolab.ttf"), HERE / "fonts" / "GeistMono.ttf"):
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def render_title(text: str, height: int, bg: tuple[int, int, int]) -> Image.Image:
    """The title on the page background colour, `height` pixels tall."""
    font = _font(max(12, int(height * 0.70)))
    left, top, right, bottom = ImageDraw.Draw(Image.new("L", (1, 1))).textbbox((0, 0), text, font=font)
    width = right - left + int(height * 0.5)
    mask = Image.new("L", (width, height), 0)
    ImageDraw.Draw(mask).text((width // 2, height // 2), text, font=font, fill=255, anchor="mm")

    # 8-bit look: shrink, threshold, enlarge without smoothing
    factor = max(3, round(height / 22))
    small = mask.resize((max(1, width // factor), max(1, height // factor)), Image.BILINEAR)
    pixels = small.point(lambda v: 255 if v > 110 else 0).resize(mask.size, Image.NEAREST)

    canvas = Image.new("RGB", (width, height), bg)
    glow = pixels.filter(ImageFilter.GaussianBlur(max(2, height * 0.06)))
    canvas.paste(Image.new("RGB", canvas.size, AMBER_GLOW), (0, 0), glow)
    canvas.paste(Image.new("RGB", canvas.size, AMBER), (0, 0), pixels)

    # CRT scanlines, only over the lit area (so the picture has no visible box on the page background)
    lines = Image.new("L", canvas.size, 0)
    draw = ImageDraw.Draw(lines)
    step = max(3, height // 28)
    for y in range(0, height, step):
        draw.line([(0, y), (width, y)], fill=100, width=max(1, step // 3))
    lit = glow.point(lambda v: 255 if v > 6 else 0)
    canvas.paste(Image.new("RGB", canvas.size, (0, 0, 0)), (0, 0), ImageChops.multiply(lines, lit))
    return canvas
