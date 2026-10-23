"""Erzeugt src/oled_rom_pkg.vhd (Bitmaps 96x64 mit 4 Bit/Pixel + 16-Farb-Palette, Anker-Sprites).

Aufruf:  python scripts/gen_rom.py [--preview ORDNER]

Bosch-Logo : Schriftzug im Bitmap, Ring + Anker als 32 vorgerenderte Dreh-Sprites (20x20).
HHN-Logo   : nachgezeichnet nach der Vorlage; assets/hhn_logo.png ersetzt es (wird eingepasst).
"""
import argparse
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 96, 64
SS = 12                                   # Uebertastung beim Zeichnen
ROOT = Path(__file__).resolve().parent.parent
FONT_BOLD = "C:/Windows/Fonts/arialbd.ttf"
FONT_BLACK = "C:/Windows/Fonts/ariblk.ttf"
FONT_DIN = "C:/Windows/Fonts/bahnschrift.ttf"

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BOSCH_RED = (227, 0, 21)
BOSCH_GREY = (110, 110, 110)
HHN_BLUE = (43, 45, 137)
HHN_TEXT = (20, 20, 20)

# Bosch-Symbol: Mittelpunkt des Rings, Sprite 20x20 darum herum (muss zu oled_render.vhd passen)
SPR = 20
SPR_N = 32
SYM_CX, SYM_CY = 11, 32
SPR_X0, SPR_Y0 = SYM_CX - SPR // 2, SYM_CY - SPR // 2


def canvas():
    return Image.new("RGB", (W * SS, H * SS), WHITE)


def downsample(img):
    return img.resize((W, H), Image.BOX)


def fit_text(img, text, font_path, box, fill):
    """Text so skalieren, dass er genau in box (x0, y0, x1, y1 in Zielpixeln) passt."""
    x0, y0, x1, y1 = (round(v * SS) for v in box)
    f = ImageFont.truetype(font_path, 200)
    l, t, r, b = f.getbbox(text)
    mask = Image.new("L", (r - l, b - t), 0)
    ImageDraw.Draw(mask).text((-l, -t), text, font=f, fill=255)
    mask = mask.resize((x1 - x0, y1 - y0), Image.LANCZOS)
    img.paste(fill, (x0, y0, x1, y1), mask)


