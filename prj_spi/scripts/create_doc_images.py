"""Erzeugt alle Bilder fuer die Dokumentation von prj_spi nach doc/img/*.png.

Aufruf:  python scripts/create_doc_images.py
Die Bilder fuer Bitmaps/Sprites stammen direkt aus scripts/gen_rom.py, Zahlen aus dem VHDL-Code.
"""
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "doc" / "img"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_rom  # noqa: E402

S = 2                                       # Zeichnen mit 2x, Ausgabe heruntergerechnet

INK = (30, 30, 36)
GREY = (120, 124, 132)
LGREY = (236, 238, 241)
WHITE = (255, 255, 255)
RED = (227, 0, 21)
BLUE = (0, 84, 159)
C_IN = (221, 235, 250)
C_FILTER = (214, 228, 245)
C_REND = (222, 244, 226)
C_MEM = (255, 236, 205)
C_CTRL = (255, 222, 214)
C_SPI = (236, 226, 250)
C_HW = (232, 232, 236)
C_WARN = (255, 245, 190)
GREEN = (40, 150, 70)
ORANGE = (235, 130, 20)
PURPLE = (120, 70, 190)

FONTS = {
    (False, False): "C:/Windows/Fonts/segoeui.ttf",
    (True, False): "C:/Windows/Fonts/segoeuib.ttf",
    (False, True): "C:/Windows/Fonts/consola.ttf",
    (True, True): "C:/Windows/Fonts/consolab.ttf",
}
_font_cache = {}

# Bildtexte sind im Quelltext ASCII; hier werden Umlaute eingesetzt.
UMLAUTS = [("Schlaeger", "Schläger"), ("Eingaenge", "Eingänge"), ("Eintraege", "Einträge"), ("Gruen", "Grün"),
           ("Haelfte", "Hälfte"), ("Metastabilitaet", "Metastabilität"), ("Pruef", "Prüf"), ("pruef", "prüf"),
           ("Schutzwiderstaenden", "Schutzwiderständen"), ("Stueck", "Stück"), ("Ueber", "Über"), ("ueber", "über"),
           ("Verlaesst", "Verlässt"), ("Waende", "Wände"), ("Wuerde", "Würde"), ("wuerde", "würde"), ("aehl", "ähl"),
           ("aendern", "ändern"), ("aendert", "ändert"), ("erhoehen", "erhöhen"), ("fuenf", "fünf"), ("fuer", "für"),
           ("gedrueckt", "gedrückt"), ("gefuehrt", "geführt"), ("gefuellt", "gefüllt"), ("geglaettet", "geglättet"),
           ("haelt", "hält"), ("haengt", "hängt"), ("kraeftiger", "kräftiger"), ("laeuft", "läuft"), ("naechst", "nächst"),
           ("muesste", "müsste"), ("vergroessert", "vergrößert"), ("waechst", "wächst"), ("zufaellig", "zufällig"),
           ("zurueck", "zurück"), ("zusaetzlich", "zusätzlich"), ("staeblich", "stäblich"), ("Taktzyklus", "Taktzyklus")]


def um(s):
    for a, b in UMLAUTS:
        s = s.replace(a, b)
    return s


def get_font(size, bold=False, mono=False):
    key = (size, bold, mono)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(FONTS[(bold, mono)], round(size * S))
    return _font_cache[key]


