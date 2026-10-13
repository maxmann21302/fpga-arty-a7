# Digitale Uhr / Wecker auf dem Arty A7-35T

Laborbericht – Digitale Schaltungstechnik mit Labor

---

## 1. Theorie / Analyse

### 1.1 Motivation und Zielbeschreibung

Umgesetzt wird eine digitale Uhr mit Weckfunktion auf einem FPGA. Das Ziel ist,
eine vollständig synchrone Digitalschaltung ohne Prozessor zu entwerfen und
dabei die typischen Bausteine einer Steuerung zu verwenden: Taktteiler, Zähler,
Zustandsautomat, Entprellung, Anzeigemultiplex.

Geforderte Funktionen laut Aufgabenstellung:

| Anforderung | Umsetzung |
|---|---|
| Ausgabe Stunden/Minuten auf 7-Segment | zwei Pmod SSD, je zwei Ziffern |
| Schalter: Ausgabe Sekunden | `sw0` schaltet die Anzeige auf MM:SS |
| Einstellung Zeit mit Pushbuttons +/- | `sw1` + `btn0..btn3` |
| Einstellung Weckzeit mit Pushbuttons +/- | `sw2` + `btn0..btn3` |
| Signalausgabe optisch | LD4..LD7 blinken mit 2 Hz |
| Signalausgabe akustisch | Buzzer, 1 kHz Ton im 2-Hz-Rhythmus |
| Option: Temperatur | nicht umgesetzt, siehe Ausblick |

### 1.2 Hardware

**Arty A7-35T** (Xilinx Artix-7, `xc7a35ticsg324-1L`)

- 100 MHz Quarzoszillator an Pin E3 – daraus werden alle internen Takte abgeleitet
- 4 Schiebeschalter, 4 Taster, 4 einzelne LEDs, 4 RGB-LEDs
- vier Pmod-Anschlüsse JA…JD (je 2×6 Pins, 3,3 V)
- separater RESET-Taster an `ck_rst` (C2), **aktiv low**

**Pmod SSD** (Digilent, zwei Ziffern)

- Common-Cathode-Anzeige mit Treibertransistoren, Segmente werden **aktiv high** angesteuert
- zwei getrennte 6-Pin-Header:
  - J1: `AA`, `AB`, `AC`, `AD`, GND, VCC
  - J2: `AE`, `AF`, `AG`, `C`, GND, VCC
- `C` ist der Digit-Select; beide Ziffern teilen sich die Segmentleitungen
- Der Dezimalpunkt ist auf dem Modul nicht beschaltet.
- Das Datenblatt fordert eine Umschaltfrequenz von mindestens 50 Hz, damit das
  Auge durch Trägheit (Persistence of Vision) beide Ziffern gleichzeitig sieht.

### 1.3 Theorie 7-Segment-Anzeige

Eine Ziffer besteht aus sieben LEDs `a`…`g`. Im Design gilt die Zuordnung
`seg(0) = a`, `seg(1) = b`, …, `seg(6) = g`.

| Ziffer | g f e d c b a | Ziffer | g f e d c b a |
|---|---|---|---|
| 0 | `0111111` | 5 | `1101101` |
| 1 | `0000110` | 6 | `1111101` |
| 2 | `1011011` | 7 | `0000111` |
| 3 | `1001111` | 8 | `1111111` |
| 4 | `1100110` | 9 | `1101111` |

Da zwei Ziffern an einem gemeinsamen Segmentbus hängen, ist ein **Zeitmultiplex**
nötig: `ssd_driver` schaltet mit 1 kHz zwischen den Ziffern um, jede Ziffer wird
also mit 500 Hz aufgefrischt.

### 1.4 Pin-Belegung

Die Pmod SSD stecken auf den **unteren Reihen** (Pins 7–10) von JA/JB bzw. JC/JD.
Die oberen Reihen bleiben dadurch frei und nehmen den Buzzer auf.

| Signal | Funktion | Pin |
|---|---|---|
| `CLK100MHZ` | Systemtakt 100 MHz | E3 |
| `ck_rst` | RESET-Taster (aktiv low) | C2 |
| `sw[0]` | Sekundenanzeige | A8 |
| `sw[1]` | Zeit stellen | C11 |
| `sw[2]` | Weckzeit stellen | C10 |
| `sw[3]` | Wecker scharf | A10 |
| `btn[0]` | Stunden + | D9 |
| `btn[1]` | Stunden − | C9 |
| `btn[2]` | Minuten + | B9 |
| `btn[3]` | Minuten − | B8 |
| `led[0..3]` | Status / Weckanzeige | H5, J5, T9, T10 |
| `seg_l[0..3]` | SSD #1 `AA`…`AD` | D13, B18, A18, K16 (JA 7–10) |
| `seg_l[4..6]`, `dsel_l` | SSD #1 `AE`,`AF`,`AG`,`C` | J17, J18, K15, J15 (JB 7–10) |
| `seg_r[0..3]` | SSD #2 `AA`…`AD` | U14, V14, T13, U13 (JC 7–10) |
| `seg_r[4..6]`, `dsel_r` | SSD #2 `AE`,`AF`,`AG`,`C` | E2, D2, H2, G2 (JD 7–10) |
| `buzzer_o` | akustisches Signal | G13 (JA Pin 1) |