def to_indexed(img):
    """Auf 16 Farben reduzieren -> (Pixelindizes, Palette)."""
    q = img.quantize(colors=16, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    pal = q.getpalette()[:48]
    colors = [tuple(pal[i:i + 3]) for i in range(0, 48, 3)]
    colors = [WHITE if min(c) >= 245 else c for c in colors]
    return list(q.tobytes()), colors


def to_indexed_fixed(img, colors):
    raw = img.tobytes()
    px = [tuple(raw[i:i + 3]) for i in range(0, len(raw), 3)]
    idx = [min(range(len(colors)), key=lambda i: sum((colors[i][c] - p[c]) ** 2 for c in range(3)))
           for p in px]
    return idx, colors + [colors[-1]] * (16 - len(colors))


def bosch_image():
    """Schriftzug rechts vom Symbol; das Symbol selbst kommt aus den Sprites."""
    img = canvas()
    fit_text(img, "BOSCH", FONT_BLACK, (31, SYM_CY - 6.5, 94, SYM_CY + 6.5), BOSCH_RED)
    return to_indexed(downsample(img))


def hhn_image():
    custom = ROOT / "assets" / "hhn_logo.png"
    if custom.exists():
        src = Image.open(custom).convert("RGB")
        src.thumbnail((W, H))
        img = Image.new("RGB", (W, H), WHITE)
        img.paste(src, ((W - src.width) // 2, (H - src.height) // 2))
        return to_indexed(img)

    # Koordinaten der Vorlage (Pixel), auf 92 Pixel Breite abgebildet
    nx0, ny0, nx1 = 112, 62, 948
    k = 92 / (nx1 - nx0)
    ox, oy = 2, (H - (335 - ny0) * k) / 2

    def p(nx, ny):
        return ((nx - nx0) * k + ox) * SS, ((ny - ny0) * k + oy) * SS

    img = canvas()
    d = ImageDraw.Draw(img)

    def rect(x0, y0, x1, y1):
        d.polygon([p(x0, y0), p(x1, y0), p(x1, y1), p(x0, y1)], fill=HHN_BLUE)

    for sx in (413, 588, 763, 899):
        rect(sx, 62, sx + 49, 215)
    rect(462, 122, 555, 155)
    rect(637, 122, 730, 155)
    d.polygon([p(763, 62), p(815, 62), p(948, 172), p(948, 215), p(896, 215), p(763, 105)],
              fill=HHN_BLUE)

    tx0, ty0 = p(nx0, 287)
    tx1, ty1 = p(nx1, 335)
    fit_text(img, "HOCHSCHULE HEILBRONN", FONT_DIN, (tx0 / SS, ty0 / SS, tx1 / SS, ty1 / SS), HHN_TEXT)
    return to_indexed(downsample(img))


def msg_image():
    img = Image.new("RGB", (W, H), BLACK)
    f = ImageFont.truetype(FONT_BOLD, 17)
    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    for s, y in [("W\u00e4hle", 3), ("einen", 23), ("Schalter", 43)]:
        l, t, r, b = md.textbbox((0, 0), s, font=f)
        md.text((48 - (r - l) / 2 - l, y - t), s, font=f, fill=255)
    img.paste(WHITE, (0, 0, W, H), mask.point(lambda v: 255 if v >= 128 else 0))
    return to_indexed_fixed(img, [BLACK, WHITE])


def sym_palette():
    return [tuple(round(255 + (g - 255) * i / 15) for g in BOSCH_GREY) for i in range(16)]


def sym_sprite(k):
    """Ring + Anker (H), um k*180/32 Grad gedreht; Deckung 0..15 pro Pixel."""
    s = 16
    big = Image.new("L", (SPR * s, SPR * s), 0)
    d = ImageDraw.Draw(big)
    c = SPR * s / 2
    r_out, r_in = 9 * s, 7.6 * s
    d.ellipse((c - r_out, c - r_out, c + r_out, c + r_out), fill=255)
    d.ellipse((c - r_in, c - r_in, c + r_in, c + r_in), fill=0)
    th = math.pi * k / SPR_N
    co, si = math.cos(th), math.sin(th)

    def rect(x0, x1, y0, y1):
        pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        d.polygon([(c + (x * co - y * si) * s, c + (x * si + y * co) * s) for x, y in pts], fill=255)

    rect(-4.3, -2.7, -5.6, 5.6)               # Staender links
    rect(2.7, 4.3, -5.6, 5.6)                 # Staender rechts
    rect(-2.7, 2.7, -0.8, 0.8)                # Quersteg
    small = big.resize((SPR, SPR), Image.BOX)
    return [round(v * 15 / 255) for v in small.tobytes()]


def rgb565(c):
    r, g, b = c
    return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)


def hex_rows(idx, width, rows):
    out = []
    for y in range(rows):
        v = 0
        for x in range(width):
            v = (v << 4) | idx[y * width + x]
        out.append(f'x"{v:0{width}X}"')
    return out


def emit_image(name, idx, palette):
    rows = hex_rows(idx, W, H)
    out = [f"    constant {name}_ROM : rom_t := ("]
    out += [f"        {r}{',' if i < H - 1 else ''}" for i, r in enumerate(rows)]
    out.append("    );")
    out.append(f"    constant {name}_PAL : pal_t := (")
    out.append(",\n".join(f'        x"{rgb565(c):04X}"' for c in palette))
    out.append("    );")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", type=Path)
    args = ap.parse_args()

    images = {"BOSCH": bosch_image(), "HHN": hhn_image(), "MSG": msg_image()}
    sym_pal = sym_palette()
    sprites = [sym_sprite(k) for k in range(SPR_N)]
    spr_rows = []
    for sp in sprites:
        spr_rows += hex_rows(sp, SPR, SPR)

    parts = [
        "-- AUTOMATISCH ERZEUGT von scripts/gen_rom.py - nicht von Hand aendern.",
        "library IEEE;",
        "use IEEE.STD_LOGIC_1164.ALL;",
        "",
        "package oled_rom_pkg is",
        "    type rom_t     is array (0 to 63) of std_logic_vector(383 downto 0);  -- 96 Pixel x 4 Bit, Pixel 0 = MSB",
        "    type pal_t     is array (0 to 15) of std_logic_vector(15 downto 0);   -- RGB565",
        f"    type spr_rom_t is array (0 to {SPR_N * SPR - 1}) of std_logic_vector({SPR * 4 - 1} downto 0);",
        "",
        f"    constant SPR_X0   : integer := {SPR_X0};   -- Sprite-Ecke oben links im Bild",
        f"    constant SPR_Y0   : integer := {SPR_Y0};",
        f"    constant SPR_SIZE : integer := {SPR};",
        f"    constant SPR_N    : integer := {SPR_N};    -- Drehwinkel k*180/{SPR_N} Grad",
        "",
    ]
    for name, (idx, pal) in images.items():
        parts += [emit_image(name, idx, pal), ""]
    parts.append("    constant SYM_PAL : pal_t := (")
    parts.append(",\n".join(f'        x"{rgb565(c):04X}"' for c in sym_pal))
    parts.append("    );")
    parts.append("    constant SPR_ROM : spr_rom_t := (")
    parts.append(",\n".join(f"        {r}" for r in spr_rows))
    parts.append("    );")
    parts += ["", "end package oled_rom_pkg;"]
    (ROOT / "src" / "oled_rom_pkg.vhd").write_text("\n".join(parts) + "\n", encoding="utf-8")

    if args.preview:
        args.preview.mkdir(parents=True, exist_ok=True)

        def build(idx, pal, spr_k=None):
            im = Image.new("RGB", (W, H))
            im.putdata([pal[i] for i in idx])
            if spr_k is not None:
                for y in range(SPR):
                    for x in range(SPR):
                        im.putpixel((SPR_X0 + x, SPR_Y0 + y), sym_pal[sprites[spr_k][y * SPR + x]])
            return im.resize((W * 6, H * 6), Image.NEAREST)

        build(*images["BOSCH"], 0).save(args.preview / "bosch.png")
        build(*images["BOSCH"], 10).save(args.preview / "bosch_rot.png")
        build(*images["HHN"]).save(args.preview / "hhn.png")
        build(*images["MSG"]).save(args.preview / "msg.png")
    print("oled_rom_pkg.vhd geschrieben")


if __name__ == "__main__":
    sys.exit(main())