class Fig:
    def __init__(self, w, h, bg=WHITE):
        self.w, self.h = w, h
        self.im = Image.new("RGB", (w * S, h * S), bg)
        self.d = ImageDraw.Draw(self.im)

    def rect(self, x, y, w, h, fill=None, outline=INK, width=2, r=10):
        self.d.rounded_rectangle([x * S, y * S, (x + w) * S, (y + h) * S], radius=r * S,
                                 fill=fill, outline=outline, width=round(width * S) if outline else 0)

    def text(self, x, y, t, size=18, bold=False, color=INK, ha="l", va="t", mono=False, lh=1.28):
        fnt = get_font(size, bold, mono)
        lines = um(t).split("\n")
        step = size * lh
        total = step * len(lines)
        if va == "m":
            y = y - total / 2
        elif va == "b":
            y = y - total
        for i, line in enumerate(lines):
            wl = fnt.getlength(line) / S
            xx = x if ha == "l" else x - wl / 2 if ha == "c" else x - wl
            self.d.text((xx * S, (y + i * step) * S), line, font=fnt, fill=color)

    def box(self, x, y, w, h, t, fill=WHITE, size=18, bold=False, outline=INK, color=INK, mono=False, r=10, width=2):
        self.rect(x, y, w, h, fill, outline, width, r)
        self.text(x + w / 2, y + h / 2, t, size, bold, color, "c", "m", mono)

    def line(self, pts, color=INK, width=2, dash=None):
        p = [(a * S, b * S) for a, b in pts]
        if dash is None:
            self.d.line(p, fill=color, width=round(width * S), joint="curve")
            return
        for (x0, y0), (x1, y1) in zip(p, p[1:]):
            length = math.hypot(x1 - x0, y1 - y0)
            n = int(length / (dash * S))
            for i in range(0, n, 2):
                a0 = i * dash * S / length
                a1 = min((i + 1) * dash * S / length, 1)
                self.d.line([(x0 + (x1 - x0) * a0, y0 + (y1 - y0) * a0),
                             (x0 + (x1 - x0) * a1, y0 + (y1 - y0) * a1)], fill=color, width=round(width * S))

    def arrow(self, pts, color=INK, width=2.5, head=12, dash=None):
        self.line(pts, color, width, dash)
        (x0, y0), (x1, y1) = pts[-2], pts[-1]
        ang = math.atan2(y1 - y0, x1 - x0)
        a, b = ang + math.radians(150), ang - math.radians(150)
        tri = [(x1 * S, y1 * S),
               ((x1 + head * math.cos(a)) * S, (y1 + head * math.sin(a)) * S),
               ((x1 + head * math.cos(b)) * S, (y1 + head * math.sin(b)) * S)]
        self.d.polygon(tri, fill=color)

    def ellipse(self, cx, cy, r, fill=None, outline=INK, width=2):
        self.d.ellipse([(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S], fill=fill,
                       outline=outline, width=round(width * S))

    def poly(self, pts, fill=None, outline=INK, width=2):
        self.d.polygon([(a * S, b * S) for a, b in pts], fill=fill, outline=outline)
        if outline:
            self.line(pts + [pts[0]], outline, width)

    def paste(self, img, x, y):
        img = img.resize((img.width * S, img.height * S), Image.NEAREST)
        self.im.paste(img, (round(x * S), round(y * S)))

    def title(self, t, sub=None):
        self.text(30, 18, t, 30, True, BLUE)
        if sub:
            self.text(30, 58, sub, 18, False, GREY)

    def save(self, name):
        OUT.mkdir(parents=True, exist_ok=True)
        self.im.resize((self.w, self.h), Image.LANCZOS).save(OUT / name, optimize=True)


def scaled(img, k):
    return img.resize((img.width * k, img.height * k), Image.NEAREST)


def rgb_image(idx, pal):
    im = Image.new("RGB", (gen_rom.W, gen_rom.H))
    im.putdata([pal[i] for i in idx])
    return im


def with_sprite(base, sprites, sym_pal, k):
    im = base.copy()
    for y in range(gen_rom.SPR):
        for x in range(gen_rom.SPR):
            im.putpixel((gen_rom.SPR_X0 + x, gen_rom.SPR_Y0 + y), sym_pal[sprites[k][y * gen_rom.SPR + x]])
    return im


# ---------------------------------------------------------------- Bilder

def fig_grundlagen():
    f = Fig(1600, 640)
    f.title("FPGA-Grundbausteine", "Ein FPGA besteht aus sehr vielen kleinen, frei verschaltbaren Bausteinen - Logik und Speicher.")
    # A: LUT
    f.rect(30, 110, 490, 430, C_IN, BLUE)
    f.text(50, 122, "1  LUT: Logik als Tabelle", 22, True, BLUE)
    f.text(50, 160, "A  B | Y = A UND B", 18, True, INK, mono=True)
    for i, (a, b) in enumerate([(0, 0), (0, 1), (1, 0), (1, 1)]):
        f.text(50, 195 + i * 30, f"{a}  {b} |   {a & b}", 18, False, INK, mono=True)
    f.box(300, 210, 120, 110, "LUT", C_MEM, 24, True)
    f.arrow([(240, 240), (300, 240)])
    f.arrow([(240, 290), (300, 290)])
    f.arrow([(420, 265), (490, 265)])
    f.text(232, 225, "A", 16, ha="r")
    f.text(232, 275, "B", 16, ha="r")
    f.text(495, 250, "Y", 16, ha="r")
    f.text(50, 340, "Eine LUT (Look-Up Table) ist ein winziger\nSpeicher. Die Eingaenge sind die Adresse,\nder Inhalt ist das Ergebnis. So kann jede\nLogikfunktion gebaut werden.\n\nArtix-7: 6 Eingaenge pro LUT\n(35T: 5 200 Slices zu je 4 LUT).", 17)
    # B: Flip-Flop
    f.rect(560, 110, 490, 430, C_IN, BLUE)
    f.text(580, 122, "2  Flip-Flop: 1 Bit Speicher", 22, True, BLUE)
    f.box(640, 170, 110, 100, "FF", C_MEM, 24, True)
    f.arrow([(590, 200), (640, 200)])
    f.arrow([(750, 200), (810, 200)])
    f.text(585, 185, "D", 16, ha="r")
    f.text(815, 185, "Q", 16)
    f.poly([(640, 245), (660, 255), (640, 265)], None, INK)
    f.arrow([(590, 255), (640, 255)])
    f.text(585, 245, "clk", 16, ha="r")
    # Wellenformen
    def wave(y, pts, color=INK):
        f.line(pts, color, 3)
    f.text(580, 300, "clk", 16, mono=True)
    clk = [(640, 330)]
    x = 640
    for i in range(5):
        clk += [(x, 330), (x, 300 + 0), (x + 40, 300), (x + 40, 330), (x + 80, 330)]
        x += 80
    f.line([(640, 330), (640, 300), (680, 300), (680, 330), (720, 330), (720, 300), (760, 300), (760, 330),
            (800, 330), (800, 300), (840, 300), (840, 330), (880, 330), (880, 300), (920, 300), (920, 330),
            (1000, 330)], INK, 3)
    f.text(580, 370, "D", 16, mono=True)
    f.line([(640, 400), (780, 400), (780, 372), (860, 372), (860, 400), (1000, 400)], BLUE, 3)
    f.text(580, 430, "Q", 16, mono=True)
    f.line([(640, 460), (720, 460), (720, 432), (880, 432), (880, 460), (1000, 460)], RED, 3)
    for xx in (720, 880):
        f.arrow([(xx, 345), (xx, 440)], GREY, 1.5, 8, dash=6)
    f.text(580, 490, "Q uebernimmt D nur bei der steigenden\nTaktflanke und haelt den Wert bis zur naechsten.", 16)
    # C: synchron
    f.rect(1090, 110, 490, 430, C_IN, BLUE)
    f.text(1110, 122, "3  Synchrone Schaltung", 22, True, BLUE)
    f.box(1115, 220, 110, 80, "Register", C_MEM, 18, True)
    f.box(1270, 200, 140, 120, "Logik\n(LUTs)", C_REND, 20, True)
    f.box(1455, 220, 110, 80, "Register", C_MEM, 18, True)
    f.arrow([(1225, 260), (1270, 260)])
    f.arrow([(1410, 260), (1455, 260)])
    f.line([(1170, 220), (1170, 185), (1510, 185)], BLUE, 2.5)
    f.arrow([(1510, 185), (1510, 220)], BLUE, 2.5)
    f.text(1340, 158, "gemeinsamer Takt (100 MHz = alle 10 ns)", 15, color=BLUE, ha="c")
    f.text(1110, 350, "Bei jeder steigenden Flanke uebernehmen alle\nRegister gleichzeitig das Ergebnis der Logik\nvor ihnen. Zwischen zwei Flanken rechnet die\nLogik; der Takt muss so langsam sein, dass sie\nfertig wird (Timing).", 17)
    f.text(30, 580, "Wichtigster Unterschied zur Software: Im FPGA wird nichts nacheinander abgearbeitet - alle Bausteine arbeiten in jedem Takt gleichzeitig.", 19, True, INK)
    f.save("01_fpga_grundlagen.png")


def fig_toolflow():
    f = Fig(1600, 560)
    f.title("Vom VHDL-Text zum laufenden FPGA", "Alle Schritte ausser der Simulation uebernimmt Vivado (Synthese, Implementierung, Bitstream).")
    xs = [30, 340, 650, 960, 1270]
    items = [("VHDL-Quellen\nsrc/*.vhd", C_IN), ("Synthese\nLogik -> LUTs + FFs", C_REND),
             ("Implementierung\nPlatzieren + Verdrahten", C_REND), ("Bitstream\n(.bit-Datei)", C_MEM), ("FPGA\nprogrammieren", C_CTRL)]
    for x, (t, c) in zip(xs, items):
        f.box(x, 190, 300, 120, t, c, 21, True)
    for a, b in zip(xs, xs[1:]):
        f.arrow([(a + 300, 250), (b, 250)], INK, 3, 14)
    f.box(30, 90, 300, 60, "gen_rom.py -> oled_rom_pkg.vhd", C_MEM, 16)
    f.arrow([(180, 150), (180, 190)])
    f.box(650, 90, 300, 60, "XDC: Pin-Zuordnung + Takt", C_WARN, 17)
    f.arrow([(800, 150), (800, 190)])
    f.text(1420, 330, "USB-JTAG,\nca. 6 s (Digilent)", 16, color=GREY, ha="c")
    f.box(30, 390, 620, 110, "Simulation (GHDL): Testbench + SSD1331-Modell\npruefen das Design am PC, bevor es gebaut wird", C_SPI, 19)
    f.arrow([(180, 390), (180, 310)], PURPLE, 2.5)
    f.text(190, 345, "gleiche Quellen", 15, color=PURPLE)
    f.box(700, 390, 870, 110, "Das Programm im FPGA ist kein Programm, sondern eine Verschaltung: Nach dem Laden\nexistieren die Module physisch und laufen parallel. Beim Ausschalten ist alles weg\n(Konfiguration im SRAM) - ausser wenn man sie ins Flash schreibt.", C_HW, 17)
    f.save("02_toolflow.png")


def fig_anschluss():
    f = Fig(1600, 720)
    f.title("Anschluss: Pmod OLEDrgb an Pmod-Header JD", "Der Stecker passt 1:1: Pin n des Moduls liegt auf Pin n von JD. GND auf GND (Pin 5/11), VCC auf VCC (Pin 6/12).")
    # Header-Skizze
    f.rect(40, 130, 520, 260, C_HW, INK)
    f.text(300, 145, "2 x 6 Pmod-Stecker (Ansicht auf die Pins)", 17, True, ha="c")
    col = {5: INK, 11: INK, 6: RED, 12: RED, 3: GREY}
    for i in range(12):
        row = 0 if i < 6 else 1
        pin = i + 1
        cx = 95 + (i % 6) * 82
        cy = 210 + row * 110
        c = col.get(pin, BLUE)
        f.ellipse(cx, cy, 26, c, INK)
        f.text(cx, cy, str(pin), 22, True, WHITE, "c", "m")
    f.text(40, 410, "obere Reihe: Pin 1-6, untere Reihe: Pin 7-12", 16, color=GREY)
    f.ellipse(55, 450, 12, INK); f.text(75, 440, "GND", 17)
    f.ellipse(150, 450, 12, RED); f.text(170, 440, "VCC 3,3 V", 17)
    f.ellipse(290, 450, 12, BLUE); f.text(310, 440, "Signal", 17)
    f.ellipse(390, 450, 12, GREY); f.text(410, 440, "nicht belegt", 17)
    # Tabelle
    hdr = ["Pin", "Signal", "Bedeutung", "JD / FPGA-Ball", "Port im Design"]
    rows = [("1", "CS", "Chip Select (aktiv low)", "JD1 / D4", "oled_cs"),
            ("2", "MOSI", "Daten FPGA -> Display", "JD2 / D3", "oled_mosi"),
            ("3", "NC", "nicht verbunden", "-", "-"),
            ("4", "SCK", "SPI-Takt", "JD4 / F3", "oled_sck"),
            ("5", "GND", "Masse", "GND", "-"),
            ("6", "VCC", "3,3 V Versorgung", "3V3", "-"),
            ("7", "D/C", "0 = Kommando, 1 = Pixeldaten", "JD7 / E2", "oled_dc"),
            ("8", "RES", "Reset des Controllers", "JD8 / D2", "oled_res"),
            ("9", "VCCEN", "Schaltet Panelspannung", "JD9 / H2", "oled_vccen"),
            ("10", "PMODEN", "Schaltet Logik-Masse", "JD10 / G2", "oled_pmoden"),
            ("11", "GND", "Masse", "GND", "-"),
            ("12", "VCC", "3,3 V Versorgung", "3V3", "-")]
    xs = [600, 660, 790, 1120, 1330]
    f.rect(590, 125, 990, 36, BLUE, BLUE, 1, 6)
    for x, h in zip(xs, hdr):
        f.text(x + 8, 132, h, 17, True, WHITE)
    for r, row in enumerate(rows):
        y = 163 + r * 38
        f.rect(590, y, 990, 38, LGREY if r % 2 == 0 else WHITE, None, 0, 0)
        for x, t in zip(xs, row):
            f.text(x + 8, y + 7, t, 17, bold=(x == 660))
    f.rect(40, 500, 520, 170, C_WARN, ORANGE)
    f.text(56, 510, "Pruefliste vor dem Einschalten", 18, True)
    f.text(56, 540, "- Modul bis zum Anschlag in JD stecken, nicht um\n  eine Reihe versetzt (Pin 1 = CS oben links)\n- bei Kabel: Pin 5+11 -> GND, Pin 6+12 -> 3V3\n- nie 5 V anlegen (Pmod-Pins max. 3,4 V)", 16)
    f.rect(590, 630, 990, 70, C_IN, BLUE)
    f.text(605, 640, "JD ist ein Standard-Pmod mit 200-Ohm-Schutzwiderstaenden - fuer SPI mit 6,25 MHz unkritisch.\nQuelle: Digilent Arty A7 Reference Manual, Abschnitt 10 (Pmod Connectors); Pmod OLEDrgb Reference Manual, Pinout Description Table.", 15)
    f.save("03_hardware_anschluss.png")


def fig_gesamt():
    f = Fig(1700, 820)
    f.title("Blockschaltbild: spi_top")
    # Eingaenge
    for y, t in [(100, "sw[3:0]\n(Schalter)"), (210, "btn[3:0]\n(Taster)"), (640, "ck_rst\n(RESET-Taster)")]:
        f.box(30, y, 170, 80, t, C_IN, 18, True)
    f.box(260, 100, 220, 190, "input_filter x 8\n\n2-FF-Synchronisierer\n+ Entprellung (10 ms)", C_FILTER, 18, True)
    f.arrow([(200, 140), (260, 140)])
    f.arrow([(200, 250), (260, 250)])
    f.box(260, 620, 220, 120, "Reset-Synchronisierer\n(2 FF)  ->  rst", C_FILTER, 17, True)
    f.arrow([(200, 680), (260, 680)])
    f.box(260, 340, 220, 60, "led[3:0] = sw_f", C_HW, 17)
    f.arrow([(370, 290), (370, 340)])
    # Render
    f.rect(560, 80, 570, 640, C_REND, GREEN, 3, 14)
    f.text(845, 92, "oled_render  (welches Bild? welche Farbe?)", 20, True, GREEN, "c")
    f.box(580, 140, 245, 110, "Modus-Dekoder\nsw -> mode\n(nur bei frame_tick)", WHITE, 17)
    f.box(865, 140, 245, 110, "Drehwinkel ang\n(0..31, alle 2 Bilder\n+1 im Modus sw1)", WHITE, 17)
    f.box(580, 290, 245, 110, "Bitmap-ROM\nBOSCH / HHN / Hinweis\n64 Zeilen x 384 Bit", C_MEM, 17)
    f.box(865, 290, 245, 110, "Sprite-ROM\nBosch-Ring + Anker\n32 Winkel x 20x20", C_MEM, 17)
    f.box(580, 450, 245, 120, "pong_game\nSpiellogik + Pixel\n(btn -> Schlaeger)", WHITE, 17)
    f.box(865, 450, 245, 120, "Pixel-Pipeline\n5 Register-Stufen\n(Zeile -> Pixel -> Palette\n-> Sprite -> Mux)", WHITE, 16)
    f.arrow([(825, 510), (865, 510)])
    f.arrow([(987, 250), (987, 290)])
    f.arrow([(702, 250), (702, 290)])
    f.arrow([(987, 400), (987, 450)])
    f.arrow([(825, 370), (845, 370), (845, 480), (865, 480)])
    f.text(845, 610, "Der Modus bestimmt, aus welcher Quelle die Pipeline liest.\nAlles ist rein synchron und kennt kein Warten.", 15, color=GREY, ha="c")
    f.arrow([(480, 150), (580, 150)], BLUE, 2.5)
    f.text(530, 125, "sw_f", 14, color=BLUE, ha="c")
    f.arrow([(480, 250), (520, 250), (520, 510), (580, 510)], BLUE, 2.5)
    f.text(505, 400, "btn_f", 14, color=BLUE, ha="r")
    # Ctrl
    f.rect(1250, 90, 220, 230, C_CTRL, RED, 3, 14)
    f.text(1360, 100, "oled_ctrl", 20, True, RED, "c")
    f.text(1360, 135, "Init-Zustandsautomat\nBild-Ablauf: Kopf +\n6144 Pixel x 2 Byte\nZaehler px, py\nframe_tick", 15, ha="c")
    f.box(1250, 370, 220, 200, "spi_tx\nSPI-Sender\nMode 3, 6,25 MHz", C_SPI, 17, True)
    f.arrow([(1360, 320), (1360, 370)])
    f.text(1372, 335, "start, data, dc, hold", 13, color=GREY)
    f.arrow([(1250, 220), (1130, 220)], RED, 2.5)
    f.text(1190, 195, "pix_x, pix_y", 14, color=RED, ha="c")
    f.arrow([(1250, 280), (1130, 280)], RED, 2.5)
    f.text(1190, 255, "frame_tick", 14, color=RED, ha="c")
    f.arrow([(1110, 540), (1150, 540), (1150, 160), (1250, 160)], GREEN, 3)
    f.text(1200, 135, "pix[15:0]", 14, color=GREEN, ha="c")
    # Pmod
    f.rect(1560, 90, 120, 560, C_HW, INK, 2, 12)
    f.text(1620, 100, "Pmod\nOLEDrgb\n(JD)", 16, True, ha="c")
    pins = [("RES", 190), ("VCCEN", 245), ("PMODEN", 300), ("CS", 410), ("MOSI", 460), ("SCK", 510), ("D/C", 555)]
    for p, y in pins:
        f.text(1568, y - 11, p, 15, True)
        f.arrow([(1470, y), (1560, y)], BLUE, 2)
    f.text(1360, 615, "CS, MOSI, SCK, D/C aus spi_tx;\nRES, VCCEN, PMODEN direkt aus oled_ctrl", 14, color=GREY, ha="c")
    f.save("04_blockschaltbild_gesamt.png")


def waveform(f, x0, y, pts, color=INK, hi=36, w=3):
    """pts: Liste (x, pegel) -> Stufenlinie, pegel 0/1."""
    path = []
    prev = None
    for x, v in pts:
        yy = y - (hi if v else 0)
        if prev is not None and prev != yy:
            path.append((x, prev))
        path.append((x, yy))
        prev = yy
    f.line(path, color, w)


def fig_spi_timing():
    f = Fig(1600, 700)
    f.title("SPI-Uebertragung eines Bytes (Mode 3, hier 0xAE = Display aus)", "Takt SCK ruht auf high; MOSI wechselt bei fallender Flanke und wird vom Display bei steigender Flanke gelesen.")
    x0, lead, bw = 200, 80, 135
    xs = x0 + lead
    xe = xs + 8 * bw
    xend = xe + 50
    rows = {"CS_N": 160, "D/C": 250, "SCK": 350, "MOSI": 470}
    for n, y in rows.items():
        f.text(40, y - 28, n, 20, True, mono=True)
    # CS
    waveform(f, 0, rows["CS_N"], [(150, 1), (x0, 1), (x0, 0), (xend, 0), (xend, 1), (1500, 1)], BLUE)
    waveform(f, 0, rows["D/C"], [(150, 0), (1500, 0)], PURPLE)
    f.text(1100, rows["D/C"] - 34, "D/C = 0: Kommando", 15, color=PURPLE)
    # SCK
    pts = [(150, 1), (xs, 1)]
    for i in range(8):
        pts += [(xs + i * bw, 0), (xs + i * bw + bw / 2, 1)]
    pts += [(xend, 1), (1500, 1)]
    waveform(f, 0, rows["SCK"], pts, RED)
    # MOSI
    bits = [1, 0, 1, 0, 1, 1, 1, 0]
    path = [(150, 0), (xs, 0)]
    f.line([(150, rows["MOSI"]), (xs - 0, rows["MOSI"])], GREY, 2, dash=8)
    for i, b in enumerate(bits):
        a, c = xs + i * bw, xs + (i + 1) * bw
        yy = rows["MOSI"] - (36 if b else 0)
        f.line([(a, yy), (c, yy)], INK, 3)
        if i > 0:
            pb = rows["MOSI"] - (36 if bits[i - 1] else 0)
            if pb != yy:
                f.line([(a, pb), (a, yy)], INK, 3)
        f.text((a + c) / 2, rows["MOSI"] + 12, f"D{7 - i}={b}", 16, ha="c", mono=True)
    f.line([(xs + 8 * bw, rows["MOSI"] - (0)), (1500, rows["MOSI"])], GREY, 2, dash=8)
    # Marker steigende Flanken
    for i in range(8):
        xr = xs + i * bw + bw / 2
        f.arrow([(xr, rows["SCK"] + 55), (xr, rows["SCK"] + 4)], GREEN, 2, 9)
        f.line([(xr, rows["SCK"] + 55), (xr, rows["MOSI"] - 42)], GREEN, 1.5, dash=5)
    f.text(xs + 8 * bw + 25, rows["SCK"] + 36, "steigende Flanke:\nDisplay liest\ndas Bit", 14, color=GREEN)
    f.text(xs - 10, rows["SCK"] + 8, "fallende Flanke:\nneues Bit\nauf MOSI", 14, color=RED, ha="r")
    # Masse
    f.line([(x0, 560), (x0, 580)], GREY, 1.5)
    f.line([(xs, 560), (xs, 580)], GREY, 1.5)
    f.arrow([(x0, 575), (xs, 575)], GREY, 1.5, 7)
    f.text((x0 + xs) / 2, 585, "Vorlauf\n80 ns", 14, color=GREY, ha="c")
    f.arrow([(xs, 575), (xs + bw, 575)], GREY, 1.5, 7)
    f.text(xs + bw / 2, 585, "1 Bit =\n160 ns", 14, color=GREY, ha="c")
    f.rect(900, 580, 650, 100, C_WARN, ORANGE)
    f.text(915, 590, "SCK = 100 MHz / 16 = 6,25 MHz (Periode 160 ns)\nDatenblatt: Taktzyklus mindestens 150 ns (SSD1331)\nByte = 8 x 160 ns = 1,28 us reine Uebertragungszeit", 15)
    f.save("05_spi_timing.png")


def fig_spi_fsm():
    f = Fig(1600, 580)
    f.title("spi_tx: Zustandsautomat des SPI-Senders", "HALF = 8 Takte: so lange bleibt SCK low bzw. high.")
    f.box(40, 200, 200, 100, "S_IDLE\nwartet auf start", C_HW, 17, True)
    f.box(360, 200, 200, 100, "S_LEAD\nCS/DC-Vorlauf\n(HALF Takte)", C_SPI, 17, True)
    f.box(700, 90, 220, 100, "S_LOW\nsck = 0\nHALF Takte halten", C_SPI, 17, True)
    f.box(700, 330, 220, 100, "S_HIGH\nsck = 1\nHALF Takte halten", C_SPI, 17, True)
    f.box(1250, 200, 200, 100, "S_TRAIL\nByte fertig", C_SPI, 17, True)
    f.arrow([(240, 250), (360, 250)])
    f.text(300, 222, "start = 1", 15, True, BLUE, "c")
    f.text(300, 318, "bei start: cs_n <- 0, dc <- dc_in, sh <- data", 15, color=BLUE, ha="c")
    f.arrow([(560, 250), (630, 250), (630, 140), (700, 140)])
    f.text(620, 95, "nach HALF Takten:\nsck <- 0, mosi <- sh(7)", 15, ha="r")
    f.arrow([(810, 190), (810, 330)])
    f.text(822, 250, "nach HALF Takten:\nsck <- 1", 15)
    f.arrow([(920, 365), (1000, 365), (1000, 140), (920, 140)])
    f.text(1012, 190, "nach HALF Takten, bits < 7:\nsck <- 0, mosi <- sh(6),\nSchieberegister schieben,\nbits <- bits + 1", 15)
    f.arrow([(920, 415), (1400, 415), (1400, 300)])
    f.text(1160, 390, "bits = 7: letztes Bit fertig", 15, ha="c")
    f.arrow([(1300, 300), (1300, 520), (140, 520), (140, 300)])
    f.text(700, 538, "hold = 0: cs_n <- 1   |   done = 1 (1 Takt)   ->   zurueck nach S_IDLE", 16, True, ha="c")
    f.save("06_spi_fsm.png")


def fig_ctrl_fsm():
    f = Fig(1600, 700)
    f.title("oled_ctrl: Ablaufsteuerung", "ST_WAIT ist ein universeller Warteschritt (Zaehler tmr) - danach geht es im naechsten Zustand weiter.")
    bw, bh = 330, 120
    xs = [30, 430, 830, 1230]
    row1 = [("ST_PWR", "PMODEN = 1\n20 ms warten"), ("ST_RST_LOW", "RES = 0\n100 us warten"),
            ("ST_RST_HIGH", "RES = 1\n3 ms warten"), ("ST_INIT", "37 Kommando-Bytes\n(D/C = 0, CS je Byte)")]
    for x, (n, t) in zip(xs, row1):
        f.box(x, 110, bw, bh, f"{n}\n{t}", C_CTRL if n != "ST_INIT" else C_SPI, 18, False)
    for a, b in zip(xs, xs[1:]):
        f.arrow([(a + bw, 170), (b, 170)], INK, 3, 14)
    row2 = [("ST_VCC", "VCCEN = 1\n25 ms warten"), ("ST_ON", "Byte 0xAF (Display an)\n100 ms warten"),
            ("ST_HDR", "6 Byte: 15 00 5F 75 00 3F\n(Fenster = ganzes Display)")]
    xs2 = [30, 430, 830]
    for x, (n, t) in zip(xs2, row2):
        f.box(x, 310, bw, bh, f"{n}\n{t}", C_CTRL if n == "ST_VCC" else C_SPI, 18)
    f.arrow([(1395, 230), (1395, 270), (195, 270), (195, 310)], INK, 3, 14)
    f.arrow([(360, 370), (430, 370)], INK, 3, 14)
    f.arrow([(760, 370), (830, 370)], INK, 3, 14)
    f.box(1230, 310, bw, bh, "ST_WAIT\n12 Takte Pipeline-Latenz\n(Pixel wird berechnet)", C_HW, 18)
    f.arrow([(1160, 370), (1230, 370)], INK, 3, 14)
    f.box(1230, 500, bw, 100, "ST_PIX_HI\nByte pix[15:8] (D/C=1)", C_SPI, 18)
    f.box(830, 500, bw, 100, "ST_PIX_LO\nByte pix[7:0]", C_SPI, 18)
    f.arrow([(1395, 430), (1395, 500)], INK, 3, 14)
    f.arrow([(1230, 550), (1160, 550)], INK, 3, 14)
    f.arrow([(995, 500), (995, 430)], RED, 3, 14)
    f.text(985, 438, "letztes Pixel:\nframe_tick, zurueck\nzum Header", 15, color=RED, ha="r")
    f.arrow([(995, 600), (995, 650), (1590, 650), (1590, 370), (1560, 370)], GREEN, 2.5, 12)
    f.text(1290, 668, "naechstes Pixel: px/py erhoehen -> ST_WAIT -> ST_PIX_HI ...", 16, color=GREEN, ha="c")
    f.text(30, 460, "Jedes Byte laeuft ueber den Unterautomaten:\nspi_start-Impuls -> auf spi_done warten.", 16, color=GREY)
    f.save("07_ctrl_fsm.png")


def fig_power():
    f = Fig(1600, 620)
    f.title("Einschaltreihenfolge des Displays", "Nicht maßstaeblich. Die Zeiten entsprechen der Digilent-Vorgabe (Pmod OLEDrgb Reference Manual) bzw. dem Code.")
    rows = {"PMODEN": 130, "RES": 215, "SPI": 300, "VCCEN": 385, "Display": 470}
    for n, y in rows.items():
        f.text(30, y - 30, n, 19, True, mono=True)
    ev = [200, 430, 540, 720, 900, 1200, 1420]
    hi = 34
    f.line([(150, rows["PMODEN"]), (ev[0], rows["PMODEN"]), (ev[0], rows["PMODEN"] - hi), (1560, rows["PMODEN"] - hi)], BLUE, 3)
    f.line([(150, rows["RES"] - hi), (ev[1], rows["RES"] - hi), (ev[1], rows["RES"]), (ev[2], rows["RES"]),
            (ev[2], rows["RES"] - hi), (1560, rows["RES"] - hi)], BLUE, 3)
    f.box(ev[3], rows["SPI"] - 40, ev[4] - ev[3], 40, "37 Byte Init", C_SPI, 15)
    f.box(ev[5], rows["SPI"] - 40, 90, 40, "0xAF", C_SPI, 15)
    f.box(ev[6], rows["SPI"] - 40, 140, 40, "Frames ...", C_SPI, 15)
    f.line([(150, rows["VCCEN"]), (ev[4], rows["VCCEN"]), (ev[4], rows["VCCEN"] - hi), (1560, rows["VCCEN"] - hi)], BLUE, 3)
    f.rect(150, rows["Display"] - 40, ev[5] + 90 - 150, 40, (60, 60, 60), None, 0, 0)
    f.text((150 + ev[5] + 90) / 2, rows["Display"] - 20, "aus", 16, False, WHITE, "c", "m")
    f.rect(ev[5] + 90, rows["Display"] - 40, 1560 - ev[5] - 90, 40, (30, 120, 70), None, 0, 0)
    f.text((ev[5] + 90 + 1560) / 2, rows["Display"] - 20, "Bild", 16, False, WHITE, "c", "m")
    def span(xa, xb, y, t):
        f.arrow([(xa, y), (xb, y)], GREY, 1.5, 7)
        f.arrow([(xb, y), (xa, y)], GREY, 1.5, 7)
        f.text((xa + xb) / 2, y - 22, t, 15, True, ORANGE, "c")
    span(ev[0], ev[1], 520, "20 ms")
    span(ev[1], ev[2], 520, "100 us")
    span(ev[2], ev[3], 520, "3 ms")
    span(ev[3], ev[4], 520, "ca. 52 us")
    span(ev[4], ev[5], 520, "25 ms")
    span(ev[5] + 90, ev[6], 520, "100 ms")
    for x in ev[:5] + [ev[5]]:
        f.line([(x, 100), (x, 540)], GREY, 1, dash=6)
    f.text(30, 575, "Reihenfolge ist wichtig: Erst die Logik-Versorgung (PMODEN), dann Reset, dann Konfiguration, ERST ZULETZT die hohe Panelspannung (VCCEN).", 17, True)
    f.save("08_einschaltsequenz.png")


def fig_bildaufbau():
    f = Fig(1600, 760)
    f.title("Wie ein Bild zum Display kommt", "96 x 64 Pixel = 6144 Pixel, jeder Pixel = 2 Byte  ->  12 288 Datenbytes pro Bild.")
    k = 7
    gx, gy = 60, 130
    f.rect(gx, gy, 96 * k, 64 * k, (245, 245, 245), INK, 2, 0)
    for i in range(0, 96, 8):
        f.line([(gx + i * k, gy), (gx + i * k, gy + 64 * k)], (210, 210, 215), 1)
    for j in range(0, 64, 8):
        f.line([(gx, gy + j * k), (gx + 96 * k, gy + j * k)], (210, 210, 215), 1)
    for r in range(4):
        y = gy + (r * 3 + 1) * k * 2 - 4
        f.arrow([(gx + 6, y), (gx + 96 * k - 6, y)], BLUE, 2.5, 10)
        if r < 3:
            f.line([(gx + 96 * k - 6, y), (gx + 6, y + 6 * k)], BLUE, 1.5, dash=7)
    f.text(gx, gy - 28, "(0,0)", 16, True)
    f.text(gx + 96 * k, gy - 28, "(95,0)", 16, True, ha="r")
    f.text(gx, gy + 64 * k + 8, "(0,63)", 16, True)
    f.text(gx + 96 * k / 2, gy + 215, "...", 34, True, BLUE, "c")
    f.text(gx + 96 * k, gy + 64 * k + 8, "(95,63)", 16, True, ha="r")
    f.text(gx + 96 * k / 2, gy + 64 * k + 34, "x: 0..95 (schnell)   y: 0..63 (langsam)  -  Zeile fuer Zeile, links -> rechts, oben -> unten", 16, ha="c", color=GREY)
    # Datenstrom
    sx = 790
    f.text(sx, 120, "Datenstrom ueber SPI pro Bild", 21, True, BLUE)
    f.box(sx, 165, 750, 70, "Kopf: 15 00 5F | 75 00 3F   (D/C = 0, Kommandos)", C_CTRL, 18, True)
    f.text(sx + 10, 242, "0x15 = Spaltenbereich 0..95   0x75 = Zeilenbereich 0..63   -> Fenster = ganzes Display", 14, color=GREY)
    f.box(sx, 285, 750, 60, "Pixeldaten (D/C = 1, CS bleibt ueber das ganze Bild low)", C_SPI, 18, True)
    labels = [("P(0,0).hi", C_MEM), ("P(0,0).lo", C_MEM), ("P(1,0).hi", C_MEM), ("P(1,0).lo", C_MEM), ("...", WHITE), ("P(95,63).hi", C_MEM), ("P(95,63).lo", C_MEM)]
    x = sx
    for t, c in labels:
        w = 100 if t != "..." else 50
        f.box(x, 370, w, 50, t, c, 13)
        x += w + 8
    f.text(sx, 435, "Das Display zaehlt die Adresse selbst hoch (Zeile voll -> naechste Zeile),\nder FPGA sendet nur Pixel in der richtigen Reihenfolge.", 16)
    f.box(sx, 510, 750, 70, "frame_tick (1 Takt)  ->  neuer Modus, neuer Winkel, Pong-Schritt\nDanach beginnt sofort das naechste Bild mit dem Kopf.", C_REND, 17)
    f.rect(sx, 610, 750, 110, C_WARN, ORANGE)
    f.text(sx + 15, 620, "Zeit: 1 Byte ca. 1,4 us  ->  1 Pixel ca. 2,9 us (inkl. 12 Takte Wartezeit)\n6144 Pixel ca. 18 ms  ->  rechnerisch ca. 55 Bilder pro Sekunde.", 16)
    f.save("09_bildaufbau.png")


def bit_cells(f, x, y, labels, widths, colors, h=60, size=17):
    for lab, w, c in zip(labels, widths, colors):
        f.box(x, y, w, h, lab, c, size, False, r=4)
        x += w


def fig_rgb565():
    f = Fig(1600, 600)
    f.title("Ein Pixel = 16 Bit (RGB565)", "5 Bit Rot, 6 Bit Gruen, 5 Bit Blau; wird als zwei Bytes gesendet (zuerst das hohe Byte).")
    cw = 60
    x0 = 190
    cols = [(255, 190, 190)] * 5 + [(190, 240, 190)] * 6 + [(190, 205, 255)] * 5
    for i in range(16):
        f.box(x0 + i * cw, 120, cw, 60, "", cols[i], 16, r=2)
        f.text(x0 + i * cw + cw / 2, 100, str(15 - i), 15, color=GREY, ha="c")
    f.text(x0 + 2.5 * cw, 195, "R (5 Bit)", 18, True, RED, "c")
    f.text(x0 + 8 * cw, 195, "G (6 Bit)", 18, True, GREEN, "c")
    f.text(x0 + 13.5 * cw, 195, "B (5 Bit)", 18, True, BLUE, "c")
    f.text(30, 140, "Bit", 18, True)
    # Beispiel Bosch-Rot
    r, g, b = 227, 0, 21
    v = ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)
    bits = f"{v:016b}"
    f.text(30, 250, "Beispiel Bosch-Rot (227, 0, 21):", 19, True)
    f.text(30, 285, "R = 227 / 8 = 28 = 11100     G = 0 / 4 = 0 = 000000     B = 21 / 8 = 2 = 00010", 18, mono=True)
    for i in range(16):
        f.box(x0 + i * cw, 340, cw, 56, bits[i], cols[i], 22, True, r=2)
    f.text(x0 + 16 * cw + 20, 355, f"= 0x{v:04X}", 24, True)
    f.rect(x0, 420, 8 * cw, 56, None, INK, 3, 6)
    f.rect(x0 + 8 * cw, 420, 8 * cw, 56, None, INK, 3, 6)
    f.text(x0 + 4 * cw, 448, f"1. Byte: 0x{v >> 8:02X}  (pix[15:8])", 18, True, ha="c", va="m")
    f.text(x0 + 12 * cw, 448, f"2. Byte: 0x{v & 255:02X}  (pix[7:0])", 18, True, ha="c", va="m")
    f.text(30, 505, "Weiss = 0xFFFF (alle Bits 1)   Schwarz = 0x0000   -   Pong und der Hinweis nutzen nur diese beiden Werte.", 17)
    f.text(30, 540, "Der Controller wurde mit Remap 0x72 auf 65k-Farben (RGB-Reihenfolge) eingestellt (siehe Init-Sequenz).", 15, color=GREY)
    f.save("10_rgb565.png")