---

## 2. Entwurf

Das Blockschaltbild, die Modulübersicht und das Zustandsdiagramm stehen in
[blockschaltbild.md](blockschaltbild.md).

### 2.1 Entwurfsentscheidungen

- **Nur ein Taktbereich.** Der 100-MHz-Takt wird nicht geteilt, sondern über
  `tick_gen` in Taktfreigaben (Clock Enables) umgesetzt. Dadurch gibt es keine
  abgeleiteten Takte, keine Clock-Domain-Crossings und keine zusätzlichen
  Timing-Constraints.
- **Zeit intern binär.** Stunden, Minuten und Sekunden werden als `unsigned(5:0)`
  geführt; die Umwandlung in BCD passiert erst unmittelbar vor der Anzeige in
  `display_mux`. Das spart Logik gegenüber durchgehenden BCD-Zählern.
- **Generic `CLK_HZ`.** Alle zeitabhängigen Module bekommen die Taktfrequenz als
  Generic. In der Simulation wird sie auf 100 bzw. 1000 verkleinert, damit eine
  simulierte Minute Mikrosekunden statt Minuten dauert.
- **Betriebsarten über Schalter statt Automat.** Die Modusauswahl ist ein reiner
  Dekoder; der einzige Automat sitzt dort, wo er gebraucht wird – im Wecker.

### 2.2 Bedienkonzept

| Bedienelement | Wirkung |
|---|---|
| RESET | Uhr auf 00:00:00, Weckzeit auf 07:00 |
| `sw0` | Anzeige MM:SS statt HH:MM |
| `sw1` | Zeit stellen – Uhr steht, Sekunden werden genullt |
| `sw2` | Weckzeit stellen (hat Vorrang vor `sw1`) |
| `sw3` | Wecker scharf |
| `btn0` / `btn1` | Stunden + / − |
| `btn2` / `btn3` | Minuten + / − |
| beliebiger Taster bei Alarm | Alarm quittieren |

Tasten halten löst nach 250 ms eine automatische Wiederholung aus, damit man
nicht 59-mal drücken muss.

Die LEDs zeigen im Normalbetrieb `led0` = Wecker scharf, `led1` = Zeit stellen,
`led2` = Weckzeit stellen, `led3` = 1-Hz-Herzschlag (Sekundentakt sichtbar).
Während des Alarms blinken alle vier LEDs mit 2 Hz.

---

## 3. Implementierung

### 3.1 Modulübersicht

| Datei | Aufgabe |
|---|---|
| `src/clock_pkg.vhd` | Typen `bcd_t`/`bcd2_t`, Funktionen `max_nat`, `to_bcd2` |
| `src/tick_gen.vhd` | generischer Vorteiler, 1-Takt-Puls alle `DIV` Takte |
| `src/debounce.vhd` | 2-FF-Synchronisation, 10 ms Entprellung, Auto-Repeat |
| `src/seg7_decoder.vhd` | BCD → Segmentmuster (aktiv high), Austastung |
| `src/ssd_driver.vhd` | Zeitmultiplex einer zweistelligen Anzeige |
| `src/clock_core.vhd` | Zeitbasis 24 h, Stellfunktion |
| `src/alarm_core.vhd` | Weckzeitregister + Automat `IDLE/RINGING/SILENCED` |
| `src/buzzer.vhd` | 1-kHz-Rechteckton, 2-Hz-Beep-Muster |
| `src/display_mux.vhd` | Anzeigeauswahl, Wandlung binär → BCD |
| `src/wecker_top.vhd` | Top-Level, strukturelle Verdrahtung |
| `constraints/arty_a7_35_wecker.xdc` | Pin-Constraints und Taktdefinition |
| `scripts/create_project.tcl` | legt das Vivado-Projekt reproduzierbar an |

### 3.2 Zentrale Mechanismen

**Sekundentakt.** `tick_gen` mit `DIV = CLK_HZ` liefert genau einen Puls pro
Sekunde. Im Stellmodus wird der Vorteiler über `clr` zurückgesetzt – die Uhr
startet nach dem Stellen also mit einer vollen Sekunde.

