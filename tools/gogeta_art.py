"""Generate normalized Gogeta UI and card art from checked-in sprite crops."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "source" / "gogeta"
GENERATED = SOURCE / "generated"

CARD_CONFIG = {
    "bigBangKamehameha": (("BIG BANG", "KAMEHAMEHA"), 40, 50, ((0,0,0),(0,1,0),(1,1,1))),
    "dragonFist": (("DRAGON", "FIST"), 70, 60, ((0,0,0),(1,1,1),(0,0,0))),
    "superEnergyBackflow": (("ENERGY", "BACKFLOW"), 25, 25, ((1,1,1),(1,1,1),(1,1,1))),
    "superKamehameha": (("SUPER", "KAMEHAMEHA"), 35, 20, ((0,0,0),(1,1,1),(0,0,0))),
}
COMMON_CARDS = ("guard", "energyUp", "moveLeft", "moveRight", "moveUp", "moveDown",
                "heal", "perfectGuard", "kikyosRevenge", "doubleRight", "doubleLeft", "summonShippo")

# The six-column, five-row numerical glyphs used by the original DM/EN panel.
DIGITS = {
    '0': ('.####.', '##..##', '##..##', '##..##', '.####.'),
    '1': ('..###.', '...##.', '...##.', '...##.', '...##.'),
    '2': ('#####.', '....##', '.#####', '##....', '######'),
    '3': ('#####.', '....##', '.####.', '....##', '#####.'),
    '4': ('##..##', '##..##', '######', '....##', '....##'),
    '5': ('######', '##....', '#####.', '....##', '#####.'),
    '6': ('.#####', '##....', '######', '##..##', '.####.'),
    '7': ('######', '....##', '...##.', '..##..', '..##..'),
}
LETTERS = dict(zip('ABCDEFGHIJKLMNOPQRSTUVWXYZ', [
    ('0110','1001','1111','1001','1001'),('1110','1001','1110','1001','1110'),
    ('0111','1000','1000','1000','0111'),('1110','1001','1001','1001','1110'),
    ('1111','1000','1110','1000','1111'),('1111','1000','1110','1000','1000'),
    ('0111','1000','1011','1001','0111'),('1001','1001','1111','1001','1001'),
    ('111','010','010','010','111'),('0011','0001','0001','1001','0110'),
    ('1001','1010','1100','1010','1001'),('1000','1000','1000','1000','1111'),
    ('10001','11011','10101','10001','10001'),('1001','1101','1011','1001','1001'),
    ('0110','1001','1001','1001','0110'),('1110','1001','1110','1000','1000'),
    ('0110','1001','1001','1011','0111'),('1110','1001','1110','1010','1001'),
    ('0111','1000','0110','0001','1110'),('11111','00100','00100','00100','00100'),
    ('1001','1001','1001','1001','0110'),('10001','10001','10001','01010','00100'),
    ('10001','10001','10101','11011','10001'),('1001','1001','0110','1001','1001'),
    ('10001','01010','00100','00100','00100'),('1111','0001','0110','1000','1111'),
]))


def native_font() -> dict[str, Image.Image]:
    samples = {'font-blades': ('BLADES','OF BLOOD'), 'font-wind': ('WIND','SCAR'),
               'attack': ('IRON','REAVER'), 'moveLeft': ('MOVE','LEFT'),
               'energyUp': ('ENERGY','UP'), 'perfectGuard': ('PERFECT','GUARD'),
               'heal': ('HEAL',), 'kikyosRevenge': ("KIKYO'S",'REVENGE')}
    glyphs = {}
    for name, lines in samples.items():
        template = Image.open(SOURCE / 'card-templates' / (name+'.png')).convert('RGBA')
        for line, text in enumerate(lines):
            top = 5+line*6
            columns = [any(template.getpixel((x,y))[:3] == (255,255,255)
                           for y in range(top,top+5)) for x in range(7,59)]
            spans = []
            start = None
            for offset, active in enumerate(columns+[False]):
                if active and start is None:
                    start = offset
                elif not active and start is not None:
                    spans.append((start+7,offset+7))
                    start = None
            for letter, (left,right) in zip(text.replace(' ',''),spans):
                if letter in glyphs:
                    continue
                glyph = Image.new('RGBA',(right-left,5))
                for y in range(5):
                    for x in range(right-left):
                        if template.getpixel((left+x,top+y))[:3] == (255,255,255):
                            glyph.putpixel((x,y),(255,255,255,255))
                glyphs[letter] = glyph
    return glyphs


def pixel_title(canvas: Image.Image, lines: tuple[str, ...]) -> None:
    font = native_font()
    pixels = []
    for line, text in enumerate(lines):
        strip = Image.new('RGBA',(100,5))
        x = 0
        for letter in text:
            if letter == ' ':
                x += 3
                continue
            glyph = font[letter]
            strip.alpha_composite(glyph,(x,0))
            x += glyph.width+1
        strip = strip.crop((0,0,max(1,x-1),5))
        if strip.width > 51:
            strip = strip.resize((51,5),Image.Resampling.NEAREST)
        pixels.extend((7+dx,5+line*6+dy) for dy in range(5) for dx in range(strip.width)
                      if strip.getpixel((dx,dy))[3])
    draw = ImageDraw.Draw(canvas)
    for x, y in pixels:
        draw.rectangle((x-1,y-1,x+1,y+1), fill=(16,16,24,255))
    for point in pixels:
        draw.point(point, fill='white')


def fusion_illustration(identifier: str) -> Image.Image:
    canvas = Image.new('RGBA', (56, 43), (74, 122, 40, 255))
    draw = ImageDraw.Draw(canvas)
    # Match the original character cards' diagonal energy backdrop.
    for offset in range(-43, 65, 8):
        draw.line((offset,0,offset+43,43), fill=(147,195,85,255), width=3)
    body = content(Image.open(SOURCE / 'portraits/portrait-source.png'))
    if identifier in ('guard', 'perfectGuard'):
        body = content(Image.open(SOURCE / 'frames/guard/02.png'))
    # The fusion vest and blue sash stay legible even at the native card size.
    body = body.resize((round(body.width*0.66), round(body.height*0.66)), Image.Resampling.NEAREST)
    canvas.alpha_composite(body, ((56-body.width)//2, 7))
    if identifier in CARD_CONFIG:
        effects = content(Image.open(SOURCE / 'card-sources' / (identifier+'.png')))
        effects = nearest_fit(effects, (51,26))
        canvas.alpha_composite(effects, (56-effects.width,43-effects.height))
    return canvas


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
    attack = identifier in CARD_CONFIG
    template = Image.open(SOURCE / 'card-templates' / ('attack.png' if attack else identifier+'.png')).convert('RGBA')
    canvas = template.copy()
    canvas.alpha_composite(fusion_illustration(identifier), (3,3))
    draw = ImageDraw.Draw(canvas)
    if attack:
        title, damage, energy, area = CARD_CONFIG[identifier]
        pixel_title(canvas, title)
        for value, top in ((damage,50),(energy,56)):
            draw.rectangle((17,top,35,top+4), fill=(28,42,58,255))
            for digit_index, digit in enumerate(f'{value:02d}'):
                for y, row in enumerate(DIGITS[digit]):
                    for x, bit in enumerate(row):
                        if bit == '#':
                            draw.point((22+digit_index*7+x, top+y), fill='white')
        for row in range(3):
            for col in range(3):
                x, y = 40+col*5, 50+row*4
                draw.rectangle((x,y,x+4,y+3), fill=(45,28,45,255))
                draw.rectangle((x+1,y+1,x+4,y+3), fill=(164,215,78,255) if area[row][col] else (96,57,78,255))
    else:
        titles = {'guard': ('GUARD',), 'energyUp': ('ENERGY','UP'),
                  'moveLeft': ('MOVE','LEFT'), 'moveRight': ('MOVE','RIGHT'),
                  'moveUp': ('MOVE','UP'), 'moveDown': ('MOVE','DOWN'),
                  'doubleLeft': ('DOUBLE','LEFT'), 'doubleRight': ('DOUBLE','RIGHT'),
                  'heal': ('HEAL',), 'perfectGuard': ('PERFECT','GUARD'),
                  'kikyosRevenge': ("KIKYO'S",'REVENGE'), 'summonShippo': ('SUMMON','SHIPPO')}
        pixel_title(canvas,titles[identifier])
    # Keep the native rounded corners and original frame outline exactly.
    for x in range(62):
        for y in range(67):
            if x < 3 or x >= 59 or y >= 64 or y < 3:
                canvas.putpixel((x,y),template.getpixel((x,y)))
    return canvas


def build(output: Path = GENERATED) -> None:
    save(make_portrait(), output / "portrait.png")
    save(make_versus(), output / "versus.png")
    for identifier in CARD_CONFIG:
        save(make_card(identifier), output / "cards" / f"{identifier}.png")
    for identifier in COMMON_CARDS:
        save(make_card(identifier), output / "common-cards" / f"{identifier}.png")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=GENERATED)
    args = parser.parse_args()
    build(args.output.resolve())
    print(f"Generated Gogeta artwork in {args.output.resolve()}")


if __name__ == "__main__":
    main()