def fig_pipeline():
    f = Fig(1700, 780)
    f.title("Pixel-Pipeline in oled_render", "Pro Takt wird jede Stufe weitergeschoben. x/y bleiben ca. 300 Takte stabil - die Pipeline hat nur 5 Stufen und ist lange fertig.")
    stages = [
        ("Stufe 1", "Zeile aus Bitmap-ROM\n(Modus waehlt BOSCH,\nHHN oder Hinweis)\nx merken\nSprite-Fenster pruefen\n(in_box, sx, Adresse)", "row1, x1,\nin_box1, sx1, sidx1"),
        ("Stufe 2", "Pixelindex aus der Zeile\nholen (4 Bit, get_px)\n\nSprite-Zeile aus\nSprite-ROM holen", "idx2, srow2,\nin_box2, sx2"),
        ("Stufe 3", "Palette: Index ->\nRGB565-Farbe\n\nSprite-Pixel (4 Bit)\nauswaehlen", "col3, sym3,\nin_box3"),
        ("Stufe 4", "Sprite-Palette:\nGrauwert -> RGB565\n\nBitmap-Farbe\ndurchreichen", "col4, sym4,\nin_box4"),
        ("Stufe 5", "Auswahl (Multiplexer):\nPong?  -> Weiss/Schwarz\nBosch + im Fenster\n   -> Sprite-Farbe\nsonst -> Bitmap-Farbe", "pix[15:0]"),
    ]
    x = 40
    for i, (t, body, regs) in enumerate(stages):
        f.rect(x, 150, 290, 330, C_REND if i < 4 else C_MEM, GREEN if i < 4 else ORANGE, 2, 12)
        f.text(x + 145, 162, t, 21, True, GREEN if i < 4 else ORANGE, "c")
        f.text(x + 145, 205, body, 17, ha="c")
        f.rect(x + 20, 400, 250, 62, WHITE, GREY, 1.5, 6)
        f.text(x + 145, 431, regs, 14, ha="c", va="m", mono=True)
        if i < 4:
            f.arrow([(x + 290, 300), (x + 330, 300)], INK, 3, 13)
        x += 330
    f.arrow([(0, 300), (40, 300)], INK, 3, 13)
    f.text(10, 270, "x, y", 17, True)
    f.box(1060, 560, 540, 110, "pong_game (2 eigene Stufen)\nVergleiche: Schlaeger, Ball, Netz, Ziffern\n-> pix_on (1 Bit)", WHITE, 17)
    f.arrow([(1500, 560), (1500, 480)], INK, 2.5)
    f.arrow([(1650, 300), (1692, 300)], INK, 3, 11)
    f.text(1672, 270, "pix", 17, True, ha="c")
    f.text(40, 520, "Warum eine Pipeline?", 20, True, BLUE)
    f.text(40, 555, "Ein einziger langer Rechenweg (ROM-Zeile -> Bit waehlen -> Palette -> Mux)\nmuesste in 10 ns fertig sein. Mit Registern dazwischen schafft jede Stufe\nihren kurzen Weg locker - die Latenz (5 Takte) spielt keine Rolle, weil\noled_ctrl vor dem Abholen 12 Takte wartet (PIPE_WAIT).", 17)
    f.text(40, 700, "Der Modus (mode), der Winkel (ang) und der Spielzustand aendern sich nur bei frame_tick,\nalso nie mitten im Bild - dadurch gibt es kein Zerreissen.", 17, True)
    f.save("11_pixel_pipeline.png")


