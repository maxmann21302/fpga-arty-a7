# FPGA-Projekte

Sammlung von VHDL-Projekten und Uebungen fuer das Digilent Arty A7-35T mit
Artix-7 FPGA. Die Projekte behandeln kombinatorische Logik, Zaehler,
7-Segment-Anzeigen, eine digitale Uhr mit Wecker sowie die Ansteuerung eines
Farbdisplays ueber SPI.

## Projekte

| Ordner | Inhalt |
| --- | --- |
| [prj1_hhn](prj1_hhn/) | Sekunden- und Minutenzaehler auf Pmod-SSD-Anzeigen, mit Reset und Start/Pause. |
| [prj_clock](prj_clock/) | Aelterer Projektstand zur 7-Segment-Anzeige und digitalen Uhr. |
| [prj_volladdierer](prj_volladdierer/) | Kombinatorischer 1-Bit-Volladdierer mit Wahrheitstabelle, VHDL und Pinbelegung. Siehe [Projekt-README](prj_volladdierer/README.md). |
| [prj_abgabe](prj_abgabe/) | Eigenstaendige Abgabe in drei Phasen: Tasterzaehler, Sekundenzaehler und Wecker. Die Phasen 1 und 2 haben automatisierte GHDL-Simulationen. Siehe [Projekt-README](prj_abgabe/README.md). |
| [prj_final](prj_final/) | Eigenstaendiges digitales Uhr-/Weckerprojekt mit Zeit- und Weckzeiteinstellung, multiplexierten Anzeigen sowie optischem und akustischem Alarm. |
| [prj_spi](prj_spi/) | Pmod-OLEDrgb-Farbdisplay ueber SPI mit Logos, animiertem Anker und Pong. Siehe [Dokumentation](prj_spi/doc/dokumentation.md). |

`prj_abgabe/phase_3` ist eine dokumentierte Kopie von `prj_final` zum Stand
der Abgabe. `prj_clock` und `prj1_hhn` enthalten fruehere beziehungsweise
kleinere Entwicklungsstaende.

## Voraussetzungen

- **AMD/Xilinx Vivado** zum Erstellen, zur Synthese und zum Programmieren der
  FPGA-Projekte.
- **GHDL mit VHDL-2008-Unterstuetzung** fuer die automatisierten Simulationen
  in `prj_abgabe/phase_1`, `prj_abgabe/phase_2` und `prj_spi`.
- **Python** fuer die optionalen Dokument- und ROM-Generatoren in den
  jeweiligen `scripts`-Ordnern; Details und Abhaengigkeiten stehen bei den
  einzelnen Projekten.

## Einstieg

Vivado-Projekte werden jeweils ueber das Tcl-Skript im zugehoerigen
Projektordner angelegt. Beispiel fuer das OLED-Projekt:

```powershell
vivado -mode gui -source scripts/create_project.tcl
```

Den Befehl aus dem Verzeichnis `prj_spi` ausfuehren. Bei den Projekten in
`prj_abgabe/phase_1` und `phase_2` erzeugt dasselbe Vorgehen jeweils ein
eigenes Vivado-Projekt. Fuer Simulationen die Anweisungen in der jeweiligen
Projekt-Dokumentation befolgen, da sich Testbench und Laufzeit je Projekt
unterscheiden.

## Hardware

Die Hauptzielplattform ist das Arty A7-35T. Einige Projekte benoetigen
zusaetzliche Pmod-Module, insbesondere Pmod-SSD-Anzeigen oder das Pmod
OLEDrgb. Pinbelegung, Verdrahtung, Reset-Polaritaet und Inbetriebnahme
unterscheiden sich je Projekt; vor einem Boardtest immer die zugehoerige
Constraints-Datei (`.xdc`) und Dokumentation pruefen.