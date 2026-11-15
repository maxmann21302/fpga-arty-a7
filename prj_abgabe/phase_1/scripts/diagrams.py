"""Technische Grafiken fuer die Phase-I-Dokumentation (Pillow)."""
from pathlib import Path
import math

from PIL import Image, ImageDraw, ImageFont

INK = "#20272B"
RED = "#C92C38"
TEAL = "#007F86"
GRAY = "#56646B"
LIGHT = "#F2F5F6"
MUTED = "#C9D1D5"
MUTED_TEXT = "#A3AEB4"
HOT_FILL = "#FCEDEE"
SEG_ON = "#E8282F"
SEG_OFF_LIGHT = "#F1E4E5"
SEG_OFF_DARK = "#373E43"
PANEL = "#1E2326"

PATTERNS = ["0111111", "0000110", "1011011", "1001111", "1100110",
            "1101101", "1111101", "0000111", "1111111", "1101111"]

STYLE = {
    "hot": dict(outline=RED, fill=HOT_FILL, width=4, title=INK, body=GRAY),
    "on": dict(outline=TEAL, fill=LIGHT, width=3, title=INK, body=GRAY),
    "off": dict(outline=MUTED, fill="#FAFBFB", width=2, title=MUTED_TEXT, body=MUTED_TEXT),
}
LINE = {"hot": (RED, 5), "on": (INK, 3), "off": (MUTED, 2)}


def font(size, bold=False, mono=False):
    name = "consola.ttf" if mono else ("calibrib.ttf" if bold else "calibri.ttf")
    path = Path("C:/Windows/Fonts") / name
    return ImageFont.truetype(str(path), size) if path.exists() else ImageFont.load_default(size=size)


def canvas(width, height, title):
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    draw.text((40, 26), title, font=font(38, True), fill=INK)
    return image, draw


def text_lines(draw, cx, cy, items, spacing=6):
    heights = [item[1].size + spacing for item in items]
    top = cy - sum(heights) / 2
    for (text, fnt, color), height in zip(items, heights):
        draw.text((cx, top), text, font=fnt, fill=color, anchor="ma")
        top += height


def box(draw, xy, title, body="", status="on", title_size=24, body_size=20, radius=10):
    style = STYLE[status]
    draw.rounded_rectangle(xy, radius=radius, fill=style["fill"], outline=style["outline"], width=style["width"])
    items = [(line, font(title_size, True), style["title"]) for line in title.split("\n")]
    if body:
        items += [(line, font(body_size), style["body"]) for line in body.split("\n")]
    text_lines(draw, (xy[0] + xy[2]) / 2, (xy[1] + xy[3]) / 2, items)


def dashed_line(draw, p0, p1, color, width, dash=12, gap=8):
    length = math.dist(p0, p1)
    if length == 0:
        return
    ux, uy = (p1[0] - p0[0]) / length, (p1[1] - p0[1]) / length
    position = 0
    while position < length:
        end = min(position + dash, length)
        draw.line((p0[0] + ux * position, p0[1] + uy * position, p0[0] + ux * end, p0[1] + uy * end),
                  fill=color, width=width)
        position = end + gap


def arrow(draw, points, status="on", head=True, dashed=False, color=None, width=None):
    line_color, line_width = LINE[status]
    color = color or line_color
    width = width or line_width
    for p0, p1 in zip(points, points[1:]):
        if dashed:
            dashed_line(draw, p0, p1, color, width)
        else:
            draw.line((*p0, *p1), fill=color, width=width)
    for point in points[1:-1]:
        r = width / 2
        draw.ellipse((point[0] - r, point[1] - r, point[0] + r, point[1] + r), fill=color)
    if head:
        (x0, y0), (x1, y1) = points[-2], points[-1]
        angle = math.atan2(y1 - y0, x1 - x0)
        size = 10 + width * 1.5
        left = (x1 - size * math.cos(angle) + size * 0.5 * math.sin(angle),
                y1 - size * math.sin(angle) - size * 0.5 * math.cos(angle))
        right = (x1 - size * math.cos(angle) - size * 0.5 * math.sin(angle),
                 y1 - size * math.sin(angle) + size * 0.5 * math.cos(angle))
        draw.polygon([(x1, y1), left, right], fill=color)


def dot(draw, point, status="on", radius=6):
    color = LINE[status][0]
    draw.ellipse((point[0] - radius, point[1] - radius, point[0] + radius, point[1] + radius), fill=color)


def label(draw, xy, text, size=19, color=GRAY, bold=False, anchor="la"):
    draw.text(xy, text, font=font(size, bold), fill=color, anchor=anchor)


def segment_polygons(x, y, w, h=None):
    h = h or 1.8 * w
    t = 0.18 * w
    g = 0.04 * w
    left, right = x + t / 2, x + w - t / 2
    top, mid, bottom = y + t / 2, y + h / 2, y + h - t / 2

    def horizontal(x1, x2, yc):
        return [(x1, yc), (x1 + t / 2, yc - t / 2), (x2 - t / 2, yc - t / 2),
                (x2, yc), (x2 - t / 2, yc + t / 2), (x1 + t / 2, yc + t / 2)]

    def vertical(xc, y1, y2):
        return [(xc, y1), (xc + t / 2, y1 + t / 2), (xc + t / 2, y2 - t / 2),
                (xc, y2), (xc - t / 2, y2 - t / 2), (xc - t / 2, y1 + t / 2)]

    return [
        horizontal(left + g, right - g, top),      # a
        vertical(right, top + g, mid - g),         # b
        vertical(right, mid + g, bottom - g),      # c
        horizontal(left + g, right - g, bottom),   # d
        vertical(left, mid + g, bottom - g),       # e
        vertical(left, top + g, mid - g),          # f
        horizontal(left + g, right - g, mid),      # g
    ]


def draw_digit(draw, x, y, w, pattern, on=SEG_ON, off=SEG_OFF_LIGHT, letters=False, h=None):
    polygons = segment_polygons(x, y, w, h)
    for index, polygon in enumerate(polygons):
        lit = pattern is not None and pattern[6 - index] == "1"
        draw.polygon(polygon, fill=on if lit else off)
        if letters:
            cx = sum(p[0] for p in polygon) / 6
            cy = sum(p[1] for p in polygon) / 6
            draw.text((cx, cy), "abcdefg"[index], font=font(int(w * 0.16), True),
                      fill="white" if lit else GRAY, anchor="mm")


def mini_display(draw, x, y, text, digit_w=34):
    pad = 12
    width = pad * 3 + digit_w * 2
    height = digit_w * 1.8 + pad * 2
    draw.rounded_rectangle((x, y, x + width, y + height), radius=8, fill=PANEL)
    for index, char in enumerate(text):
        pattern = PATTERNS[int(char)] if char.isdigit() else None
        draw_digit(draw, x + pad + index * (digit_w + pad), y + pad, digit_w, pattern, on="#FF3B3B", off=SEG_OFF_DARK)
    return width, height