def fig_rom():
    base, pal = gen_rom.bosch_image()
    y = 32
    row = base[y * 96:(y + 1) * 96]
    f = Fig(1600, 700)
    f.title("Bitmap-ROM: so liegt ein Bild im FPGA", "Jede Zeile ist ein 384-Bit-Wort: 96 Pixel x 4 Bit Palettenindex. Pixel 0 steht ganz links (MSB).")
    f.text(30, 100, f"Beispiel: Zeile y = {y} des Bosch-Bitmaps", 20, True)
    x0, cw = 30, 120
    show = list(range(0, 4)) + [None] + list(range(31, 34)) + [None] + [95]
    x = x0
    for sx in show:
        if sx is None:
            f.text(x + 20, 160, "...", 22, True, ha="c")
            x += 40
            continue
        idx = row[sx]
        f.box(x, 130, cw, 70, f"x={sx}\nidx={idx:X}", C_MEM if idx else WHITE, 16, r=4)
        x += cw + 6
    hexrow = "".join(f"{i:X}" for i in row)
    f.text(30, 225, "als Hex-Zeichen im VHDL (je Pixel eine Stelle):", 17, True)
    f.text(30, 255, hexrow[:48], 15, mono=True)
    f.text(30, 278, hexrow[48:], 15, mono=True)
    f.text(30, 325, "Pixel x liegt in den Bits (383 - 4x) bis (380 - 4x)  ->  get_px() prueft fuer x = 0..95, welcher Treffer es ist.", 17)
    # Palette
    f.text(30, 380, "Palette (16 Eintraege je Bild, RGB565):", 20, True)
    for i in range(6):
        c = pal[i]
        v = gen_rom.rgb565(c)
        f.rect(30 + i * 250, 420, 52, 52, c, INK, 2, 6)
        f.text(95 + i * 250, 424, f"idx {i}\n0x{v:04X}", 16, mono=True)
    f.rect(30, 510, 1540, 160, C_WARN, ORANGE)
    f.text(50, 522, "Speicherbedarf (aus gen_rom.py):", 18, True)
    f.text(50, 552, "3 Bitmaps (Bosch, HHN, Hinweis): 3 x 64 x 384 Bit = 73 728 Bit\nSprite-ROM (32 Winkel x 20 Zeilen x 80 Bit)  = 51 200 Bit\nDas passt bequem in den Artix-7 (225 KB Block-RAM, zusaetzlich LUT-ROM).\nDie Bilder aendert man nie von Hand: python scripts/gen_rom.py erzeugt src/oled_rom_pkg.vhd neu.", 16)
    f.save("12_rom_format.png")


