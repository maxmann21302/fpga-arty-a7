---
marp: true
theme: default
paginate: true
header: 'Digitale Uhr / Wecker – Arty A7-35T'
---

# Digitale Uhr / Wecker

**Labor Digitale Schaltungstechnik**

FPGA-Design in VHDL auf dem Arty A7-35T
mit zwei Pmod SSD

---

## Agenda

1. Aufgabenstellung
2. Hardware
3. Entwurf – Blockschaltbild
4. Der Weck-Automat
5. Implementierung in VHDL
6. Verifikation: Simulation und Board
7. Ergebnis und Ausblick

---

## 1. Aufgabenstellung

- **Uhr**
  - Stunden und Minuten auf 7-Segment-Anzeigen
  - Schalter blendet die Sekunden ein
  - Zeit stellen über Pushbuttons +/−
- **Wecker**
  - Weckzeit stellen über Pushbuttons +/−
  - Signalausgabe **optisch** (LEDs) und **akustisch**
- Option: Temperaturanzeige

---

## 2. Hardware

| Baustein | Eigenschaft |
|---|---|
| Arty A7-35T | Artix-7, 100 MHz Oszillator |
| Bedienung | 4 Schalter, 4 Taster, RESET |
| Anzeige | 2× Pmod SSD = 4 Ziffern |
| Signal | LD4…LD7 + Buzzer an JA Pin 1 |

- Pmod SSD: **Common Cathode**, Segmente aktiv high
- zwei 6-Pin-Header je Modul (`J1`/`J2`) → JA+JB bzw. JC+JD, jeweils **untere Reihe**
- links (Stunden) auf JC/JD, rechts (Minuten/Sekunden) auf JA/JB
- gemeinsamer Segmentbus → **Zeitmultiplex nötig** (≥ 50 Hz)

---

## 3. Entwurf – Blockschaltbild

```text
 sw/btn ──▶ debounce ──▶ Mode-Dekoder
                             │
     ┌───────────────────────┼───────────────────────┐
     ▼                       ▼                       ▼
 clock_core             alarm_core               display_mux
 hh:mm:ss (24 h)        Weckzeit + FSM           Auswahl + bin→BCD
     │                       │                       │
     │                       ├──▶ buzzer ──▶ akustisch
     │                       └──▶ LED-Logik ─▶ optisch
     └───────────────────────────────────────▶ 2× ssd_driver ─▶ Pmod SSD
```

Alle zeitabhängigen Module nutzen denselben Vorteiler `tick_gen`.

---

## 3b. Entwurfsentscheidungen

- **Ein einziger Taktbereich** – `tick_gen` erzeugt Clock Enables statt
  abgeleiteter Takte → keine Clock-Domain-Probleme
- **Zeit binär, BCD erst vor der Anzeige** → weniger Logik
- **Generic `CLK_HZ`** in allen Modulen → Simulation läuft 100 000-fach schneller
- Modusauswahl als Dekoder, Automat nur dort wo nötig: im Wecker

---

## 4. Der Weck-Automat

```text
            match_min & ss=0
   ┌────────┐ ──────────────▶ ┌──────────┐
   │  IDLE  │                 │ RINGING  │
   └────────┘ ◀────────────── └──────────┘
        ▲      match_min = 0        │ stop (Taste)
        │                           ▼
        │      match_min = 0   ┌──────────┐
        └───────────────────── │ SILENCED │
                               └──────────┘
```

- `match_min = (hh = al_hh) und (mm = al_mm)`
- `SILENCED` verhindert sofortiges Wiederanspringen in derselben Minute
- Auto-Stopp nach einer Minute

---

## 5. Implementierung – Modulstruktur

| Modul | Aufgabe |
|---|---|
| `clock_pkg` | Typen, `max_nat`, `to_bcd2` |
| `tick_gen` | generischer Vorteiler |
| `debounce` | Entprellung + Auto-Repeat |
| `seg7_decoder` | BCD → Segmente |
| `ssd_driver` | Zeitmultiplex 2 Ziffern |
| `clock_core` | Zeitbasis 24 h |
| `alarm_core` | Weckzeit + Automat |
| `buzzer` | Ton + Beep-Muster |
| `display_mux` | Anzeigeauswahl |
| `wecker_top` | strukturelles Top-Level |

---

## 5b. Codeausschnitt: Zeitbasis

```vhdl
u_sec : entity work.tick_gen
    generic map (DIV => CLK_HZ)
    port map (clk => clk, rst => rst,
              en  => run, clr => set_mode, tick => tick);
```

- `DIV = CLK_HZ` → genau ein Puls pro Sekunde
- `set_mode` hält die Uhr an **und** nullt den Vorteiler
- in der Simulation ist `CLK_HZ = 100` → eine Sekunde dauert 1 µs

---

## 6. Verifikation – Simulation

| Testbench | Inhalt |
|---|---|
| `tb_seg7_decoder` | alle Muster 0…9, Austastung |
| `tb_clock_core` | Überträge, Tageswechsel 23:59 → 00:00, Stellmodus |
| `tb_wecker_top` | Weckzeit stellen, Alarm, Buzzer, Quittieren |

Alle Prüfungen als `assert` – die Simulation meldet Fehler selbst,
kein manuelles Ablesen von Wellenformen nötig.

---

## 6b. Verifikation – Board

1. RESET → `00 00`, Herzschlag-LED im Sekundentakt
2. `sw0` → Minuten/Sekunden
3. `sw1` + Taster → Zeit stellen
4. `sw2` + Taster → Weckzeit stellen
5. `sw3` → scharf; zur Weckzeit blinken die LEDs und der Buzzer piept
6. beliebiger Taster → Alarm quittiert

---

## 7. Ergebnis

- Vollständig synchrones Design, ein Taktbereich, keine Timing-Verletzungen
- Modularer, wiederverwendbarer Aufbau – `tick_gen` wird viermal instanziiert
- Komplette Funktion der Aufgabenstellung umgesetzt
- Selbstprüfende Testbenches

**Ausblick**

- Temperatur über XADC oder Pmod TMP2
- Snooze als zusätzlicher Zustand im Automaten
- 12-Stunden-Format mit AM/PM über eine RGB-LED

---

# Fragen?

Quellen: Digilent Arty A7 Reference Manual, Pmod SSD Reference Manual,
Vorlesungsskript Digitale Schaltungstechnik