def display_text(value):
    """Anzeige wie im RTL: fuehrende Null unterdrueckt, None = dunkel."""
    if value is None:
        return "  "
    return f"{value:2d}" if value >= 10 else f" {value}"


def switch_row(draw, x, y, bits):
    label(draw, (x, y + 4), "Schalter:", 20, GRAY, True)
    for index in range(4):
        sw = 3 - index
        left = x + 100 + index * 62
        on = bits[index] == "1"
        draw.rounded_rectangle((left, y, left + 44, y + 54), radius=6, fill=TEAL if on else "#E4E8EA",
                               outline=TEAL if on else MUTED, width=2)
        knob = y + 4 if on else y + 30
        draw.rounded_rectangle((left + 6, knob, left + 38, knob + 20), radius=4, fill="white")
        label(draw, (left + 22, y + 60), f"SW{sw}", 16, GRAY, True, "ma")


# --------------------------------------------------------------------------- Architektur

MODE_INFO = {
    None: dict(title="GESAMTARCHITEKTUR  |  phase1_top", bits=None, value=None, info=[
        "Alle Register laufen mit CLK100MHZ (100 MHz, eine Taktdomäne). Asynchrone Eingänge werden über je 2 Flipflops synchronisiert.",
        "Der Modus-Decoder wählt über den Wert-MUX genau eine Quelle; Tasten wirken nur auf das Register des aktiven Modus.",
        "value (0 … 99) wird in Zehner/Einer zerlegt; ssd_driver multiplext beide Ziffern im 1-ms-Raster auf das Pmod SSD.",
    ]),
    "sw0": dict(title="SW0 = 1  |  ZÄHLER 0 … 99", bits="0001", value=42, info=[
        "BTN0: +1 (99 + 1 → 0)    BTN1: −1 (nicht unter 0)    BTN2: +10 (über 99 → 0)    BTN3: −10 (nicht unter 0)",
        "Jeder entprellte Tastendruck erzeugt genau einen 1-Takt-Puls press(i); langes Halten zählt nicht weiter.",
        "count bleibt beim Wechsel in einen anderen Modus erhalten. Beispielanzeige: 42 (Zehner 4, Einer 2).",
    ]),
    "sw1": dict(title="SW1 = 1  |  MATRIKELNUMMER MARK: 91", bits="0010", value=91, info=[
        "Der Wert-MUX legt die Konstante MATR_MARK = 91 auf value. Tasten haben in diesem Modus keine Wirkung.",
        "Zehner 9 → gfedcba = 1101111, Einer 1 → 0000110. Beide Ziffern leuchten, da value ≥ 10.",
        "Zähler (count) und Binärregister (bin_value) behalten ihre Werte unverändert im Hintergrund.",
    ]),
    "sw2": dict(title="SW2 = 1  |  MATRIKELNUMMER MAXI: 93", bits="0100", value=93, info=[
        "Der Wert-MUX legt die Konstante MATR_MAXI = 93 auf value. Tasten haben in diesem Modus keine Wirkung.",
        "Zehner 9 → gfedcba = 1101111, Einer 3 → 1001111. Beide Ziffern leuchten, da value ≥ 10.",
        "Zähler (count) und Binärregister (bin_value) behalten ihre Werte unverändert im Hintergrund.",
    ]),
    "sw3": dict(title="SW3 = 1  |  BINÄREINGABE 0 … 15", bits="1000", value=11, info=[
        "BTNi toggelt Bit i von bin_value: BTN0 = Wertigkeit 1, BTN1 = 2, BTN2 = 4, BTN3 = 8.",
        "Beispiel: BTN0, BTN1, BTN3 je einmal gedrückt → bin_value = 1011 → 8 + 2 + 1 = 11 → Anzeige 11.",
        "Werte 0 … 9 einstellig (linke Ziffer dunkel), 10 … 15 zweistellig. Erneuter Druck löscht das Bit wieder.",
    ]),
    "off": dict(title="KEIN ODER MEHRERE SCHALTER  |  ANZEIGE DUNKEL", bits="0011", value=None, info=[
        "Jede Kombination außer 0001, 0010, 0100, 1000 ergibt show = 0 (Beispiel oben: SW0 + SW1 = 0011).",
        "Die Ausblendung erzwingt seg_r = 0000000 in beiden Slots; ssd_driver und dsel_r laufen unverändert weiter.",
        "Tasten werden ignoriert; count und bin_value bleiben erhalten und erscheinen beim gültigen Modus wieder.",
    ]),
}

DISPLAY_PATH = {"mux", "value", "show", "bcd", "blank", "bcd_out", "blank_out", "driver", "driver_out", "pmod"}
HOT = {
    None: set(),
    "sw0": {"btn", "debounce", "press", "press_cnt", "en", "en_cnt", "counter", "counter_out"} | DISPLAY_PATH,
    "sw1": {"mark", "mark_out"} | DISPLAY_PATH,
    "sw2": {"maxi", "maxi_out"} | DISPLAY_PATH,
    "sw3": {"btn", "debounce", "press", "press_bin", "en", "en_bin", "binary", "binary_out"} | DISPLAY_PATH,
    "off": {"dark", "dark_out", "mux", "show", "blank", "blank_out", "driver", "driver_out", "pmod"},
}
COMMON = {"clk", "rst", "rst_sync", "sw", "sw_sync", "sw_line", "decoder", "mode_sel"} | DISPLAY_PATH


