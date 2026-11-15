"""Erzeugt Bericht (DOCX/MD), Grafiken und Praesentation (PPTX) fuer Phase I.

Aufruf aus beliebigem Ordner:  python phase_1/scripts/create_docs.py
PDF anschliessend aus der DOCX-Datei mit Word exportieren (siehe README).
"""
from pathlib import Path
import math
import textwrap

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt as DocPt, RGBColor as DocColor
from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches, Pt

import diagrams

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "doc"
IMG = DOC / "img"
INK, RED, TEAL, GRAY, LIGHT = "20272B", "C92C38", "007F86", "56646B", "F2F5F6"
TITLE = "Phase I – 7-Segment-Anzeige mit Betriebsarten"
GROUP = "Gruppe: Mark (Endziffern Matrikelnummer 91) und Maxi (93)"
SIM_TIME = "69.050 ns"


def source(rel):
    return (ROOT / rel).read_text(encoding="utf-8").splitlines()


def excerpt(rel, start, end):
    lines = source(rel)
    first = next(i for i, line in enumerate(lines) if start in line)
    last = next(i for i in range(first, len(lines)) if end in lines[i])
    return textwrap.dedent("\n".join(lines[first:last + 1]))


def P(text):
    return ("p", text)


def H(text):
    return ("h2", text)


def F(name, caption):
    return ("img", name, caption)


def T(headers, rows):
    return ("table", headers, rows)


def C(code):
    return ("code", code)


def L(items):
    return ("list", items)


PINS = [
    ("CLK100MHZ", "E3", "Board-Oszillator", "100 MHz, Periode 10 ns"),
    ("ck_rst", "C2", "RESET-Taster (rot)", "aktiv Low"),
    ("sw[0]", "A8", "SW0", "Modus Zähler"),
    ("sw[1]", "C11", "SW1", "Modus 91 (Mark)"),
    ("sw[2]", "C10", "SW2", "Modus 93 (Maxi)"),
    ("sw[3]", "A10", "SW3", "Modus Binäreingabe"),
    ("btn[0]", "D9", "BTN0", "+1 / Bit 0"),
    ("btn[1]", "C9", "BTN1", "−1 / Bit 1"),
    ("btn[2]", "B9", "BTN2", "+10 / Bit 2"),
    ("btn[3]", "B8", "BTN3", "−10 / Bit 3"),
    ("seg_r[0]", "D13", "JA7 → SSD AA", "Segment a"),
    ("seg_r[1]", "B18", "JA8 → SSD AB", "Segment b"),
    ("seg_r[2]", "A18", "JA9 → SSD AC", "Segment c"),
    ("seg_r[3]", "K16", "JA10 → SSD AD", "Segment d"),
    ("seg_r[4]", "J17", "JB7 → SSD AE", "Segment e"),
    ("seg_r[5]", "J18", "JB8 → SSD AF", "Segment f"),
    ("seg_r[6]", "K15", "JB9 → SSD AG", "Segment g"),
    ("dsel_r", "J15", "JB10 → SSD C", "Ziffernauswahl (0: rechts)"),
]

SOURCES = [
    "Aufgabenstellung: Laborfolien „Labor: 7-Segment-Anzeige“, Phase I (Folien 210/211), phase_1/task/image3.png und image4.png.",
    "Digilent Arty A7 Reference Manual: https://digilent.com/reference/programmable-logic/arty-a7/reference-manual",
    "Digilent Pmod SSD Reference Manual: https://digilent.com/reference/pmod/pmodssd/reference-manual",
    "Digilent Master-XDC: https://github.com/Digilent/digilent-xdc/blob/master/Arty-A7-35-Master.xdc",
    "GHDL-Dokumentation: https://ghdl.github.io/ghdl/",
    "Lokale Referenz: prj_final/src und prj_final/constraints/arty_a7_35_wecker.xdc (Pinbelegung, Anzeigemodule).",
]


