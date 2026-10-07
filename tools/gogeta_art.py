"""Generate normalized Gogeta UI and card art from checked-in sprite crops."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "source" / "gogeta"
GENERATED = SOURCE / "generated"

CARD_CONFIG = {
    "bigBangKamehameha": ("BBK", 40, 50, (55, 135, 255, 230)),
    "dragonFist": ("DRAGON", 70, 60, (255, 105, 35, 230)),
    "superEnergyBackflow": ("BURST", 25, 25, (255, 225, 70, 230)),
    "superKamehameha": ("KAME", 35, 20, (80, 180, 255, 230)),
}


def content(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    box = rgba.getbbox()
    if not box:
        raise ValueError("source image contains no visible pixels")
    return rgba.crop(box)


def nearest_fit(image: Image.Image, maximum: tuple[int, int]) -> Image.Image:
    result = content(image)
    ratio = min(maximum[0] / result.width, maximum[1] / result.height)
    size = (max(1, round(result.width * ratio)), max(1, round(result.height * ratio)))
    return result.resize(size, Image.Resampling.NEAREST)


def save(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGBA").save(path, "PNG", optimize=True)


def make_portrait() -> Image.Image:
    source = content(Image.open(SOURCE / "portraits" / "portrait-source.png"))
    upper = source.crop((0, 0, source.width, max(1, round(source.height * 0.62))))
    sprite = nearest_fit(upper, (100, 98))
    canvas = Image.new("RGBA", (120, 120), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((3, 3, 116, 116), radius=10, fill=(10, 18, 34, 220), outline=(255, 190, 20, 255), width=4)
    x = (120 - sprite.width) // 2
    y = 12 + (94 - sprite.height) // 2
    canvas.alpha_composite(sprite, (x, y))
    draw.rectangle((9, 96, 110, 111), fill=(25, 13, 0, 230), outline=(255, 190, 20, 255), width=1)
    draw.text((38, 99), "GOGETA", font=ImageFont.load_default(), fill=(255, 226, 112, 255))
    return canvas


def make_versus() -> Image.Image:
    source = nearest_fit(Image.open(SOURCE / "portraits" / "versus-source.png"), (190, 250))
    canvas = Image.new("RGBA", (400, 300), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    center = (205, 150)
    for radius, alpha in ((132, 34), (105, 52), (78, 70)):
        draw.ellipse(
            (center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius),
            outline=(70, 165, 255, alpha),
            width=5,
        )
    for offset in range(-120, 141, 32):
        draw.line((center[0] + offset, 275, center[0] + offset // 2, 20), fill=(110, 210, 255, 90), width=3)
    x = 196 - source.width // 2
    y = 282 - source.height
    shadow = Image.new("RGBA", source.size, (0, 0, 0, 0))
    shadow.putalpha(source.getchannel("A").point(lambda value: value * 120 // 255))
    canvas.alpha_composite(shadow, (x + 7, y + 7))
    canvas.alpha_composite(source, (x, y))
    draw.rounded_rectangle((255, 220, 390, 282), radius=9, fill=(6, 12, 30, 215), outline=(255, 193, 34, 255), width=3)
    draw.text((280, 236), "GOGETA", font=ImageFont.load_default(), fill=(255, 231, 135, 255))
    draw.text((276, 254), "FUSION WARRIOR", font=ImageFont.load_default(), fill=(130, 205, 255, 255))
    return canvas


def make_card(identifier: str) -> Image.Image:
    label, damage, energy, accent = CARD_CONFIG[identifier]
    source = nearest_fit(Image.open(SOURCE / "card-sources" / f"{identifier}.png"), (54, 43))
    canvas = Image.new("RGBA", (62, 67), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((1, 1, 60, 65), radius=5, fill=(12, 17, 30, 240), outline=(255, 193, 36, 255), width=2)
    draw.rectangle((4, 4, 57, 45), fill=(6, 11, 24, 215), outline=accent, width=1)
    canvas.alpha_composite(source, ((62 - source.width) // 2, 5 + (40 - source.height) // 2))
    draw.rectangle((4, 47, 57, 62), fill=(18, 9, 0, 235), outline=(255, 193, 36, 220), width=1)
    draw.text((6, 48), label[:9], font=ImageFont.load_default(), fill=(255, 232, 150, 255))
    draw.text((6, 56), f"D{damage} E{energy}", font=ImageFont.load_default(), fill=(145, 215, 255, 255))
    return canvas


def build(output: Path = GENERATED) -> None:
    save(make_portrait(), output / "portrait.png")
    save(make_versus(), output / "versus.png")
    for identifier in CARD_CONFIG:
        save(make_card(identifier), output / "cards" / f"{identifier}.png")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=GENERATED)
    args = parser.parse_args()
    build(args.output.resolve())
    print(f"Generated Gogeta artwork in {args.output.resolve()}")


if __name__ == "__main__":
    main()