def fig_sprites():
    base, pal = gen_rom.bosch_image()
    sprites = [gen_rom.sym_sprite(k) for k in range(gen_rom.SPR_N)]
    sym_pal = gen_rom.sym_palette()
    f = Fig(1600, 760)
    f.title("Bosch-Symbol: 32 vorgerenderte Dreh-Sprites", "Der Anker (H) hat nach 180 Grad wieder dieselbe Form - 32 Schritte x 5,625 Grad reichen fuer die volle Drehung.")
    ks = [0, 4, 8, 12, 16, 20, 24, 28]
    for i, k in enumerate(ks):
        im = Image.new("RGB", (20, 20))
        im.putdata([sym_pal[v] for v in sprites[k]])
        f.rect(30 + i * 192, 100, 168, 168, WHITE, GREY, 1, 0)
        f.paste(scaled(im, 8), 30 + i * 192 + 4, 104)
        f.text(30 + i * 192 + 84, 276, f"k = {k}  ({k * 180 / 32:.1f} Grad)", 15, ha="c")
    full = with_sprite(rgb_image(base, pal), sprites, sym_pal, 0)
    f.paste(scaled(full, 5), 30, 350)
    kx, ky = 30 + gen_rom.SPR_X0 * 5, 350 + gen_rom.SPR_Y0 * 5
    f.rect(kx, ky, 100, 100, None, RED, 3, 0)
    f.text(30, 680, "Bosch-Bild: Schriftzug kommt aus dem Bitmap, das rote\nQuadrat (20 x 20 Pixel, Ecke (1,22)) aus dem Sprite.", 16)
    f.arrow([(kx + 100, ky + 20), (640, 400)], RED, 2.5)
    f.text(660, 360, "Sprite-Fenster", 22, True, RED)
    f.text(660, 400, "Liegt der aktuelle Pixel (x, y) im Fenster, ersetzt die Sprite-Farbe die Bitmap-Farbe:\n\n    sx = x - 1        sy = y - 22        (0..19)\n    Zeile im Sprite-ROM = ang * 20 + sy\n    Pixel = Bits (79 - 4 sx) .. (76 - 4 sx)\n    Farbe = SYM_PAL(Pixel)   (16 Grauwerte von Weiss bis Grau)\n\nsw0: ang = 0 (H steht aufrecht)\nsw1: ang zaehlt alle 2 Bilder hoch (0..31, dann wieder 0)\n\nVorteil: keine Multiplikation / kein Sinus im FPGA, Kanten sind\nsauber geglaettet. Nachteil: nur die 32 festen Winkel.", 17, mono=False)
    f.save("13_sprites.png")