def architecture(path, mode=None):
    info = MODE_INFO[mode]
    image, draw = canvas(1800, 1000, info["title"])

    def st(key):
        if mode is None:
            return "on"
        if key in HOT[mode]:
            return "hot"
        return "on" if key in COMMON else "off"

    if info["bits"]:
        switch_row(draw, 1120, 18, info["bits"])
        label(draw, (1540, 22), "Anzeige:", 20, GRAY, True)
        mini_display(draw, 1630, 12, display_text(info["value"]), 30)

    # Eingaenge
    box(draw, (40, 105, 210, 175), "CLK100MHZ", "E3, 100 MHz", st("clk"), 22, 18)
    box(draw, (40, 225, 210, 295), "ck_rst", "C2, aktiv Low", st("rst"), 22, 18)
    box(draw, (40, 385, 210, 455), "sw[3:0]", "Schiebeschalter", st("sw"), 22, 18)
    box(draw, (40, 595, 210, 665), "btn[3:0]", "Taster, aktiv High", st("btn"), 22, 18)
    label(draw, (225, 128), "→ taktet alle Register (eine Taktdomäne, kein abgeleiteter Takt)", 19, GRAY)

    # Synchronisation
    box(draw, (260, 205, 500, 315), "Reset-Sync", "2 FF, async. Anforderung\nsynchrone Freigabe", st("rst_sync"), 23, 18)
    box(draw, (260, 370, 500, 470), "Schalter-Sync", "2 FF → sw_sync[3:0]", st("sw_sync"), 23, 18)
    box(draw, (260, 560, 500, 700), "4 × btn_debounce", "2 FF + 10 ms stabil\n→ press[3:0]\n1-Takt-Puls je Druck", st("debounce"), 23, 18)
    arrow(draw, [(210, 260), (260, 260)], st("rst"))
    arrow(draw, [(210, 420), (260, 420)], st("sw"))
    arrow(draw, [(210, 630), (260, 630)], st("btn"))
    label(draw, (262, 322), "rst → btn_debounce, count, bin_value, ssd_driver", 17, RED)

    # Modus-Decoder
    box(draw, (560, 370, 790, 470), "Modus-Decoder", "genau ein Schalter = 1\nsonst show = 0", st("decoder"), 23, 18)
    arrow(draw, [(500, 420), (560, 420)], st("sw_line"))

    # Funktionsbloecke
    box(draw, (900, 105, 1150, 235), "Zähler  (SW0)", "count 0 … 99\n+1  −1  +10  −10", st("counter"), 23, 19)
    box(draw, (900, 265, 1150, 345), "Konstante 91", "MATR_MARK  (SW1)", st("mark"), 23, 18)
    box(draw, (900, 370, 1150, 450), "Konstante 93", "MATR_MAXI  (SW2)", st("maxi"), 23, 18)
    box(draw, (900, 480, 1150, 610), "Binärregister (SW3)", "bin_value 0 … 15\nBTNi toggelt Bit i", st("binary"), 23, 19)
    box(draw, (900, 640, 1150, 720), "keine Quelle", "0 oder ≥ 2 Schalter", st("dark"), 23, 18)

    # press-Bus (x = 835) und Freigabe-Bus (x = 865)
    arrow(draw, [(500, 630), (835, 630), (835, 515)], st("press"), head=False)
    arrow(draw, [(835, 515), (835, 140), (900, 140)], st("press_cnt"))
    arrow(draw, [(835, 515), (900, 515)], st("press_bin"))
    label(draw, (560, 600), "press[3:0]", 19, LINE[st("press")][0], True)
    color, width = LINE[st("en")]
    draw.line((790, 420, 826, 420), fill=color, width=width)
    draw.line((844, 420, 865, 420), fill=color, width=width)
    arrow(draw, [(865, 420), (865, 200), (900, 200)], st("en_cnt"), dashed=True)
    arrow(draw, [(865, 420), (865, 575), (900, 575)], st("en_bin"), dashed=True)
    label(draw, (868, 236), "en", 17, LINE[st("en_cnt")][0], True)
    label(draw, (868, 600), "en", 17, LINE[st("en_bin")][0], True)

    # Wert-MUX
    box(draw, (1195, 105, 1270, 720), "Wert-\nMUX", "", st("mux"), 22)
    for key, y in [("counter_out", 170), ("mark_out", 305), ("maxi_out", 410), ("binary_out", 545), ("dark_out", 680)]:
        arrow(draw, [(1150, y), (1195, y)], st(key))
    arrow(draw, [(675, 470), (675, 790), (1232, 790), (1232, 720)], st("mode_sel"))
    label(draw, (690, 760), "Auswahl (Modus)", 19, LINE[st("mode_sel")][0], True)

    # BCD und Ausblendung
    box(draw, (1330, 240, 1545, 400), "BCD-Zerlegung", "tens = value / 10\nones = value mod 10", st("bcd"), 23, 19)
    box(draw, (1330, 450, 1545, 590), "Ausblendung", "show: Einer an\nshow_tens:\nshow und value ≥ 10", st("blank"), 23, 18)
    arrow(draw, [(1270, 320), (1330, 320)], st("value"))
    arrow(draw, [(1270, 520), (1330, 520)], st("show"))
    label(draw, (1278, 292), "value", 16, LINE[st("value")][0], True)
    label(draw, (1278, 492), "show", 16, LINE[st("show")][0], True)

    # Treiber und Pmod
    box(draw, (1590, 200, 1770, 610), "ssd_driver", "tick_gen:\nPuls je 1 ms\n\nsel toggelt\n\nMUX\nEiner / Zehner\n\nseg7_decoder\n→ gfedcba", st("driver"), 23, 18)
    arrow(draw, [(1545, 320), (1590, 320)], st("bcd_out"))
    arrow(draw, [(1545, 520), (1590, 520)], st("blank_out"))
    box(draw, (1590, 665, 1770, 765), "Pmod SSD", "seg_r[6:0], dsel_r", st("pmod"), 23, 17)
    arrow(draw, [(1680, 610), (1680, 665)], st("driver_out"))

    # Info-Panel
    draw.rounded_rectangle((40, 830, 1760, 980), radius=10, fill=LIGHT)
    for index, line in enumerate(info["info"]):
        label(draw, (64, 846 + index * 42), line, 23, INK if index == 0 else GRAY, index == 0)
    image.save(path)


# --------------------------------------------------------------------------- weitere Grafiken

def hierarchy(path):
    image, draw = canvas(1800, 900, "MODULHIERARCHIE UND PROZESSE")
    box(draw, (600, 100, 1200, 210), "phase1_top", "Top-Level, Ports: CLK100MHZ, ck_rst, sw, btn, seg_r, dsel_r", "hot", 30, 19)
    box(draw, (120, 290, 520, 400), "btn_debounce  × 4", "for-generate gen_btn(0 … 3)\nSync + Entprellung + Puls", "on", 25, 18)
    box(draw, (1000, 290, 1400, 400), "ssd_driver", "Multiplex zweier Ziffern", "on", 25, 18)
    box(draw, (880, 480, 1160, 580), "tick_gen", "DIV = 100.000 → Puls je 1 ms", "on", 23, 17)
    box(draw, (1240, 480, 1520, 580), "seg7_decoder", "kombinatorisch: BCD → gfedcba", "on", 23, 17)
    box(draw, (1480, 290, 1740, 400), "clock_pkg", "Package: max_nat()", "off", 23, 18)
    arrow(draw, [(700, 210), (700, 250), (320, 250), (320, 290)], "hot")
    arrow(draw, [(1100, 210), (1100, 250), (1200, 250), (1200, 290)], "hot")
    arrow(draw, [(1120, 400), (1120, 440), (1020, 440), (1020, 480)], "on")
    arrow(draw, [(1280, 400), (1280, 440), (1380, 440), (1380, 480)], "on")
    arrow(draw, [(1480, 345), (1400, 345)], "on", dashed=True)
    label(draw, (1410, 312), "use", 17, GRAY)
    label(draw, (130, 420), "rot = von phase1_top instanziierte Entities", 19, RED)
    label(draw, (130, 448), "blau = Unterinstanzen von ssd_driver", 19, TEAL)
    procs = [
        ("Reset-Sync", "reset_sync(1:0)\n→ rst"),
        ("Schalter-Sync", "sw_meta → sw_sync"),
        ("Register-Prozess", "count, bin_value"),
        ("Modus-Decoder", "value, show"),
        ("BCD + Ausblendung", "tens, ones,\nshow_tens, seg_r"),
    ]
    arrow(draw, [(800, 210), (800, 650)], "on", head=False)
    draw.line((180, 650, 1620, 650), fill=INK, width=3)
    label(draw, (820, 610), "Prozesse / nebenläufige Anweisungen in phase1_top", 20, TEAL, True)
    for index, (title, body) in enumerate(procs):
        left = 40 + index * 350
        arrow(draw, [(left + 155, 650), (left + 155, 700)], "on")
        box(draw, (left, 700, left + 310, 810), title, body, "on", 23, 18)
    label(draw, (40, 840), "Alle Quellen liegen lokal in phase_1/src; ssd_driver, seg7_decoder, tick_gen und clock_pkg sind unveränderte Kopien aus prj_final.", 20, GRAY)
    image.save(path)


