# Abgabe: 7-Segment-Anzeige, Sekundenzaehler und Wecker

Zielhardware: **Digilent Arty A7-35T**, FPGA `xc7a35ticsg324-1L`,
100-MHz-Systemtakt und externes Digilent Pmod SSD.
Jede Phase ist ein eigenstaendiger Projektordner.
Das bestehende Projekt `prj_final` wurde nicht veraendert.

## Phase 1: Anzeige mit Betriebsarten

[phase_1](phase_1) setzt die Aufgaben aus image3/image4 um. Die Schalter
SW0 ... SW3 waehlen die Betriebsart (genau ein Schalter oben):

| Schalter | Anzeige | Taster |
| --- | --- | --- |
| SW0 | Zaehler 0 ... 99, Start 0 | BTN0 +1, BTN1 -1, BTN2 +10, BTN3 -10; nie < 0, > 99 -> 0 |
| SW1 | 91 (Matrikelnummer Mark) | - |
| SW2 | 93 (Matrikelnummer Maxi) | - |
| SW3 | Binaereingabe 0 ... 15 (dezimal angezeigt) | BTNi invertiert Bit i |
| keiner / mehrere | dunkel | - |

- Taster sind entprellt (10 ms); ein Druck ist genau ein Schritt, Halten wiederholt nicht.
- Zaehler und Binaerwert bleiben beim Moduswechsel erhalten; **ck_rst** setzt beide auf 0.

Unterlagen (erzeugt mit `python phase_1/scripts/create_docs.py`):

- [Bericht als PDF, 25 Seiten](phase_1/doc/bericht_phase_1.pdf)
- [Bearbeitbarer Bericht als DOCX](phase_1/doc/bericht_phase_1.docx)
- [Bericht als Markdown](phase_1/doc/bericht_phase_1.md)
- [PowerPoint: 32 Folien mit Sprechernotizen, ca. 40 Minuten](phase_1/doc/praesentation_phase_1.pptx)
- Blockschaltbilder je Betriebsart, Segment-/Multiplex-/Entprell-Grafiken: [phase_1/doc/img](phase_1/doc/img)

## Phase 2: Sekundenzaehler, 4-stelliger Zaehler und Stoppuhr

[phase_2](phase_2) setzt die Aufgabe aus image5 um (Zaehler im Sekundentakt
0 ... 99, Reset per Taster) und erweitert sie mit einem **zweiten Pmod SSD an JC/JD**:

| Schalter | SSD links (JC/JD) | SSD rechts (JA/JB) | Taster |
| --- | --- | --- | --- |
| SW0 | dunkel | Sekunden 00 ... 99 (Pflicht), 99 -> 00 | - |
| SW1 | Tausender/Hunderter | Zehner/Einer: Sekunden 0000 ... 9999 | - |
| SW2 | Stoppuhr Sekunden 00 ... 99 | Hundertstel 00 ... 99 | BTN0 Start, BTN1 Stopp, BTN2 Nullen (nur im Stopp) |
| keiner / mehrere / SW3 | dunkel | dunkel | - |

- Alle Zaehler und eine laufende Stoppuhr laufen beim Moduswechsel im Hintergrund weiter.
- 99.99 -> 00.00, die Stoppuhr laeuft weiter. Fuehrende Nullen werden angezeigt.
- **ck_rst** setzt alles zurueck und haelt die Stoppuhr an.

Unterlagen (erzeugt mit `python phase_2/scripts/create_docs.py`):

- [Bericht als PDF, 25 Seiten](phase_2/doc/bericht_phase_2.pdf)
- [Bearbeitbarer Bericht als DOCX](phase_2/doc/bericht_phase_2.docx)
- [Bericht als Markdown](phase_2/doc/bericht_phase_2.md)
- [PowerPoint: 35 Folien mit Sprechernotizen, ca. 40 Minuten](phase_2/doc/praesentation_phase_2.pptx)
- Blockschaltbilder je Betriebsart, Zeitbasis, Kaskade, Stoppuhr, Verdrahtung: [phase_2/doc/img](phase_2/doc/img)

## Phase 3: Wecker

[phase_3](phase_3) ist die **unveraenderte Kopie von prj_final** mit allen
29 zum Kopierzeitpunkt vorhandenen Dateien, einschliesslich Dokumentation,
Testbenches, Aufgabenbildern und Projekt-Tcl. Die Dateiinhalte wurden mit
SHA-256 gegen das Original verglichen. Dies ist ein Integritaetsnachweis,
kein neuer Funktionstest des Weckers.

## Verdrahtung fuer Phase 1 und 2

Phase 1 braucht ein Pmod SSD, Phase 2 zwei. Wie im Weckerprojekt werden die
Pmod-Ports **jeweils in der unteren Reihe, Pins 7 bis 10**, verwendet: JA/JB fuer
das rechte SSD (Phase 1 und 2), JC/JD fuer das linke SSD (nur Phase 2). Nicht mit
den oberen Pins 1 bis 4 verwechseln. Versorgung ausschalten, bevor umgesteckt wird;
3,3-V-Versorgung und gemeinsame Masse entsprechend Pmod-Dokumentation anschliessen.

