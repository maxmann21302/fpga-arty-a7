"""Technische Grafiken fuer die Phase-II-Dokumentation (Pillow)."""
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


def two_digits(value):
    """Anzeige wie im RTL: immer zweistellig mit fuehrender Null, None = dunkel."""
    return "  " if value is None else f"{value:02d}"


def dual_display(draw, x, y, left, right, digit_w=30, gap=14, captions=None):
    """Beide Pmod SSD nebeneinander: links JC/JD, rechts JA/JB."""
    width, height = mini_display(draw, x, y, two_digits(left), digit_w)
    mini_display(draw, x + width + gap, y, two_digits(right), digit_w)
    if captions:
        label(draw, (x + width / 2, y + height + 6), captions[0], max(14, digit_w // 2), GRAY, True, "ma")
        label(draw, (x + width * 1.5 + gap, y + height + 6), captions[1], max(14, digit_w // 2), GRAY, True, "ma")
    return 2 * width + gap, height


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


# --------------------------------------------------------------------------- Signalfluss

def signal_flow(path):
    image, draw = canvas(1600, 650, "PHASE 2  |  SIGNALFLUSS")
    blocks = [("100 MHz", ""), ("Zeitbasis", "1 s  |  10 ms"), ("Zähler / Stoppuhr", "00 … 99 | 0000 … 9999\n00.00 … 99.99"),
              ("BCD + 2 × SSD", "Mux + Decoder\nJA/JB  |  JC/JD")]
    xs = [55, 445, 835, 1225]
    for x, (title, body) in zip(xs, blocks):
        box(draw, (x, 170, x + 310, 340), title, body, "on", 27, 20)
    for x in xs[:-1]:
        arrow(draw, [(x + 310, 255), (x + 390, 255)], "on")
    box(draw, (835, 70, 1145, 130), "SW0 … SW2, BTN0 … BTN2", "", "on", 20)
    arrow(draw, [(990, 130), (990, 170)], "on")
    draw.line((90, 465, 1480, 465), fill=RED, width=4)
    for x in xs[1:]:
        draw.line((x + 155, 355, x + 155, 465), fill=RED, width=3)
    label(draw, (60, 400), "Reset", 22, RED, True)
    label(draw, (60, 520), "Gemeinsamer Systemtakt: 100 MHz  |  ck_rst: asynchron anfordern, synchron freigeben  |  Zählen nur über 1-Takt-Freigabepulse", 22, GRAY)
    image.save(path)


# --------------------------------------------------------------------------- Architektur

MODE_INFO = {
    None: dict(title="GESAMTARCHITEKTUR  |  phase2_top", bits=None, show=None, info=[
        "Eine Taktdomäne (100 MHz). Zwei tick_gen erzeugen 1-Takt-Pulse: tick_sec jede Sekunde, tick_cs alle 10 ms (nur wenn running = 1).",
        "Zähler A, Zähler B und die Stoppuhr laufen immer im Hintergrund; der Modus-Decoder wählt nur aus, was angezeigt wird.",
        "Der Anzeige-MUX liefert je SSD einen Wert 0 … 99 plus Freigabe; to_bcd2 zerlegt, zwei ssd_driver multiplexen unabhängig.",
    ]),
    "sw0": dict(title="SW0 = 1  |  SEKUNDENZÄHLER 00 … 99", bits="0001", show=(None, 42), info=[
        "tick_sec erhöht cnt_a einmal pro Sekunde: 00, 01, …, 99, 00. Angezeigt auf dem rechten SSD (JA/JB).",
        "Das linke SSD (JC/JD) ist dunkel: show_l = 0 → blank_l = 1 → seg_l = 0000000; dsel_l läuft weiter.",
        "Taster wirken nicht. Zähler B und Stoppuhr laufen im Hintergrund weiter; nur ck_rst setzt alles zurück.",
    ]),
    "sw1": dict(title="SW1 = 1  |  SEKUNDENZÄHLER 0000 … 9999", bits="0010", show=(12, 34), info=[
        "Zähler B ist als zwei Paare 0 … 99 aufgebaut: cnt_b_lo (Zehner/Einer) und cnt_b_hi (Tausender/Hunderter).",
        "Bei cnt_b_lo = 99 erzeugt tick_sec den Übertrag in cnt_b_hi. 9999 + 1 → 0000. Führende Nullen werden angezeigt.",
        "Linkes SSD (JC/JD) = cnt_b_hi, rechtes SSD (JA/JB) = cnt_b_lo. Beispielanzeige: 1234 s.",
    ]),
    "sw2": dict(title="SW2 = 1  |  STOPPUHR 00.00 … 99.99 s", bits="0100", show=(12, 34), info=[
        "BTN0 Start, BTN1 Stopp, BTN2 Nullen (nur im Stopp). Die Tasten wirken nur, solange sw_sync = 0100 ist.",
        "running gibt den 10-ms-Vorteiler frei; tick_cs zählt stop_cs (Hundertstel), Übertrag nach stop_s (Sekunden).",
        "Links (JC/JD) Sekunden, rechts (JA/JB) Hundertstel. 99.99 → 00.00 und weiter. Beispielanzeige: 12.34 s.",
    ]),
    "off": dict(title="KEIN / MEHRERE SCHALTER ODER SW3  |  BEIDE SSD DUNKEL", bits="0011", show=(None, None), info=[
        "Jede Kombination außer 0001, 0010, 0100 ergibt show_l = show_r = 0 (Beispiel oben: SW0 + SW1 = 0011).",
        "Beide seg7_decoder erhalten blank = 1 → seg_l = seg_r = 0000000. Beide ssd_driver laufen weiter.",
        "Taster werden ignoriert. Alle Zähler und eine laufende Stoppuhr zählen im Hintergrund weiter.",
    ]),
}

BTN_PATH = {"btn", "debounce", "press", "gate", "en_gate", "ctrl_in"}
DARK = {"dark", "dark_out"}
LEFT_PATH = {"l_in", "bcd_l", "l_mid", "drv_l", "l_out", "pmod_l"}
RIGHT_PATH = {"r_in", "bcd_r", "r_mid", "drv_r", "r_out", "pmod_r"}
HOT = {
    None: set(),
    "sw0": {"tick_sec_gen", "tick_sec_a", "cnt_a", "cnt_a_out", "mux"} | RIGHT_PATH,
    "sw1": {"tick_sec_gen", "tick_sec_b", "cnt_b", "cnt_b_out", "mux"} | LEFT_PATH | RIGHT_PATH,
    "sw2": BTN_PATH | {"ctrl", "running", "tick_cs_gen", "tick_cs", "zero", "clr", "stop_cnt", "stop_out", "mux"}
           | LEFT_PATH | RIGHT_PATH,
    "off": DARK | {"mux"} | LEFT_PATH | RIGHT_PATH,
}
OFF = {
    None: set(),
    "sw0": BTN_PATH | DARK | LEFT_PATH,
    "sw1": BTN_PATH | DARK,
    "sw2": DARK,
    "off": BTN_PATH,
}


def architecture(path, mode=None):
    info = MODE_INFO[mode]
    image, draw = canvas(1800, 1000, info["title"])

    def st(key):
        if key in HOT[mode]:
            return "hot"
        return "off" if key in OFF[mode] else "on"

    if info["bits"]:
        switch_row(draw, 1000, 18, info["bits"])
        label(draw, (1420, 22), "Anzeige:", 20, GRAY, True)
        dual_display(draw, 1505, 14, *info["show"], digit_w=24, gap=10)

    # Eingaenge
    box(draw, (40, 105, 210, 175), "CLK100MHZ", "E3, 100 MHz", st("clk"), 22, 18)
    box(draw, (40, 225, 210, 295), "ck_rst", "C2, aktiv Low", st("rst"), 22, 18)
    box(draw, (40, 385, 210, 455), "sw[3:0]", "Schiebeschalter", st("sw"), 22, 18)
    box(draw, (40, 600, 210, 670), "btn[2:0]", "BTN0 … BTN2", st("btn"), 22, 18)
    label(draw, (225, 128), "→ taktet alle Register", 19, GRAY)

    # Synchronisation
    box(draw, (260, 205, 500, 315), "Reset-Sync", "2 FF, async. Anforderung\nsynchrone Freigabe", st("rst_sync"), 23, 18)
    box(draw, (260, 370, 500, 470), "Schalter-Sync", "2 FF → sw_sync[3:0]", st("sw_sync"), 23, 18)
    box(draw, (260, 560, 500, 700), "3 × btn_debounce", "2 FF + 10 ms stabil\n→ press[2:0]\n1-Takt-Puls je Druck", st("debounce"), 23, 18)
    arrow(draw, [(210, 260), (260, 260)], st("rst"))
    arrow(draw, [(210, 420), (260, 420)], st("sw"))
    arrow(draw, [(210, 635), (260, 635)], st("btn"))
    label(draw, (262, 322), "rst → alle Register", 17, RED)

    # Zeitbasis, Modus-Decoder, Tasten-Freigabe
    box(draw, (560, 105, 790, 195), "tick_gen  1 s", "DIV = CLK_HZ → tick_sec", st("tick_sec_gen"), 23, 18)
    box(draw, (560, 370, 790, 470), "Modus-Decoder", "one-hot: 0001 / 0010 / 0100\nsonst dunkel", st("decoder"), 23, 17)
    box(draw, (560, 540, 790, 640), "Tasten-Freigabe", "nur sw_sync = 0100\nstart / stop / zero", st("gate"), 23, 17)
    box(draw, (560, 700, 790, 800), "tick_gen  10 ms", "DIV = CLK_HZ / 100\nen = running, clr = zero", st("tick_cs_gen"), 23, 17)
    arrow(draw, [(500, 420), (560, 420)], st("sw_line"))
    arrow(draw, [(500, 590), (560, 590)], st("press"))
    label(draw, (505, 562), "press", 17, LINE[st("press")][0], True)
    arrow(draw, [(675, 470), (675, 540)], st("en_gate"), dashed=True)
    label(draw, (684, 490), "en", 17, LINE[st("en_gate")][0], True)
    arrow(draw, [(640, 640), (640, 700)], st("clr"))
    label(draw, (575, 655), "clr", 17, LINE[st("clr")][0], True)

    # Quellen
    box(draw, (880, 105, 1150, 195), "Zähler A  (SW0)", "cnt_a 0 … 99", st("cnt_a"), 23, 18)
    box(draw, (880, 225, 1150, 335), "Zähler B  (SW1)", "cnt_b_hi | cnt_b_lo\n0000 … 9999", st("cnt_b"), 23, 18)
    box(draw, (880, 355, 1150, 425), "keine Quelle", "0 / ≥ 2 Schalter, SW3", st("dark"), 21, 17)
    box(draw, (880, 540, 1150, 640), "Start / Stopp", "running-Flipflop", st("ctrl"), 23, 18)
    box(draw, (880, 700, 1150, 800), "Stoppuhr  (SW2)", "stop_s | stop_cs\n00.00 … 99.99", st("stop_cnt"), 23, 18)
    arrow(draw, [(790, 150), (880, 150)], st("tick_sec_a"))
    arrow(draw, [(835, 150), (835, 280), (880, 280)], st("tick_sec_b"))
    label(draw, (796, 118), "tick_sec", 17, LINE[st("tick_sec_a")][0], True)
    arrow(draw, [(790, 590), (880, 590)], st("ctrl_in"))
    arrow(draw, [(880, 622), (830, 622), (830, 725), (790, 725)], st("running"))
    label(draw, (836, 650), "running", 17, LINE[st("running")][0], True)
    arrow(draw, [(790, 770), (880, 770)], st("tick_cs"))
    label(draw, (796, 777), "tick_cs", 17, LINE[st("tick_cs")][0], True)
    arrow(draw, [(1015, 640), (1015, 700)], st("zero"))
    label(draw, (1025, 655), "zero", 17, LINE[st("zero")][0], True)

    # Anzeige-MUX
    box(draw, (1185, 105, 1280, 800), "Anzeige-\nMUX", "", st("mux"), 17)
    for key, y in [("cnt_a_out", 150), ("cnt_b_out", 280), ("dark_out", 390), ("stop_out", 750)]:
        arrow(draw, [(1150, y), (1185, y)], st(key))
    arrow(draw, [(790, 455), (1185, 455)], st("sel"))
    label(draw, (800, 470), "Auswahl (Modus)", 17, LINE[st("sel")][0], True)

    # zwei Anzeigepfade
    box(draw, (1320, 220, 1530, 340), "to_bcd2  links", "bcd_l\nblank_l = not show_l", st("bcd_l"), 21, 17)
    box(draw, (1320, 550, 1530, 670), "to_bcd2  rechts", "bcd_r\nblank_r = not show_r", st("bcd_r"), 21, 17)
    arrow(draw, [(1280, 280), (1320, 280)], st("l_in"))
    arrow(draw, [(1280, 610), (1320, 610)], st("r_in"))
    label(draw, (1283, 248), "val_l", 15, LINE[st("l_in")][0], True)
    label(draw, (1283, 578), "val_r", 15, LINE[st("r_in")][0], True)
    box(draw, (1580, 200, 1770, 360), "ssd_driver", "display_l\n1 ms Multiplex", st("drv_l"), 22, 17)
    box(draw, (1580, 530, 1770, 690), "ssd_driver", "display_r\n1 ms Multiplex", st("drv_r"), 22, 17)
    arrow(draw, [(1530, 280), (1580, 280)], st("l_mid"))
    arrow(draw, [(1530, 610), (1580, 610)], st("r_mid"))
    box(draw, (1580, 400, 1770, 480), "SSD links", "JC/JD: seg_l, dsel_l", st("pmod_l"), 21, 16)
    box(draw, (1580, 730, 1770, 810), "SSD rechts", "JA/JB: seg_r, dsel_r", st("pmod_r"), 21, 16)
    arrow(draw, [(1675, 360), (1675, 400)], st("l_out"))
    arrow(draw, [(1675, 690), (1675, 730)], st("r_out"))

    # Info-Panel
    draw.rounded_rectangle((40, 840, 1760, 985), radius=10, fill=LIGHT)
    for index, line in enumerate(info["info"]):
        label(draw, (64, 854 + index * 42), line, 23, INK if index == 0 else GRAY, index == 0)
    image.save(path)


# --------------------------------------------------------------------------- weitere Grafiken

def hierarchy(path):
    image, draw = canvas(1800, 920, "MODULHIERARCHIE UND PROZESSE")
    box(draw, (500, 100, 1300, 210), "phase2_top", "Ports: CLK100MHZ, ck_rst, sw, btn, seg_r, dsel_r, seg_l, dsel_l", "hot", 30, 19)
    box(draw, (40, 290, 400, 400), "btn_debounce  × 3", "for-generate gen_btn(0 … 2)\nSync + Entprellung + Puls", "on", 24, 18)
    box(draw, (440, 290, 800, 400), "tick_gen  × 2", "u_tick_sec: DIV = CLK_HZ\nu_tick_cs: DIV = CLK_HZ / 100", "on", 24, 18)
    box(draw, (840, 290, 1290, 400), "ssd_driver  × 2", "display_l (JC/JD), display_r (JA/JB)", "on", 24, 18)
    box(draw, (1430, 290, 1760, 400), "clock_pkg", "bcd2_t, to_bcd2(), max_nat()", "off", 23, 18)
    box(draw, (840, 480, 1050, 580), "tick_gen", "Puls je 1 ms", "on", 23, 17)
    box(draw, (1080, 480, 1290, 580), "seg7_decoder", "BCD → gfedcba", "on", 23, 17)
    arrow(draw, [(620, 210), (620, 250), (220, 250), (220, 290)], "hot")
    arrow(draw, [(620, 250), (620, 290)], "hot")
    arrow(draw, [(1065, 210), (1065, 290)], "hot")
    arrow(draw, [(945, 400), (945, 480)], "on")
    arrow(draw, [(1185, 400), (1185, 480)], "on")
    arrow(draw, [(1430, 345), (1290, 345)], "on", dashed=True)
    label(draw, (1330, 312), "use", 17, GRAY)
    label(draw, (40, 420), "rot = von phase2_top instanziiert", 19, RED)
    label(draw, (40, 448), "blau = Unterinstanzen je ssd_driver", 19, TEAL)
    procs = [
        ("Reset-Sync", "reset_sync(1:0) → rst"),
        ("Schalter-Sync", "sw_meta → sw_sync"),
        ("Sekunden-Prozess", "cnt_a, cnt_b_lo,\ncnt_b_hi"),
        ("Stoppuhr-Prozess", "running, stop_cs,\nstop_s"),
        ("Anzeige-MUX", "val_l/r, show_l/r"),
        ("nebenläufig", "sw_start/stop/zero,\nbcd_l/r, blank_l/r"),
    ]
    arrow(draw, [(900, 210), (900, 245)], "on", head=False)
    draw.line((900, 245, 1380, 245), fill=INK, width=3)
    draw.line((1380, 245, 1380, 650), fill=INK, width=3)
    draw.line((170, 650, 1630, 650), fill=INK, width=3)
    label(draw, (40, 610), "Prozesse / nebenläufige Anweisungen in phase2_top", 20, TEAL, True)
    for index, (title, body) in enumerate(procs):
        left = 40 + index * 292
        arrow(draw, [(left + 130, 650), (left + 130, 700)], "on")
        box(draw, (left, 700, left + 260, 810), title, body, "on", 22, 17)
    label(draw, (40, 850), "Alle Quellen liegen lokal in phase_2/src. btn_debounce, ssd_driver, seg7_decoder, tick_gen und clock_pkg sind unveränderte Kopien aus Phase I;", 20, GRAY)
    label(draw, (40, 878), "neu ist nur phase2_top. tick_gen wird erstmals mit en/clr genutzt (Stoppuhr-Vorteiler).", 20, GRAY)
    image.save(path)


def seg_anatomy(path):
    image, draw = canvas(1800, 900, "AUFBAU EINER ZIFFER UND BITZUORDNUNG (BEIDE PMOD SSD)")
    draw_digit(draw, 90, 130, 300, "1111111", letters=True, h=560)
    label(draw, (240, 720), "7 LED-Segmente a … g", 21, GRAY, anchor="ma")
    label(draw, (240, 750), "(Dezimalpunkt nicht angeschlossen)", 19, GRAY, anchor="ma")
    headers = ["Bit", "Seg.", "Pmod", "rechts: Port", "Arty", "Pin", "links: Port", "Arty", "Pin"]
    rows = [
        ("6", "g", "AG", "seg_r[6]", "JB9", "K15", "seg_l[6]", "JD9", "H2"),
        ("5", "f", "AF", "seg_r[5]", "JB8", "J18", "seg_l[5]", "JD8", "D2"),
        ("4", "e", "AE", "seg_r[4]", "JB7", "J17", "seg_l[4]", "JD7", "E2"),
        ("3", "d", "AD", "seg_r[3]", "JA10", "K16", "seg_l[3]", "JC10", "U13"),
        ("2", "c", "AC", "seg_r[2]", "JA9", "A18", "seg_l[2]", "JC9", "T13"),
        ("1", "b", "AB", "seg_r[1]", "JA8", "B18", "seg_l[1]", "JC8", "V14"),
        ("0", "a", "AA", "seg_r[0]", "JA7", "D13", "seg_l[0]", "JC7", "U14"),
        ("–", "Ziffer", "C", "dsel_r", "JB10", "J15", "dsel_l", "JD10", "G2"),
    ]
    x0, y0, widths, row_h = 460, 130, [60, 90, 90, 160, 100, 90, 160, 100, 90], 62
    xs = [x0]
    for width in widths:
        xs.append(xs[-1] + width)
    draw.rectangle((x0, y0, xs[-1], y0 + row_h), fill=TEAL)
    for index, header in enumerate(headers):
        label(draw, ((xs[index] + xs[index + 1]) / 2, y0 + 18), header, 21, "white", True, "ma")
    for r, row in enumerate(rows):
        top = y0 + row_h * (r + 1)
        draw.rectangle((x0, top, xs[-1], top + row_h), fill=LIGHT if r % 2 == 0 else "white", outline="#DDE3E6")
        for index, cell in enumerate(row):
            label(draw, ((xs[index] + xs[index + 1]) / 2, top + 18), cell, 21, RED if index == 1 else INK, index == 1, "ma")
    label(draw, (x0, 720), "VHDL-Vektor seg(6 downto 0) = \"g f e d c b a\"  →  linkes Bit = g, rechtes Bit = a", 23, INK, True)
    label(draw, (x0, 760), "Logisch 1 = Segment leuchtet (aktiv High, gemeinsame Kathode). Beide SSD nutzen dieselbe Bitreihenfolge.", 21, GRAY)
    label(draw, (x0, 794), "Rechtes SSD: JA/JB untere Reihe (wie Phase I). Linkes SSD: JC/JD untere Reihe (Pins 7 … 10).", 21, GRAY)
    image.save(path)


def seg_circuit(path):
    image, draw = canvas(1800, 950, "ELEKTRISCHES PRINZIP JE PMOD SSD: GEMEINSAME ANODEN, GETRENNTE KATHODEN")
    names = ["AA (a)", "AB (b)", "AC (c)", "AD (d)", "AE (e)", "AF (f)", "AG (g)"]
    draw.rounded_rectangle((40, 110, 260, 720), radius=10, fill=LIGHT, outline=TEAL, width=3)
    label(draw, (150, 660), "FPGA", 30, INK, True, "ma")
    ys = [150 + i * 75 for i in range(7)]
    for index, y in enumerate(ys):
        label(draw, (245, y - 12), f"seg[{index}]", 20, INK, True, "ra")
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
    for name, x in digit_x.items():
        bus = bus_x[name]
        box(draw, (bus - 95, 790, bus + 95, 870), "Schalter", "C = 1" if name == "links" else "C = 0", "on", 20, 18)
        draw.line((bus, 870, bus, 900), fill=INK, width=4)
        draw.line((bus - 30, 900, bus + 30, 900), fill=INK, width=4)
        draw.line((bus - 18, 910, bus + 18, 910), fill=INK, width=4)
        draw.line((bus - 6, 920, bus + 6, 920), fill=INK, width=4)
    box(draw, (40, 790, 260, 870), "dsel → C", "dsel_r / dsel_l", "hot", 22, 18)
    arrow(draw, [(260, 830), (bus_x["links"] - 95, 830)], "hot")
    draw.line((bus_x["links"] + 95, 830, bus_x["rechts"] - 95, 830), fill=RED, width=5)
    draw.ellipse((bus_x["rechts"] - 140, 815, bus_x["rechts"] - 110, 845), outline=RED, width=4)
    label(draw, (bus_x["rechts"] - 125, 795), "NOT", 16, RED, True, "ma")
    x = 1440
    label(draw, (x, 130), "Regel", 28, INK, True)
    rules = [
        "Segment leuchtet, wenn",
        "Anode = 1  UND",
        "Kathode der Ziffer",
        "liegt auf GND.",
        "",
        "AA … AG sind für beide",
        "Ziffern eines SSD gemeinsam.",
        "C wählt die Kathode:",
        "→ je SSD immer nur",
        "eine Ziffer gleichzeitig.",
        "",
        "Phase II: zwei SSD,",
        "2 × 9 = 18 Signalleitungen,",
        "zwei unabhängige Multiplexer.",
    ]
    for index, line in enumerate(rules):
        label(draw, (x, 180 + index * 34), line, 22, INK if index < 4 else GRAY, index < 4)
    label(draw, (x, 760), "Prinzipdarstellung;", 18, GRAY)
    label(draw, (x, 784), "Detailbeschaltung siehe", 18, GRAY)
    label(draw, (x, 808), "Digilent-Schaltplan.", 18, GRAY)
    label(draw, (x, 838), "C = 0 → rechts: wie Phase I,", 18, RED)
    label(draw, (x, 862), "am Board je SSD", 18, RED)
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
    label(draw, (50, 545), "„sonst“: Eingänge 10 … 15 erzeugen einen Mittelstrich; in Phase II treten sie durch to_bcd2 (/10, mod 10 auf 0 … 99) nie auf.", 22, GRAY)
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
    image, draw = canvas(1800, 860, "ZEITMULTIPLEX JE SSD AM BEISPIEL „42“  (REFRESH_HZ = 500, DIV = 100.000)")
    x0, unit, slots = 330, 175, 8
    rows = [("tick (tick_gen)", 150), ("sel = dsel", 260), ("seg[6:0]", 370), ("rechte Ziffer (Einer)", 490), ("linke Ziffer (Zehner)", 590)]
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
    label(draw, (40, 790), "Beide ssd_driver (display_l, display_r) arbeiten gleich und unabhängig: Jede Ziffer ist 50 % der Zeit an, 500 Hz liegen weit", 21, GRAY)
    label(draw, (40, 820), "über der Flimmergrenze. Bei blank = 1 liefert seg7_decoder in beiden Slots 0000000 – so wird das linke SSD in SW0 dunkel.", 21, GRAY)
    image.save(path)


def debounce_timing(path):
    image, draw = canvas(1800, 880, "ENTPRELLUNG IN btn_debounce  (DEBOUNCE_CYCLES = 1.000.000 → 10 ms)")
    x0, scale = 300, 46
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
    base, top = 470, 370
    ramps = [(2.08, 2.33), (2.58, 2.78), (3.08, 13.08), (16.08, 16.38), (16.68, 26.68)]
    draw.line((to_x(0), base, to_x(30), base), fill="#E3E8EA", width=1)
    for start, end in ramps:
        height = (end - start) / 10 * (base - top)
        draw.line((to_x(start), base, to_x(end), base - height, to_x(end), base), fill=TEAL, width=3)
    dashed_line(draw, (to_x(0), top), (to_x(30), top), TEAL, 1, 8, 6)
    label(draw, (to_x(27.0), top - 30), "N − 1", 18, TEAL, True)
    draw.line((to_x(0), 555, to_x(13.08), 555, to_x(13.08), 510, to_x(26.68), 510, to_x(26.68), 555, to_x(30), 555), fill=INK, width=4)
    draw.line((to_x(0), 665, to_x(13.08), 665, to_x(13.08), 620, to_x(13.25), 620, to_x(13.25), 665, to_x(30), 665), fill=RED, width=4)
    label(draw, (to_x(13.4), 616), "genau 1 Takt (10 ns) → z. B. Start", 20, RED, True)
    label(draw, (to_x(26.9), 625), "Loslassen: kein Puls", 19, GRAY)
    arrow(draw, [(to_x(3.08), 760), (to_x(13.08), 760)], "on", color=TEAL, width=3)
    arrow(draw, [(to_x(13.08), 760), (to_x(3.08), 760)], "on", color=TEAL, width=3)
    label(draw, (to_x(8.08), 770), "10 ms ununterbrochen abweichend", 20, TEAL, True, "ma")
    label(draw, (40, 820), "Unverändert aus Phase I: Jede Rückkehr zum alten Pegel setzt cnt auf 0; nur 0 → 1 erzeugt press_o. Die Stoppuhr reagiert damit genau einmal pro Druck.", 21, GRAY)
    image.save(path)


def display_modes(path):
    image, draw = canvas(1800, 1000, "ANZEIGE JE BETRIEBSART  (links: SSD an JC/JD  |  rechts: SSD an JA/JB)")
    rows = [
        ("0001", "SW0: Sekunden 00 … 99", None, 42, ("aus (dunkel)", "Sekunden 00 … 99"), "Beispiel: 42 s seit Reset (Überlauf 99 → 00)"),
        ("0010", "SW1: Sekunden 0000 … 9999", 12, 34, ("Tausender | Hunderter", "Zehner | Einer"), "Beispiel: 1234 s, führende Nullen sichtbar (0007)"),
        ("0100", "SW2: Stoppuhr", 12, 34, ("Sekunden 00 … 99", "Hundertstel 00 … 99"), "Beispiel: 12,34 s; Auflösung 10 ms, 99.99 → 00.00"),
        ("sonst", "kein / mehrere / SW3", None, None, ("dunkel", "dunkel"), "z. B. 0000, 0011, 1000, 1111: beide SSD dunkel"),
    ]
    for index, (bits, name, left, right, captions, note) in enumerate(rows):
        y = 105 + index * 215
        hot = bits != "sonst"
        draw.rounded_rectangle((40, y, 1760, y + 195), radius=12, fill=HOT_FILL if hot else "#F7F8F9",
                               outline=RED if hot else MUTED, width=3)
        label(draw, (70, y + 22), bits, 40, INK if hot else MUTED_TEXT, True)
        label(draw, (70, y + 82), name, 28, RED if hot else GRAY, True)
        label(draw, (70, y + 130), note, 20, GRAY)
        dual_display(draw, 960, y + 18, left, right, digit_w=50, gap=220, captions=captions)
    image.save(path)


def wiring(path):
    image, draw = canvas(1800, 1000, "VERDRAHTUNG: ARTY A7-35T (JA … JD, UNTERE REIHE) → ZWEI PMOD SSD")
    colors = ["#E8282F", "#F08C00", "#2F9E44", "#1971C2", "#495057", "#C2255C"]

    def header(x, y, name, fpga):
        label(draw, (x, y - 40), name, 26, INK, True)
        for row, names in enumerate([["1", "2", "3", "4", "GND", "VCC"], ["7", "8", "9", "10", "GND", "VCC"]]):
            for index, text in enumerate(names):
                left, upper = x + index * 92, y + row * 66
                active = row == 1
                fill = colors[index] if active else "#F1F3F4"
                draw.rounded_rectangle((left, upper, left + 84, upper + 58), radius=6, fill=fill,
                                       outline=INK if active else MUTED, width=2)
                label(draw, (left + 42, upper + 6), text, 19, "white" if active else MUTED_TEXT, True, "ma")
                if active and index < 4:
                    label(draw, (left + 42, upper + 31), fpga[index], 17, "white", False, "ma")
        return x + 6 * 92

    draw.rounded_rectangle((40, 100, 760, 900), radius=16, outline=TEAL, width=3)
    label(draw, (60, 112), "Arty A7-35T", 30, TEAL, True)
    headers = [
        (190, "Pmod JC  →  SSD links, J1", ["U14", "V14", "T13", "U13"]),
        (370, "Pmod JD  →  SSD links, J2", ["E2", "D2", "H2", "G2"]),
        (570, "Pmod JA  →  SSD rechts, J1", ["D13", "B18", "A18", "K16"]),
        (750, "Pmod JB  →  SSD rechts, J2", ["J17", "J18", "K15", "J15"]),
    ]
    ends = [(header(110, y, name, pins), y + 66 + 29) for y, name, pins in headers]

    for top, bottom, title, conn_y in [(110, 510, "Pmod SSD links  (seg_l, dsel_l)", [ends[0][1], ends[1][1]]),
                                       (525, 900, "Pmod SSD rechts  (seg_r, dsel_r)", [ends[2][1], ends[3][1]])]:
        draw.rounded_rectangle((1060, top, 1760, bottom), radius=16, outline=RED, width=3)
        label(draw, (1080, top + 10), title, 26, RED, True)
        for cy, name, names in [(conn_y[0], "J1", ["AA", "AB", "AC", "AD", "GND", "VCC"]),
                                (conn_y[1], "J2", ["AE", "AF", "AG", "C", "GND", "VCC"])]:
            label(draw, (1085, cy - 18), name, 24, INK, True)
            for index, text in enumerate(names):
                left = 1130 + index * 92
                draw.rounded_rectangle((left, cy - 29, left + 84, cy + 29), radius=6, fill=colors[index], outline=INK, width=2)
                label(draw, (left + 42, cy - 12), text, 21, "white", True, "ma")
    for end_x, cy in ends:
        draw.line((end_x + 10, cy, 1075, cy), fill=INK, width=14)
    label(draw, (60, 920), "Nur die unteren Reihen (Pins 7 … 12) werden genutzt; obere Reihen frei. Farben = 1:1-Zuordnung (Pin 7 → AA/AE, … Pin 10 → AD/C, 11/12 = GND/VCC).", 20, INK)
    label(draw, (60, 952), "Onboard: SW0 … SW3 = A8, C11, C10, A10  |  BTN0 … BTN3 = D9, C9, B9, B8  |  RESET = C2  |  CLK100MHZ = E3. Versorgung beim Umstecken trennen.", 20, GRAY)
    image.save(path)


def mode_table(path):
    image, draw = canvas(1800, 980, "ALLE 16 SCHALTERSTELLUNGEN  (sw = SW3 SW2 SW1 SW0)")
    meaning = {"0001": ("SW0: Sek. 00 … 99", None, 42), "0010": ("SW1: Sek. 0 … 9999", 12, 34),
               "0100": ("SW2: Stoppuhr", 12, 34)}
    for value in range(16):
        bits = format(value, "04b")
        col, row = value % 4, value // 4
        x, y = 50 + col * 430, 100 + row * 210
        valid = bits in meaning
        draw.rounded_rectangle((x, y, x + 400, y + 190), radius=12, fill=HOT_FILL if valid else "#F7F8F9",
                               outline=RED if valid else MUTED, width=4 if valid else 2)
        label(draw, (x + 22, y + 18), bits, 40, INK if valid else MUTED_TEXT, True)
        if valid:
            name, left, right = meaning[bits]
            label(draw, (x + 22, y + 140), name, 24, RED, True)
            dual_display(draw, x + 170, y + 22, left, right, digit_w=34, gap=10)
        else:
            text = "kein Schalter" if bits == "0000" else ("SW3: ungültig" if bits == "1000" else "mehrere Schalter")
            label(draw, (x + 22, y + 140), text + " → dunkel", 22, GRAY, True)
            dual_display(draw, x + 170, y + 22, None, None, digit_w=34, gap=10)
    label(draw, (50, 945), "Nur 0001, 0010 und 0100 wählen eine Anzeige. Die übrigen 13 Stellungen (inkl. SW3 allein) ergeben zwei dunkle SSD.", 22, INK, True)
    image.save(path)


def timebase(path):
    image, draw = canvas(1800, 1000, "ZEITBASIS: tick_sec (1 s) UND tick_cs (10 ms, nur wenn running = 1)")
    # oberer Teil: Sekundentakt
    x0, unit = 330, 240
    label(draw, (40, 100), "Sekundentakt (Ausschnitt um 99 → 100 s)", 24, TEAL, True)
    for slot in range(6):
        x = x0 + slot * unit
        dashed_line(draw, (x, 140), (x, 440), MUTED, 1, 6, 6)
        label(draw, (x, 448), f"{98 + slot} s", 19, GRAY, anchor="ma")
    label(draw, (40, 160), "tick_sec", 23, INK, True)
    draw.line((x0, 205, x0 + 5 * unit, 205), fill=TEAL, width=4)
    for slot in range(1, 5):
        x = x0 + slot * unit
        draw.line((x, 205, x, 160, x + 10, 160, x + 10, 205), fill=TEAL, width=4)
    label(draw, (x0 + 4 * unit + 20, 160), "1 Takt = 10 ns", 18, TEAL)
    signals = [("cnt_a  (SW0)", 240, ["98", "99", "00", "01", "02"]),
               ("cnt_b_hi | cnt_b_lo  (SW1)", 310, ["00|98", "00|99", "01|00", "01|01", "01|02"]),
               ("Anzeige SW1", 380, ["0098", "0099", "0100", "0101", "0102"])]
    for name, y, values in signals:
        label(draw, (40, y + 10), name, 21, INK, True)
        for slot, value in enumerate(values):
            x = x0 + slot * unit + (12 if slot else 0)
            right = x0 + (slot + 1) * unit
            draw.polygon([(x, y + 25), (x + 12, y), (right - 12, y), (right, y + 25), (right - 12, y + 50), (x + 12, y + 50)],
                         outline=INK, fill="#FFF7E8" if value in ("00", "01|00", "0100") else "#E9F5F6", width=2)
            label(draw, ((x + right) / 2, y + 12), value, 21, RED if value in ("00", "01|00", "0100") else INK, True, "ma")
    # unterer Teil: Stoppuhr
    y0 = 520
    x0, unit = 330, 120
    label(draw, (40, y0 - 30), "Stoppuhr (10 ms je Schritt, BTN0 bei 10 ms, BTN1 bei 70 ms)", 24, TEAL, True)
    for slot in range(12):
        x = x0 + slot * unit
        dashed_line(draw, (x, y0 + 10), (x, y0 + 330), MUTED, 1, 6, 6)
        label(draw, (x, y0 + 338), f"{slot * 10}", 18, GRAY, anchor="ma")
    label(draw, (x0 + 12 * unit - 30, y0 + 338), "ms", 18, GRAY)
    label(draw, (40, y0 + 25), "press (Start / Stopp)", 21, INK, True)
    draw.line((x0, y0 + 70, x0 + 11 * unit, y0 + 70), fill=RED, width=4)
    for slot, text in [(1, "Start"), (7, "Stopp")]:
        x = x0 + slot * unit
        draw.line((x, y0 + 70, x, y0 + 30, x + 8, y0 + 30, x + 8, y0 + 70), fill=RED, width=4)
        label(draw, (x + 14, y0 + 28), text, 18, RED, True)
    label(draw, (40, y0 + 105), "running", 21, INK, True)
    wave_level(draw, x0, 0, unit, [0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0], y0 + 100, y0 + 140, INK)
    label(draw, (40, y0 + 175), "tick_cs", 21, INK, True)
    draw.line((x0, y0 + 210, x0 + 11 * unit, y0 + 210), fill=TEAL, width=4)
    for slot in range(2, 8):
        x = x0 + slot * unit
        draw.line((x, y0 + 210, x, y0 + 170, x + 8, y0 + 170, x + 8, y0 + 210), fill=TEAL, width=4)
    label(draw, (40, y0 + 255), "stop_s . stop_cs", 21, INK, True)
    values = ["00.00", "00.00", "00.01", "00.02", "00.03", "00.04", "00.05", "00.06", "00.06", "00.06", "00.06"]
    for slot, value in enumerate(values):
        x = x0 + slot * unit + (8 if slot else 0)
        right = x0 + (slot + 1) * unit
        draw.polygon([(x, y0 + 270), (x + 8, y0 + 250), (right - 8, y0 + 250), (right, y0 + 270), (right - 8, y0 + 290), (x + 8, y0 + 290)],
                     outline=INK, fill="#E9F5F6", width=2)
        label(draw, ((x + right) / 2, y0 + 258), value, 17, INK, True, "ma")
    label(draw, (40, y0 + 380), "Der 10-ms-Vorteiler (u_tick_cs) zählt nur bei running = 1 und behält im Stopp seinen Stand – beim Fortsetzen geht kein Bruchteil verloren.", 21, GRAY)
    label(draw, (40, y0 + 412), "Nullen (BTN2 im Stopp) setzt stop_s, stop_cs und den Vorteiler (clr) zurück. Bild idealisiert: tatsächlich +10 ms Entprellung und wenige Takte Latenz.", 21, GRAY)
    image.save(path)


def cascade(path):
    image, draw = canvas(1800, 900, "ZÄHLERKASKADE AUS ZWEI 0 … 99-STUFEN")
    rows = [
        (120, "Zähler B (SW1)", "tick_sec", "cnt_b_lo", "Zehner | Einer", "cnt_b_hi", "Tausender | Hunderter",
         [("0099 + 1 s", "0100"), ("0999 + 1 s", "1000"), ("9999 + 1 s", "0000")]),
        (470, "Stoppuhr (SW2)", "tick_cs", "stop_cs", "Hundertstel", "stop_s", "Sekunden",
         [("00.99 + 10 ms", "01.00"), ("09.99 + 10 ms", "10.00"), ("99.99 + 10 ms", "00.00")]),
    ]
    for y, name, tick, lo, lo_text, hi, hi_text, examples in rows:
        label(draw, (40, y), name, 28, RED, True)
        box(draw, (40, y + 60, 230, y + 160), tick, "1-Takt-Puls", "on", 24, 18)
        box(draw, (330, y + 50, 620, y + 170), lo, f"0 … 99\n{lo_text}", "hot", 24, 18)
        box(draw, (780, y + 50, 1070, y + 170), hi, f"0 … 99\n{hi_text}", "hot", 24, 18)
        arrow(draw, [(230, y + 110), (330, y + 110)], "on")
        arrow(draw, [(620, y + 110), (780, y + 110)], "hot")
        label(draw, (632, y + 70), "Übertrag", 19, RED, True)
        label(draw, (632, y + 122), "bei lo = 99", 18, RED)
        label(draw, (340, y + 185), "lo = 99 → lo ← 0 und hi + 1;  hi = 99 → hi ← 0", 20, GRAY)
        for index, (before, after) in enumerate(examples):
            yy = y + 30 + index * 90
            label(draw, (1140, yy + 22), before, 22, INK, True)
            label(draw, (1350, yy + 22), "→", 26, RED, True)
            digits = after.replace(".", "")
            dual_display(draw, 1400, yy, int(digits[:2]), int(digits[2:]), digit_w=26, gap=8)
    draw.rounded_rectangle((40, 780, 1760, 880), radius=10, fill=LIGHT)
    label(draw, (64, 795), "Warum zwei Paare statt eines Zählers 0 … 9999?", 23, INK, True)
    label(draw, (64, 835), "Jedes Paar passt direkt auf ein SSD: to_bcd2 (÷ 10, mod 10 auf 7 Bit) aus clock_pkg wird je SSD wiederverwendet – keine ÷ 1000 / ÷ 100 auf 14 Bit nötig.", 21, GRAY)
    image.save(path)


def stopwatch(path):
    image, draw = canvas(1800, 950, "STOPPUHR: ZUSTÄNDE UND TASTEN (nur bei sw = 0100 wirksam)")
    stopped, running = (330, 420), (900, 420)
    for (cx, cy), title, body, status in [(stopped, "GESTOPPT", "running = 0\nStand bleibt", "on"),
                                         (running, "LÄUFT", "running = 1\n+1 je 10 ms", "hot")]:
        style = STYLE[status]
        draw.ellipse((cx - 170, cy - 110, cx + 170, cy + 110), fill=style["fill"], outline=style["outline"], width=5)
        text_lines(draw, cx, cy, [(title, font(34, True), INK)] + [(line, font(22), GRAY) for line in body.split("\n")])
    arrow(draw, [(470, 360), (760, 360)], "hot")
    label(draw, (615, 320), "BTN0  Start", 24, RED, True, "ma")
    arrow(draw, [(760, 480), (470, 480)], "on")
    label(draw, (615, 492), "BTN1  Stopp", 24, INK, True, "ma")
    # Schleifen
    draw.arc((230, 170, 430, 330), 180, 360, fill=TEAL, width=4)
    draw.line((230, 250, 230, 331), fill=TEAL, width=4)
    arrow(draw, [(430, 250), (430, 329)], "on", color=TEAL)
    label(draw, (330, 120), "BTN2: Nullen → 00.00", 22, TEAL, True, "ma")
    label(draw, (330, 148), "BTN1: keine Änderung", 19, GRAY, anchor="ma")
    draw.arc((800, 170, 1000, 330), 180, 360, fill=MUTED, width=4)
    draw.line((800, 250, 800, 331), fill=MUTED, width=4)
    arrow(draw, [(1000, 250), (1000, 329)], "off")
    label(draw, (900, 120), "BTN2: ignoriert", 22, GRAY, True, "ma")
    label(draw, (900, 148), "BTN0: keine Änderung", 19, GRAY, anchor="ma")
    arrow(draw, [(60, 420), (160, 420)], "on", color=RED)
    label(draw, (40, 380), "ck_rst", 22, RED, True)
    label(draw, (40, 440), "→ 00.00", 19, RED)
    draw.rounded_rectangle((40, 600, 1130, 900), radius=10, fill=LIGHT)
    rules = [
        ("sw_start = SW2 und press(0)", "running ← 1"),
        ("sw_stop  = SW2 und press(1)", "running ← 0 (Start hat Vorrang)"),
        ("sw_zero  = SW2 und press(2) und running = 0", "stop_s, stop_cs, Vorteiler ← 0"),
        ("tick_cs (nur bei running = 1)", "stop_cs + 1, Übertrag in stop_s"),
        ("Moduswechsel", "Stoppuhr läuft im Hintergrund weiter"),
    ]
    for index, (cond, action) in enumerate(rules):
        label(draw, (64, 620 + index * 54), cond, 22, INK, True)
        label(draw, (650, 620 + index * 54), action, 22, GRAY)
    # Beispielablauf
    label(draw, (1220, 100), "Beispielablauf", 28, INK, True)
    seq = [("Reset", 0, 0), ("BTN0, 2,02 s warten", None, None), ("BTN1 → Stopp", 2, 2), ("BTN2 → Nullen", 0, 0),
           ("BTN0 … 1,5 s … BTN1", 1, 50), ("BTN0, Wechsel auf SW0", None, None), ("zurück SW2: läuft", None, None)]
    for index, (action, s, cs) in enumerate(seq):
        y = 150 + index * 110
        label(draw, (1220, y + 22), action, 21, GRAY, True)
        if s is None:
            label(draw, (1600, y + 22), "läuft …", 21, RED, True)
        else:
            dual_display(draw, 1530, y, s, cs, digit_w=24, gap=8)
    image.save(path)


def display_path(path):
    image, draw = canvas(1800, 820, "ANZEIGEPFAD MIT ZWEI TREIBERN  (Beispiel SW2: 12.34 s)")
    for index, (side, value, bcd, port, pins) in enumerate([("links", 12, "tens 1 / ones 2", "seg_l, dsel_l", "JC/JD"),
                                                            ("rechts", 34, "tens 3 / ones 4", "seg_r, dsel_r", "JA/JB")]):
        y = 130 + index * 300
        box(draw, (40, y + 15, 260, y + 125), f"val_{side[0]}", f"= {value} (0 … 99)", "hot", 26, 20)
        box(draw, (40, y + 140, 260, y + 220), f"show_{side[0]}", "= 1 (SW2)", "on", 24, 19)
        box(draw, (340, y + 15, 600, y + 125), "to_bcd2", bcd, "on", 26, 20)
        box(draw, (340, y + 140, 600, y + 220), "not", f"blank_{side[0]} = 0", "on", 24, 19)
        arrow(draw, [(260, y + 70), (340, y + 70)], "hot")
        arrow(draw, [(260, y + 180), (340, y + 180)], "on")
        draw.rounded_rectangle((690, y - 20, 1290, y + 240), radius=12, outline=TEAL, width=3)
        label(draw, (705, y - 12), f"ssd_driver  display_{side[0]}", 22, TEAL, True)
        box(draw, (710, y + 30, 880, y + 110), "MUX", "sel: ones / tens", "on", 22, 17)
        box(draw, (920, y + 30, 1270, y + 110), "seg7_decoder", "digit, blank → gfedcba", "on", 22, 17)
        box(draw, (710, y + 140, 1270, y + 220), "tick_gen + sel-Register", "Puls je 1 ms → sel toggelt = dsel", "on", 22, 17)
        arrow(draw, [(600, y + 70), (710, y + 70)], "hot")
        arrow(draw, [(600, y + 180), (660, y + 180), (660, y + 125), (1095, y + 125), (1095, y + 110)], "on")
        arrow(draw, [(880, y + 70), (920, y + 70)], "on")
        box(draw, (1380, y + 20, 1600, y + 120), port, pins, "hot", 22, 19)
        arrow(draw, [(1270, y + 70), (1380, y + 70)], "hot")
        arrow(draw, [(1270, y + 180), (1490, y + 180), (1490, y + 120)], "on")
        mini_display(draw, 1630, y + 20, two_digits(value), 32)
    label(draw, (40, 740), "Beide Pfade sind identisch und unabhängig. Fehlt die Freigabe (show = 0), setzt der Decoder über blank = 1 alle Segmente auf 0;", 21, GRAY)
    label(draw, (40, 772), "dsel läuft weiter. Gegenüber Phase I entfällt die Unterdrückung der führenden Null – alle Werte erscheinen zweistellig (00 … 99).", 21, GRAY)
    image.save(path)


def generate_all(directory):
    directory.mkdir(parents=True, exist_ok=True)
    signal_flow(directory / "signalfluss.png")
    architecture(directory / "architektur.png")
    for mode in ["sw0", "sw1", "sw2", "off"]:
        architecture(directory / f"modus_{mode}.png", mode)
    hierarchy(directory / "hierarchie.png")
    seg_anatomy(directory / "segment_aufbau.png")
    seg_circuit(directory / "segment_elektrisch.png")
    seg_digits(directory / "segment_muster.png")
    mux_timing(directory / "multiplex_timing.png")
    debounce_timing(directory / "entprell_timing.png")
    display_modes(directory / "anzeige_modi.png")
    wiring(directory / "verdrahtung.png")
    mode_table(directory / "schalter_tabelle.png")
    timebase(directory / "zeitbasis.png")
    cascade(directory / "kaskade.png")
    stopwatch(directory / "stoppuhr.png")
    display_path(directory / "anzeigepfad.png")


if __name__ == "__main__":
    generate_all(Path(__file__).resolve().parents[1] / "doc" / "img")