def seg_anatomy(path):
    image, draw = canvas(1800, 900, "AUFBAU EINER ZIFFER UND BITZUORDNUNG")
    draw_digit(draw, 110, 130, 330, "1111111", letters=True, h=600)
    label(draw, (275, 760), "7 LED-Segmente a … g (Dezimalpunkt hier ungenutzt)", 21, GRAY, anchor="ma")
    headers = ["Bit", "Segment", "VHDL-Port", "Pmod-Pin", "Arty-Pmod", "FPGA-Pin"]
    rows = [
        ("6", "g", "seg_r[6]", "AG", "JB9", "K15"),
        ("5", "f", "seg_r[5]", "AF", "JB8", "J18"),
        ("4", "e", "seg_r[4]", "AE", "JB7", "J17"),
        ("3", "d", "seg_r[3]", "AD", "JA10", "K16"),
        ("2", "c", "seg_r[2]", "AC", "JA9", "A18"),
        ("1", "b", "seg_r[1]", "AB", "JA8", "B18"),
        ("0", "a", "seg_r[0]", "AA", "JA7", "D13"),
        ("–", "Ziffer", "dsel_r", "C", "JB10", "J15"),
    ]
    x0, y0, widths, row_h = 640, 130, [80, 120, 170, 140, 150, 150], 64
    xs = [x0]
    for width in widths:
        xs.append(xs[-1] + width)
    draw.rectangle((x0, y0, xs[-1], y0 + row_h), fill=TEAL)
    for index, header in enumerate(headers):
        label(draw, ((xs[index] + xs[index + 1]) / 2, y0 + 18), header, 23, "white", True, "ma")
    for r, row in enumerate(rows):
        top = y0 + row_h * (r + 1)
        draw.rectangle((x0, top, xs[-1], top + row_h), fill=LIGHT if r % 2 == 0 else "white", outline="#DDE3E6")
        for index, cell in enumerate(row):
            label(draw, ((xs[index] + xs[index + 1]) / 2, top + 18), cell, 23, RED if index == 1 else INK, index == 1, "ma")
    label(draw, (x0, 730), "VHDL-Vektor seg(6 downto 0) = \"g f e d c b a\"  →  linkes Bit = g, rechtes Bit = a", 23, INK, True)
    label(draw, (x0, 770), "Logisch 1 = Segment leuchtet (aktiv High, gemeinsame Kathode).", 22, GRAY)
    label(draw, (x0, 806), "Beispiel 2 = 1011011: g, e, d, b, a an; f und c aus.", 22, GRAY)
    image.save(path)


def seg_circuit(path):
    image, draw = canvas(1800, 950, "ELEKTRISCHES PRINZIP: ZWEI ZIFFERN, GEMEINSAME ANODEN, GETRENNTE KATHODEN")
    names = ["AA (a)", "AB (b)", "AC (c)", "AD (d)", "AE (e)", "AF (f)", "AG (g)"]
    draw.rounded_rectangle((40, 110, 260, 720), radius=10, fill=LIGHT, outline=TEAL, width=3)
    label(draw, (150, 660), "FPGA", 30, INK, True, "ma")
    ys = [150 + i * 75 for i in range(7)]
    for index, y in enumerate(ys):
        label(draw, (245, y - 12), f"seg_r[{index}]", 20, INK, True, "ra")
    digit_x = {"links": 640, "rechts": 1120}
    bus_x = {name: x + 170 for name, x in digit_x.items()}
    for y, name in zip(ys, names):
        draw.line((260, y, 1420, y), fill=RED, width=4)
        label(draw, (290, y - 30), name, 19, RED, True)
    for name, x in digit_x.items():
        draw.rounded_rectangle((x - 40, 110, x + 230, 720), radius=12, outline=TEAL, width=3)
        label(draw, (x + 95, 728), f"Ziffer {name}", 23, TEAL, True, "ma")
        bus = bus_x[name]
        for y in ys:
            dot(draw, (x, y), "on", 6)
            draw.line((x, y, x, y + 30, x + 40, y + 30), fill=INK, width=3)
            draw.polygon([(x + 40, y + 18), (x + 40, y + 42), (x + 76, y + 30)], fill=SEG_ON)
            draw.line((x + 78, y + 16, x + 78, y + 44), fill=INK, width=4)
            draw.line((x + 78, y + 30, bus, y + 30), fill=INK, width=3)
            dot(draw, (bus, y + 30), "on", 5)
        draw.line((bus, ys[0] + 30 - 10, bus, 690), fill=INK, width=4)
        for y in ys[1:]:
            draw.rectangle((bus - 6, y - 4, bus + 6, y + 4), fill="white")
            draw.line((bus - 6, y, bus + 6, y), fill=RED, width=4)
        draw.line((bus, 690, bus, 790), fill=INK, width=4)
        label(draw, (bus - 12, 650), f"K_{name}", 19, INK, True, "ra")
    # Kathodenschalter
    for name, x in digit_x.items():
        bus = bus_x[name]
        box(draw, (bus - 95, 790, bus + 95, 870), "Schalter", "C = 1" if name == "links" else "C = 0", "on", 20, 18)
        draw.line((bus, 870, bus, 900), fill=INK, width=4)
        draw.line((bus - 30, 900, bus + 30, 900), fill=INK, width=4)
        draw.line((bus - 18, 910, bus + 18, 910), fill=INK, width=4)
        draw.line((bus - 6, 920, bus + 6, 920), fill=INK, width=4)
    box(draw, (40, 790, 260, 870), "dsel_r → C", "J15 / JB10", "hot", 22, 18)
    arrow(draw, [(260, 830), (bus_x["links"] - 95, 830)], "hot")
    draw.line((bus_x["links"] + 95, 830, bus_x["rechts"] - 95, 830), fill=RED, width=5)
    draw.ellipse((bus_x["rechts"] - 140, 815, bus_x["rechts"] - 110, 845), outline=RED, width=4)
    label(draw, (bus_x["rechts"] - 125, 795), "NOT", 16, RED, True, "ma")
    # Erklaerung
    x = 1440
    label(draw, (x, 130), "Regel", 28, INK, True)
    rules = [
        "Segment leuchtet, wenn",
        "Anode = 1  UND",
        "Kathode der Ziffer",
        "liegt auf GND.",
        "",
        "AA … AG sind für beide",
        "Ziffern gemeinsam.",
        "C wählt, welche",
        "Kathode leitet:",
        "→ immer nur eine",
        "Ziffer gleichzeitig.",
        "",
        "Daher Zeitmultiplex:",
        "9 Signalleitungen statt",
        "2 × 7 + 2.",
    ]
    for index, line in enumerate(rules):
        label(draw, (x, 180 + index * 34), line, 22, INK if index < 4 else GRAY, index < 4)
    label(draw, (x, 760), "Prinzipdarstellung;", 18, GRAY)
    label(draw, (x, 784), "Detailbeschaltung siehe", 18, GRAY)
    label(draw, (x, 808), "Digilent-Schaltplan.", 18, GRAY)
    label(draw, (x, 838), "C = 0 → rechts: Annahme", 18, RED)
    label(draw, (x, 862), "aus ssd_driver, am Board", 18, RED)
    label(draw, (x, 886), "zu bestätigen.", 18, RED)
    image.save(path)


