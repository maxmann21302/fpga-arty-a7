"""Erzeugt Bericht (DOCX/MD), Grafiken und Praesentation (PPTX) fuer Phase II.

Aufruf aus beliebigem Ordner:  python phase_2/scripts/create_docs.py
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
TITLE = "Phase II – Sekundenzähler, 4-stelliger Zähler und Stoppuhr"
GROUP = "Gruppe: Marc (Endziffern Matrikelnummer 91) und Maxi (93)"
SIM_TIME = "101.151.070 ns"
PASS_TEXT = ("PASS: phase 2 SW0 00..99 (1 s, 99->00, left dark), SW1 0000..9999 (9999->0000), "
             "SW2 stopwatch (start/stop/zero, 10 ms, 99.99->00.00, background), buttons only in SW2, "
             "invalid switches dark, reset")


def source(rel):
    return (ROOT / rel).read_text(encoding="utf-8").splitlines()


def excerpt(rel, start, end, nth=1):
    lines = source(rel)
    first = next(i for i, line in enumerate(lines) if start in line)
    hits = [i for i in range(first, len(lines)) if end in lines[i]]
    return textwrap.dedent("\n".join(lines[first:hits[nth - 1] + 1]))


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
    ("ck_rst", "C2", "RESET-Taster (rot)", "aktiv Low, setzt alles zurück"),
    ("sw[0]", "A8", "SW0", "Sekunden 00 … 99"),
    ("sw[1]", "C11", "SW1", "Sekunden 0000 … 9999"),
    ("sw[2]", "C10", "SW2", "Stoppuhr"),
    ("sw[3]", "A10", "SW3", "ohne Funktion (→ dunkel)"),
    ("btn[0]", "D9", "BTN0", "Stoppuhr Start"),
    ("btn[1]", "C9", "BTN1", "Stoppuhr Stopp"),
    ("btn[2]", "B9", "BTN2", "Stoppuhr Nullen (im Stopp)"),
    ("btn[3]", "B8", "BTN3", "ohne Funktion"),
    ("seg_r[0 … 3]", "D13, B18, A18, K16", "JA7 … JA10 → SSD rechts AA … AD", "Segmente a … d"),
    ("seg_r[4 … 6]", "J17, J18, K15", "JB7 … JB9 → SSD rechts AE … AG", "Segmente e … g"),
    ("dsel_r", "J15", "JB10 → SSD rechts C", "Ziffernauswahl rechts"),
    ("seg_l[0 … 3]", "U14, V14, T13, U13", "JC7 … JC10 → SSD links AA … AD", "Segmente a … d"),
    ("seg_l[4 … 6]", "E2, D2, H2", "JD7 … JD9 → SSD links AE … AG", "Segmente e … g"),
    ("dsel_l", "G2", "JD10 → SSD links C", "Ziffernauswahl links"),
]

SOURCES = [
    "Aufgabenstellung: Laborfolie „Labor: 7-Segment-Anzeige“, Phase II (Folie 212), phase_2/task/image5.png.",
    "Digilent Arty A7 Reference Manual: https://digilent.com/reference/programmable-logic/arty-a7/reference-manual",
    "Digilent Pmod SSD Reference Manual: https://digilent.com/reference/pmod/pmodssd/reference-manual",
    "Digilent Master-XDC: https://github.com/Digilent/digilent-xdc/blob/master/Arty-A7-35-Master.xdc",
    "GHDL-Dokumentation: https://ghdl.github.io/ghdl/",
    "Lokale Referenz: phase_1 (Module und Testmethodik), prj_clock (Pinbelegung JC/JD für ein zweites Pmod SSD).",
]


def sections():
    sync_code = excerpt("src/phase2_top.vhd", "process (CLK100MHZ, ck_rst)", "sw_sync <= sw_meta;")
    gate_code = excerpt("src/phase2_top.vhd", "sw_start <= '1'", "tick => tick_cs);")
    tick_code = excerpt("src/tick_gen.vhd", "if rst = '1' or clr = '1' then", "end if;", 2)
    sec_code = excerpt("src/phase2_top.vhd", "elsif tick_sec = '1' then", "cnt_b_lo <= cnt_b_lo + 1;")
    stop_code = excerpt("src/phase2_top.vhd", "if sw_start = '1' then", "stop_cs <= stop_cs + 1;")
    mux_code = excerpt("src/phase2_top.vhd", "process (sw_sync, cnt_a", "end process;")
    display_code = excerpt("src/phase2_top.vhd", "bcd_l   <= to_bcd2", "dsel   => dsel_r")
    debounce_code = excerpt("src/btn_debounce.vhd", "if rst = '1' then", "press_o <= press;")
    xdc_code = excerpt("constraints/arty_a7_35_ssd.xdc", "## Pmod SSD links", "[get_ports dsel_l]")
    tb_code = excerpt("sim/tb_phase2_top.vhd", "procedure wait_second", "end procedure;")
    return [
        ("Einleitung, Ziel und Anforderungen", [
            P("Phase II des Labors baut auf der 7-Segment-Ansteuerung aus Phase I auf. Laut Aufgabenstellung (Folie 212) ist eine 7-Segment-Anzeige mit Zähler zu implementieren, der im Sekundentakt von 0 bis 99 zählt und per Taster zurückgesetzt werden kann. Gefordert sind VHDL-Implementierung und Testbench, der Test per Simulation und am Board sowie Präsentation und Bericht mit Anhang (VHDL-Code, Testbench, Links)."),
            P("Unsere Umsetzung erfüllt die Pflicht in der Betriebsart SW0 und erweitert sie – wie schon in Phase I – über die Schiebeschalter zu einem Mehrmodus-Design. Ein zweites Pmod SSD an den Pmod-Ports JC und JD verdoppelt die Anzeige auf vier Stellen. Damit entstehen zwei weitere Betriebsarten: ein vierstelliger Sekundenzähler 0000 … 9999 (SW1) und eine Stoppuhr mit Start, Stopp und Nullen über die Taster (SW2), die links Sekunden und rechts Hundertstelsekunden anzeigt."),
            P("Der Bericht beschreibt den implementierten Stand exakt. Die RTL-Simulation wurde mit GHDL 6.0.0 durchgeführt und bestanden – einschließlich eines vollständigen Durchlaufs bis 9999 → 0000 –; zusätzlich wurden alle synthetisierbaren Quellen mit GHDL im Modus VHDL-93 analysiert und synthetisiert. Ein Vivado-Build mit Timing-Analyse und der physische Boardtest sind noch offen und als Prüfliste in Kapitel 15 aufgeführt."),
            T(["ID", "Anforderung", "Umsetzung", "Nachweis"], [
                ("P2-01", "Start nach Reset bei 0", "alle Zähler 0, Stoppuhr steht", "TB „start“"),
                ("P2-02", "Ungültige Schalter: dunkel", "show_l = show_r = 0", "TB: 6 Stellungen"),
                ("P2-03", "SW0: Sekundentakt 0 … 99 (Pflicht)", "tick_sec → cnt_a", "TB: Sekunde 1 … 102"),
                ("P2-04", "SW0: 99 → 00", "Überlauf cnt_a", "TB: Sekunde 100"),
                ("P2-05", "SW0: zweites SSD aus", "show_l = 0", "TB: links dunkel"),
                ("P2-06", "SW1: 0000 … 9999 über beide SSD", "cnt_b_hi | cnt_b_lo", "TB „SW1 0103“"),
                ("P2-07", "SW1: 9999 → 0000", "Übertragskaskade", "TB: 9998 … 10001 s"),
                ("P2-08", "Zähler laufen im Hintergrund", "tick_sec immer aktiv", "TB: Moduswechsel"),
                ("P2-09", "SW2: Start / Stopp, 10 ms", "running, tick_cs", "TB „2 s“"),
                ("P2-10", "SW2: Stand bleibt im Stopp", "en = running", "TB „hold“"),
                ("P2-11", "SW2: Nullen nur im Stopp", "sw_zero mit running = 0", "TB: beide Fälle"),
                ("P2-12", "SW2: 99.99 → 00.00, läuft weiter", "Übertragskaskade", "TB „overflow“"),
                ("P2-13", "Tasten nur in SW2 wirksam", "Freigabe über sw_sync", "TB: SW0/SW1 + Taster"),
                ("P2-14", "Stoppuhr läuft im Hintergrund", "running unabhängig vom Modus", "TB „background“"),
                ("P2-15", "Reset per Taster (ck_rst)", "rst → alle Register", "TB „reset“"),
            ]),
        ]),
        ("Hardware: Arty A7-35T und zwei Pmod SSD", [
            P("Zielplattform ist wie in Phase I das Arty A7-35T mit dem FPGA xc7a35ticsg324-1L und einem 100-MHz-Oszillator an Pin E3. Verwendet werden die Schiebeschalter SW0 … SW3, die Taster BTN0 … BTN3 (gedrückt = 1) und der rote RESET-Taster ck_rst (gedrückt = 0). Alle Signale nutzen LVCMOS33."),
            P("Neu ist ein zweites Digilent Pmod SSD. Jedes Modul hat zwei Ziffern mit gemeinsamer Kathode, sieben gemeinsame Segmentleitungen AA … AG und einen Auswahlpin C, verteilt auf die Stecker J1 (AA … AD) und J2 (AE, AF, AG, C). Zwei Module benötigen damit 18 Signalleitungen und vier Pmod-Ports. Das rechte SSD bleibt unverändert an JA/JB (wie Phase I), das linke SSD wird an JC/JD angeschlossen."),
            P("Verdrahtung: Beide SSD werden an die UNTERE Reihe (Pins 7 … 12) der Pmod-Ports gesteckt – J1 an JA bzw. JC, J2 an JB bzw. JD. Die oberen Reihen (Pins 1 … 6) bleiben frei. Die Pinbelegung von JC/JD stammt aus dem Digilent-Master-XDC und ist identisch mit der im Uhrenprojekt (prj_clock) erprobten Zuordnung. Vor dem Umstecken die Versorgung trennen und GND/VCC-Orientierung prüfen."),
            F("verdrahtung.png", "Verdrahtung: JC/JD → linkes SSD, JA/JB → rechtes SSD, jeweils untere Reihe"),
            T(["Port", "FPGA-Pin", "Verbindung", "Bedeutung"], PINS),
            P("JB und JC sind beim Arty „High-Speed“-Pmods ohne Serienwiderstände, JA und JD „Standard“-Pmods mit 200-Ω-Schutzwiderständen. Für die langsam schaltenden Segmentleitungen (Umschaltung alle 1 ms) ist das unkritisch; beide SSD werden logisch identisch angesteuert. Eventuelle Helligkeitsunterschiede zwischen den Steckern sind beim Boardtest zu beobachten."),
        ]),
        ("Funktionsweise der 7-Segment-Anzeige (Kurzfassung)", [
            P("Die Grundlagen wurden im Bericht zu Phase I ausführlich behandelt und gelten unverändert. Dieses Kapitel fasst sie zusammen und ergänzt die Zuordnung für das zweite SSD."),
            H("3.1 Segmente und Bitreihenfolge"),
            P("Eine Ziffer besteht aus sieben LED-Segmenten a … g. Im VHDL-Vektor seg(6 downto 0) steht Bit 6 für g und Bit 0 für a („gfedcba“); logisch 1 schaltet ein Segment ein (aktiv High, gemeinsame Kathode). Beide SSD nutzen dieselbe Reihenfolge: seg_r[i] und seg_l[i] treiben jeweils Segment i des rechten bzw. linken Moduls."),
            F("segment_aufbau.png", "Segmentbezeichnung und Zuordnung Bit → Pmod-Pin → Arty-Port → FPGA-Pin für beide SSD"),
            H("3.2 Gemeinsame Kathode und Zeitmultiplex"),
            P("Innerhalb eines SSD sind die Anoden gleichnamiger Segmente beider Ziffern verbunden; der Pin C wählt, welche Kathode leitet. Es leuchtet je SSD also immer nur eine Ziffer, und beide Ziffern müssen zeitlich abwechselnd angesteuert werden. In Phase II gibt es zwei solche Module mit je eigenem C-Pin; sie werden von zwei unabhängigen, identischen Multiplexern (ssd_driver) angesteuert."),
            F("segment_elektrisch.png", "Prinzipschaltung eines Pmod SSD"),
            P("Der seg7_decoder übersetzt eine BCD-Ziffer kombinatorisch in das Segmentmuster. Für den Eingang blank = 1 liefert er 0000000 – darüber werden in Phase II ganze SSD dunkel geschaltet."),
            F("segment_muster.png", "Segmentmuster aller Dezimalziffern"),
            P("tick_gen im ssd_driver erzeugt mit DIV = CLK_HZ / (2 · REFRESH_HZ) = 100.000 alle 1 ms einen Puls, der die Ziffernauswahl umschaltet. Jede Ziffer wird mit 500 Hz und 50 % Tastverhältnis angesteuert – weit oberhalb der Flimmergrenze. Beide SSD werden auf diese Weise gleichzeitig, aber unabhängig gemultiplext."),
            F("multiplex_timing.png", "Zeitmultiplex eines SSD am Beispiel 42"),
        ]),
        ("Bedienkonzept und Betriebsarten", [
            P("Wie in Phase I wählen die Schiebeschalter die Betriebsart; gültig ist nur eine Stellung mit genau einem Schalter auf 1 (one-hot). In Phase II sind drei Betriebsarten belegt: SW0, SW1 und SW2. SW3 allein und alle Stellungen mit keinem oder mehreren Schaltern schalten beide SSD dunkel. Die Taster wirken ausschließlich in der Betriebsart SW2 (Stoppuhr)."),
            T(["sw (SW3 … SW0)", "Betriebsart", "SSD links (JC/JD)", "SSD rechts (JA/JB)", "Taster"], [
                ("0001", "SW0: Sekundenzähler", "dunkel", "00 … 99", "keine Wirkung"),
                ("0010", "SW1: Sekundenzähler 4-stellig", "Tausender | Hunderter", "Zehner | Einer", "keine Wirkung"),
                ("0100", "SW2: Stoppuhr", "Sekunden 00 … 99", "Hundertstel 00 … 99", "BTN0 Start, BTN1 Stopp, BTN2 Nullen"),
                ("1000", "SW3: nicht belegt", "dunkel", "dunkel", "keine Wirkung"),
                ("0000 / mehrere", "keine gültige Wahl", "dunkel", "dunkel", "keine Wirkung"),
            ]),
            F("anzeige_modi.png", "Anzeige beider SSD je Betriebsart"),
            F("schalter_tabelle.png", "Alle 16 Schalterstellungen mit resultierender Anzeige"),
            P("Getroffene Entwurfsentscheidungen, die über die Aufgabenstellung hinausgehen und deshalb explizit festgelegt wurden:"),
            L([
                "Reset ausschließlich über den roten RESET-Taster ck_rst: Er setzt beide Sekundenzähler und die Stoppuhr auf 0 und hält die Stoppuhr an. Das erfüllt „Reset per Taster“.",
                "Zähler A (SW0) und Zähler B (SW1) sind getrennte Register. Beide laufen unabhängig von der Schalterstellung ab Reset im Hintergrund weiter; die Schalter wählen nur aus, was angezeigt wird. Da beide vom selben Sekundenpuls getaktet werden, gilt stets Zähler A = Zähler B mod 100.",
                "Überlauf: 99 → 00 (SW0), 9999 → 0000 (SW1), 99.99 → 00.00 (SW2); die Stoppuhr läuft dabei weiter.",
                "Alle Werte werden mit führender Null angezeigt (00, 0042, 01.50). Anders als in Phase I gibt es keine Unterdrückung führender Nullen – bei einer Uhr bzw. Stoppuhr ist die feste Stellenzahl lesbarer.",
                "Stoppuhr-Auflösung 10 ms (Hundertstel), weil das rechte SSD nur zwei Stellen hat. Bereich 00.00 … 99.99 s.",
                "Nullen (BTN2) ist nur im Stopp wirksam, damit eine laufende Messung nicht versehentlich gelöscht wird. Start bei laufender Uhr und Stopp bei stehender Uhr ändern nichts.",
                "Die Stoppuhr läuft beim Wechsel in einen anderen Modus weiter und kann erst nach Rückkehr zu SW2 angehalten werden.",
            ]),
        ]),
        ("Gesamtarchitektur", [
            P("Das Design besitzt genau eine Taktdomäne: Alle Register werden mit CLK100MHZ getaktet. Langsame Vorgänge – 1 s, 10 ms, 1 ms Multiplex, 10 ms Entprellung – werden ausschließlich über Zähler und 1-Takt-Freigabepulse realisiert. Es gibt keinen abgeleiteten Takt; dadurch bleibt die Timing-Analyse einfach und es entstehen keine Taktdomänenübergänge."),
            F("signalfluss.png", "Signalfluss Phase II"),
            P("Der Datenfluss im Detail: Reset und Schalter werden synchronisiert, die Taster BTN0 … BTN2 zusätzlich entprellt. Zwei tick_gen-Instanzen bilden die Zeitbasis: u_tick_sec liefert jede Sekunde einen Puls für beide Sekundenzähler, u_tick_cs alle 10 ms einen Puls für die Stoppuhr – aber nur, solange running = 1 ist. Die Tasten-Freigabe lässt Start, Stopp und Nullen nur in der Betriebsart SW2 durch. Der Anzeige-MUX wählt je SSD einen Wert 0 … 99 und eine Freigabe; to_bcd2 zerlegt die Werte in Ziffern, zwei ssd_driver geben sie aus."),
            F("architektur.png", "Gesamtblockschaltbild von phase2_top"),
            F("hierarchie.png", "Modulhierarchie und Prozesse"),
            T(["Signal", "Typ / Bereich", "Bedeutung"], [
                ("rst", "std_logic", "synchron freigegebener Reset (reset_sync(1))"),
                ("sw_sync", "std_logic_vector(3 downto 0)", "synchronisierte Schalter"),
                ("press", "std_logic_vector(2 downto 0)", "1-Takt-Puls je Druck auf BTN0 … BTN2"),
                ("tick_sec / tick_cs", "std_logic", "1-Takt-Puls je Sekunde / je 10 ms (bei running)"),
                ("cnt_a", "natural range 0 to 99", "Zähler A (SW0)"),
                ("cnt_b_hi, cnt_b_lo", "natural range 0 to 99", "Zähler B (SW1), Tausender/Hunderter bzw. Zehner/Einer"),
                ("running", "std_logic", "Stoppuhr läuft"),
                ("sw_start / sw_stop / sw_zero", "std_logic", "freigegebene Tastenpulse der Stoppuhr"),
                ("stop_s, stop_cs", "natural range 0 to 99", "Stoppuhr: Sekunden / Hundertstel"),
                ("val_l, val_r", "natural range 0 to 99", "anzuzeigender Wert je SSD"),
                ("show_l, show_r", "std_logic", "Freigabe je SSD"),
                ("bcd_l, bcd_r", "bcd2_t (Record tens/ones)", "BCD-Ziffern je SSD"),
                ("blank_l, blank_r", "std_logic", "Dunkelschaltung je SSD (not show)"),
            ]),
        ]),
        ("Eingangsstufe und Zeitbasis", [
            H("6.1 Reset, Schalter und Taster"),
            P("Reset- und Schaltersynchronisation sind unverändert aus Phase I übernommen: ck_rst (aktiv Low) setzt die zweistufige Kette reset_sync asynchron, die Freigabe erfolgt synchron nach zwei Taktflanken. Die Schalter durchlaufen zwei Flipflops gegen Metastabilität. Nach dem Loslassen des Resets beginnt auch der Sekundenvorteiler neu – das erste Sekundenintervall ist also vollständig."),
            C(sync_code),
            P("Die Taster BTN0 … BTN2 werden mit drei Instanzen des unveränderten btn_debounce aus Phase I verarbeitet (for-generate gen_btn). Jeder akzeptierte Druck erzeugt nach 10 ms Stabilität genau einen 1-Takt-Puls; Halten oder Loslassen erzeugen keine weiteren Pulse. BTN3 ist in Phase II ohne Funktion und wird nicht ausgewertet."),
            F("entprell_timing.png", "Zeitverlauf der Entprellung (unverändert aus Phase I)"),
            C(debounce_code),
            H("6.2 Zeitbasis mit zwei tick_gen-Instanzen"),
            P("Für die Zeitbasis wird der vorhandene generische Pulsgeber tick_gen zweimal instanziiert. u_tick_sec mit DIV = CLK_HZ = 100.000.000 liefert genau jede Sekunde einen Puls tick_sec. u_tick_cs mit DIV = CLK_HZ / 100 = 1.000.000 liefert alle 10 ms einen Puls tick_cs. Für die Stoppuhr werden erstmals die bereits vorhandenen Eingänge en und clr von tick_gen genutzt: en = running hält den Vorteiler im Stopp an, ohne seinen Stand zu verlieren; clr = sw_zero setzt ihn beim Nullen zurück."),
            C(tick_code),
            F("zeitbasis.png", "Zeitbasis: Sekundenpuls mit Zählerübergang 0099 → 0100 und Stoppuhr mit Start/Stopp"),
            T(["Größe", "Formel", "Wert (Board)", "Wert (Simulation)"], [
                ("Systemtakt", "CLK_HZ", "100 MHz", "1 kHz (Periode 10 ns, skaliert)"),
                ("Sekundenpuls", "DIV = CLK_HZ", "100.000.000 Takte = 1 s", "1.000 Takte"),
                ("Stoppuhr-Puls", "DIV = CLK_HZ / 100", "1.000.000 Takte = 10 ms", "10 Takte"),
                ("Multiplex-Slot", "CLK_HZ / (2 · REFRESH_HZ)", "100.000 Takte = 1 ms", "5 Takte"),
                ("Entprellung", "DEBOUNCE_CYCLES", "1.000.000 Takte = 10 ms", "4 Takte"),
            ]),
            H("6.3 Tasten-Freigabe"),
            P("Die Freigabe der Stoppuhr-Tasten ist als drei nebenläufige Zuweisungen formuliert. sw_start und sw_stop sind nur bei sw_sync = 0100 aktiv; sw_zero zusätzlich nur bei running = 0. In allen anderen Betriebsarten werden die press-Pulse verworfen – sie verändern weder running noch den Stoppuhrstand."),
            C(gate_code),
        ]),
        ("Betriebsart SW0: Sekundenzähler 00 … 99", [
            P("Die Betriebsart SW0 erfüllt die Pflichtaufgabe: Ein Zähler zählt im Sekundentakt von 0 bis 99 und beginnt danach wieder bei 0; der Reset-Taster setzt ihn zurück. cnt_a wird bei jedem tick_sec um 1 erhöht, bei 99 auf 0 gesetzt. Angezeigt wird der Wert zweistellig auf dem rechten SSD (JA/JB); das linke SSD an JC/JD bleibt dunkel."),
            F("modus_sw0.png", "Aktiver Datenpfad in Betriebsart SW0"),
            P("Das linke SSD wird über show_l = 0 abgeschaltet: blank_l = 1 erzwingt im seg7_decoder das Muster 0000000 in beiden Zeitschlitzen, während dsel_l weiter umschaltet. Elektrisch fließt damit kein Segmentstrom. Die Taster sind in SW0 wirkungslos; Zähler B und eine laufende Stoppuhr zählen im Hintergrund weiter."),
            T(["Zeit seit Reset", "cnt_a", "SSD links", "SSD rechts"], [
                ("0 … < 1 s", "0", "dunkel", "00"),
                ("1 s", "1", "dunkel", "01"),
                ("42 s", "42", "dunkel", "42"),
                ("99 s", "99", "dunkel", "99"),
                ("100 s", "0", "dunkel", "00"),
                ("101 s", "1", "dunkel", "01"),
            ]),
        ]),
        ("Betriebsart SW1: Sekundenzähler 0000 … 9999", [
            P("In der Betriebsart SW1 werden beide SSD genutzt: Ein vierstelliger Zähler zählt die Sekunden seit dem Reset von 0000 bis 9999 (2 h 46 min 39 s) und beginnt dann wieder bei 0000. Das linke SSD zeigt Tausender und Hunderter, das rechte Zehner und Einer; führende Nullen werden angezeigt."),
            F("modus_sw1.png", "Aktiver Datenpfad in Betriebsart SW1"),
            P("Zähler B ist nicht als ein Binärzähler 0 … 9999 aufgebaut, sondern als Kaskade zweier Stufen 0 … 99: cnt_b_lo zählt jede Sekunde; erreicht es 99, wird es beim nächsten Puls 0 und cnt_b_hi um 1 erhöht (Übertrag). Bei 99|99 laufen beide Stufen auf 0. Diese Aufteilung passt direkt auf die beiden SSD: Jede Stufe wird mit derselben Funktion to_bcd2 (÷ 10, mod 10 auf 7 Bit) in zwei Ziffern zerlegt. Eine Zerlegung eines 14-Bit-Werts mit ÷ 1000 und ÷ 100 entfällt."),
            F("kaskade.png", "Zählerkaskade aus zwei 0 … 99-Stufen für SW1 und SW2"),
            P("Zähler A und Zähler B werden im selben Prozess vom gleichen tick_sec getaktet:"),
            C(sec_code),
            T(["Zeit seit Reset", "cnt_b_hi", "cnt_b_lo", "Anzeige"], [
                ("7 s", "0", "7", "00 | 07"),
                ("99 s", "0", "99", "00 | 99"),
                ("100 s", "1", "0", "01 | 00"),
                ("1234 s", "12", "34", "12 | 34"),
                ("9999 s", "99", "99", "99 | 99"),
                ("10000 s", "0", "0", "00 | 00"),
            ]),
        ]),
        ("Betriebsart SW2: Stoppuhr", [
            P("In der Betriebsart SW2 arbeitet das Design als Stoppuhr mit einer Auflösung von 10 ms. Das linke SSD zeigt die Sekunden 00 … 99, das rechte die Hundertstel 00 … 99. BTN0 startet, BTN1 stoppt, BTN2 setzt im Stopp auf 00.00 zurück."),
            F("modus_sw2.png", "Aktiver Datenpfad in Betriebsart SW2"),
            H("9.1 Zustände und Tasten"),
            P("Die Steuerung besteht aus einem einzigen Flipflop running mit den Zuständen GESTOPPT (0) und LÄUFT (1). sw_start setzt running, sw_stop löscht es; treffen beide im selben Takt ein, hat Start Vorrang (praktisch ausgeschlossen, da zwei entprellte Pulse exakt gleichzeitig kommen müssten). Nullen ist nur im Zustand GESTOPPT wirksam. Nach dem Reset ist die Stoppuhr gestoppt und steht auf 00.00."),
            F("stoppuhr.png", "Zustände der Stoppuhr, Tastenwirkung und Beispielablauf"),
            H("9.2 Zählwerk"),
            P("Das Zählwerk ist wie Zähler B eine Kaskade zweier 0 … 99-Stufen: stop_cs (Hundertstel) zählt jeden tick_cs; bei 99 folgt der Übertrag nach stop_s (Sekunden). Nach 99.99 laufen beide auf 00.00, die Stoppuhr zählt weiter. Nullen hat Vorrang vor einem gleichzeitigen tick_cs."),
            C(stop_code),
            H("9.3 Genauigkeit"),
            L([
                "Auflösung: 10 ms. Die Anzeige zeigt die abgeschlossenen Hundertstel (abgeschnitten, nicht gerundet).",
                "Zeitbasis: 1.000.000 Takte des 100-MHz-Oszillators je Schritt; die Genauigkeit entspricht der des Board-Oszillators.",
                "Latenz: Start und Stopp werden beide durch die Entprellung um 10 ms plus wenige Takte verzögert. Da die Verzögerung für beide Flanken gleich ist, hebt sie sich in der gemessenen Dauer auf.",
                "Unterbrechung: Im Stopp hält der Vorteiler seinen Stand (en = running). Beim Fortsetzen geht kein angefangenes Hundertstel verloren; Start/Stopp-Folgen summieren sich korrekt.",
                "Nullen setzt auch den Vorteiler zurück (clr), sodass nach dem nächsten Start genau 10 ms bis zur ersten Hundertstel vergehen.",
            ]),
        ]),
        ("Ungültige Schalterstellungen", [
            P("Steht kein Schalter, nur SW3 oder stehen mehrere Schalter auf 1, gibt es keine eindeutige Betriebsart. Der Anzeige-MUX setzt dann show_l = show_r = 0 (when-others-Zweig). Beide seg7_decoder erhalten blank = 1 und geben 0000000 aus; die ssd_driver laufen unverändert weiter. Die Taster werden ignoriert. Alle Zähler und eine laufende Stoppuhr zählen im Hintergrund weiter."),
            F("modus_off.png", "Datenpfad bei ungültiger Schalterstellung (Beispiel 0011)"),
            P("Die Auswahl für beide SSD trifft eine einzige case-Anweisung. Werte und Freigaben entstehen aus demselben Vergleich und können daher nie widersprüchlich sein:"),
            C(mux_code),
        ]),
        ("Anzeigepfad mit zwei Treibern", [
            P("Je SSD gibt es einen eigenen, identischen Anzeigepfad. Der Wert val_l bzw. val_r (0 … 99) wird mit to_bcd2 aus clock_pkg in Zehner und Einer zerlegt. Das Ergebnis ist ein Record vom Typ bcd2_t; seine Elemente tens und ones werden direkt an die Ports digit1 und digit0 des ssd_driver gelegt. Die Freigabe wird invertiert an den Port blank angeschlossen."),
            F("anzeigepfad.png", "Anzeigepfad beider SSD am Beispiel der Stoppuhr 12.34 s"),
            P("Gegenüber Phase I entfällt die externe Ausblendung im Top-Level (show_tens): Da alle Werte zweistellig angezeigt werden, genügt der blank-Eingang des ssd_driver, der schon im Weckerprojekt vorhanden war. Damit bleibt das Top-Level schlanker; ssd_driver und seg7_decoder sind unverändert."),
            C(display_code),
            P("Die beiden ssd_driver besitzen je einen eigenen tick_gen für den 1-ms-Takt. Sie laufen nach dem Reset synchron, sind aber logisch unabhängig. Eine gemeinsame Nutzung des Multiplex-Pulses wäre möglich, brächte aber nur wenige Flipflops Ersparnis und würde den unveränderten Treiber modifizieren."),
        ]),
        ("Wiederverwendung aus Phase I und Dateien", [
            P("Alle Quellen liegen lokal in phase_2/src; das Projekt ist eigenständig. Neu ist nur phase2_top.vhd. Alle übrigen Module sind unveränderte Kopien aus Phase I – dort teils bereits aus dem Weckerprojekt übernommen. Das zeigt den Nutzen einer generischen Modulbibliothek: tick_gen wird mit anderen Generics als Sekunden- und 10-ms-Vorteiler genutzt, ssd_driver zweimal instanziiert."),
            T(["Datei", "Inhalt", "Status ggü. Phase I"], [
                ("src/phase2_top.vhd", "Top-Level: Sync, Zeitbasis, Zähler, Stoppuhr, Anzeige-MUX", "neu"),
                ("src/btn_debounce.vhd", "Synchronisation, Entprellung, 1-Takt-Puls (3 Instanzen)", "unverändert"),
                ("src/tick_gen.vhd", "generischer Pulsgeber, jetzt auch mit en/clr genutzt", "unverändert"),
                ("src/ssd_driver.vhd", "Multiplex zweier Ziffern (2 Instanzen)", "unverändert"),
                ("src/seg7_decoder.vhd", "BCD → gfedcba, blank", "unverändert"),
                ("src/clock_pkg.vhd", "bcd2_t, to_bcd2(), max_nat()", "unverändert"),
                ("sim/tb_phase2_top.vhd", "selbstprüfende Testbench beider SSD", "neu"),
                ("constraints/arty_a7_35_ssd.xdc", "Pins, IO-Standard, Takt", "erweitert um seg_l, dsel_l"),
                ("scripts/run_sim.ps1", "GHDL-Simulation, Wellenform optional (-Wave)", "angepasst"),
                ("scripts/create_project.tcl", "Vivado-Projekt", "unverändert"),
            ]),
            P("Die Generics CLK_HZ, DEBOUNCE_CYCLES und REFRESH_HZ trennen Logik und Zeitkonstanten. Alle abgeleiteten Teiler (1 s, 10 ms, 1 ms) werden aus CLK_HZ berechnet; die Testbench verkleinert CLK_HZ und prüft damit dieselbe Logik in kurzer Simulationszeit."),
            P("Der synthetisierbare Code verwendet ausschließlich VHDL-93-Sprachmittel (bedingte Zuweisungen nur nebenläufig, keine Ausdrücke in Port-Maps; Record-Elemente wie bcd_r.ones sind als Port-Aktual zulässig). Analyse und Synthese aller Quellen mit GHDL im Modus --std=93c liefen fehlerfrei. Das Vivado-Projekt wird als VHDL-2008 angelegt, weil die Testbench std.env.finish verwendet."),
        ]),
        ("Pin-Constraints und Vivado-Ablauf", [
            P("constraints/arty_a7_35_ssd.xdc ordnet alle 26 Ports zu, setzt LVCMOS33 und beschreibt den 100-MHz-Takt (create_clock, Periode 10 ns). Gegenüber Phase I sind die acht Signale des linken SSD hinzugekommen; die Schalter, Taster und das rechte SSD sind unverändert."),
            C(xdc_code),
            P("Projektanlage: Im Ordner phase_2 „vivado -mode gui -source scripts/create_project.tcl“ ausführen oder im Vivado-Tcl-Terminal „source scripts/create_project.tcl“. Das Skript erkennt die Phase am Ordnernamen, legt das Projekt unter vivado/ an und setzt phase2_top bzw. tb_phase2_top als Top-Level. Danach: Behavioral Simulation, Synthesis, Implementation, Report Timing Summary / DRC, Generate Bitstream, Hardware Manager."),
            P("Hinweis zur Behavioral Simulation in Vivado: Die Testbench simuliert über 10.000 beschleunigte Sekunden (≈ 10 Mio. Takte). In xsim dauert das deutlich länger als in GHDL; für einen schnellen Blick genügt es, die Simulation nach den ersten Abschnitten abzubrechen."),
            T(["Prüfpunkt", "Akzeptanzkriterium"], [
                ("Top-Level", "phase2_top / tb_phase2_top"),
                ("Part", "xc7a35ticsg324-1L"),
                ("Ports", "alle 26 Ports zugeordnet, keine unconstrained-IO-Warnung"),
                ("Timing", "10-ns-Takt, WNS und WHS ≥ 0"),
                ("Bitstream", "erzeugt und auf das Board geladen"),
            ]),
        ]),
        ("Simulation und Testergebnisse", [
            P("tb_phase2_top ist selbstprüfend und betrachtet das Design als Black Box: Assertions prüfen nur die externen Ausgänge seg_r/dsel_r und seg_l/dsel_l gegen unabhängig in der Testbench hinterlegte Segmentmuster. Die Prozedur read_ssd beobachtet beide SSD über 12 Takte, dekodiert jedes Muster zurück in eine Ziffer, verlangt, dass jeder der vier Zeitschlitze gesehen wird und sich innerhalb des Fensters nicht ändert, und liefert je SSD einen Wert 0 … 99 oder „dunkel“. Ein nur halb dunkles SSD oder ein ungültiges Muster ist ein Fehler."),
            P("Simulationsparameter: CLK_HZ = 1000 (1 s = 1.000 Takte, 10 ms = 10 Takte), DEBOUNCE_CYCLES = 4, REFRESH_HZ = 100 (Zeitschlitz = 5 Takte). Um Sekundenwerte deterministisch zu prüfen, misst die Testbench den Zeitpunkt des ersten Sekundenpulses und liest danach jeden Sekundenwert in der Mitte seines Intervalls (wait_second). Lange Wartezeiten werden mit wait for übersprungen; so lässt sich der Überlauf bei 10.000 s in rund 40 s Rechenzeit prüfen."),
            C(tb_code),
            T(["ID", "Stimulus", "Erwartung"], [
                ("P2-01", "Reset, sw = 0001 / 0010 / 0100", "– | 00, 00 | 00, 00 | 00"),
                ("P2-02", "0000, 0011, 0101, 0110, 1000, 1111", "beide SSD dunkel"),
                ("P2-03/04/05", "SW0, Sekunde 1 … 102", "– | n mod 100, links dunkel"),
                ("P2-06", "SW1 bei 103 s, 104 s", "01 | 03, 01 | 04"),
                ("P2-08", "SW0 bei 105 s, SW1 nach Stoppuhrtests", "– | 05, aktueller Sekundenstand"),
                ("P2-07", "SW1 bei 9998 … 10001 s", "99|98, 99|99, 00|00, 00|01"),
                ("P2-09", "Start, 2.000 Takte, Stopp", "02.00 … 02.05"),
                ("P2-10", "3.000 Takte warten", "Wert unverändert"),
                ("P2-11", "Nullen bei laufender Uhr", "ignoriert, Wert läuft weiter"),
                ("P2-13", "BTN0/BTN2 in SW0 und SW1", "Stoppuhr unverändert"),
                ("P2-11", "Nullen im Stopp", "00 | 00"),
                ("P2-14", "Start, 3.000 Takte in SW0, zurück, Stopp", "03.00 … 03.10"),
                ("P2-12", "Start, 100,5 s", "00.45 … 00.60"),
                ("P2-15", "Reset bei laufender Stoppuhr", "alles 0, Stoppuhr steht"),
            ]),
            P(f"Ergebnis mit GHDL 6.0.0: „{PASS_TEXT}“ nach {SIM_TIME} Simulationszeit, ohne Assertion-Fehler. Das Protokoll liegt in sim/testergebnis.txt. Aufruf aus dem Ordner phase_2: ./scripts/run_sim.ps1 -Ghdl <Pfad zu ghdl.exe> [-Wave]. Ohne -Wave wird keine Wellenform geschrieben, da sie für 10 Mio. Takte mehrere 100 MB groß wird."),
            P("Gegenprobe der Testbench: In einer Kopie des Designs wurde die SW2-Freigabe des Start-Tasters entfernt. Die Testbench bricht dann mit einer Assertion ab („buttons outside SW2 changed the stopwatch“). Die Tests erkennen also tatsächlich Fehlverhalten und laufen nicht nur durch."),
            P("Grenzen der Simulation: Die Zeitkonstanten sind verkleinert; geprüft wird die Logik, nicht die absolute Ganggenauigkeit des Oszillators. Prellen realer Taster, Helligkeit, Ghosting und die korrekte Steckerorientierung lassen sich nur am Board prüfen."),
        ]),
        ("Boardabnahme, Fazit und Quellen", [
            P("Die logischen Anforderungen sind in der RTL-Simulation nachgewiesen. Offen sind Synthese, Implementation und Timing-Analyse in Vivado sowie der Boardtest. Die folgende Prüfliste ist ein Abnahmeplan; Datum, Vivado-Version und Beobachtungen werden beim Test eingetragen."),
            L([
                "[ ] Verdrahtung bei ausgeschalteter Versorgung geprüft (JA/JB und JC/JD jeweils untere Reihe, GND/VCC)",
                "[ ] Alle Schalter aus: beide SSD dunkel; SW3 allein: dunkel",
                "[ ] SW0: rechts 00, 01, 02 … im Sekundentakt (mit Handy-Stoppuhr über 60 s vergleichen); links dunkel",
                "[ ] SW0: Überlauf 99 → 00 beobachten; RESET setzt auf 00",
                "[ ] SW1: vier Stellen, z. B. 0123; Übergang xx99 → (xx+1)00 korrekt",
                "[ ] Linke/rechte Ziffer je SSD richtig zugeordnet (sonst dsel invertieren); linkes/rechtes SSD nicht vertauscht",
                "[ ] SW2: BTN0 startet, BTN1 stoppt, Anzeige s | Hundertstel; BTN2 im Stopp → 00.00, während des Laufs ohne Wirkung",
                "[ ] SW2: Stoppuhr starten, auf SW0 wechseln, zurück auf SW2: Stoppuhr läuft weiter",
                "[ ] Taster in SW0/SW1 ohne Wirkung",
                "[ ] kein sichtbares Flackern oder Ghosting; Helligkeit beider SSD vergleichbar; Timing-Bericht ohne Verletzungen",
            ]),
            P("Fazit: Phase II erfüllt die Pflichtaufgabe – Sekundenzähler 0 … 99 mit Reset per Taster – in der Betriebsart SW0 und erweitert sie um einen vierstelligen Sekundenzähler und eine Stoppuhr mit 10 ms Auflösung auf zwei SSD. Der Aufbau trennt wie in Phase I Eingabe, Zustand und Anzeige. Bis auf das Top-Level wurden alle Module unverändert aus Phase I übernommen; neu sind nur die Zeitbasis aus zwei tick_gen, die Übertragskaskaden und der Anzeige-MUX für zwei SSD. Die Struktur ist damit eine direkte Vorstufe für die Uhr bzw. den Wecker in Phase III."),
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
    footer.text = "Arty A7-35T / 2 × Pmod SSD  |  RTL-Simulation bestanden; Vivado-Build und Boardtest offen  |  Seite "
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
                lines += ["| " + " | ".join(cell.replace("|", "\\|") for cell in row) + " |" for row in rows] + [""]
            elif kind == "code":
                lines += ["```vhdl", block[1], "```", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


# --------------------------------------------------------------------------- PPTX

def S(title, minutes, notes, bullets=(), image=None, layout=None, code=None, subtitle=None):
    layout = layout or ("image" if image and not bullets else "split" if image else "code" if code else "text")
    return dict(title=title, minutes=minutes, notes=notes, bullets=list(bullets), image=image,
                layout=layout, code=code, subtitle=subtitle)


def slides():
    sync_code = excerpt("src/phase2_top.vhd", "process (CLK100MHZ, ck_rst)", "sw_sync <= sw_meta;")
    gate_code = excerpt("src/phase2_top.vhd", "sw_start <= '1'", "tick => tick_cs);")
    sec_code = excerpt("src/phase2_top.vhd", "elsif tick_sec = '1' then", "cnt_b_lo <= cnt_b_lo + 1;")
    stop_code = excerpt("src/phase2_top.vhd", "if sw_start = '1' then", "stop_cs <= stop_cs + 1;")
    mux_code = excerpt("src/phase2_top.vhd", "process (sw_sync, cnt_a", "end process;")
    tb_code = excerpt("sim/tb_phase2_top.vhd", "procedure wait_second", "end procedure;")
    return [
        S("Sekundenzähler, 4-stelliger Zähler und Stoppuhr", 1.0,
          "Begrüßung, Vorstellung von Marc und Maxi. Thema: Phase II des Labors – ein Zähler im Sekundentakt auf der 7-Segment-Anzeige des Arty A7-35T. "
          "Wir haben die Pflichtaufgabe, also den Sekundenzähler von 0 bis 99 mit Reset, umgesetzt und um ein zweites Pmod SSD, einen vierstelligen Zähler und eine Stoppuhr erweitert. "
          "Der Vortrag dauert etwa 40 Minuten, danach beantworten wir gerne Fragen.",
          ["Labor Digitale Schaltungstechnik – Phase II", "Arty A7-35T + 2 × Pmod SSD", "Marc (91) & Maxi (93)"], "signalfluss.png", layout="title"),
        S("Agenda", 1.0,
          "Ablauf: Zuerst Aufgabe und unser Funktionsumfang, dann die Hardware mit dem zweiten SSD und eine kurze Wiederholung der 7-Segment-Theorie aus Phase I. "
          "Im Entwurfsteil zeigen wir die Gesamtarchitektur, die Zeitbasis und jede Betriebsart mit ihrem Datenpfad. Zum Schluss Implementierung, Testbench, Ergebnisse, Boardtest und Fazit.",
          ["1  Aufgabe und Funktionsumfang", "2  Hardware: zwei Pmod SSD an JA … JD", "3  Theorie kurz: Segmente, Multiplex",
           "4  Entwurf: Architektur, Zeitbasis, Betriebsarten", "5  Implementierung, Constraints, Test", "6  Ergebnis, Boardtest, Fazit"]),
        S("Aufgabenstellung Phase II", 1.5,
          "Laut Laborfolie 212: Implementierung der 7-Segment-Anzeige mit Zähler. Gezählt wird im Sekundentakt von 0 bis 99, ein Reset per Taster setzt den Zähler zurück. "
          "Als Ergebnis gefordert: Präsentation mit Fragerunde, Bericht über Teil I und II, VHDL-Implementierung mit Testbench, Test in Simulation und am Board, Anhang mit Code. "
          "Die Pflicht erfüllen wir in der Betriebsart SW0. Den Rest des Vortrags zeigen wir, wie wir das erweitert haben.",
          ["Pflicht: Zähler im Sekundentakt 0 … 99", "Pflicht: Reset per Taster", "VHDL-Implementierung + Testbench",
           "Test: Simulation + Board", "Ergebnis: Präsentation + Bericht"]),
        S("Unser Funktionsumfang", 1.5,
          "Wie in Phase I wählen die Schalter die Betriebsart. SW0 ist die Pflicht: Sekunden 00 bis 99 auf dem rechten SSD, das linke bleibt aus. "
          "SW1 nutzt beide SSD als vierstelligen Sekundenzähler 0000 bis 9999. SW2 ist eine Stoppuhr: links Sekunden, rechts Hundertstel, gesteuert mit BTN0 Start, BTN1 Stopp und BTN2 Nullen. "
          "Alles andere – kein Schalter, mehrere oder SW3 – ergibt zwei dunkle Anzeigen. Der rote RESET-Taster setzt alles zurück.",
          image="anzeige_modi.png", subtitle="SW0 Pflicht | SW1 vierstellig | SW2 Stoppuhr | sonst dunkel"),
        S("Hardware: zweites Pmod SSD", 1.0,
          "Das Board ist dasselbe wie in Phase I. Neu ist ein zweites Pmod SSD. Jedes SSD braucht neun Signale – sieben Segmente und den Auswahlpin C – also zwei Pmod-Ports. "
          "Das rechte SSD bleibt an JA und JB, das linke kommt an JC und JD. Insgesamt sind es damit 18 Anzeigeleitungen. Die Pins für JC und JD haben wir aus dem Digilent-Master-XDC bzw. unserem Uhrenprojekt übernommen.",
          ["Arty A7-35T, 100 MHz, SW0 … SW3, BTN0 … BTN3, RESET", "SSD rechts: JA/JB (wie Phase I)", "SSD links: JC/JD (neu)",
           "2 × 9 = 18 Signale, LVCMOS33"]),
        S("Verdrahtung JA … JD", 1.5,
          "Beide SSD stecken jeweils in der UNTEREN Reihe, Pins 7 bis 12. J1 trägt AA bis AD, J2 AE, AF, AG und C. "
          "Oben im Bild das linke SSD an JC und JD, unten das rechte an JA und JB. Unter den Pins stehen die FPGA-Pins aus dem XDC. Vor dem Umstecken die Versorgung trennen und die Orientierung prüfen.",
          image="verdrahtung.png", subtitle="Untere Reihe (7 … 12) – J1 an JA/JC, J2 an JB/JD"),
        S("Bitzuordnung beider SSD", 0.5,
          "Die Bitreihenfolge ist für beide SSD gleich: Bit 6 ist g, Bit 0 ist a. Die Tabelle verfolgt jedes Segment bis zum FPGA-Pin, links für das rechte SSD, rechts für das linke. "
          "Diese Tabelle ist beim Boardtest der erste Prüfpunkt, wenn ein Segment falsch leuchtet.",
          image="segment_aufbau.png", subtitle="seg_r[i] und seg_l[i] → Segment i, Reihenfolge gfedcba"),
        S("Wiederholung: gemeinsame Kathode", 0.5,
          "Kurze Wiederholung aus Phase I: Ein Segment leuchtet, wenn seine Anode 1 ist und die Kathode seiner Ziffer leitet. Die Anoden sind für beide Ziffern eines SSD gemeinsam, C wählt die Ziffer. "
          "Deshalb leuchtet je SSD immer nur eine Ziffer, und wir brauchen den Zeitmultiplex – jetzt eben zweimal.",
          image="segment_elektrisch.png", subtitle="Je SSD leuchtet immer nur eine Ziffer → Multiplex"),
        S("Segmentcodierung", 0.5,
          "Der seg7_decoder ist unverändert: rein kombinatorisch, BCD-Ziffer rein, sieben Bits raus. Neu genutzt wird sein blank-Eingang: blank gleich 1 ergibt 0000000 – damit schalten wir ganze SSD dunkel.",
          image="segment_muster.png", subtitle="Unverändert aus Phase I – blank = 1 → 0000000"),
        S("Zeitmultiplex je SSD", 1.5,
          "Jeder ssd_driver schaltet jede Millisekunde zwischen Einer und Zehner um. Muster und Auswahl wechseln in derselben Taktflanke. Ein Bild dauert 2 ms, jede Ziffer wird mit 500 Hz angesteuert – das Auge sieht beide Ziffern gleichzeitig. "
          "In Phase II laufen zwei solche Treiber parallel und unabhängig, einer pro SSD.",
          image="multiplex_timing.png", subtitle="1 ms je Ziffer, 500 Hz – zwei Treiber laufen parallel"),
        S("Signalfluss", 1.0,
          "Der grobe Signalfluss: Der 100-MHz-Takt speist eine Zeitbasis, die Pulse für 1 s und 10 ms liefert. Diese Pulse treiben die Zähler und die Stoppuhr. Schalter und Taster wählen den Modus und steuern die Stoppuhr. "
          "Am Ende stehen BCD-Zerlegung und zwei SSD-Treiber. Der Reset wirkt auf alle Blöcke – asynchron angefordert, synchron freigegeben.",
          image="signalfluss.png", subtitle="Takt → Zeitbasis → Zähler/Stoppuhr → BCD + 2 × SSD"),
        S("Gesamtarchitektur", 2.0,
          "Das komplette Blockschaltbild. Links die Eingangsstufe: Reset-Sync, Schalter-Sync und drei Entprell-Instanzen. Daneben die Zeitbasis mit zwei tick_gen, der Modus-Decoder und die Tasten-Freigabe. "
          "In der Mitte die Quellen: Zähler A für SW0, Zähler B für SW1 und die Stoppuhr mit dem running-Flipflop. Wichtig: Alle Quellen laufen immer, der Anzeige-MUX wählt nur aus, was man sieht. "
          "Rechts zwei identische Anzeigepfade mit to_bcd2 und ssd_driver. Auf den nächsten Folien färben wir je Betriebsart den aktiven Pfad rot ein.",
          image="architektur.png", subtitle="Eingang → Zeitbasis / Quellen → Anzeige-MUX → zwei Anzeigepfade"),
        S("Modulhierarchie und Wiederverwendung", 1.0,
          "Neu ist nur das Top-Level phase2_top. Alle anderen Module sind unveränderte Kopien aus Phase I: drei btn_debounce, zwei tick_gen, zwei ssd_driver mit je tick_gen und seg7_decoder, dazu das Package clock_pkg mit to_bcd2. "
          "Das zeigt den Vorteil generischer Module: tick_gen dient einmal als Sekunden-, einmal als 10-ms-Teiler, nur mit anderem Generic.",
          image="hierarchie.png", subtitle="1 neue Entity, 5 unverändert wiederverwendete Module"),
        S("Synchronisation: Reset und Schalter", 1.0,
          "Unverändert aus Phase I: Der Reset wird asynchron angefordert und synchron nach zwei Flanken freigegeben. Die Schalter laufen durch zwei Flipflops. "
          "Neu ist nur die Wirkung: rst setzt jetzt auch die beiden tick_gen zurück. Nach dem Loslassen beginnt also ein vollständiges erstes Sekundenintervall.",
          ["Reset: asynchron anfordern,", "synchron freigeben (2 FF)", "Schalter: 2-FF-Synchronisierer", "rst setzt auch die Vorteiler zurück"], code=sync_code),
        S("Entprellung der Taster", 1.0,
          "Auch die Entprellung ist unverändert: Nach 10 ms stabilem Pegel entsteht pro Druck genau ein 1-Takt-Puls; Halten und Loslassen erzeugen nichts. "
          "Für die Stoppuhr bedeutet das: Start und Stopp kommen jeweils 10 ms verzögert – aber beide gleich, die gemessene Dauer stimmt also.",
          image="entprell_timing.png", subtitle="3 Instanzen für BTN0 … BTN2 – ein Druck = ein Puls"),
        S("Zeitbasis: zwei tick_gen", 1.5,
          "Die Zeitbasis: u_tick_sec teilt durch 100 Millionen und liefert jede Sekunde einen Puls von 10 ns. Oben sieht man den Übergang von 99 auf 100 Sekunden: cnt_a springt auf 00, Zähler B macht den Übertrag auf 0100. "
          "u_tick_cs teilt durch eine Million, also 10 ms, und läuft nur bei running gleich 1. Unten: Start bei 10 ms, ab dann jede 10 ms ein Schritt, Stopp bei 70 ms – der Stand bleibt stehen.",
          image="zeitbasis.png", subtitle="tick_sec: DIV = 100.000.000 | tick_cs: DIV = 1.000.000, en = running"),
        S("Tasten-Freigabe und 10-ms-Vorteiler", 1.0,
          "Im Code sind das drei nebenläufige Zuweisungen: Start und Stopp nur bei sw_sync gleich 0100, Nullen zusätzlich nur, wenn die Uhr steht. "
          "Darunter die Instanz des 10-ms-Vorteilers: en gleich running hält ihn im Stopp an, ohne den Stand zu verlieren; clr gleich sw_zero setzt ihn beim Nullen zurück. Die Ports en und clr gab es in tick_gen schon – wir nutzen sie hier zum ersten Mal.",
          ["Tasten nur bei sw_sync = 0100", "Nullen nur bei running = 0", "en = running: Vorteiler pausiert", "clr = sw_zero: Vorteiler auf 0"], code=gate_code),
        S("Modus-Decoder: 16 Schalterstellungen", 1.0,
          "Gültig sind nur drei one-hot-Stellungen: 0001, 0010 und 0100. SW3 allein ist in Phase II nicht belegt. Die übrigen 13 Stellungen ergeben zwei dunkle SSD. "
          "Wie in Phase I entstehen Wert und Freigabe aus derselben case-Anweisung – sie können nie widersprüchlich sein.",
          image="schalter_tabelle.png", subtitle="3 gültige Stellungen – 13 von 16 ergeben „dunkel“"),
        S("SW0: Sekundenzähler 00 … 99 (Pflicht)", 1.5,
          "Die Pflichtaufgabe. Rot ist der aktive Pfad: tick_sec, Zähler A, Anzeige-MUX, rechter Anzeigepfad. Jede Sekunde plus 1, nach 99 kommt 00. "
          "Das linke SSD ist grau: show_l ist 0, blank_l ist 1, die Segmente sind aus. Die Taster haben keine Wirkung. Zähler B und eine laufende Stoppuhr zählen im Hintergrund weiter.",
          image="modus_sw0.png", subtitle="sw = 0001: cnt_a +1 je Sekunde, rechtes SSD, linkes SSD aus"),
        S("SW1: Sekundenzähler 0000 … 9999", 1.5,
          "Mit SW1 werden beide SSD genutzt. Zähler B zählt die Sekunden seit dem Reset bis 9999, das sind 2 Stunden 46 Minuten 39 Sekunden, dann wieder 0000. "
          "Links stehen Tausender und Hunderter, rechts Zehner und Einer. Führende Nullen zeigen wir an – 0042 ist bei einer Zeitanzeige besser lesbar als 42 mit Lücken.",
          image="modus_sw1.png", subtitle="sw = 0010: links cnt_b_hi, rechts cnt_b_lo"),
        S("Zählerkaskade", 1.5,
          "Den vierstelligen Zähler haben wir als Kaskade zweier Stufen von 0 bis 99 gebaut. Die untere Stufe zählt jede Sekunde; bei 99 gibt sie den Übertrag an die obere Stufe weiter. "
          "Vorteil: Jede Stufe passt genau auf ein SSD und wird mit derselben Funktion to_bcd2 zerlegt – keine Division eines 14-Bit-Werts durch 1000 nötig. "
          "Die Stoppuhr ist genauso aufgebaut: Hundertstel unten, Sekunden oben.",
          image="kaskade.png", subtitle="lo = 99 → lo ← 0, hi + 1 – gleiches Prinzip für Zähler B und Stoppuhr"),
        S("Sekunden-Prozess im Code", 1.0,
          "Beide Sekundenzähler stehen im selben Prozess und reagieren auf denselben tick_sec. Zähler A ist ein einfacher Modulo-100-Zähler, Zähler B die Kaskade mit verschachteltem if. "
          "Alle Grenzen werden vor der Rechnung geprüft, sodass kein Signal seinen Bereich 0 bis 99 verlässt.",
          ["ein Puls → beide Zähler", "cnt_a: modulo 100", "cnt_b: lo/hi-Kaskade", "Grenzprüfung vor Rechnung"], code=sec_code),
        S("SW2: Stoppuhr – Datenpfad", 1.5,
          "Jetzt die Stoppuhr. Rot sind die Taster mit Entprellung, die Tasten-Freigabe, das running-Flipflop, der 10-ms-Vorteiler und das Zählwerk. "
          "Links stehen die Sekunden, rechts die Hundertstel. Das rechte SSD hat nur zwei Stellen, daher ist die Auflösung 10 ms.",
          image="modus_sw2.png", subtitle="sw = 0100: links Sekunden, rechts Hundertstel"),
        S("Stoppuhr: Zustände und Tasten", 2.0,
          "Die Steuerung ist ein einziges Flipflop: GESTOPPT oder LÄUFT. BTN0 startet, BTN1 stoppt. BTN2 nullt – aber nur im Stopp, damit eine laufende Messung nicht versehentlich gelöscht wird. "
          "Rechts ein Beispielablauf: Start, 2,02 Sekunden, Stopp, Nullen, dann eine Messung von 1,50 Sekunden. Wechselt man bei laufender Uhr den Modus, läuft sie im Hintergrund weiter.",
          image="stoppuhr.png", subtitle="BTN0 Start | BTN1 Stopp | BTN2 Nullen nur im Stopp"),
        S("Stoppuhr im Code", 1.0,
          "Im Code: running wird von sw_start gesetzt und von sw_stop gelöscht. Darunter das Zählwerk: Nullen hat Vorrang, sonst zählt tick_cs die Hundertstel mit Übertrag in die Sekunden. "
          "Nach 99,99 Sekunden beginnt die Stoppuhr wieder bei 00,00 und läuft weiter.",
          ["running: Start setzt, Stopp löscht", "Nullen vor Zählen", "Kaskade stop_cs → stop_s", "99.99 → 00.00, läuft weiter"], code=stop_code),
        S("Wie genau ist die Stoppuhr?", 1.0,
          "Die Auflösung ist 10 ms. Die Zeitbasis kommt direkt vom 100-MHz-Oszillator des Boards. Start und Stopp werden beide um die gleichen 10 ms Entprellzeit verzögert, das hebt sich in der Messung auf. "
          "Wichtig ist auch: Im Stopp behält der Vorteiler seinen Stand. Wer mehrmals startet und stoppt, verliert keine angefangenen Hundertstel.",
          ["Auflösung 10 ms, Anzeige abgeschnitten", "Zeitbasis: 100-MHz-Oszillator", "Entprell-Latenz bei Start und Stopp gleich → hebt sich auf",
           "Vorteiler pausiert im Stopp → kein Verlust", "Nullen setzt auch den Vorteiler zurück"]),
        S("Ungültig: beide SSD dunkel", 0.5,
          "Bei keinem, mehreren Schaltern oder SW3 sind show_l und show_r gleich 0. Beide Decoder bekommen blank gleich 1, beide SSD sind dunkel. Im Hintergrund zählt alles weiter – schaltet man zurück, ist der aktuelle Stand sofort da.",
          image="modus_off.png", subtitle="show_l = show_r = 0 → beide SSD dunkel, Zähler laufen weiter"),
        S("Anzeigepfad mit zwei Treibern", 1.5,
          "Je SSD gibt es einen identischen Pfad: Der Wert 0 bis 99 geht in to_bcd2 und wird in Zehner und Einer zerlegt. Das Ergebnis ist ein Record; seine Elemente gehen direkt an den ssd_driver. "
          "Die Freigabe wird invertiert an blank angeschlossen. Anders als in Phase I brauchen wir keine eigene Ausblendung im Top-Level mehr, weil alle Werte zweistellig angezeigt werden.",
          image="anzeigepfad.png", subtitle="val → to_bcd2 → ssd_driver (MUX, Decoder, blank) → seg, dsel"),
        S("Anzeige-MUX im Code", 1.0,
          "Der Anzeige-MUX ist eine case-Anweisung über sw_sync. Zuerst werden Defaults gesetzt – Wert 0 und dunkel. Jeder gültige Modus legt Werte und Freigaben für das linke und rechte SSD fest. "
          "Der others-Zweig ändert nichts, beide bleiben dunkel. So entsteht kein Latch, und Wert und Freigabe passen immer zusammen.",
          ["Defaults: 0, dunkel", "SW0: nur rechts", "SW1: hi links, lo rechts", "SW2: s links, cs rechts", "others: beide dunkel"], code=mux_code),
        S("Pin-Constraints und Vivado", 1.0,
          "Die XDC-Datei ordnet jetzt 26 Ports zu: Takt, Reset, vier Schalter, vier Taster und 16 Anzeigeleitungen. Neu sind seg_l und dsel_l auf JC und JD. "
          "Das Tcl-Skript legt das Projekt reproduzierbar an. Vivado-Build und Timing-Analyse sind noch offen und Teil der Boardabnahme.",
          ["seg_r / dsel_r: JA/JB (unverändert)", "seg_l: U14, V14, T13, U13, E2, D2, H2", "dsel_l: G2 (JD10)", "create_clock 10 ns, LVCMOS33",
           "scripts/create_project.tcl → vivado/"]),
        S("Testbench-Strategie", 1.0,
          "Die Testbench ist selbstprüfend und schaut nur auf die Ausgänge beider SSD. read_ssd liest 12 Takte lang beide Anzeigen, dekodiert die Muster zurück in Ziffern und prüft, dass nichts flackert. "
          "Die Zeit ist skaliert: 1 Sekunde gleich 1000 Takte. Die Prozedur wait_second liest jeden Sekundenwert genau in der Mitte der Sekunde, und überspringt lange Wartezeiten mit wait for – so testen wir sogar den Überlauf bei 10.000 Sekunden.",
          ["Black-Box: seg/dsel beider SSD", "1 s ≙ 1000 Takte", "Lesen in Sekundenmitte", "10.000 s in ca. 40 s Rechenzeit"], code=tb_code),
        S("Simulationsergebnis", 1.0,
          "Getestet: Startwerte, alle ungültigen Stellungen, SW0 über 102 Sekunden mit Überlauf, SW1 vierstellig und der Überlauf von 9999 auf 0000, die Stoppuhr mit Start, Stopp, Halten, Nullen im Lauf und im Stopp, Hintergrundbetrieb, Überlauf bei 99,99, Taster in falschen Modi und Reset. "
          f"GHDL 6.0.0 meldet PASS nach {SIM_TIME} simulierter Zeit. Als Gegenprobe haben wir einen Fehler eingebaut – die Testbench hat ihn erkannt.",
          ["GHDL 6.0.0: PASS, keine Assertion-Fehler", "alle 15 Anforderungen P2-01 … P2-15", "inkl. 9999 → 0000 und 99.99 → 00.00",
           "Gegenprobe: eingebauter Fehler wird erkannt", "VHDL-93-Analyse + Synthese mit GHDL fehlerfrei"]),
        S("Boardtest und Live-Demo", 2.0,
          "Ablauf am Board: Alle Schalter aus – dunkel. SW0: Sekunden zählen, mit einer Handy-Stoppuhr vergleichen, RESET drücken. SW1: vier Stellen. "
          "SW2: Start, Stopp, Nullen; Nullen im Lauf ohne Wirkung. Dann Stoppuhr starten, auf SW0 wechseln und zurück – sie läuft weiter. Zum Schluss Taster in SW0 und SW1 – keine Wirkung.",
          ["Alle Schalter aus → dunkel", "SW0: 00, 01, … – Vergleich Handy, RESET", "SW1: 4 Stellen", "SW2: Start, Stopp, Nullen",
           "Moduswechsel: Stoppuhr läuft weiter"]),
        S("Fazit und Ausblick", 1.0,
          "Zusammenfassung: Die Pflicht – Sekundenzähler 0 bis 99 mit Reset – ist erfüllt und um ein zweites SSD, einen vierstelligen Zähler und eine Stoppuhr erweitert. "
          "Bis auf das Top-Level haben wir alle Module unverändert aus Phase I übernommen. Zeitbasis, Kaskade und Mehrfach-Anzeige sind direkt die Bausteine für die Uhr bzw. den Wecker in Phase III. "
          "Offen sind Vivado-Timing und der protokollierte Boardtest. Vielen Dank – wir freuen uns auf Fragen.",
          ["Pflicht erfüllt + 2 Zusatzmodi", "2 SSD, 4 Stellen, Stoppuhr 10 ms", "1 neues Modul, 5 wiederverwendet", "Offen: Vivado-Timing, Boardprotokoll",
           "Phase III: Uhr / Wecker auf gleicher Basis"]),
        S("Fragen?", 0.0,
          "Fragerunde. Mögliche Fragen: Warum kein abgeleiteter 1-Hz-Takt? Warum zwei Stufen statt eines Zählers bis 9999? Was passiert, wenn Start und Stopp gleichzeitig kommen? "
          "Wie genau ist die Stoppuhr? Warum ist Nullen nur im Stopp erlaubt? Warum läuft alles im Hintergrund weiter?",
          ["Vielen Dank!", "Marc & Maxi"], "anzeige_modi.png", layout="title"),
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
            add_text(slide, 0.7, 0.9, 12, 1.2, [item["title"]], 40, RED, True)
            add_text(slide, 0.75, 2.05, 12, 1.6, item["bullets"], 24, INK, spacing=6)
            fit_picture(slide, item["image"], 0.7, 3.55, 12.0, 3.5)
        else:
            add_text(slide, 0.6, 0.22, 11.5, 0.4, ["DIGITALE SCHALTUNGSTECHNIK  |  PHASE II"], 12, TEAL, True)
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
                size = 13 if len(code_lines) <= 22 and max(map(len, code_lines)) <= 72 else 11
                shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(5.0), Inches(1.45), Inches(7.95), Inches(5.5))
                shape.fill.solid()
                shape.fill.fore_color.rgb = RGBColor.from_string(LIGHT)
                shape.line.fill.background()
                add_text(slide, 5.15, 1.55, 7.7, 5.3, code_lines, size, INK, font_name="Consolas", spacing=0)
            else:
                add_text(slide, 0.6, 1.6, 12.0, 5.2, item["bullets"], 26, bullets=True, spacing=14)
        add_text(slide, 0.6, 7.05, 10.8, 0.3, ["Arty A7-35T + 2 × Pmod SSD  |  Marc & Maxi"], 10, GRAY)
        add_text(slide, 12.2, 7.0, 0.8, 0.35, [f"{index:02d}"], 14, RED, True)
        minutes = item["minutes"]
        timing = f"Zeitbudget: {minutes:g} min (gesamt 40 min + Fragerunde)." if minutes else "Fragerunde (außerhalb der 40 min)."
        slide.notes_slide.notes_text_frame.text = f"{timing}\n\n{item['notes']}"
    presentation.save(path)


def main():
    diagrams.generate_all(IMG)
    content = sections()
    make_docx(DOC / "bericht_phase_2.docx", content)
    make_markdown(DOC / "bericht_phase_2.md", content)
    data = slides()
    make_pptx(DOC / "praesentation_phase_2.pptx", data)
    print(f"{len(content)} Kapitel, {len(list(IMG.glob('*.png')))} Grafiken, {len(data)} Folien "
          f"({sum(s['minutes'] for s in data):g} min) erzeugt")


if __name__ == "__main__":
    main()