def pong_frame():
    im = Image.new("RGB", (96, 64), (0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([4, 25, 5, 38], fill=WHITE)
    d.rectangle([90, 25, 91, 38], fill=WHITE)
    d.rectangle([46, 30, 48, 32], fill=WHITE)
    for y in range(64):
        if (y >> 2) % 2 == 0:
            im.putpixel((47, y), WHITE)
    zero = ["111", "101", "101", "101", "111"]
    for x0 in (35, 55):
        for gy in range(5):
            for gx in range(3):
                if zero[gy][gx] == "1":
                    d.rectangle([x0 + gx * 2, 3 + gy * 2, x0 + gx * 2 + 1, 3 + gy * 2 + 1], fill=WHITE)
    return im


def fig_vorschau():
    base, pal = gen_rom.bosch_image()
    sprites = [gen_rom.sym_sprite(k) for k in range(gen_rom.SPR_N)]
    sym_pal = gen_rom.sym_palette()
    hhn = rgb_image(*gen_rom.hhn_image())
    msg = rgb_image(*gen_rom.msg_image())
    screens = [("sw0", "Bosch-Logo", with_sprite(rgb_image(base, pal), sprites, sym_pal, 0)),
               ("sw1", "Bosch, Anker dreht sich", with_sprite(rgb_image(base, pal), sprites, sym_pal, 9)),
               ("sw2", "HHN-Logo", hhn),
               ("sw3", "Pong 1 gegen 1", pong_frame()),
               ("kein / mehrere", "Waehle einen Schalter", msg)]
    f = Fig(1700, 440)
    f.title("Die fuenf Bildschirme (aus den echten ROM-Daten gerendert)")
    for i, (sw, name, im) in enumerate(screens):
        x = 30 + i * 330
        f.rect(x - 6, 96, 96 * 3 + 12, 64 * 3 + 12, (50, 50, 55), INK, 2, 8)
        f.paste(scaled(im, 3), x, 102)
        f.text(x + 144, 310, sw, 20, True, BLUE, "c")
        f.text(x + 144, 340, name, 17, ha="c")
    f.text(30, 400, "Das echte Display ist 0,8 x 0,5 Zoll gross (Digilent) - Farben wirken dort kraeftiger als am Bildschirm.", 15, color=GREY)
    f.save("14_bildschirme.png")


def fig_modus():
    f = Fig(1600, 640)
    f.title("Schalter -> Bild (Moduswahl)", "Es zaehlt nur eine Stellung mit GENAU einem Schalter oben. Alles andere zeigt den Hinweis.")
    hdr = ["sw3", "sw2", "sw1", "sw0", "Ergebnis"]
    xs = [60, 170, 280, 390, 520]
    f.rect(40, 100, 1500, 44, BLUE, BLUE, 1, 8)
    for x, h in zip(xs, hdr):
        f.text(x, 108, h, 20, True, WHITE)
    rows = [("0000", "kein Schalter -> Hinweis 'Waehle einen Schalter'", C_WARN),
            ("0001", "Bosch-Logo (Anker steht)", C_REND),
            ("0010", "Bosch-Logo, Anker rotiert", C_REND),
            ("0100", "HHN-Logo", C_REND),
            ("1000", "Pong, 1 gegen 1", C_REND),
            ("0011", "mehrere Schalter -> Hinweis", C_WARN),
            ("0101", "mehrere Schalter -> Hinweis", C_WARN),
            ("1111", "alle oben -> Hinweis", C_WARN)]
    for r, (bits, res, c) in enumerate(rows):
        y = 150 + r * 52
        f.rect(40, y, 1500, 48, c, GREY, 1, 6)
        for x, b in zip(xs, bits):
            f.ellipse(x + 20, y + 24, 14, BLUE if b == "1" else WHITE, INK, 2)
            f.text(x + 46, y + 10, b, 20, True, mono=True)
        f.text(xs[4], y + 10, res, 20)
    f.text(40, 580, "VHDL (decode): when \"0001\" => M_BOSCH; \"0010\" => M_ROT; \"0100\" => M_HHN; \"1000\" => M_PONG; when others => M_MSG", 16, mono=True)
    f.text(40, 610, "Blau gefuellt = Schalter oben (1).  Der Modus wird nur bei frame_tick uebernommen.", 16, color=GREY)
    f.save("15_moduswahl.png")


def fig_frame_timing():
    f = Fig(1600, 620)
    f.title("Zeitlicher Ablauf eines Bildes", "Nicht maßstaeblich - es zaehlt die Reihenfolge der Schritte.")
    f.rect(40, 100, 1520, 80, C_HW, INK, 2, 8)
    f.box(40, 100, 150, 80, "Kopf\n6 Byte", C_CTRL, 17, True)
    f.box(190, 100, 1220, 80, "6144 Pixel  (je Pixel: warten 12 Takte, Byte hi, Byte lo)   ca. 18 ms", C_SPI, 19, True)
    f.box(1410, 100, 150, 80, "frame_tick", C_REND, 17, True)
    f.text(40, 190, "Bild n", 18, True, BLUE)
    f.arrow([(1485, 180), (1485, 260)], RED, 3)
    f.rect(1000, 265, 560, 190, C_REND, GREEN)
    f.text(1015, 275, "Bei frame_tick (1 Takt):", 17, True, GREEN)
    f.text(1015, 305, "- mode  <- decode(sw)\n- ang   <- ang + 1  (alle 2 Bilder, nur sw1)\n- Pong: Schlaeger bewegen, Ball ein Schritt,\n         Punkte, Aufschlag-Zaehler", 16)
    f.text(40, 270, "Ein Pixel im Detail:", 18, True, BLUE)
    x = 40
    for t, w, c in [("warten\n12 Takte\n(120 ns)", 200, C_HW), ("SPI-Byte hi\n= 140 Takte\n(1,4 us)", 330, C_SPI), ("SPI-Byte lo\n= 140 Takte\n(1,4 us)", 330, C_SPI)]:
        f.box(x, 310, w, 90, t, c, 16)
        x += w
    f.text(40, 410, "Summe ca. 294 Takte = 2,94 us pro Pixel", 16, True)
    f.text(40, 470, "Rechenbeispiel:  6144 x 2,94 us = 18,06 ms  (+ 6 Kopf-Bytes = 8,4 us)\nBilder pro Sekunde = 1 / 18,07 ms = ca. 55 Hz", 17, mono=False)
    f.text(40, 540, "Die Zeit ist fast nur SPI-Uebertragung. Wuerde man SCK auf 12,5 MHz erhoehen, wuerde es doppelt so schnell -\ndas erlaubt der Controller laut Datenblatt aber nicht (min. 150 ns Taktzyklus).", 16, color=GREY)
    f.save("16_bildzeit.png")


def fig_pong_feld():
    f = Fig(1700, 800)
    f.title("Pong: Spielfeld und Abmessungen (alle Angaben in Pixeln)", "Das Feld ist das Display selbst: 96 x 64, Ursprung (0,0) oben links.")
    k = 7
    gx, gy = 40, 120
    f.rect(gx, gy, 96 * k, 64 * k, (0, 0, 0), INK, 2, 0)
    def P(x, y, w, h, c=WHITE):
        f.rect(gx + x * k, gy + y * k, w * k, h * k, c, None, 0, 0)
    P(4, 25, 2, 14)
    P(90, 25, 2, 14)
    P(46, 30, 3, 3, (255, 200, 40))
    for y in range(64):
        if (y >> 2) % 2 == 0:
            P(47, y, 1, 1, (150, 150, 150))
    zero = ["111", "101", "101", "101", "111"]
    for x0 in (35, 55):
        for gyy in range(5):
            for gxx in range(3):
                if zero[gyy][gxx] == "1":
                    P(x0 + gxx * 2, 3 + gyy * 2, 2, 2)
    # Beschriftung rechts
    tx = 790
    marks = [(1, "Linker Schlaeger", "x = 4..5 (2 breit), 14 hoch, Start y = 25..38\nbtn0 hoch, btn1 runter, je 3 px pro Bild", (12, 30)),
             (2, "Rechter Schlaeger", "x = 90..91, 14 hoch, Start y = 25..38\nbtn2 hoch, btn3 runter", (84, 30)),
             (3, "Ball", "3 x 3 Pixel, Start bei (46,30)\nGeschwindigkeit vx = +-2 .. +-4, vy = -2..+2 px/Bild", (56, 41)),
             (4, "Netz", "x = 47, 4 Pixel an / 4 Pixel aus (nur Optik)", (41, 54)),
             (5, "Punktestand", "3 x 5 Ziffern, doppelt vergroessert (6 x 10 px)\nlinks ab x = 35, rechts ab x = 55, y = 3", (26, 8))]
    for n, h, t, (mx, my) in marks:
        f.ellipse(gx + mx * k, gy + my * k, 15, ORANGE, WHITE)
        f.text(gx + mx * k, gy + my * k, str(n), 18, True, WHITE, "c", "m")
    for i, (n, h, t, _) in enumerate(marks):
        y = 130 + i * 120
        f.ellipse(tx + 15, y + 15, 15, ORANGE, WHITE)
        f.text(tx + 15, y + 15, str(n), 18, True, WHITE, "c", "m")
        f.text(tx + 45, y, h, 20, True, BLUE)
        f.text(tx + 45, y + 30, t, 16)
    f.rect(gx, gy + 64 * k + 20, 96 * k, 110, C_WARN, ORANGE)
    f.text(gx + 15, gy + 64 * k + 30, "Waende: oben (y = 0) und unten (y = 63) - der Ball prallt ab.\nTor: Verlaesst der Ball links (x <= 0) oder rechts (x + 3 >= 96)\ndas Feld, bekommt der Gegner einen Punkt.", 15)
    f.save("17_pong_spielfeld.png")


def diamond(f, cx, cy, w, h, t, fill=C_WARN, size=16):
    f.poly([(cx, cy - h / 2), (cx + w / 2, cy), (cx, cy + h / 2), (cx - w / 2, cy)], fill, INK, 2)
    f.text(cx, cy, t, size, False, INK, "c", "m")


def fig_pong_ablauf():
    f = Fig(1600, 1020)
    f.title("Pong: was bei jedem frame_tick passiert (ca. 55 mal pro Sekunde)")
    cx = 420
    f.box(cx - 170, 70, 340, 56, "Start: frame_tick = 1 und Modus = Pong", C_HW, 17)
    f.arrow([(cx, 126), (cx, 150)])
    f.box(cx - 170, 150, 340, 66, "Schlaeger bewegen\nnur eine Taste gedrueckt: +-3 px, Grenzen 0..50", C_REND, 16)
    f.arrow([(cx, 216), (cx, 245)])
    diamond(f, cx, 290, 330, 90, "Spielende-Pause\n(over_cnt > 0)?")
    f.arrow([(cx + 165, 290), (800, 290)])
    f.text(cx + 175, 268, "ja", 15, True)
    f.box(800, 255, 420, 70, "over_cnt - 1;  bei 1: Punkte auf 0 setzen,\nAufschlag-Pause starten", C_REND, 15)
    f.arrow([(cx, 335), (cx, 365)])
    f.text(cx + 8, 340, "nein", 15, True)
    diamond(f, cx, 410, 330, 90, "Aufschlag-Pause\n(serve_cnt > 0)?")
    f.arrow([(cx + 165, 410), (800, 410)])
    f.text(cx + 175, 388, "ja", 15, True)
    f.box(800, 375, 420, 70, "serve_cnt - 1  (45 Bilder = ca. 0,8 s)\nBall ruht in der Mitte", C_REND, 15)
    f.arrow([(cx, 455), (cx, 485)])
    f.text(cx + 8, 460, "nein", 15, True)
    f.box(cx - 170, 485, 340, 60, "naechste Position:  nx = bx + vx,  ny = by + vy", C_REND, 16)
    f.arrow([(cx, 545), (cx, 575)])
    f.box(cx - 170, 575, 340, 70, "Wand oben/unten?  ny < 0  oder  ny > 61\n-> ny begrenzen, vy = -vy", C_REND, 16)
    f.arrow([(cx, 645), (cx, 675)])
    diamond(f, cx, 725, 340, 100, "Schlaeger getroffen?\n(x- UND y-Ueberlappung,\nBall fliegt zum Schlaeger)")
    f.arrow([(cx + 170, 725), (800, 725)])
    f.text(cx + 180, 703, "ja", 15, True)
    f.box(800, 670, 520, 110, "Ball an Schlaegerkante setzen\nvx = -(|vx| + 1), max. Betrag 4  (wird schneller)\nvy = Zone des Treffers (siehe naechstes Bild)", C_MEM, 15)
    f.arrow([(cx, 775), (cx, 805)])
    f.text(cx + 8, 782, "nein", 15, True)
    diamond(f, cx, 850, 340, 90, "Ball ausserhalb?\nnx <= 0  oder  nx + 3 >= 96")
    f.arrow([(cx + 170, 850), (800, 850)])
    f.text(cx + 180, 828, "ja", 15, True)
    f.box(800, 800, 520, 110, "Punkt fuer den Gegner (Zaehler + 1)\nBall in die Mitte, Aufschlag Richtung Verlierer\nvy zufaellig (LFSR); bei 9 Punkten: over_cnt = 150", C_MEM, 15)
    f.arrow([(cx, 895), (cx, 940)])
    f.text(cx + 8, 905, "nein", 15, True)
    f.box(cx - 170, 940, 340, 56, "bx, by <- nx, ny  (Ball bewegt)", C_REND, 16)
    f.rect(1250, 100, 320, 200, C_WARN, ORANGE)
    f.text(1265, 110, "Wichtig:", 17, True)
    f.text(1265, 140, "Der Ablauf ist ein einziger\ngetakteter Prozess. Ein 'Bild'\nist hier ein Spielschritt.\nGezeichnet wird in einer\nseparaten Pipeline.", 15)
    f.save("18_pong_ablauf.png")


def fig_ablenkung():
    f = Fig(1500, 560)
    f.title("Pong: Ablenkwinkel haengt vom Treffpunkt ab", "offset = (ny + 1) - Schlaegerposition   (Ball-Mitte relativ zur Schlaegeroberkante)")
    k = 22
    px, py = 180, 130
    zones = [(0, 4, "-2", (255, 205, 205)), (4, 7, "-1", (255, 232, 205)), (7, 10, "+1", (215, 240, 220)), (10, 14, "+2", (190, 225, 255))]
    for a, b, v, c in zones:
        f.rect(px, py + a * k, 40, (b - a) * k, c, INK, 2, 0)
        f.text(px + 60, py + (a + b) / 2 * k, f"offset {a}..{b - 1}:  vy = {v}", 18, True, va="m")
        yc = py + (a + b) / 2 * k
        vy = int(v)
        f.arrow([(px - 5, yc), (px - 100, yc + vy * 26)], BLUE, 2.5, 11)
    f.text(px + 20, py - 30, "Schlaeger (14 px)", 16, True, ha="c")
    f.text(620, 120, "Der Ball kommt von rechts, vx wechselt das Vorzeichen\n(und waechst um 1 bis max. 4).\n\nObere Haelfte  ->  Ball fliegt nach oben (vy negativ)\nUntere Haelfte ->  Ball fliegt nach unten (vy positiv)\nAussen steiler (+-2), innen flacher (+-1).\n\nDamit kann der Spieler den Ball gezielt lenken;\neine Ablenkung von 0 gibt es bewusst nicht -\nder Ball fliegt nie waagerecht.", 18)
    f.save("19_pong_ablenkung.png")


def fig_entprellung():
    f = Fig(1600, 640)
    f.title("Entprellung: input_filter", "Mechanische Schalter prellen einige Millisekunden. Der Filter uebernimmt einen neuen Pegel erst, wenn er 10 ms lang stabil war.")
    f.box(40, 130, 150, 70, "Eingang d\n(asynchron)", C_IN, 16)
    f.box(240, 130, 130, 70, "FF", C_MEM, 18, True)
    f.box(410, 130, 130, 70, "FF", C_MEM, 18, True)
    f.box(600, 120, 220, 90, "sync(1) = stable?\nnein: Zaehler + 1\nja: Zaehler = 0", C_REND, 15)
    f.box(870, 130, 150, 70, "stable\n= q", C_MEM, 17, True)
    for a, b in [(190, 240), (370, 410), (540, 600), (820, 870)]:
        f.arrow([(a, 165), (b, 165)])
    f.text(305, 215, "2-FF-Sync.", 15, color=GREY, ha="c")
    f.text(475, 215, "gegen Metastabilitaet", 15, color=GREY, ha="c")
    f.text(710, 215, "Zaehler = 1 000 000 (10 ms)\n-> stable <- sync(1)", 15, color=GREY, ha="c")
    # Wellenformen
    f.text(40, 290, "d (prellt)", 17, True, mono=True)
    f.line([(200, 340), (400, 340), (400, 300), (430, 300), (430, 340), (455, 340), (455, 300), (480, 300), (480, 340),
            (500, 340), (500, 300), (1500, 300)], BLUE, 3)
    f.text(40, 390, "q (stabil)", 17, True, mono=True)
    f.line([(200, 440), (880, 440), (880, 400), (1500, 400)], RED, 3)
    f.arrow([(500, 360), (880, 360)], GREY, 1.5, 8)
    f.arrow([(880, 360), (500, 360)], GREY, 1.5, 8)
    f.text(690, 335, "10 ms stabil abwarten", 16, True, ORANGE, "c")
    f.line([(500, 290), (500, 450)], GREY, 1.2, dash=6)
    f.line([(880, 290), (880, 450)], GREY, 1.2, dash=6)
    f.text(40, 500, "Wichtig fuer das Design: Alle Schalter und Taster laufen durch input_filter (8 Stueck).\nDie Taster liegen im Ruhezustand auf 0 und liefern 1, wenn gedrueckt (Arty A7). Der RESET-Taster ist umgekehrt (aktiv low)\nund wird nur durch einen 2-FF-Synchronisierer gefuehrt.", 17)
    f.rect(40, 570, 1500, 50, C_WARN, ORANGE)
    f.text(55, 580, "Quelle zu den Tastern: Digilent Arty A7 Reference Manual, Abschnitt 9 (Basic I/O).", 16)
    f.save("20_entprellung.png")


def fig_testbench():
    f = Fig(1600, 560)
    f.title("Simulation: tb_spi_top (GHDL)", "Ein Software-Modell des Displays liest die SPI-Signale mit und prueft den Inhalt Bit fuer Bit.")
    f.box(40, 160, 260, 120, "Stimulus\nsw, btn, ck_rst\n(Prozess in der Testbench)", C_IN, 17)
    f.box(370, 140, 340, 160, "DUT: spi_top\n(das echte Design)\nCLK_HZ = 1 MHz, SPI_HALF = 2\n(nur zum schnelleren Simulieren)", C_REND, 17, True)
    f.box(790, 140, 340, 160, "SSD1331-Modell\nschiebt Bits bei SCK-Anstieg ein\nD/C = 0 -> Kommandoliste\nD/C = 1 -> Bildspeicher (12 288 Byte)", C_SPI, 17)
    f.arrow([(300, 220), (370, 220)])
    f.arrow([(710, 220), (790, 220)])
    f.text(750, 150, "CS, SCK,\nMOSI, D/C", 13, color=GREY, ha="c")
    f.arrow([(960, 300), (960, 360)])
    f.box(40, 360, 1500, 160, "Pruefungen (alle mit assert):\n1. Init: erstes Kommando 0xAE, 0xAF an Position 37, genau 44 Kommandos nach Bild 1, Kopf 15 00 5F 75 00 3F\n2. Bildinhalt aller 6144 Pixel stimmt mit der ROM-Palette ueberein (Hinweis, Bosch, HHN)\n3. Sprite-Fenster passt zu einem Drehwinkel; im Modus sw1 laeuft der Winkel hoch (>= 5)\n4. Pong: Schlaeger bei x=4/x=91, Ball in der Mitte; btn0 bewegt linken Schlaeger um 12 px, rechter bleibt\n5. Mehrere Schalter -> Hinweisbild", C_HW, 16)
    f.save("21_testbench.png")


def main():
    for fn in (fig_grundlagen, fig_toolflow, fig_anschluss, fig_gesamt, fig_spi_timing, fig_spi_fsm, fig_ctrl_fsm,
               fig_power, fig_bildaufbau, fig_rgb565, fig_pipeline, fig_rom, fig_sprites, fig_vorschau, fig_modus,
               fig_frame_timing, fig_pong_feld, fig_pong_ablauf, fig_ablenkung, fig_entprellung, fig_testbench):
        fn()
        print("ok", fn.__name__)


if __name__ == "__main__":
    main()