def seg_digits(path):
    image, draw = canvas(1800, 620, "SEGMENTMUSTER DES DECODERS  (gfedcba, 1 = an)")
    for value in range(11):
        x = 50 + value * 160
        pattern = PATTERNS[value] if value < 10 else "1000000"
        draw.rounded_rectangle((x, 110, x + 140, 430), radius=10, fill=PANEL)
        draw_digit(draw, x + 25, 135, 90, pattern, on="#FF3B3B", off=SEG_OFF_DARK, h=170)
        caption = str(value) if value < 10 else "sonst"
        label(draw, (x + 70, 330), caption, 30, "white", True, "ma")
        label(draw, (x + 70, 450), pattern, 22, INK, True, "ma")
        lit = "".join(letter for i, letter in enumerate("abcdefg") if pattern[6 - i] == "1")
        label(draw, (x + 70, 485), lit, 19, GRAY, anchor="ma")
    label(draw, (50, 545), "„sonst“: Eingänge 10 … 15 erzeugen einen Mittelstrich; in Phase I treten sie durch Zerlegung (/10, mod 10) nie auf.", 22, GRAY)
    image.save(path)


def wave_level(draw, x0, y, width_per_unit, levels, high, low, color, width=4):
    points = []
    for index, level in enumerate(levels):
        yy = high if level else low
        xa = x0 + index * width_per_unit
        if points and points[-1][1] != yy:
            points.append((xa, yy))
        elif not points:
            points.append((xa, yy))
        points.append((xa + width_per_unit, yy))
    draw.line(points, fill=color, width=width)


def mux_timing(path):
    image, draw = canvas(1800, 860, "ZEITMULTIPLEX AM BEISPIEL „42“  (REFRESH_HZ = 500, DIV = 100.000)")
    x0, unit, slots = 330, 175, 8
    rows = [("tick (tick_gen)", 150), ("sel = dsel_r", 260), ("seg_r[6:0]", 370), ("rechte Ziffer (Einer)", 490), ("linke Ziffer (Zehner)", 590)]
    for name, y in rows:
        label(draw, (40, y + 8), name, 23, INK, True)
        draw.line((x0, y + 60, x0 + unit * slots, y + 60), fill="#E3E8EA", width=1)
    for slot in range(slots + 1):
        x = x0 + slot * unit
        dashed_line(draw, (x, 130), (x, 670), MUTED, 1, 6, 6)
        label(draw, (x, 680), f"{slot} ms", 19, GRAY, anchor="ma")
    for slot in range(1, slots + 1):
        x = x0 + slot * unit
        draw.line((x - 1, 205, x - 1, 160, x + 9, 160, x + 9, 205), fill=TEAL, width=4)
    draw.line((x0, 205, x0 + unit * slots, 205), fill=TEAL, width=4)
    wave_level(draw, x0, 0, unit, [slot % 2 for slot in range(slots)], 270, 315, TEAL)
    for slot in range(slots):
        x = x0 + slot * unit
        ones = slot % 2 == 0
        text = "Einer 2: 1011011" if ones else "Zehner 4: 1100110"
        draw.polygon([(x + 6, 400), (x + 18, 375), (x + unit - 18, 375), (x + unit - 6, 400),
                      (x + unit - 18, 425), (x + 18, 425)], outline=INK, fill="#FFF7E8" if ones else "#E9F5F6", width=2)
        label(draw, (x + unit / 2, 388), text, 17, INK, True, "ma")
        if ones:
            draw.rectangle((x + 4, 500, x + unit - 4, 545), fill=SEG_ON)
            label(draw, (x + unit / 2, 510), "„2“ leuchtet", 19, "white", True, "ma")
        else:
            draw.rectangle((x + 4, 600, x + unit - 4, 645), fill=SEG_ON)
            label(draw, (x + unit / 2, 610), "„4“ leuchtet", 19, "white", True, "ma")
    arrow(draw, [(x0, 725), (x0 + unit, 725)], "on", color=RED, width=3)
    arrow(draw, [(x0 + unit, 725), (x0, 725)], "on", color=RED, width=3)
    label(draw, (x0 + unit / 2, 735), "1 Slot = 1 ms", 20, RED, True, "ma")
    arrow(draw, [(x0 + 2 * unit, 725), (x0 + 4 * unit, 725)], "on", color=TEAL, width=3)
    arrow(draw, [(x0 + 4 * unit, 725), (x0 + 2 * unit, 725)], "on", color=TEAL, width=3)
    label(draw, (x0 + 3 * unit, 735), "1 Bild = 2 ms → 500 Hz je Ziffer", 20, TEAL, True, "ma")
    label(draw, (40, 790), "Jede Ziffer ist 50 % der Zeit an. Da 500 Hz weit über der Flimmergrenze des Auges (ca. 50 … 100 Hz) liegen,", 21, GRAY)
    label(draw, (40, 820), "erscheinen beide Ziffern gleichzeitig. Bei blank/show = 0 wird seg_r im jeweiligen Slot auf 0000000 gesetzt.", 21, GRAY)
    image.save(path)