def sections():
    counter_code = excerpt("src/phase1_top.vhd", "elsif sw_sync = MODE_COUNT then", "bin_value <= bin_value xor unsigned(press);")
    decoder_code = excerpt("src/phase1_top.vhd", "process (sw_sync, count, bin_value)", "end process;")
    display_code = excerpt("src/phase1_top.vhd", "tens <= to_unsigned(value / 10, 4);", "dsel_r <= driver_sel;")
    sync_code = excerpt("src/phase1_top.vhd", "process (CLK100MHZ, ck_rst)", "sw_sync <= sw_meta;")
    debounce_code = excerpt("src/btn_debounce.vhd", "if rst = '1' then", "press_o <= press;")
    xdc_code = excerpt("constraints/arty_a7_35_ssd.xdc", "## SW0", "[get_ports {btn[3]}]")
    return [
        ("Einleitung, Ziel und Anforderungen", [
            P("Die erste Laborphase verbindet eine VHDL-Beschreibung mit einer sichtbaren Ausgabe am Digilent Arty A7-35T. Laut Aufgabenstellung (Folie 210) sind die Ansteuerung der 7-Segment-Anzeige, eine VHDL-Implementierung mit Testbench sowie die Ausgabe der Zahl „0“ über das Arty-Board und ein Pmod mit zwei 7-Segment-Einheiten gefordert. Folie 211 legt den Umfang von Präsentation und Bericht fest: Theorie (Motivation, Arty + Pmod, 7-Segment-Anzeige inklusive Pinbelegung), Entwurf (Blockschaltbild), Implementierung (VHDL, Testbench, Constraints) und Test (Simulation und Board)."),
            P("Unsere Umsetzung erfüllt die Pflicht – nach dem Reset zeigt der Modus SW0 die Zahl 0 – und erweitert sie zu einem Mehrmodus-Design. Vier Schiebeschalter wählen die Betriebsart, vier Taster verändern den angezeigten Wert. Damit werden alle Grundlagen der Phase I (Segmentcodierung, Zeitmultiplex zweier Ziffern, Pinzuordnung) und zusätzlich die sichere Verarbeitung asynchroner Eingänge (Synchronisation, Entprellung, Flankenauswertung) an einem überschaubaren Beispiel demonstriert."),
            P("Der Bericht beschreibt den implementierten Stand exakt. Die RTL-Simulation wurde mit GHDL 6.0.0 durchgeführt und bestanden; zusätzlich wurden alle synthetisierbaren Quellen mit GHDL im Modus VHDL-93 analysiert und synthetisiert. Ein Vivado-Build mit Timing-Analyse und der physische Boardtest sind noch offen und als Prüfliste in Kapitel 15 aufgeführt."),
            T(["ID", "Anforderung", "Umsetzung", "Nachweis"], [
                ("P1-01", "Ausgabe der Zahl 0", "SW0 nach Reset: rechts 0, links dunkel", "TB „start“"),
                ("P1-02", "SW0: BTN0 addiert 1", "press(0) → count + 1", "TB: +1 über 0 … 99"),
                ("P1-03", "SW0: BTN1 subtrahiert 1, nie < 0", "bei count = 0 bleibt 0", "TB „0 − 1 clamps“"),
                ("P1-04", "SW0: BTN2 addiert 10", "count + 10; ≥ 90 → 0", "TB „95 + 10 overflow“"),
                ("P1-05", "SW0: BTN3 subtrahiert 10, nie < 0", "count < 10 → 0", "TB „9 − 10 clamps“"),
                ("P1-06", "99 + 1 ergibt 0", "Überlauf auf 0", "TB: +1-Durchlauf"),
                ("P1-07", "SW1: Anzeige 91 (Mark)", "Konstante MATR_MARK", "TB „SW1 Mark“"),
                ("P1-08", "SW2: Anzeige 93 (Maxi)", "Konstante MATR_MAXI", "TB „SW2 Maxi“"),
                ("P1-09", "SW3: Zahl binär über Taster", "BTNi toggelt Bit i (0 … 15)", "TB: alle 16 Werte"),
                ("P1-10", "Mehrere Schalter: Anzeige dunkel", "show = 0 (auch bei 0 Schaltern)", "TB: 5 Kombinationen"),
                ("P1-11", "Ein Druck = genau ein Schritt", "btn_debounce, 10 ms", "TB Prellen/Halten"),
                ("P1-12", "Reset über ck_rst", "count = bin_value = 0", "TB „reset“"),
                ("P1-13", "Eigenständiges Vivado-Projekt", "Tcl-Skript + XDC", "Build offen"),
            ]),
        ]),
        ("Hardware: Arty A7-35T und Pmod SSD", [
            P("Zielplattform ist das Arty A7-35T mit dem FPGA xc7a35ticsg324-1L (Artix-7) und einem 100-MHz-Oszillator an Pin E3. Auf dem Board werden die Schiebeschalter SW0 … SW3, die Taster BTN0 … BTN3 und der rote RESET-Taster (ck_rst) verwendet. Die Taster liefern gedrückt eine logische 1 (aktiv High), ck_rst liefert gedrückt eine 0 (aktiv Low). Ein Schiebeschalter in Stellung „oben/ON“ liefert 1. Alle Signale nutzen den IO-Standard LVCMOS33."),
            P("Die Anzeige ist das externe Digilent Pmod SSD: zwei 7-Segment-Ziffern mit gemeinsamer Kathode. Das Modul hat zwei 6-polige Stecker: J1 mit AA … AD und J2 mit AE, AF, AG und C, jeweils plus GND und VCC. Die sieben Segmentleitungen AA … AG sind für beide Ziffern gemeinsam; der Pin C wählt die aktive Ziffer. Damit benötigt die Anzeige nur neun Signalleitungen."),
            P("Verdrahtung wie im Weckerprojekt: J1 an die UNTERE Reihe (Pins 7 … 12) von JA, J2 an die UNTERE Reihe von JB. Die obere Reihe (Pins 1 … 6) bleibt frei. Vor dem Umstecken die Versorgung trennen, die Orientierung (GND/VCC) prüfen und nur die 3,3-V-Pmod-Versorgung verwenden."),
            F("verdrahtung.png", "Verdrahtung Arty JA/JB (untere Reihe) zum Pmod SSD J1/J2 mit FPGA-Pins"),
            T(["Port", "FPGA-Pin", "Verbindung", "Bedeutung"], PINS),
        ]),
        ("Funktionsweise der 7-Segment-Anzeige", [
            H("3.1 Aufbau einer Ziffer"),
            P("Eine Ziffer besteht aus sieben einzeln ansteuerbaren LED-Segmenten, die nach Konvention im Uhrzeigersinn mit a (oben), b (oben rechts), c (unten rechts), d (unten), e (unten links), f (oben links) und g (Mitte) bezeichnet werden. Der Dezimalpunkt wird nicht verwendet. Im VHDL-Vektor seg(6 downto 0) steht Bit 6 für g und Bit 0 für a; als Text geschrieben ergibt sich die Reihenfolge „gfedcba“. Bit i des Ports seg_r ist über den Pmod-Pin A(a+i) mit dem Segment verbunden – zum Beispiel seg_r[0] → AA → Segment a."),
            F("segment_aufbau.png", "Segmentbezeichnung a … g und Zuordnung Bit → Port → Pmod-Pin → FPGA-Pin"),
            H("3.2 Elektrisches Prinzip: gemeinsame Kathode"),
            P("Jedes Segment ist eine Leuchtdiode. Sie leuchtet, wenn ihre Anode positiv gegenüber der Kathode ist und Strom fließt. Bei einer Anzeige mit gemeinsamer Kathode sind die Kathoden aller sieben Segmente einer Ziffer miteinander verbunden. Die Anode jedes Segments wird über eine eigene Leitung angesteuert. Ein Segment leuchtet also genau dann, wenn seine Anodenleitung auf 1 liegt UND die gemeinsame Kathode seiner Ziffer leitend mit GND verbunden ist. Daraus folgt die aktiv-High-Logik: seg_r(i) = 1 schaltet Segment i ein."),
            P("Beim Pmod SSD sind die Anodenleitungen gleichnamiger Segmente beider Ziffern verbunden (AA versorgt das a-Segment links und rechts). Der Pin C entscheidet, welche Kathode leitet. Es leuchtet deshalb immer nur eine Ziffer; würden beide Kathoden gleichzeitig leiten, zeigten beide Ziffern dasselbe Muster. Die Zuordnung C = 0 → rechte Ziffer stammt aus dem vorhandenen ssd_driver und wird beim Boardtest bestätigt; bei vertauschten Ziffern genügt es, im Treiber dsel <= not sel zu setzen. Die genaue elektrische Beschaltung (Vorwiderstände, Kathodentreiber) ist dem Digilent-Schaltplan zu entnehmen; für die Logik ist nur die obige Regel relevant."),
            F("segment_elektrisch.png", "Prinzipschaltung: gemeinsame Anodenleitungen AA … AG, getrennte Kathoden, Auswahl über C"),
            H("3.3 Segmentcodierung"),
            P("Der kombinatorische seg7_decoder übersetzt eine 4-Bit-Ziffer (BCD) direkt in das 7-Bit-Muster. Er benötigt keinen Takt; Änderungen am Eingang wirken nach der Gatterlaufzeit. Für die ungültigen BCD-Werte 10 … 15 liefert er einen Mittelstrich (nur g). Diese Werte treten in Phase I nicht auf, weil value immer mit / 10 und mod 10 zerlegt wird."),
            F("segment_muster.png", "Segmentmuster aller Dezimalziffern und des Ersatzzeichens"),
            T(["Ziffer", "gfedcba", "leuchtende Segmente", "Ziffer", "gfedcba", "leuchtende Segmente"], [
                (str(v), diagrams.PATTERNS[v], ", ".join(c for i, c in enumerate("abcdefg") if diagrams.PATTERNS[v][6 - i] == "1"),
                 str(v + 5), diagrams.PATTERNS[v + 5], ", ".join(c for i, c in enumerate("abcdefg") if diagrams.PATTERNS[v + 5][6 - i] == "1"))
                for v in range(5)
            ]),
            H("3.4 Zeitmultiplex zweier Ziffern"),
            P("Weil die Segmentleitungen gemeinsam sind, wird zwischen den Ziffern zeitlich umgeschaltet: Im ersten Zeitschlitz liegt das Muster der Einerstelle an und C wählt die rechte Ziffer; im zweiten Zeitschlitz das Muster der Zehnerstelle mit C für die linke Ziffer. Segmentmuster und Auswahl wechseln in derselben Taktflanke, damit kein Muster kurzzeitig auf der falschen Ziffer erscheint."),
            P("Den Takt für das Umschalten liefert tick_gen mit DIV = max(1, CLK_HZ / (2 · REFRESH_HZ)) = 100.000.000 / 1.000 = 100.000. Alle 100.000 Systemtakte (1 ms) entsteht ein 1-Takt-Puls, der das sel-Register invertiert. Ein vollständiges Bild aus beiden Ziffern dauert 2 ms; jede Ziffer wird also 500-mal pro Sekunde mit 50 % Tastverhältnis angesteuert. Das liegt weit über der Flimmergrenze des Auges (je nach Helligkeit und Blickwinkel etwa 50 … 100 Hz), daher erscheinen beide Ziffern gleichzeitig und ruhig."),
            F("multiplex_timing.png", "Zeitverlauf des Multiplex für den Wert 42: Puls, Auswahl, Segmentmuster, leuchtende Ziffer"),
            T(["Größe", "Formel", "Wert"], [
                ("Systemtakt", "f_clk", "100 MHz, T = 10 ns"),
                ("Teiler tick_gen", "CLK_HZ / (2 · REFRESH_HZ)", "100.000"),
                ("Zeitschlitz je Ziffer", "DIV · 10 ns", "1 ms"),
                ("Vollbild (beide Ziffern)", "2 · Zeitschlitz", "2 ms"),
                ("Wiederholrate je Ziffer", "1 / 2 ms", "500 Hz"),
                ("Tastverhältnis je Ziffer", "1 Slot von 2", "50 %"),
            ]),
            H("3.5 Ausblendung und führende Null"),
            P("Eine Ziffer wird dunkel, indem in ihrem Zeitschlitz alle Segmentleitungen auf 0 gesetzt werden; C schaltet unverändert weiter. Das Top-Level nutzt dafür zwei Freigaben: show (gültige Betriebsart, gilt für die Einerstelle) und show_tens (show UND value ≥ 10, gilt für die Zehnerstelle). Werte von 0 bis 9 erscheinen dadurch einstellig ohne führende Null, und bei ungültiger Schalterstellung bleibt die gesamte Anzeige dunkel."),
        ]),
        ("Bedienkonzept und Betriebsarten", [
            P("Die Betriebsart wird ausschließlich über die vier Schiebeschalter gewählt. Gültig ist nur eine Stellung, in der genau ein Schalter auf 1 steht (one-hot). Jede andere Stellung – kein Schalter oder mehrere Schalter – ergibt eine dunkle Anzeige. Die Taster wirken nur in den Betriebsarten SW0 und SW3; in allen anderen Stellungen werden ihre Pulse ignoriert."),
            T(["sw (SW3 … SW0)", "Betriebsart", "Anzeige", "Wirkung der Taster"], [
                ("0001", "SW0: Zähler", "count, 0 … 99", "BTN0 +1, BTN1 −1, BTN2 +10, BTN3 −10"),
                ("0010", "SW1: Matrikelnummer Mark", "91", "keine"),
                ("0100", "SW2: Matrikelnummer Maxi", "93", "keine"),
                ("1000", "SW3: Binäreingabe", "bin_value, 0 … 15", "BTNi invertiert Bit i"),
                ("0000", "keine Auswahl", "dunkel", "keine"),
                ("alle übrigen 11", "mehrere Schalter", "dunkel", "keine"),
            ]),
            F("schalter_tabelle.png", "Alle 16 Schalterstellungen mit resultierender Anzeige"),
            P("Getroffene Entwurfsentscheidungen, die über die mündliche Aufgabenbeschreibung hinausgehen und deshalb explizit festgelegt wurden:"),
            L([
                "Zähler und Binärwert sind getrennte Register. Beide behalten ihren Wert, solange ein anderer Modus aktiv ist, und erscheinen beim Zurückschalten wieder. Nur ck_rst setzt beide auf 0.",
                "Untere Grenze: −1 bei 0 und −10 bei Werten kleiner 10 ergeben 0 (Sättigung). Negative Zahlen entstehen nie.",
                "Obere Grenze: Jedes Ergebnis über 99 ergibt 0 – also 99 + 1 → 0 und ebenso 95 + 10 → 0 („zurück auf 0“).",
                "Binäreingabe als Toggle: Jeder Druck auf BTNi invertiert Bit i. So lässt sich jede Zahl 0 … 15 einstellen, ohne Taster gleichzeitig halten zu müssen. Die Anzeige erfolgt dezimal.",
                "Führende Null wird in allen Modi unterdrückt (0 … 9 einstellig).",
                "Gleichzeitige Pulse im Zählermodus werden priorisiert: BTN0 > BTN1 > BTN2 > BTN3. Im Binärmodus werden gleichzeitige Pulse alle übernommen (XOR).",
                "Beim mechanischen Umschalten können für Mikrosekunden Zwischenstellungen (z. B. 0000 oder 0011) auftreten. Die Anzeige ist dann kurz dunkel; Registerwerte ändern sich dadurch nicht, weil ohne Tastendruck keine Pulse entstehen.",
            ]),
        ]),
        ("Gesamtarchitektur", [
            P("Das Design besitzt genau eine Taktdomäne: Alle Register werden mit CLK100MHZ getaktet. Langsame Vorgänge (1-ms-Multiplex, 10-ms-Entprellung) werden über Zähler und 1-Takt-Freigabepulse realisiert, nicht über abgeleitete Takte. Das vermeidet Taktversatz und vereinfacht die Timing-Analyse."),
            P("Der Datenfluss verläuft von links nach rechts: Die asynchronen Eingänge werden synchronisiert (Reset, Schalter) bzw. synchronisiert und entprellt (Taster). Der Modus-Decoder bestimmt aus sw_sync, welche Quelle der Wert-MUX auf value legt und ob die Anzeige freigegeben ist (show). Die Register count und bin_value reagieren nur auf press-Pulse, wenn ihr Modus aktiv ist (Freigabe en). value wird in Zehner und Einer zerlegt und vom ssd_driver im Zeitmultiplex ausgegeben; die Ausblendung blendet ungültige oder führende Stellen aus."),
            F("architektur.png", "Gesamtblockschaltbild von phase1_top"),
            P("Die Modulhierarchie ist flach: phase1_top instanziiert viermal btn_debounce (for-generate) und einmal ssd_driver, der wiederum tick_gen und seg7_decoder enthält. Die übrige Logik ist in vier Prozessen und wenigen nebenläufigen Zuweisungen im Top-Level beschrieben."),
            F("hierarchie.png", "Modulhierarchie und Prozesse"),
            T(["Signal", "Typ / Bereich", "Bedeutung"], [
                ("rst", "std_logic", "synchron freigegebener Reset (reset_sync(1))"),
                ("sw_sync", "std_logic_vector(3 downto 0)", "synchronisierte Schalter"),
                ("press", "std_logic_vector(3 downto 0)", "1-Takt-Puls je akzeptiertem Tastendruck"),
                ("count", "natural range 0 to 99", "Zählerstand (SW0)"),
                ("bin_value", "unsigned(3 downto 0)", "Binärwert (SW3)"),
                ("value", "natural range 0 to 99", "anzuzeigender Wert der aktiven Quelle"),
                ("show / show_tens", "std_logic", "Freigabe Einer- bzw. Zehnerstelle"),
                ("tens / ones", "unsigned(3 downto 0)", "BCD-Ziffern für ssd_driver"),
                ("driver_seg / driver_sel", "std_logic_vector / std_logic", "Ausgang des ssd_driver vor der Ausblendung"),
            ]),
        ]),
        ("Eingangsstufe: Reset, Schalter, Entprellung", [
            H("6.1 Reset: asynchron anfordern, synchron freigeben"),
            P("ck_rst (aktiv Low) setzt die zweistufige Kette reset_sync asynchron auf „11“. Nach dem Loslassen werden mit den nächsten zwei steigenden Flanken Nullen nachgeschoben; rst = reset_sync(1) fällt also synchron zum Takt. So kann das Lösen des Resets keine Setup-/Hold-Verletzung in den nachfolgenden Registern verursachen. rst setzt btn_debounce, count, bin_value und den ssd_driver zurück."),
            H("6.2 Synchronisation der Schalter"),
            P("Die Schalter sind zum Systemtakt asynchron. Zwei hintereinander geschaltete Flipflops (sw_meta → sw_sync) reduzieren die Wahrscheinlichkeit, dass ein metastabiler Zustand die Modus-Logik erreicht, auf ein vernachlässigbares Maß. Eine Entprellung der Schalter ist nicht nötig: Prellen beim Umschalten führt nur zu einer kurzen Zwischenanzeige, nicht zu Registeränderungen."),
            C(sync_code),
            H("6.3 Entprellung der Taster (btn_debounce)"),
            P("Mechanische Taster prellen beim Drücken und Loslassen für einige Millisekunden. Ohne Entprellung würde ein einzelner Druck mehrere Zählschritte auslösen. btn_debounce synchronisiert den Taster zunächst mit zwei Flipflops und vergleicht dann sync(1) mit dem zuletzt akzeptierten Zustand stable. Weicht der Eingang ab, zählt cnt hoch; kehrt er zum alten Zustand zurück, beginnt cnt wieder bei 0. Erst wenn der Eingang DEBOUNCE_CYCLES = 1.000.000 Takte (10 ms) ununterbrochen abweicht, wird stable übernommen."),
            P("Bei der Übernahme wird press für genau einen Takt auf den neuen Pegel gesetzt. Nur der Übergang 0 → 1 erzeugt also einen Puls; Halten erzeugt keine weiteren Pulse (kein Auto-Repeat), Loslassen erzeugt keinen Puls. Die Latenz von der letzten Prellflanke bis zum Puls beträgt 10 ms plus drei Systemtakte."),
            F("entprell_timing.png", "Zeitverlauf der Entprellung: roher Taster, synchronisiert, Zähler, stabiler Zustand, Puls"),
            C(debounce_code),
            T(["Parameter / Zustand", "Wert / Wirkung"], [
                ("DEBOUNCE_CYCLES", "1.000.000 Takte = 10 ms (Simulation: 4)"),
                ("Synchronisation", "2 FF, + 20 ns Latenz"),
                ("stable 0 → 1", "press = 1 für einen Takt (10 ns)"),
                ("stable bleibt 1 (Halten)", "keine weiteren Pulse"),
                ("stable 1 → 0 (Loslassen)", "kein Puls, nur Freigabe für den nächsten Druck"),
                ("Instanzen", "4 (gen_btn: BTN0 … BTN3)"),
            ]),
        ]),
        ("Betriebsart SW0: Zähler 0 … 99", [
            P("Ist nur SW0 eingeschaltet, legt der Modus-Decoder count auf value und gibt die Anzeige frei. Die vier Taster verändern count; der rote Pfad im folgenden Bild zeigt alle in diesem Modus aktiven Blöcke. Nach dem Reset ist count = 0 – damit ist die geforderte Ausgabe der Zahl „0“ erfüllt."),
            F("modus_sw0.png", "Aktiver Datenpfad in Betriebsart SW0"),
            P("Pro Taktflanke wird höchstens eine Änderung ausgeführt. Die if/elsif-Kette prüft die Pulse in der Reihenfolge BTN0, BTN1, BTN2, BTN3. Vor jeder Rechnung wird die Grenze geprüft, sodass count den Bereich 0 … 99 nie verlässt – auch nicht kurzzeitig. Das ist wichtig, weil count als natural range 0 to 99 deklariert ist; ein Wert außerhalb wäre in der Simulation ein Laufzeitfehler."),
            F("zaehler_regeln.png", "Entscheidungslogik des Zählers je Taktflanke"),
            T(["Ausgangswert", "Taste", "Ergebnis", "Regel"], [
                ("0", "BTN0 (+1)", "1", "normal"),
                ("99", "BTN0 (+1)", "0", "Überlauf → 0"),
                ("0", "BTN1 (−1)", "0", "untere Grenze"),
                ("20", "BTN1 (−1)", "19", "normal"),
                ("42", "BTN2 (+10)", "52", "normal"),
                ("95", "BTN2 (+10)", "0", "Ergebnis > 99 → 0"),
                ("42", "BTN3 (−10)", "32", "normal"),
                ("7", "BTN3 (−10)", "0", "untere Grenze"),
            ]),
            C(counter_code),
        ]),
        ("Betriebsarten SW1 und SW2: Matrikelnummern", [
            P("In den Betriebsarten SW1 und SW2 zeigt die Anzeige eine feste Zahl: die Endziffern der Matrikelnummern der Gruppenmitglieder, 91 für Mark und 93 für Maxi. Die Werte sind als Konstanten MATR_MARK und MATR_MAXI im Top-Level hinterlegt und können dort zentral geändert werden. Es gibt kein Register – der Wert-MUX legt die Konstante direkt auf value. Die Taster haben keine Wirkung; count und bin_value bleiben unverändert erhalten."),
            F("modus_sw1.png", "Aktiver Datenpfad in Betriebsart SW1 (91)"),
            F("modus_sw2.png", "Aktiver Datenpfad in Betriebsart SW2 (93)"),
            T(["Modus", "value", "Zehner (links)", "Muster", "Einer (rechts)", "Muster"], [
                ("SW1", "91", "9", diagrams.PATTERNS[9], "1", diagrams.PATTERNS[1]),
                ("SW2", "93", "9", diagrams.PATTERNS[9], "3", diagrams.PATTERNS[3]),
            ]),
            P("Da beide Werte ≥ 10 sind, ist show_tens = 1 und beide Ziffern leuchten. Die Zehnerziffer 9 ist in beiden Modi identisch; der Unterschied ist nur an der rechten Ziffer sichtbar – ein guter Test für die korrekte Zuordnung der Segmente b, c und d."),
        ]),
        ("Betriebsart SW3: Binäreingabe", [
            P("In der Betriebsart SW3 wird eine Zahl binär über die vier Taster eingegeben. Jeder Taster ist einem Bit von bin_value fest zugeordnet: BTN0 → Bit 0 (Wertigkeit 1), BTN1 → Bit 1 (2), BTN2 → Bit 2 (4), BTN3 → Bit 3 (8). Jeder entprellte Druck invertiert das zugehörige Bit (Toggle-Flipflop). Der einstellbare Bereich ist 0 … 15; angezeigt wird der Wert dezimal."),
            F("modus_sw3.png", "Aktiver Datenpfad in Betriebsart SW3"),
            P("In VHDL ist das eine einzige Zeile: bin_value <= bin_value xor unsigned(press). Da press nur für einen Takt 1 ist, wird jedes Bit pro Druck genau einmal invertiert. Gleichzeitige Pulse mehrerer Taster werden alle übernommen."),
            F("binaer_eingabe.png", "Toggle-Bits mit Wertigkeiten und Beispielsequenz"),
            T(["Aktion", "bin_value", "Rechnung", "Anzeige"], [
                ("Reset", "0000", "0", "0"),
                ("BTN0", "0001", "1", "1"),
                ("BTN1", "0011", "2 + 1", "3"),
                ("BTN3", "1011", "8 + 2 + 1", "11"),
                ("BTN1", "1001", "8 + 1", "9"),
                ("BTN2", "1101", "8 + 4 + 1", "13"),
            ]),
        ]),
        ("Ungültige Schalterstellungen", [
            P("Steht kein Schalter oder stehen mehrere Schalter auf 1, gibt es keine eindeutige Quelle. Der Modus-Decoder setzt dann show = 0 (der when-others-Zweig der case-Anweisung). Die Ausblendung setzt seg_r in beiden Zeitschlitzen auf 0000000; ssd_driver und dsel_r laufen unverändert weiter. Tastendrücke werden ignoriert, weil weder count noch bin_value freigegeben sind."),
            F("modus_off.png", "Datenpfad bei ungültiger Schalterstellung (Beispiel 0011)"),
            P("Die Entscheidung über alle 16 Stellungen trifft eine einzige case-Anweisung. Weil die Freigaben aus demselben Vergleich entstehen, können Wert-MUX und Ausblendung nie widersprüchlich sein:"),
            C(decoder_code),
        ]),
        ("Anzeigepfad im Detail", [
            P("Der Anzeigepfad ist für alle Betriebsarten identisch. value (0 … 99) wird kombinatorisch zerlegt: tens = value / 10 und ones = value mod 10. Die Division durch die Konstante 10 erzeugt die Synthese als kleine Logikfunktion (7 Eingangsbits); es entsteht weder ein Divisionsrechenwerk noch ein zusätzlicher Takt. Beide Ziffern gehen an den unveränderten ssd_driver aus dem Weckerprojekt."),
            P("Im ssd_driver erzeugt tick_gen alle 1 ms einen Puls; das sel-Register wechselt bei jedem Puls. sel steuert den Ziffern-MUX (0: ones, 1: tens) und wird gleichzeitig als dsel_r an Pin C ausgegeben. Der seg7_decoder erzeugt aus der gewählten Ziffer das Muster. Im Top-Level entscheidet die Ausblendung anhand von sel, ob das Muster durchgeschaltet wird: im Einer-Slot bei show = 1, im Zehner-Slot bei show_tens = 1."),
            F("anzeigepfad.png", "Anzeigepfad von value bis zu den Pmod-Pins, mit beiden Zeitschlitzen für 42"),
            C(display_code),
        ]),
        ("VHDL-Implementierung und Dateien", [
            P("Alle Quellen liegen lokal im Ordner phase_1/src; das Projekt hat keine Verweise auf andere Ordner. Neu bzw. geändert sind phase1_top.vhd und btn_debounce.vhd. ssd_driver, seg7_decoder, tick_gen und clock_pkg sind unveränderte Kopien aus prj_final."),
            T(["Datei", "Inhalt", "Status"], [
                ("src/phase1_top.vhd", "Top-Level: Reset/Schalter-Sync, Register, Modus-Decoder, BCD, Ausblendung", "neu"),
                ("src/btn_debounce.vhd", "Synchronisation, Entprellung, 1-Takt-Puls", "neu"),
                ("src/ssd_driver.vhd", "Multiplex zweier Ziffern", "unverändert"),
                ("src/seg7_decoder.vhd", "BCD → gfedcba", "unverändert"),
                ("src/tick_gen.vhd", "generischer Pulsgeber", "unverändert"),
                ("src/clock_pkg.vhd", "Hilfsfunktion max_nat", "unverändert"),
                ("sim/tb_phase1_top.vhd", "selbstprüfende Testbench", "neu"),
                ("constraints/arty_a7_35_ssd.xdc", "Pins, IO-Standard, Takt", "erweitert um sw, btn"),
            ]),
            P("Die Generics CLK_HZ, DEBOUNCE_CYCLES und REFRESH_HZ trennen die Logik von den Zeitkonstanten. Auf dem Board gelten die Standardwerte (100 MHz, 10 ms, 500 Hz); die Testbench setzt kleinere Werte, um alle Funktionen in kurzer Simulationszeit zu prüfen."),
            P("Der synthetisierbare Code verwendet ausschließlich VHDL-93-Sprachmittel (keine bedingten Zuweisungen in Prozessen, keine Ausdrücke in Port-Maps). Eine Analyse und Synthese aller Quellen mit GHDL im Modus --std=93c lief fehlerfrei. Das Vivado-Projekt wird trotzdem als VHDL-2008 angelegt, weil die Testbench std.env.finish verwendet."),
        ]),
        ("Pin-Constraints und Vivado-Ablauf", [
            P("constraints/arty_a7_35_ssd.xdc ordnet alle Ports den FPGA-Pins zu, setzt LVCMOS33 und beschreibt den 100-MHz-Takt (create_clock, Periode 10 ns). Gegenüber der vorherigen Version sind die Schalter sw[3:0] und die Taster btn[3:0] hinzugekommen; der frühere Einzeltaster btn_up entfällt. Die Pins stammen aus dem Digilent-Master-XDC bzw. dem Weckerprojekt."),
            C(xdc_code),
            P("Projektanlage: Im Ordner phase_1 „vivado -mode gui -source scripts/create_project.tcl“ ausführen oder im Vivado-Tcl-Terminal „source scripts/create_project.tcl“. Das Skript legt das Projekt unter vivado/ an, fügt alle Quellen, die Testbench und die Constraints hinzu und setzt phase1_top bzw. tb_phase1_top als Top-Level. Danach: Behavioral Simulation, Synthesis, Implementation, Report Timing Summary / DRC, Generate Bitstream, Hardware Manager."),
            T(["Prüfpunkt", "Akzeptanzkriterium"], [
                ("Top-Level", "phase1_top / tb_phase1_top"),
                ("Part", "xc7a35ticsg324-1L"),
                ("Ports", "alle 18 Ports zugeordnet, keine unconstrained-IO-Warnung"),
                ("Timing", "10-ns-Takt, WNS und WHS ≥ 0"),
                ("Bitstream", "erzeugt und auf das Board geladen"),
            ]),
        ]),
        ("Simulation und Testergebnisse", [
            P("tb_phase1_top ist selbstprüfend: Assertions vergleichen die externen Ausgänge seg_r und dsel_r mit unabhängig in der Testbench hinterlegten Mustern. Die Prozedur expect_number(n) beobachtet jeweils 24 Takte, prüft in jedem Takt das Muster des gerade aktiven Zeitschlitzes (rechts: Einer, links: Zehner oder dunkel) und verlangt, dass beide Zeitschlitze tatsächlich beobachtet wurden. Verglichen wird an der fallenden Flanke, nachdem Register und Kombinatorik eingeschwungen sind."),
            P("Simulationsparameter: CLK_HZ = 100, DEBOUNCE_CYCLES = 4, REFRESH_HZ = 10 (Zeitschlitz = 5 Takte). Ein Tastendruck dauert in der Testbench 10 Takte gedrückt und 10 Takte losgelassen. Die Logik ist identisch zur Hardware, nur die Zeitkonstanten sind verkleinert. Die Simulation prüft nicht das elektrische Prellen eines realen Tasters und keine analogen Eigenschaften der LEDs."),
            T(["Test", "Stimulus", "Erwartung"], [
                ("Kein Schalter", "sw = 0000 nach Reset", "beide Ziffern dunkel"),
                ("Startwert", "sw = 0001", "rechts 0, links dunkel"),
                ("Untere Grenze", "BTN1, BTN3 bei 0; BTN3 bei 9", "0"),
                ("Prellen", "1-Takt-Pulse auf BTN0", "kein Schritt"),
                ("Halten / Loslassen", "BTN0 über 150 Takte gedrückt", "genau +1"),
                ("Voller Durchlauf", "99 × BTN0 ab 1", "jeder Wert 2 … 99 und 99 → 0 korrekt"),
                ("±10", "BTN2/BTN3/BTN1 gemischt", "10, 20, 19, 9, 0"),
                ("Überlauf +10", "95 + BTN2", "0"),
                ("SW1 / SW2", "sw = 0010 / 0100, Taster drücken", "91 / 93, Taster ohne Wirkung"),
                ("Wert erhalten", "zurück auf SW0", "42 unverändert"),
                ("SW3", "alle Werte 0 … 15 per Toggle", "jeder Wert korrekt, dann 15 → 7"),
                ("Mehrere Schalter", "0011, 0101, 1100, 1111", "dunkel, Taster ignoriert"),
                ("Reset", "ck_rst = 0", "count = bin_value = 0"),
            ]),
            P(f"Ergebnis mit GHDL 6.0.0: „PASS: phase 1 modes SW0 counter (+1/-1/+10/-10, clamp 0, 99->0), SW1 91, SW2 93, SW3 binary, invalid switches blank, bounce, hold, reset“ nach {SIM_TIME} Simulationszeit, ohne Assertion-Fehler. Das Protokoll liegt in sim/testergebnis.txt, die Wellenform in sim/build/simulation.ghw. Aufruf aus dem Ordner phase_1: ./scripts/run_sim.ps1 -Ghdl <Pfad zu ghdl.exe>."),
        ]),
        ("Boardabnahme, Fazit und Quellen", [
            P("Die logischen Anforderungen sind in der RTL-Simulation nachgewiesen. Offen sind Synthese, Implementation und Timing-Analyse in Vivado sowie der Boardtest. Die folgende Prüfliste ist ein Abnahmeplan; Datum, Vivado-Version und Beobachtungen werden beim Test eingetragen."),
            L([
                "[ ] Verdrahtung bei ausgeschalteter Versorgung geprüft (JA/JB untere Reihe, GND/VCC)",
                "[ ] Alle Schalter aus: Anzeige dunkel",
                "[ ] SW0: rechts 0, links dunkel; BTN0 zählt pro Druck genau einmal, Halten zählt nicht weiter",
                "[ ] SW0: BTN1/BTN3 bei 0 bleiben 0; 99 + 1 → 0; 95 + 10 → 0; 9 → 10 zeigt beide Ziffern",
                "[ ] Linke/rechte Ziffer richtig zugeordnet (sonst dsel invertieren)",
                "[ ] SW1 zeigt 91, SW2 zeigt 93",
                "[ ] SW3: BTN0, BTN1, BTN3 → 11; erneuter Druck löscht das Bit",
                "[ ] Zwei Schalter gleichzeitig: dunkel; nach Rückkehr zu SW0 ist der alte Zählerstand da",
                "[ ] RESET setzt Zähler und Binärwert auf 0",
                "[ ] kein sichtbares Flackern oder Ghosting; Timing-Bericht ohne Verletzungen",
            ]),
            P("Fazit: Das Design trennt Eingabeverarbeitung (Synchronisation, Entprellung), Zustandslogik (Zähler, Binärregister, Modus-Decoder) und Anzeige (BCD-Zerlegung, Multiplex, Decoder). Jede Schicht ist einzeln verständlich und testbar. Der Anzeigepfad wird in Phase II unverändert für den Sekundenzähler weiterverwendet; dort ändert sich nur die Quelle von value."),
            *[P(s) for s in SOURCES],
        ]),
    ]