**Entprellung.** Ein Taster prellt einige Millisekunden. `debounce` übernimmt
einen neuen Pegel erst, wenn er 10 ms stabil anliegt, und erzeugt daraus einen
Ein-Takt-Puls – so zählt ein Druck genau einen Schritt weiter.

**Stellen ohne Übertrag.** Beim Verstellen der Minuten wird bewusst *kein*
Übertrag auf die Stunden erzeugt; das entspricht dem Verhalten handelsüblicher
Uhren und verhindert, dass man die Stunde beim Minutenstellen verliert.

**Alarmlogik.** Siehe Zustandsdiagramm. Wichtig ist der Zustand `SILENCED`:
ohne ihn würde der Alarm nach dem Quittieren sofort wieder anspringen, weil die
Weckbedingung für die volle Minute erfüllt bleibt.

### 3.3 Projekt anlegen

```powershell
cd prj_final
vivado -mode batch -source scripts/create_project.tcl
```

Das Skript erzeugt `prj_final/vivado/wecker.xpr`, fügt Quellen, Simulations-
dateien und Constraints hinzu und setzt die Top-Module.

---

## 4. Test

### 4.1 Simulation

| Testbench | Prüft |
|---|---|
| `sim/tb_seg7_decoder.vhd` | alle Segmentmuster 0…9 und die Austastung |
| `sim/tb_clock_core.vhd` | Sekundentakt, Übertrag s→min→h, Tageswechsel 23:59→00:00, Einfrieren im Stellmodus, Minuten-Dekrement ohne Stundenübertrag |
| `sim/tb_wecker_top.vhd` | Weckzeit stellen, Alarm zur Weckzeit, akustisches Signal, Quittieren per Taster, Status-LED |

Die Testbenches setzen `CLK_HZ` auf 100 bzw. 1000. Eine simulierte Stunde
dauert damit Millisekunden statt Stunden, ohne dass der RTL-Code verändert wird.

Ausführen in Vivado: *Flow Navigator → Simulation → Run Simulation →
Run Behavioral Simulation* (Top der Simulation ggf. über
*Set as Top* im `sim_1`-Fileset umstellen).

### 4.2 Test auf dem Board

1. Bitstream erzeugen und laden.
2. RESET drücken → Anzeige `00` `00`, `led3` blinkt im Sekundentakt.
3. `sw0` einschalten → Anzeige wechselt auf Minuten/Sekunden.
4. `sw1` einschalten → Uhr bleibt stehen, `btn0..btn3` stellen die Zeit.
5. `sw2` einschalten → Anzeige zeigt die Weckzeit, Taster stellen sie.
6. `sw3` einschalten → bei Erreichen der Weckzeit blinken alle LEDs und der
   Buzzer piept; ein beliebiger Tastendruck quittiert.

### 4.3 Fehlerbilder und Abhilfe

| Beobachtung | Ursache | Abhilfe |
|---|---|---|
| Ziffern vertauscht | Digit-Select invertiert | `dsel <= not sel;` in `ssd_driver` |
| Segmente invers (Geisterbild) | Anzeige doch aktiv low | `seg` in `seg7_decoder` invertieren |
| Anzeige flimmert | Refresh zu langsam | `REFRESH_HZ` erhöhen |
| Taster zählt mehrfach | Prellen | `DEBOUNCE_MS` erhöhen |
| Uhr geht nach | falscher `CLK_HZ`-Wert | Generic prüfen |

---

## 5. Ausblick

- **Temperaturanzeige** über den im Artix-7 integrierten XADC: Der Systemmonitor
  liefert die Chiptemperatur ohne externen Sensor. Alternativ ein Pmod TMP2 am
  freien oberen Teil von JC/JD. Die Anzeige ließe sich über einen weiteren
  Schalter auf dieselben Displays legen.
- **Snooze-Funktion**: zusätzlicher Zustand im Automaten, der den Alarm um
  fünf Minuten verschiebt.
- **12-Stunden-Format** mit AM/PM-Anzeige über eine der RGB-LEDs.

---

## Anhang

### A. Quellenverzeichnis

- Digilent: Arty A7 Reference Manual und Master-XDC
- Digilent: Pmod SSD Reference Manual (Common Cathode, zwei 6-Pin-Header,
  Umschaltung ≥ 50 Hz)
- Vorlesungsfolien „Digitale Schaltungstechnik mit Labor", Prof. Dr.-Ing. R. Gessler

### B. Dateistruktur

```text
prj_final/
├── src/            10 VHDL-Module
├── sim/            3 Testbenches
├── constraints/    arty_a7_35_wecker.xdc
├── scripts/        create_project.tcl
└── doc/            blockschaltbild.md, dokumentation.md, praesentation.md
```

Der vollständige VHDL-Code befindet sich in `src/` und `sim/` und gehört als
Anhang in den abzugebenden Bericht.