def debounce_timing(path):
    image, draw = canvas(1800, 880, "ENTPRELLUNG IN btn_debounce  (DEBOUNCE_CYCLES = 1.000.000 → 10 ms)")
    x0, scale = 300, 46  # px pro ms, Achse 0 … 30 ms
    rows = [("btn (roh, prellt)", 140), ("sync(1)  (+2 Takte)", 250), ("cnt", 360), ("stable", 500), ("press_o", 610)]
    for name, y in rows:
        label(draw, (40, y + 10), name, 23, INK, True)
    for ms in range(0, 31, 5):
        x = x0 + ms * scale
        dashed_line(draw, (x, 130), (x, 690), MUTED, 1, 6, 6)
        label(draw, (x, 700), f"{ms} ms", 19, GRAY, anchor="ma")

    def to_x(ms):
        return x0 + ms * scale

    edges = [(0, 0), (2.0, 1), (2.25, 0), (2.5, 1), (2.7, 0), (3.0, 1), (16.0, 0), (16.3, 1), (16.6, 0)]

    def raw(offset, y_high, y_low, color):
        points = []
        level = 0
        for t, new_level in edges:
            x = to_x(t + offset)
            points.append((x, y_high if level else y_low))
            level = new_level
            points.append((x, y_high if level else y_low))
        points.append((to_x(30), y_high if level else y_low))
        draw.line(points, fill=color, width=4)

    raw(0, 150, 195, RED)
    raw(0.08, 260, 305, INK)
    # cnt: Rampen, die bei Rueckkehr zum alten Zustand neu beginnen
    base, top = 470, 370
    ramps = [(2.08, 2.33), (2.58, 2.78), (3.08, 13.08), (16.08, 16.38), (16.68, 26.68)]
    draw.line((to_x(0), base, to_x(30), base), fill="#E3E8EA", width=1)
    for start, end in ramps:
        height = (end - start) / 10 * (base - top)
        draw.line((to_x(start), base, to_x(end), base - height, to_x(end), base), fill=TEAL, width=3)
    dashed_line(draw, (to_x(0), top), (to_x(30), top), TEAL, 1, 8, 6)
    label(draw, (to_x(27.0), top - 30), "N − 1", 18, TEAL, True)
    # stable
    draw.line((to_x(0), 555, to_x(13.08), 555, to_x(13.08), 510, to_x(26.68), 510, to_x(26.68), 555, to_x(30), 555), fill=INK, width=4)
    # press
    draw.line((to_x(0), 665, to_x(13.08), 665, to_x(13.08), 620, to_x(13.25), 620, to_x(13.25), 665, to_x(30), 665), fill=RED, width=4)
    label(draw, (to_x(13.4), 616), "genau 1 Takt (10 ns) → +1", 20, RED, True)
    label(draw, (to_x(26.9), 625), "Loslassen: kein Puls", 19, GRAY)
    arrow(draw, [(to_x(3.08), 760), (to_x(13.08), 760)], "on", color=TEAL, width=3)
    arrow(draw, [(to_x(13.08), 760), (to_x(3.08), 760)], "on", color=TEAL, width=3)
    label(draw, (to_x(8.08), 770), "10 ms ununterbrochen abweichend", 20, TEAL, True, "ma")
    label(draw, (40, 820), "Jede Rückkehr zum alten Pegel setzt cnt auf 0. Erst nach N gleichen, abweichenden Abtastungen wird stable übernommen; nur 0 → 1 erzeugt press_o.", 21, GRAY)
    image.save(path)


def diamond(draw, cx, cy, w, h, text, status="on"):
    style = STYLE[status]
    draw.polygon([(cx, cy - h / 2), (cx + w / 2, cy), (cx, cy + h / 2), (cx - w / 2, cy)],
                 fill=style["fill"], outline=style["outline"], width=style["width"])
    text_lines(draw, cx, cy, [(line, font(21, True), INK) for line in text.split("\n")])


def counter_flow(path):
    image, draw = canvas(1800, 960, "SW0: RECHENREGELN DES ZÄHLERS PRO TAKTFLANKE")
    box(draw, (560, 95, 1240, 165), "rising_edge(CLK) und rst = 0 und sw_sync = 0001", "", "on", 23)
    columns = [
        ("press(0)?\nBTN0", "count = 99?", ("count ← 0", "Überlauf"), ("count ← count + 1", "")),
        ("press(1)?\nBTN1", "count ≥ 1?", ("count ← count − 1", ""), ("count bleibt 0", "untere Grenze")),
        ("press(2)?\nBTN2", "count ≥ 90?", ("count ← 0", "Überlauf"), ("count ← count + 10", "")),
        ("press(3)?\nBTN3", "count ≥ 10?", ("count ← count − 10", ""), ("count ← 0", "untere Grenze")),
    ]
    xs = [230, 650, 1070, 1490]
    arrow(draw, [(900, 165), (900, 190), (xs[0], 190), (xs[0], 220)], "on")
    for index, (question, condition, yes, no) in enumerate(columns):
        cx = xs[index]
        diamond(draw, cx, 300, 230, 150, question)
        if index < 3:
            arrow(draw, [(cx + 115, 300), (xs[index + 1] - 115, 300)], "on")
            label(draw, (cx + 125, 270), "nein", 19, GRAY, True)
        else:
            arrow(draw, [(cx + 115, 300), (1740, 300), (1740, 820), (1600, 820)], "on")
            label(draw, (cx + 125, 270), "nein", 19, GRAY, True)
        arrow(draw, [(cx, 375), (cx, 430)], "hot")
        label(draw, (cx + 10, 390), "ja", 19, RED, True)
        diamond(draw, cx, 510, 230, 150, condition, "hot")
        arrow(draw, [(cx - 115, 510), (cx - 120, 510), (cx - 120, 640)], "hot")
        arrow(draw, [(cx + 115, 510), (cx + 120, 510), (cx + 120, 640)], "hot")
        label(draw, (cx - 155, 560), "ja", 19, RED, True)
        label(draw, (cx + 128, 560), "nein", 19, RED, True)
        box(draw, (cx - 207, 640, cx - 28, 730), yes[0], yes[1], "hot", 18, 16)
        box(draw, (cx + 28, 640, cx + 207, 730), no[0], no[1], "hot", 18, 16)
    box(draw, (1300, 790, 1600, 850), "count bleibt", "", "on", 21)
    label(draw, (40, 880), "Priorität bei gleichzeitigen Pulsen: BTN0 > BTN1 > BTN2 > BTN3 (if/elsif) → höchstens eine Änderung pro Takt; count bleibt immer in 0 … 99.", 21, INK, True)
    label(draw, (40, 915), "Beispiele: 99 +1 → 0 | 0 −1 → 0 | 95 +10 → 0 | 7 −10 → 0 | 42 −10 → 32 | 19 +1 → 20", 21, GRAY)
    image.save(path)