# --------------------------------------------------------------------------- DOCX

def shade(cell, color):
    properties = cell._tc.get_or_add_tcPr()
    fill = OxmlElement("w:shd")
    fill.set(qn("w:val"), "clear")
    fill.set(qn("w:color"), "auto")
    fill.set(qn("w:fill"), color)
    properties.append(fill)


def make_docx(path, content):
    doc = Document()
    setup = doc.sections[0]
    setup.page_height, setup.page_width = Cm(29.7), Cm(21)
    setup.top_margin = setup.bottom_margin = Cm(1.8)
    setup.left_margin = setup.right_margin = Cm(2)
    normal = doc.styles["Normal"]
    normal.font.name, normal.font.size = "Calibri", DocPt(10.5)
    normal.paragraph_format.space_after = DocPt(6)
    normal.paragraph_format.line_spacing = 1.1
    for name in ["Title", "Heading 1", "Heading 2"]:
        doc.styles[name].font.color.rgb = DocColor.from_string(RED if name != "Heading 2" else TEAL)
    setup.header.paragraphs[0].text = f"DIGITALE SCHALTUNGSTECHNIK  |  {TITLE}"
    setup.header.paragraphs[0].style = doc.styles["Caption"]
    footer = setup.footer.paragraphs[0]
    footer.text = "Arty A7-35T / Pmod SSD  |  RTL-Simulation bestanden; Vivado-Build und Boardtest offen  |  Seite "
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), "PAGE")
    footer._p.append(field)

    doc.add_heading(TITLE, 0)
    doc.add_paragraph(f"Laborbericht Digitale Schaltungstechnik  |  {GROUP}", "Subtitle")
    doc.add_paragraph("Inhalt", "Heading 2")
    for index, (title, _) in enumerate(content, 1):
        doc.add_paragraph(f"{index:02d}  {title}")
    doc.add_picture(str(IMG / "architektur.png"), width=Cm(17))
    caption = doc.add_paragraph("Gesamtblockschaltbild (Details in Kapitel 05)", "Caption")
    caption.alignment = WD_ALIGN_PARAGRAPH.CENTER

    figure = 0
    for index, (title, blocks) in enumerate(content, 1):
        doc.add_page_break()
        doc.add_heading(f"{index:02d}  {title}", 1)
        for block in blocks:
            kind = block[0]
            if kind == "p":
                paragraph = doc.add_paragraph(block[1])
                if block[1].startswith(("Digilent", "GHDL-", "Aufgabenstellung:", "Lokale Referenz:")):
                    for run in paragraph.runs:
                        run.font.size = DocPt(8.5)
            elif kind == "h2":
                doc.add_heading(block[1], 2)
            elif kind == "list":
                for item in block[1]:
                    doc.add_paragraph(item, "List Bullet")
            elif kind == "img":
                figure += 1
                doc.add_picture(str(IMG / block[1]), width=Cm(17))
                doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
                caption = doc.add_paragraph(f"Abbildung {figure}: {block[2]}", "Caption")
                caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
            elif kind == "table":
                headers, rows = block[1], block[2]
                table = doc.add_table(rows=1, cols=len(headers))
                table.style = "Table Grid"
                for cell, text in zip(table.rows[0].cells, headers):
                    cell.text = text
                    shade(cell, TEAL)
                    for run in cell.paragraphs[0].runs:
                        run.font.bold = True
                        run.font.color.rgb = DocColor.from_string("FFFFFF")
                for r, row in enumerate(rows):
                    cells = table.add_row().cells
                    for cell, text in zip(cells, row):
                        cell.text = text
                        if r % 2 == 0:
                            shade(cell, LIGHT)
                for row in table.rows:
                    for cell in row.cells:
                        for paragraph in cell.paragraphs:
                            paragraph.paragraph_format.space_after = DocPt(1)
                            for run in paragraph.runs:
                                run.font.size = DocPt(9)
                doc.add_paragraph()
            elif kind == "code":
                paragraph = doc.add_paragraph()
                paragraph.paragraph_format.space_after = DocPt(8)
                paragraph.paragraph_format.line_spacing = 1.0
                properties = paragraph._p.get_or_add_pPr()
                fill = OxmlElement("w:shd")
                fill.set(qn("w:val"), "clear")
                fill.set(qn("w:fill"), LIGHT)
                properties.append(fill)
                run = paragraph.add_run(block[1])
                run.font.name, run.font.size = "Consolas", DocPt(8.5)
    doc.save(path)