| Signal | FPGA-Pin | Verbindung |
| --- | --- | --- |
| CLK100MHZ | E3 | Board-Oszillator |
| ck_rst | C2 | Reset, aktiv Low |
| sw[0..3] | A8, C11, C10, A10 | SW0 ... SW3 |
| btn[0..3] | D9, C9, B9, B8 | BTN0 ... BTN3 |
| seg_r[0], Segment a | D13 | JA7 -> SSD AA |
| seg_r[1], Segment b | B18 | JA8 -> SSD AB |
| seg_r[2], Segment c | A18 | JA9 -> SSD AC |
| seg_r[3], Segment d | K16 | JA10 -> SSD AD |
| seg_r[4], Segment e | J17 | JB7 -> SSD AE |
| seg_r[5], Segment f | J18 | JB8 -> SSD AF |
| seg_r[6], Segment g | K15 | JB9 -> SSD AG |
| dsel_r | J15 | JB10 -> SSD C |
| seg_l[0..3], Segment a..d (Phase 2) | U14, V14, T13, U13 | JC7 ... JC10 -> SSD links AA ... AD |
| seg_l[4..6], Segment e..g (Phase 2) | E2, D2, H2 | JD7 ... JD9 -> SSD links AE ... AG |
| dsel_l (Phase 2) | G2 | JD10 -> SSD links C |

Segmente sind aktiv High, Bitreihenfolge `gfedcba`.
Die Zuordnung `dsel_r=0` fuer die rechte Stelle entspricht dem vorhandenen
Wecker-Anzeigetreiber und ist beim Boardtest zu kontrollieren.

## Vivado-Projekt erstellen

Im gewuenschten Phasenordner, zum Beispiel `phase_1`:

```powershell
vivado -mode gui -source scripts/create_project.tcl
```

Alternativ aus diesem Ordner im Vivado-Tcl-Terminal:

```tcl
source scripts/create_project.tcl
```

Das Projekt entsteht jeweils unter `vivado/`. Phase 1/2 nutzen VHDL-2008.
Top-Level: `phase1_top` / `phase2_top`, Simulation: `tb_phase1_top` /
`tb_phase2_top`. Danach Behavioral Simulation, Synthesis, Implementation,
Timing/DRC und Generate Bitstream ausfuehren. Phase 3 behaelt sein originales
Wecker-Skript und seine urspruengliche Projektkonfiguration.

## Automatisierte Simulation fuer Phase 1 und 2

Voraussetzung: GHDL mit VHDL-2008-Unterstuetzung. Aus dem jeweiligen Phasenordner:

```powershell
./scripts/run_sim.ps1 -Ghdl ghdl
```

Liegt GHDL nicht im PATH, bei `-Ghdl` den vollstaendigen Pfad zu `ghdl.exe`
angeben. Das Skript legt die Arbeitsbibliothek (und in Phase 1 die Wellenform)
unter `sim/build/` ab. In Phase 2 wird die Wellenform nur mit `-Wave` erzeugt,
weil 10.000 simulierte Sekunden mehrere 100 MB ergeben (Laufzeit ca. 40 s).
Die selbstpruefenden Testbenches stoppen bei einer falschen Ausgabe mit Fehler.
Die verkleinerten Simulationsparameter beschleunigen den Test; sie sind keine
realen Sekunden- oder Entprellmessungen.

Tatsaechlich ausgefuehrte Tests mit **GHDL 6.0.0**:

| Phase | Ergebnis | Abdeckung |
| --- | --- | --- |
| 1 | PASS bei 69.050 ns | SW0: Start 0, +-1, +-10, Grenze 0, 99 -> 0, 95 + 10 -> 0; SW1 91; SW2 93; SW3 alle 0..15; ungueltige Schalter dunkel; Prellen, Halten, Reset, Werterhalt |
| 2 | PASS bei 101.151.070 ns | SW0 Sekunde 1..102 inkl. 99 -> 00, links dunkel; SW1 4-stellig inkl. 9999 -> 0000; Stoppuhr Start/Stopp/Halten/Nullen (im Lauf ignoriert), Hintergrundbetrieb, 99.99 -> 00.00; Taster ausserhalb SW2 wirkungslos; ungueltige Schalter dunkel; Reset |

Protokolle: [Phase 1](phase_1/sim/testergebnis.txt),
[Phase 2](phase_2/sim/testergebnis.txt).

## Dokumente bearbeiten und neu erzeugen

Die Berichte enthalten Theorie, Blockschaltbilder fuer Phase I+II,
Pinbelegung, Implementierung, Testmethodik, beobachtete Ergebnisse,
Board-Prueflisten und Quellen. Die vollstaendigen VHDL-Dateien und
Testbenches sind als separate, direkt kompilierbare Abgabedateien enthalten.

Phase 1: 32 Folien, 40 Minuten; Phase 2: 35 Folien, 40 Minuten (jeweils mit
Sprechernotizen, Fragerunde zusaetzlich).

```powershell
python -m pip install -r scripts/requirements.txt
python phase_1/scripts/create_docs.py   # Phase 1
python phase_2/scripts/create_docs.py   # Phase 2
```

Die Generatoren aktualisieren DOCX, Markdown, PPTX und PNG-Grafiken.
PDFs anschliessend aus den aktualisierten DOCX-Dateien mit Word exportieren
(Phase 1: 25 Seiten, Phase 2: 25 Seiten).

## Vor der endgueltigen Abgabe

- Autor und Gruppe in Berichten und Praesentationen ergaenzen.
- Vivado-Synthese, Implementation, DRC und Timinganalyse durchfuehren.
- Den realen Boardtest anhand der Prueflisten durchfuehren und protokollieren.
- Gemessene Ressourcen-, Timing- und Boarddaten ergaenzen.

**Offener Nachweis:** Auf diesem Rechner war Vivado nicht verfuegbar.
Es wurde kein physischer Boardtest durchgefuehrt. Die Dokumente trennen
die bestandene RTL-Simulation ausdruecklich von diesen offenen Schritten.