def binary_mode(path):
    image, draw = canvas(1800, 900, "SW3: BINÄREINGABE ÜBER VIER TOGGLE-BITS")
    weights = [8, 4, 2, 1]
    example = "1011"
    for index in range(4):
        bit = 3 - index
        cx = 230 + index * 260
        draw.ellipse((cx - 55, 110, cx + 55, 220), fill=LIGHT, outline=TEAL, width=4)
        label(draw, (cx, 145), f"BTN{bit}", 28, INK, True, "ma")
        arrow(draw, [(cx, 220), (cx, 290)], "hot" if example[index] == "1" else "on")
        label(draw, (cx + 10, 236), f"press({bit})", 18, GRAY)
        box(draw, (cx - 105, 290, cx + 105, 410), f"Bit {bit}", "T-Flipflop:\nPuls → Bit invertieren", "hot" if example[index] == "1" else "on", 25, 17)
        arrow(draw, [(cx, 410), (cx, 470)], "hot" if example[index] == "1" else "on")
        draw.rounded_rectangle((cx - 60, 470, cx + 60, 570), radius=10, fill=RED if example[index] == "1" else "#E4E8EA")
        label(draw, (cx, 487), example[index], 56, "white" if example[index] == "1" else GRAY, True, "ma")
        label(draw, (cx, 590), f"Wertigkeit {weights[index]}", 22, INK, True, "ma")
        label(draw, (cx, 620), f"= {weights[index] * int(example[index])}", 22, GRAY, anchor="ma")
    label(draw, (100, 690), "bin_value = 1011 (binär) = 8 + 0 + 2 + 1 = 11", 34, INK, True)
    label(draw, (100, 745), "VHDL: bin_value <= bin_value xor unsigned(press);  (alle gleichzeitigen Pulse werden übernommen)", 22, GRAY)
    label(draw, (100, 785), "Die Anzeige zeigt den Wert dezimal: 0 … 9 einstellig, 10 … 15 zweistellig.", 22, GRAY)
    x = 1250
    label(draw, (x, 110), "Beispielsequenz", 28, INK, True)
    sequence = [("Start / Reset", "0000", 0), ("BTN0", "0001", 1), ("BTN1", "0011", 3), ("BTN3", "1011", 11), ("BTN1", "1001", 9), ("BTN2", "1101", 13)]
    for index, (action, bits, value) in enumerate(sequence):
        y = 165 + index * 98
        label(draw, (x, y + 18), action, 22, GRAY, True)
        label(draw, (x + 150, y + 14), bits, 30, INK, True)
        mini_display(draw, x + 280, y, display_text(value), 30)
    label(draw, (x, 770), "Zweiter Druck auf dieselbe Taste", 20, GRAY)
    label(draw, (x, 798), "löscht das Bit wieder (Toggle).", 20, GRAY)
    image.save(path)


def mode_table(path):
    image, draw = canvas(1800, 980, "ALLE 16 SCHALTERSTELLUNGEN  (sw = SW3 SW2 SW1 SW0)")
    meaning = {"0001": ("Zähler", "SW0", 42), "0010": ("Mark", "SW1", 91),
               "0100": ("Maxi", "SW2", 93), "1000": ("Binär", "SW3", 11)}
    for value in range(16):
        bits = format(value, "04b")
        col, row = value % 4, value // 4
        x, y = 50 + col * 430, 100 + row * 210
        valid = bits in meaning
        draw.rounded_rectangle((x, y, x + 400, y + 190), radius=12, fill=HOT_FILL if valid else "#F7F8F9",
                               outline=RED if valid else MUTED, width=4 if valid else 2)
        label(draw, (x + 22, y + 18), bits, 40, INK if valid else MUTED_TEXT, True)
        if valid:
            name, sw, example = meaning[bits]
            label(draw, (x + 22, y + 72), f"{sw}: {name}", 26, RED, True)
            label(draw, (x + 22, y + 112), "Beispiel" if sw in ("SW0", "SW3") else "fest", 20, GRAY)
            mini_display(draw, x + 250, y + 30, display_text(example), 50)
        else:
            label(draw, (x + 22, y + 72), "keine gültige Wahl" if bits != "0000" else "kein Schalter", 24, GRAY, True)
            label(draw, (x + 22, y + 112), "show = 0 → dunkel", 20, GRAY)
            mini_display(draw, x + 250, y + 30, "  ", 50)
    label(draw, (50, 945), "Nur „genau ein Schalter = 1“ (one-hot) wählt eine Quelle. Alle anderen 12 Kombinationen ergeben eine dunkle Anzeige.", 22, INK, True)
    image.save(path)