def make_markdown(path, content):
    lines = [f"# {TITLE}", "", f"Laborbericht Digitale Schaltungstechnik | {GROUP}", "",
             "Status: RTL-Simulation (GHDL 6.0.0) bestanden; Vivado-Build und physischer Boardtest offen.", "",
             "![Gesamtblockschaltbild](img/architektur.png)", ""]
    figure = 0
    for index, (title, blocks) in enumerate(content, 1):
        lines += [f"## {index:02d} {title}", ""]
        for block in blocks:
            kind = block[0]
            if kind == "p":
                lines += [block[1], ""]
            elif kind == "h2":
                lines += [f"### {block[1]}", ""]
            elif kind == "list":
                lines += [f"- {item}" for item in block[1]] + [""]
            elif kind == "img":
                figure += 1
                lines += [f"![{block[2]}](img/{block[1]})", "", f"*Abbildung {figure}: {block[2]}*", ""]
            elif kind == "table":
                headers, rows = block[1], block[2]
                lines += ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
                lines += ["| " + " | ".join(row) + " |" for row in rows] + [""]
            elif kind == "code":
                lines += ["```vhdl", block[1], "```", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


# --------------------------------------------------------------------------- PPTX

def S(title, minutes, notes, bullets=(), image=None, layout=None, code=None, subtitle=None):
    layout = layout or ("image" if image and not bullets else "split" if image else "code" if code else "text")
    return dict(title=title, minutes=minutes, notes=notes, bullets=list(bullets), image=image,
                layout=layout, code=code, subtitle=subtitle)


def slides():
    counter_code = excerpt("src/phase1_top.vhd", "elsif sw_sync = MODE_COUNT then", "bin_value <= bin_value xor unsigned(press);")
    debounce_code = excerpt("src/btn_debounce.vhd", "sync <= sync(0) & btn_i;", "cnt <= cnt + 1;") + "\nend if;"
    sync_code = excerpt("src/phase1_top.vhd", "process (CLK100MHZ, ck_rst)", "sw_sync <= sw_meta;")
    return [
        S("7-Segment-Anzeige mit Betriebsarten", 1.0,
          "Begrüßung, Vorstellung von Mark und Maxi. Thema: Phase I des Labors – Ansteuerung der 7-Segment-Anzeige auf dem Arty A7-35T mit dem Pmod SSD. "
          "Kurz ankündigen: Wir haben die Pflichtaufgabe (Ausgabe der Zahl 0) zu einem Design mit vier Betriebsarten erweitert. Der Vortrag dauert etwa 40 Minuten, danach Fragen. "
          "Das Bild unten ist das Gesamtblockschaltbild, auf das wir im Laufe des Vortrags Stück für Stück eingehen.",
          ["Labor Digitale Schaltungstechnik – Phase I", "Arty A7-35T + Pmod SSD", "Mark (91) & Maxi (93)"], "architektur.png", layout="title"),
        S("Agenda", 1.0,
          "Überblick über den Ablauf: Zuerst die Aufgabe und unser Funktionsumfang, dann die Hardware. Danach ein ausführlicher Theorieteil zur 7-Segment-Anzeige – Aufbau, elektrisches Prinzip, Codierung und Zeitmultiplex. "
          "Im Entwurfsteil zeigen wir die Gesamtarchitektur und gehen jede Betriebsart einzeln mit ihrem Datenpfad durch. Zum Schluss Implementierung, Constraints, Testbench, Ergebnisse, Boardtest und Fazit.",
          ["1  Aufgabe und Funktionsumfang", "2  Hardware: Arty A7-35T, Pmod SSD, Verdrahtung", "3  Theorie: 7-Segment, gemeinsame Kathode, Multiplex",
           "4  Entwurf: Architektur, Eingangsstufe, Betriebsarten", "5  Implementierung, Constraints, Test", "6  Ergebnis, Boardtest, Fazit"]),
        S("Aufgabenstellung Phase I", 1.5,
          "Laut Laborfolie 210: Ansteuerung der 7-Segment-Anzeige mit VHDL-Implementierung, Testbench und Ausgabe der Zahl 0 auf Arty plus Pmod mit zwei 7-Segment-Einheiten. "
          "Folie 211 legt das Ergebnis fest: Präsentation und Kurzbericht mit Theorie, Entwurf (Blockschaltbild), Implementierung (VHDL, Testbench, Pin-Constraints) und Test (Simulation und Board). "
          "Diese Gliederung haben wir für Bericht und Vortrag übernommen. Die Zahl 0 erscheint bei uns nach dem Reset im Modus SW0.",
          ["Pflicht: VHDL-Implementierung + Testbench", "Pflicht: Arty + Pmod SSD zeigt die Zahl „0“", "Ergebnis: Präsentation + Bericht",
           "Gliederung: Theorie → Entwurf → Implementierung → Test"]),
        S("Unser Funktionsumfang", 1.5,
          "Die Schalter wählen die Betriebsart. SW0: Zähler 0 bis 99 – BTN0 plus 1, BTN1 minus 1, BTN2 plus 10, BTN3 minus 10. Nie unter 0; über 99 geht es auf 0 zurück. "
          "SW1 zeigt 91, die Endziffern der Matrikelnummer von Mark; SW2 zeigt 93 für Maxi. SW3 ist eine Binäreingabe: Jeder Taster schaltet ein Bit um, angezeigt wird der Dezimalwert 0 bis 15. "
          "Steht kein Schalter oder stehen mehrere Schalter oben, bleibt die Anzeige dunkel. Rechts sieht man alle 16 Schalterstellungen – nur vier sind gültig.",
          ["SW0: Zähler 0 … 99 (±1, ±10)", "SW1: 91 (Mark)", "SW2: 93 (Maxi)", "SW3: Binäreingabe 0 … 15", "sonst: Anzeige dunkel"], "schalter_tabelle.png"),
        S("Hardware: Arty A7-35T und Pmod SSD", 1.5,
          "Das Arty A7-35T trägt einen Artix-7 xc7a35t und einen 100-MHz-Oszillator. Wir nutzen vier Schiebeschalter, vier Taster und den roten RESET-Taster. Taster sind aktiv High, RESET ist aktiv Low. "
          "Das Pmod SSD ist ein externes Modul mit zwei Ziffern, gemeinsamer Kathode. Es hat zwei 6-polige Stecker J1 und J2 mit insgesamt neun Signalen: sieben Segmente AA bis AG und den Auswahlpin C. "
          "Alle IOs laufen mit 3,3 V, IO-Standard LVCMOS33.",
          ["Artix-7 xc7a35ticsg324-1L, 100 MHz an E3", "SW0 … SW3, BTN0 … BTN3, RESET (aktiv Low)", "Pmod SSD: 2 Ziffern, gemeinsame Kathode",
           "9 Signale: AA … AG + C, LVCMOS33 / 3,3 V"]),
        S("Verdrahtung JA/JB → J1/J2", 1.5,
          "Wichtig: Das SSD wird an die UNTERE Reihe von JA und JB gesteckt, also Pins 7 bis 12. J1 trägt AA bis AD, J2 trägt AE, AF, AG und C. Pins 11 und 12 sind GND und VCC. "
          "Die Farben zeigen die 1:1-Zuordnung. Unter jedem Pin steht der FPGA-Pin aus dem XDC. Vor dem Umstecken immer die Versorgung trennen und die Orientierung prüfen – ein verdrehter Stecker vertauscht VCC und GND.",
          image="verdrahtung.png", subtitle="Untere Reihe (7 … 12) verwenden – Versorgung beim Umstecken trennen"),
        S("Aufbau einer Ziffer", 1.5,
          "Eine Ziffer hat sieben Segmente a bis g, im Uhrzeigersinn ab oben, g in der Mitte. Im VHDL-Vektor ist Bit 0 das Segment a und Bit 6 das Segment g; als String geschrieben ergibt sich gfedcba. "
          "Die Tabelle verfolgt jedes Bit bis zum FPGA-Pin: seg_r[0] geht über JA7 an AA, also Segment a. Diese Kette ist bei der Fehlersuche der erste Prüfpunkt. "
          "Beispiel: Die 2 hat das Muster 1011011 – g, e, d, b und a leuchten.",
          image="segment_aufbau.png", subtitle="Bitreihenfolge gfedcba: Bit 6 = g … Bit 0 = a"),
        S("Elektrisches Prinzip: gemeinsame Kathode", 2.0,
          "Jedes Segment ist eine LED. Sie leuchtet nur, wenn die Anode auf 1 liegt UND die Kathode der Ziffer leitend mit GND verbunden ist. Gemeinsame Kathode heißt: alle sieben Kathoden einer Ziffer sind verbunden. "
          "Beim Pmod SSD sind außerdem die Anoden gleichnamiger Segmente beider Ziffern verbunden – AA versorgt beide a-Segmente. Der Pin C entscheidet, welche Kathode leitet; die andere ist gesperrt. "
          "Konsequenz: Es kann immer nur eine Ziffer leuchten. Das spart Leitungen – 9 statt 16 – erzwingt aber den Zeitmultiplex. "
          "Die Zuordnung C gleich 0 für rechts übernehmen wir aus dem vorhandenen Treiber und prüfen sie am Board.",
          image="segment_elektrisch.png", subtitle="Segment leuchtet, wenn Anode = 1 und Kathode der Ziffer auf GND"),
        S("Segmentcodierung 0 … 9", 1.5,
          "Der seg7_decoder ist rein kombinatorisch: eine with-select-Anweisung, die jede BCD-Ziffer auf ihr Muster abbildet. Kein Takt, keine Speicherung. "
          "Unter jeder Ziffer steht das Muster in gfedcba-Reihenfolge und die leuchtenden Segmente. Die 8 hat alle Segmente an, die 1 nur b und c. "
          "Für die Eingänge 10 bis 15 gibt der Decoder einen Mittelstrich aus. In unserem Design kommen diese Werte nie vor, weil der Wert immer durch 10 geteilt bzw. modulo 10 genommen wird.",
          image="segment_muster.png", subtitle="Kombinatorischer Decoder: BCD-Ziffer → 7-Bit-Muster (1 = an)"),
        S("Zeitmultiplex", 2.0,
          "Hier sieht man den Multiplex am Beispiel 42. tick_gen erzeugt jede Millisekunde einen 1-Takt-Puls. Mit jedem Puls kippt sel – und sel ist gleichzeitig dsel_r, also Pin C. "
          "Bei sel gleich 0 liegt das Muster der Einerstelle, also der 2, an und die rechte Ziffer leuchtet. Bei sel gleich 1 das Muster der 4 auf der linken Ziffer. "
          "Muster und Auswahl wechseln in derselben Taktflanke, deshalb erscheint nie ein Muster auf der falschen Ziffer. Ein Vollbild dauert 2 ms, also 500 Hz pro Ziffer – das Auge sieht beide Ziffern gleichzeitig.",
          image="multiplex_timing.png", subtitle="1 ms je Ziffer, 2 ms je Bild → 500 Hz Wiederholrate"),
        S("Multiplex: Rechnung und Grenzen", 0.5,
          "Die Rechnung: DIV gleich CLK_HZ durch zwei mal REFRESH_HZ, also 100 Millionen durch 1000 gleich 100.000 Takte pro Zeitschlitz. "
          "Jede Ziffer ist 50 Prozent der Zeit an, daher etwas dunkler als bei statischer Ansteuerung. Helligkeit und Ghosting sind analoge Effekte und nur am Board zu bewerten.",
          ["DIV = CLK_HZ / (2 · REFRESH_HZ) = 100.000", "Zeitschlitz 1 ms, Bild 2 ms, 500 Hz je Ziffer", "Tastverhältnis 50 % je Ziffer",
           "Flimmergrenze ca. 50 … 100 Hz → deutlich darüber", "Helligkeit / Ghosting nur am Board prüfbar"]),
        S("Gesamtarchitektur", 2.0,
          "Das ist das komplette Blockschaltbild. Eine einzige Taktdomäne: alles läuft mit 100 MHz, langsame Vorgänge nur über Freigabepulse. "
          "Links die Eingangsstufe: Reset-Synchronisation, Schalter-Synchronisation und vier Entprell-Instanzen, die press-Pulse liefern. In der Mitte der Modus-Decoder: Er wählt über den Wert-MUX die Quelle und gibt Zähler oder Binärregister frei. "
          "Rechts der gemeinsame Anzeigepfad: BCD-Zerlegung, Ausblendung und ssd_driver. Auf den nächsten Folien färben wir für jede Betriebsart den aktiven Pfad rot ein.",
          image="architektur.png", subtitle="Eingangsstufe → Modus-Decoder / Quellen → Wert-MUX → Anzeigepfad"),
        S("Modulhierarchie", 1.0,
          "Die Hierarchie ist bewusst flach. phase1_top instanziiert viermal btn_debounce über ein for-generate und einmal den ssd_driver. Der ssd_driver enthält tick_gen und seg7_decoder. "
          "Die eigentliche Funktionslogik steckt in vier Prozessen im Top-Level: Reset-Sync, Schalter-Sync, Register-Prozess und Modus-Decoder, plus nebenläufige Zuweisungen für BCD und Ausblendung. "
          "Die Anzeigemodule sind unveränderte Kopien aus unserem Weckerprojekt.",
          image="hierarchie.png", subtitle="2 neue Entities, 4 wiederverwendete Module"),
        S("Synchronisation: Reset und Schalter", 1.5,
          "Alle Eingänge sind asynchron zum Takt. Der Reset wird asynchron angefordert: ck_rst gleich 0 setzt die Kette sofort auf 11. Freigegeben wird er synchron: Nach dem Loslassen schieben zwei Flanken Nullen nach. "
          "So kann das Loslassen des Resets keine Timing-Verletzung erzeugen. Die Schalter laufen durch zwei Flipflops gegen Metastabilität. Entprellen müssen wir sie nicht – ein Prellen beim Umschalten erzeugt nur eine kurze Zwischenanzeige und ändert keine Register.",
          ["Reset: asynchron anfordern,", "synchron freigeben (2 FF)", "Schalter: 2-FF-Synchronisierer", "kein Entprellen der Schalter nötig"], code=sync_code),
        S("Entprellung der Taster", 1.5,
          "Ein Taster prellt einige Millisekunden. btn_debounce vergleicht den synchronisierten Eingang mit dem akzeptierten Zustand stable. Weicht er ab, zählt cnt hoch; jede Rückkehr setzt cnt auf 0. "
          "Erst nach einer Million Takten, also 10 ms ununterbrochener Abweichung, wird stable übernommen. Genau dann erzeugt der Übergang 0 nach 1 einen Puls von einem Takt. "
          "Halten erzeugt keine weiteren Pulse, Loslassen erzeugt keinen Puls. Ein Druck ist also genau ein Ereignis.",
          image="entprell_timing.png", subtitle="10 ms stabil → genau ein 1-Takt-Puls pro Druck"),
        S("btn_debounce im Code", 1.0,
          "Der Kern in wenigen Zeilen: Schieberegister für die Synchronisation, Vergleich mit stable, Zähler. Die Zeile press <= sync(1) ist der Trick: Bei der Übernahme wird press auf den neuen Pegel gesetzt – nur bei einem Druck ist das 1. "
          "Da press im nächsten Takt wieder 0 wird, entsteht ein Puls von genau einem Takt. Vier Instanzen über for-generate, eine pro Taster.",
          ["2 FF, dann Stabilitätszähler", "Rückkehr → cnt = 0", "press <= sync(1) bei Übernahme", "→ Puls nur für 0 → 1, 1 Takt lang"], code=debounce_code),
        S("Modus-Decoder: 16 Schalterstellungen", 1.5,
          "Der Modus-Decoder ist eine case-Anweisung über sw_sync. Gültig sind nur die vier one-hot-Stellungen 0001, 0010, 0100 und 1000. Alles andere, auch 0000, fällt in den others-Zweig: show gleich 0, Anzeige dunkel. "
          "Weil Wert-MUX und Freigabe aus derselben case-Anweisung kommen, können sie nie widersprüchlich sein. Die Beispielanzeigen zeigen, was in den gültigen Modi erscheint.",
          image="schalter_tabelle.png", subtitle="Nur one-hot-Stellungen sind gültig – 12 von 16 ergeben „dunkel“"),
        S("SW0: Datenpfad des Zählers", 1.5,
          "Jetzt der Zählermodus. Rot ist alles, was in diesem Modus aktiv ist: Taster, Entprellung, press-Bus, Freigabe en vom Modus-Decoder, das Register count, der Wert-MUX und der Anzeigepfad. "
          "Grau sind die inaktiven Quellen. Wichtig: count ist ein eigenes Register und behält seinen Wert, wenn wir in einen anderen Modus wechseln. Nach Reset steht hier die geforderte 0.",
          image="modus_sw0.png", subtitle="sw = 0001: press-Pulse verändern count (0 … 99)"),
        S("SW0: Rechenregeln", 1.5,
          "Pro Taktflanke prüft eine if/elsif-Kette die vier Pulse in fester Reihenfolge. Vor jeder Rechnung wird die Grenze geprüft. Plus 1 bei 99 ergibt 0. Minus 1 bei 0 bleibt 0. "
          "Plus 10 ab 90 ergibt 0 – unsere Interpretation von „über 99 zurück auf 0“. Minus 10 unter 10 ergibt 0. Damit verlässt count nie den Bereich 0 bis 99, auch nicht für einen Takt. "
          "Gleichzeitige Pulse sind praktisch ausgeschlossen, wären aber durch die Priorität eindeutig geregelt.",
          image="zaehler_regeln.png", subtitle="Grenzen werden vor jeder Rechnung geprüft – count bleibt in 0 … 99"),
        S("SW0 im Code", 1.0,
          "So sieht das in VHDL aus. Der Zweig wird nur betreten, wenn sw_sync gleich MODE_COUNT ist – das ist die Freigabe en aus dem Blockschaltbild. "
          "Der Binärmodus ist darunter eine einzige Zeile mit XOR. Die Abfragen count >= 1 und count >= 90 sorgen dafür, dass die Subtraktion bzw. Addition nur im gültigen Bereich ausgeführt wird.",
          ["Zweig nur bei sw_sync = 0001", "if/elsif → Priorität BTN0 … BTN3", "Grenzprüfung vor Rechnung", "darunter: Binärmodus per XOR"], code=counter_code),
        S("SW1: Matrikelnummer Mark – 91", 1.0,
          "Im Modus SW1 wird keine Logik gerechnet: Der Wert-MUX legt die Konstante MATR_MARK, also 91, auf value. Die Taster haben keine Wirkung – count und bin_value bleiben im Hintergrund unverändert. "
          "Angezeigt wird links die 9 mit 1101111 und rechts die 1 mit 0000110.",
          image="modus_sw1.png", subtitle="sw = 0010: Konstante MATR_MARK = 91"),
        S("SW2: Matrikelnummer Maxi – 93", 0.5,
          "Genauso SW2 mit der Konstante 93 für Maxi. Die Zehnerziffer ist identisch, der Unterschied liegt nur rechts: die 3 mit 1001111. Das ist am Board ein schöner Test für die Segmente.",
          image="modus_sw2.png", subtitle="sw = 0100: Konstante MATR_MAXI = 93"),
        S("SW3: Datenpfad der Binäreingabe", 1.0,
          "Im Binärmodus führen die press-Pulse zum Binärregister bin_value. Das Prinzip ist das gleiche wie beim Zähler, nur die Rechenregel ist eine andere. "
          "Werte 0 bis 9 werden einstellig, 10 bis 15 zweistellig angezeigt.",
          image="modus_sw3.png", subtitle="sw = 1000: press-Pulse toggeln bin_value (0 … 15)"),
        S("SW3: Bitgewichtung und Toggle", 1.5,
          "Jeder Taster gehört zu einem Bit: BTN0 Wertigkeit 1, BTN1 2, BTN2 4, BTN3 8. Ein Druck invertiert das Bit – wie ein T-Flipflop. "
          "Beispiel: BTN0, BTN1 und BTN3 je einmal gedrückt ergibt 1011, also 8 plus 2 plus 1 gleich 11. Ein zweiter Druck auf BTN1 löscht Bit 1 wieder: 1001 gleich 9. "
          "Das Toggle-Konzept haben wir gewählt, damit man keine vier Taster gleichzeitig halten muss. In VHDL: bin_value XOR press.",
          image="binaer_eingabe.png", subtitle="BTNi invertiert Bit i: Wertigkeiten 1, 2, 4, 8"),
        S("Kein oder mehrere Schalter: dunkel", 1.0,
          "Stehen mehrere Schalter oben, etwa SW0 und SW1, oder gar keiner, gibt es keine eindeutige Quelle. show wird 0, die Ausblendung erzwingt 0000000 auf allen Segmenten. "
          "ssd_driver und dsel_r laufen weiter, nur die Segmente bleiben aus. Tasten werden ignoriert. Schaltet man zurück auf einen gültigen Modus, erscheinen die alten Werte wieder.",
          image="modus_off.png", subtitle="show = 0 → seg_r = 0000000 in beiden Zeitschlitzen"),
        S("Anzeigepfad im Detail", 1.5,
          "Zum Schluss des Entwurfs der gemeinsame Anzeigepfad. value wird durch 10 geteilt und modulo 10 genommen – bei einer Konstante ist das kleine kombinatorische Logik, kein Dividierer. "
          "Der MUX im ssd_driver wählt per sel die Einer oder Zehner, der Decoder erzeugt das Muster, die Ausblendung schaltet es nur bei show bzw. show_tens durch. "
          "Unten die beiden Zeitschlitze für 42. Für Werte unter 10 ist show_tens gleich 0, die linke Ziffer bleibt dunkel – das ist die Unterdrückung der führenden Null.",
          image="anzeigepfad.png", subtitle="value → /10, mod 10 → MUX (sel) → Decoder → Ausblendung → seg_r"),
        S("Pin-Constraints und Vivado", 1.0,
          "Die XDC-Datei ordnet alle 18 Ports zu und setzt LVCMOS33. create_clock beschreibt den 10-ns-Takt für die Timing-Analyse. Neu sind die Schalter und Taster, die Pins stammen aus dem Digilent-Master-XDC. "
          "Das Tcl-Skript legt das Projekt reproduzierbar an. Den Vivado-Build und die Timing-Analyse haben wir noch nicht durchgeführt – das ist offen und Teil der Boardabnahme.",
          ["sw[3:0]: A8, C11, C10, A10", "btn[3:0]: D9, C9, B9, B8", "seg_r: D13 … K15, dsel_r: J15", "create_clock 10 ns, LVCMOS33", "scripts/create_project.tcl → vivado/"]),
        S("Testbench-Strategie", 1.0,
          "Die Testbench ist selbstprüfend. Sie schaut nur auf die externen Ausgänge, nicht auf interne Signale – so wird der Decoder mitgetestet. expect_number beobachtet 24 Takte und prüft in jedem Takt das Muster des aktiven Zeitschlitzes, und dass beide Slots gesehen wurden. "
          "Die Zeitkonstanten sind verkleinert: 4 Takte Entprellung, 5 Takte pro Zeitschlitz. Die Logik ist identisch zur Hardware.",
          ["Assertions auf seg_r / dsel_r (Black-Box)", "beide Zeitschlitze pro Prüfung", "DEBOUNCE_CYCLES = 4, Slot = 5 Takte",
           "Vergleich an der fallenden Flanke"]),
        S("Simulationsergebnis", 1.0,
          "Getestet: Startwert, untere Grenzen, Prellen, Halten, der komplette Durchlauf von 0 bis 99 und zurück auf 0, plus/minus 10, Überlauf bei 95 plus 10, beide Matrikelnummern, alle 16 Binärwerte, vier ungültige Kombinationen, Werterhalt beim Moduswechsel und Reset. "
          f"GHDL 6.0.0 meldet PASS nach {SIM_TIME} ohne Assertion-Fehler. Zusätzlich haben wir alle Quellen im Modus VHDL-93 analysiert und synthetisiert.",
          ["GHDL 6.0.0: PASS, keine Assertion-Fehler", f"Simulationszeit {SIM_TIME}", "alle 100 Zählerwerte, alle 16 Binärwerte", "Grenzen, Prellen, Halten, Reset, Werterhalt",
           "VHDL-93-Analyse + Synthese mit GHDL fehlerfrei"]),
        S("Boardtest und Live-Demo", 1.5,
          "Ablauf am Board: Erst alle Schalter aus – dunkel. Dann SW0: 0, einige Drücke, Halten testen, minus bei 0, über 99. Dann SW1 und SW2. Dann SW3 mit der Sequenz BTN0, BTN1, BTN3 für 11. "
          "Zwei Schalter gleichzeitig – dunkel, zurück zu SW0 – alter Wert. Zum Schluss RESET. Sind die Ziffern vertauscht, wird im Treiber dsel invertiert.",
          ["Alle Schalter aus → dunkel", "SW0: 0, Zählen, Grenzen, 99 → 0", "SW1 / SW2: 91 / 93", "SW3: BTN0, BTN1, BTN3 → 11",
           "Zwei Schalter → dunkel; RESET → 0"]),
        S("Fazit und Ausblick", 1.0,
          "Zusammenfassung: Die Pflicht – Zahl 0, VHDL, Testbench – ist erfüllt und um vier Betriebsarten erweitert. Das Design trennt sauber Eingabe, Zustand und Anzeige. Jede Schicht ist einzeln testbar. "
          "In Phase II wird derselbe Anzeigepfad für einen Sekundenzähler 00 bis 99 weiterverwendet – nur die Quelle von value ändert sich. Offen sind Vivado-Timing und der protokollierte Boardtest. Vielen Dank – wir freuen uns auf Fragen.",
          ["Pflicht erfüllt + 4 Betriebsarten", "Eingabe | Zustand | Anzeige getrennt", "Simulation vollständig bestanden", "Offen: Vivado-Timing, Boardprotokoll",
           "Phase II: gleicher Anzeigepfad, Sekunden-Enable"]),
        S("Fragen?", 0.0,
          "Fragerunde. Mögliche Fragen: Warum zwei Flipflops? Warum kein abgeleiteter Takt? Warum Toggle statt gehaltener Taster? Was passiert bei gleichzeitigem Drücken? Wie groß ist die Division durch 10 in Hardware?",
          ["Vielen Dank!", "Mark & Maxi"], "schalter_tabelle.png", layout="title"),
    ]


def add_text(slide, left, top, width, height, lines, size=24, color=INK, bold=False, font_name="Calibri", bullets=False, spacing=10):
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    frame = box.text_frame
    frame.word_wrap = True
    frame.margin_left = frame.margin_right = Inches(0.05)
    for index, line in enumerate(lines):
        paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        paragraph.text = ("•  " + line) if bullets else line
        paragraph.font.name = font_name
        paragraph.font.size = Pt(size)
        paragraph.font.bold = bold
        paragraph.font.color.rgb = RGBColor.from_string(color)
        paragraph.space_after = Pt(spacing)
    return box


def fit_picture(slide, name, left, top, max_w, max_h):
    with Image.open(IMG / name) as image:
        ratio = image.width / image.height
    width, height = max_w, max_w / ratio
    if height > max_h:
        height, width = max_h, max_h * ratio
    slide.shapes.add_picture(str(IMG / name), Inches(left + (max_w - width) / 2), Inches(top), Inches(width), Inches(height))


def make_pptx(path, data):
    presentation = Presentation()
    presentation.slide_width, presentation.slide_height = Inches(13.333), Inches(7.5)
    total = sum(item["minutes"] for item in data)
    assert math.isclose(total, 40), total
    for index, item in enumerate(data, 1):
        slide = presentation.slides.add_slide(presentation.slide_layouts[6])
        stripe = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.14), Inches(7.5))
        stripe.fill.solid()
        stripe.fill.fore_color.rgb = RGBColor.from_string(RED)
        stripe.line.fill.background()
        layout = item["layout"]
        if layout == "title":
            add_text(slide, 0.7, 0.9, 12, 1.2, [item["title"]], 44, RED, True)
            add_text(slide, 0.75, 2.05, 12, 1.6, item["bullets"], 24, INK, spacing=6)
            fit_picture(slide, item["image"], 0.7, 3.55, 12.0, 3.5)
        else:
            add_text(slide, 0.6, 0.22, 11.5, 0.4, ["DIGITALE SCHALTUNGSTECHNIK  |  PHASE I"], 12, TEAL, True)
            add_text(slide, 0.6, 0.5, 12.2, 0.8, [item["title"]], 32, INK, True)
            if layout == "image":
                if item["subtitle"]:
                    add_text(slide, 0.62, 1.2, 12.2, 0.4, [item["subtitle"]], 18, GRAY)
                fit_picture(slide, item["image"], 0.6, 1.7, 12.2, 5.25)
            elif layout == "split":
                add_text(slide, 0.6, 1.55, 4.3, 5.2, item["bullets"], 21, bullets=True)
                fit_picture(slide, item["image"], 5.0, 1.55, 8.0, 5.3)
            elif layout == "code":
                add_text(slide, 0.6, 1.55, 4.3, 5.2, item["bullets"], 21, bullets=True)
                code_lines = item["code"].splitlines()
                size = 13 if len(code_lines) <= 22 else 11
                shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(5.0), Inches(1.45), Inches(7.95), Inches(5.5))
                shape.fill.solid()
                shape.fill.fore_color.rgb = RGBColor.from_string(LIGHT)
                shape.line.fill.background()
                add_text(slide, 5.15, 1.55, 7.7, 5.3, code_lines, size, INK, font_name="Consolas", spacing=0)
            else:
                add_text(slide, 0.6, 1.6, 12.0, 5.2, item["bullets"], 26, bullets=True, spacing=14)
        add_text(slide, 0.6, 7.05, 10.8, 0.3, ["Arty A7-35T + Pmod SSD  |  Mark & Maxi"], 10, GRAY)
        add_text(slide, 12.2, 7.0, 0.8, 0.35, [f"{index:02d}"], 14, RED, True)
        minutes = item["minutes"]
        timing = f"Zeitbudget: {minutes:g} min (gesamt 40 min + Fragerunde)." if minutes else "Fragerunde (außerhalb der 40 min)."
        slide.notes_slide.notes_text_frame.text = f"{timing}\n\n{item['notes']}"
    presentation.save(path)


def main():
    diagrams.generate_all(IMG)
    content = sections()
    make_docx(DOC / "bericht_phase_1.docx", content)
    make_markdown(DOC / "bericht_phase_1.md", content)
    data = slides()
    make_pptx(DOC / "praesentation_phase_1.pptx", data)
    print(f"{len(content)} Kapitel, {len(list(IMG.glob('*.png')))} Grafiken, {len(data)} Folien "
          f"({sum(s['minutes'] for s in data):g} min) erzeugt")


if __name__ == "__main__":
    main()
