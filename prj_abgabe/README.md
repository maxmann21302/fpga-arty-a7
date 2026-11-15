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

## Phase 2: Sekundenzaehler 00 bis 99

[phase_2](phase_2) setzt die Aufgabe aus image5 um:

- Automatischer Start nach Resetfreigabe, **ein Schritt pro Sekunde**.
- Beide Stellen sind aktiv: **00, 01, ..., 99, 00**.
- **ck_rst** setzt Zahlenstand und Sekundenteiler zurueck.
- Nach dem Loslassen beginnt ein neues vollstaendiges Sekundenintervall.
- Kein Start-/Stop-Taster; BTN0 wird hier nicht verwendet.

Unterlagen:

- [Kombinierter Bericht Phase I+II als PDF, 20 Seiten](phase_2/doc/bericht_phase_1_und_2.pdf)
- [Bearbeitbarer kombinierter Bericht als DOCX](phase_2/doc/bericht_phase_1_und_2.docx)
- [Kombinierter Bericht als Markdown](phase_2/doc/bericht_phase_1_und_2.md)
- [PowerPoint: 14 Folien mit Sprechernotizen, ca. 20 Minuten](phase_2/doc/praesentation_phase_2.pptx)

## Phase 3: Wecker

[phase_3](phase_3) ist die **unveraenderte Kopie von prj_final** mit allen
29 zum Kopierzeitpunkt vorhandenen Dateien, einschliesslich Dokumentation,
Testbenches, Aufgabenbildern und Projekt-Tcl. Die Dateiinhalte wurden mit
SHA-256 gegen das Original verglichen. Dies ist ein Integritaetsnachweis,
kein neuer Funktionstest des Weckers.

## Verdrahtung fuer Phase 1 und 2

Ein Pmod SSD reicht aus. Wie im Weckerprojekt werden **JA und JB jeweils
in der unteren Reihe, Pins 7 bis 10**, verwendet. Nicht mit den oberen
Pins 1 bis 4 verwechseln. Versorgung ausschalten, bevor umgesteckt wird;
3,3-V-Versorgung und gemeinsame Masse entsprechend Pmod-Dokumentation anschliessen.

| Signal | FPGA-Pin | Verbindung |
| --- | --- | --- |
| CLK100MHZ | E3 | Board-Oszillator |
| ck_rst | C2 | Reset, aktiv Low |
| sw[0..3] | A8, C11, C10, A10 | SW0 ... SW3, nur Phase 1 |
| btn[0..3] | D9, C9, B9, B8 | BTN0 ... BTN3, nur Phase 1 |
| seg_r[0], Segment a | D13 | JA7 -> SSD AA |
| seg_r[1], Segment b | B18 | JA8 -> SSD AB |
| seg_r[2], Segment c | A18 | JA9 -> SSD AC |
| seg_r[3], Segment d | K16 | JA10 -> SSD AD |
| seg_r[4], Segment e | J17 | JB7 -> SSD AE |
| seg_r[5], Segment f | J18 | JB8 -> SSD AF |
| seg_r[6], Segment g | K15 | JB9 -> SSD AG |
| dsel_r | J15 | JB10 -> SSD C |

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
angeben. Das Skript legt Arbeitsbibliothek und Wellenform unter `sim/build/` ab.
Die selbstpruefenden Testbenches stoppen bei einer falschen Ausgabe mit Fehler.
Die verkleinerten Simulationsparameter beschleunigen den Test; sie sind keine
realen Sekunden- oder Entprellmessungen.

Tatsaechlich ausgefuehrte Tests mit **GHDL 6.0.0**:

| Phase | Ergebnis | Abdeckung |
| --- | --- | --- |
| 1 | PASS bei 69.050 ns | SW0: Start 0, +-1, +-10, Grenze 0, 99 -> 0, 95 + 10 -> 0; SW1 91; SW2 93; SW3 alle 0..15; ungueltige Schalter dunkel; Prellen, Halten, Reset, Werterhalt |
| 2 | PASS bei 1.033.690 ns | Exakte Taktanzahl je Schritt, alle 00..99, 09 -> 10, 99 -> 00, beide Slots, Reset und Intervallneustart |

Protokolle: [Phase 1](phase_1/sim/testergebnis.txt),
[Phase 2](phase_2/sim/testergebnis.txt).

## Dokumente bearbeiten und neu erzeugen

Die Berichte enthalten Theorie, Blockschaltbilder fuer Phase I+II,
Pinbelegung, Implementierung, Testmethodik, beobachtete Ergebnisse,
Board-Prueflisten und Quellen. Die vollstaendigen VHDL-Dateien und
Testbenches sind als separate, direkt kompilierbare Abgabedateien enthalten.

Phase 1: 32 Folien, 40 Minuten; Phase 2: 14 Folien, 20 Minuten (jeweils mit
Sprechernotizen, Fragerunde zusaetzlich).

```powershell
python -m pip install -r scripts/requirements.txt
python phase_1/scripts/create_docs.py   # Phase 1
python scripts/create_documents.py      # Phase 2 (kombinierter Bericht)
```

Die Generatoren aktualisieren DOCX, Markdown, PPTX und PNG-Grafiken.
PDFs anschliessend aus den aktualisierten DOCX-Dateien mit Word exportieren
(Phase 1: 25 Seiten, Phase 2: 20 Seiten).

## Vor der endgueltigen Abgabe

- Autor und Gruppe in Berichten und Praesentationen ergaenzen.
- Vivado-Synthese, Implementation, DRC und Timinganalyse durchfuehren.
- Den realen Boardtest anhand der Prueflisten durchfuehren und protokollieren.
- Gemessene Ressourcen-, Timing- und Boarddaten ergaenzen.

**Offener Nachweis:** Auf diesem Rechner war Vivado nicht verfuegbar.
Es wurde kein physischer Boardtest durchgefuehrt. Die Dokumente trennen
die bestandene RTL-Simulation ausdruecklich von diesen offenen Schritten.