def display_path(path):
    image, draw = canvas(1800, 900, "ANZEIGEPFAD: VON value ZU seg_r / dsel_r  (Beispiel value = 42)")
    box(draw, (40, 250, 220, 350), "value", "= 42 (0 … 99)", "hot", 26, 20)
    box(draw, (300, 130, 520, 230), "÷ 10", "tens = 4", "on", 26, 20)
    box(draw, (300, 370, 520, 470), "mod 10", "ones = 2", "on", 26, 20)
    arrow(draw, [(220, 300), (260, 300), (260, 180), (300, 180)], "hot")
    arrow(draw, [(260, 300), (260, 420), (300, 420)], "hot")
    draw.polygon([(600, 120), (700, 160), (700, 440), (600, 480)], fill=LIGHT, outline=TEAL, width=3)
    label(draw, (650, 285), "MUX", 24, INK, True, "ma")
    arrow(draw, [(520, 180), (600, 180)], "on")
    arrow(draw, [(520, 420), (600, 420)], "on")
    label(draw, (610, 168), "1", 20, GRAY, True)
    label(draw, (610, 408), "0", 20, GRAY, True)
    box(draw, (780, 250, 1010, 350), "seg7_decoder", "digit → gfedcba", "on", 24, 19)
    arrow(draw, [(700, 300), (780, 300)], "on")
    label(draw, (712, 266), "mux", 18, GRAY)
    box(draw, (1090, 240, 1310, 360), "Ausblendung", "sel = 0: show\nsel = 1: show_tens", "on", 24, 18)
    arrow(draw, [(1010, 300), (1090, 300)], "on")
    label(draw, (1013, 268), "driver_seg", 15, GRAY)
    box(draw, (1390, 250, 1560, 350), "seg_r[6:0]", "AA … AG", "hot", 24, 19)
    arrow(draw, [(1310, 300), (1390, 300)], "hot")
    box(draw, (560, 560, 780, 660), "tick_gen", "Puls alle 1 ms", "on", 24, 19)
    box(draw, (860, 560, 1080, 660), "sel-Register", "toggelt je Puls", "on", 24, 19)
    arrow(draw, [(780, 610), (860, 610)], "on")
    arrow(draw, [(1080, 610), (1390, 610)], "hot")
    arrow(draw, [(970, 560), (970, 520), (650, 520), (650, 462)], "on")
    arrow(draw, [(1200, 610), (1200, 360)], "on")
    dot(draw, (1200, 610), "hot")
    box(draw, (1390, 560, 1560, 660), "dsel_r", "→ Pin C", "hot", 24, 19)
    box(draw, (1630, 250, 1770, 660), "Pmod\nSSD", "", "on", 26)
    arrow(draw, [(1560, 300), (1630, 300)], "hot")
    arrow(draw, [(1560, 610), (1630, 610)], "hot")
    box(draw, (1090, 110, 1310, 190), "show, show_tens", "vom Modus-Decoder", "on", 20, 17)
    arrow(draw, [(1200, 190), (1200, 240)], "on")
    # Tabelle der beiden Slots
    draw.rounded_rectangle((40, 700, 1770, 880), radius=10, fill=LIGHT)
    rows = [("sel = 0 (1 ms)", "ones = 2", "1011011", "show = 1 → durchgeschaltet", "rechte Ziffer zeigt 2", "2"),
            ("sel = 1 (1 ms)", "tens = 4", "1100110", "show_tens = 1 (42 ≥ 10)", "linke Ziffer zeigt 4", "4")]
    for index, row in enumerate(rows):
        y = 720 + index * 80
        for col, (x, text) in enumerate(zip([60, 280, 470, 680, 1100], row[:5])):
            label(draw, (x, y + 16), text, 23, INK if col in (0, 2) else GRAY, col in (0, 2))
        draw.rounded_rectangle((1500, y, 1560, y + 70), radius=6, fill=PANEL)
        draw_digit(draw, 1512, y + 8, 36, PATTERNS[int(row[5])], on="#FF3B3B", off=SEG_OFF_DARK, h=54)
    label(draw, (1590, 740), "Für value < 10", 19, GRAY)
    label(draw, (1590, 765), "ist show_tens = 0", 19, GRAY)
    label(draw, (1590, 790), "→ linke Ziffer", 19, GRAY)
    label(draw, (1590, 815), "dunkel.", 19, GRAY)
    image.save(path)


def wiring(path):
    image, draw = canvas(1800, 900, "VERDRAHTUNG: ARTY A7-35T (JA/JB, UNTERE REIHE) → PMOD SSD (J1/J2)")
    colors = ["#E8282F", "#F08C00", "#2F9E44", "#1971C2", "#495057", "#C2255C"]

    def header(x, y, name, top, bottom, fpga, active_row="bottom"):
        label(draw, (x, y - 40), name, 28, INK, True)
        for row, names in enumerate([top, bottom]):
            for index, text in enumerate(names):
                left, upper = x + index * 92, y + row * 70
                active = (row == 1) == (active_row == "bottom")
                fill = colors[index] if active else "#F1F3F4"
                draw.rounded_rectangle((left, upper, left + 84, upper + 62), radius=6, fill=fill,
                                       outline=INK if active else MUTED, width=2)
                label(draw, (left + 42, upper + 8), text, 20, "white" if active else MUTED_TEXT, True, "ma")
                if active and index < 4 and fpga:
                    label(draw, (left + 42, upper + 34), fpga[index], 17, "white", False, "ma")
        return x + 6 * 92

    draw.rounded_rectangle((40, 100, 760, 820), radius=16, outline=TEAL, width=3)
    label(draw, (60, 112), "Arty A7-35T", 30, TEAL, True)
    end_ja = header(110, 230, "Pmod JA", ["1", "2", "3", "4", "GND", "VCC"], ["7", "8", "9", "10", "GND", "VCC"],
                    ["D13", "B18", "A18", "K16"])
    end_jb = header(110, 500, "Pmod JB", ["1", "2", "3", "4", "GND", "VCC"], ["7", "8", "9", "10", "GND", "VCC"],
                    ["J17", "J18", "K15", "J15"])
    label(draw, (110, 660), "Oben (1 … 6): frei. Unten (7 … 12): genutzt.", 20, GRAY)
    label(draw, (110, 700), "Onboard: SW0 … SW3 = A8, C11, C10, A10", 20, GRAY)
    label(draw, (110, 730), "BTN0 … BTN3 = D9, C9, B9, B8", 20, GRAY)
    label(draw, (110, 760), "RESET (ck_rst) = C2, CLK100MHZ = E3", 20, GRAY)

    draw.rounded_rectangle((1060, 100, 1760, 820), radius=16, outline=RED, width=3)
    label(draw, (1080, 112), "Pmod SSD", 30, RED, True)
    for y, name, names in [(300, "J1", ["AA", "AB", "AC", "AD", "GND", "VCC"]), (570, "J2", ["AE", "AF", "AG", "C", "GND", "VCC"])]:
        label(draw, (1130, y - 40), name, 28, INK, True)
        for index, text in enumerate(names):
            left = 1130 + index * 92
            draw.rounded_rectangle((left, y, left + 84, y + 62), radius=6, fill=colors[index], outline=INK, width=2)
            label(draw, (left + 42, y + 18), text, 22, "white", True, "ma")
    draw.line((end_ja + 10, 331, 1120, 331), fill=INK, width=16)
    draw.line((end_jb + 10, 601, 1120, 601), fill=INK, width=16)
    label(draw, (790, 345), "6-poliges Kabel / Direktsteckung", 19, GRAY)
    label(draw, (790, 615), "6-poliges Kabel / Direktsteckung", 19, GRAY)
    mini_display(draw, 1300, 690, "42", 40)
    label(draw, (60, 840), "Farben zeigen die 1:1-Zuordnung: JA7 → AA, JA8 → AB, JA9 → AC, JA10 → AD, JB7 → AE, JB8 → AF, JB9 → AG, JB10 → C; Pin 11/12 = GND/VCC (3,3 V).", 20, INK)
    image.save(path)


def generate_all(directory):
    directory.mkdir(parents=True, exist_ok=True)
    architecture(directory / "architektur.png")
    for mode in ["sw0", "sw1", "sw2", "sw3", "off"]:
        architecture(directory / f"modus_{mode}.png", mode)
    hierarchy(directory / "hierarchie.png")
    seg_anatomy(directory / "segment_aufbau.png")
    seg_circuit(directory / "segment_elektrisch.png")
    seg_digits(directory / "segment_muster.png")
    mux_timing(directory / "multiplex_timing.png")
    debounce_timing(directory / "entprell_timing.png")
    counter_flow(directory / "zaehler_regeln.png")
    binary_mode(directory / "binaer_eingabe.png")
    mode_table(directory / "schalter_tabelle.png")
    display_path(directory / "anzeigepfad.png")
    wiring(directory / "verdrahtung.png")
