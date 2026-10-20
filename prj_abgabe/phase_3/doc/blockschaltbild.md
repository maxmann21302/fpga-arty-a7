# Blockschaltbild – Digitale Uhr / Wecker

## 1. Gesamt-Architektur (Phase I + II)

```mermaid
flowchart LR
    subgraph IN["Eingänge Arty A7-35T"]
        CLK["CLK100MHZ<br/>100 MHz (E3)"]
        RSTB["RESET-Taster<br/>ck_rst (C2, aktiv low)"]
        SW["sw0..sw3<br/>Betriebsart"]
        BTN["btn0..btn3<br/>+/- Eingabe"]
    end

    subgraph CORE["wecker_top"]
        SYNC["Reset-<br/>Synchronizer"]
        DB["4x debounce<br/>Entprellung + Auto-Repeat"]
        MODE["Mode-Dekoder<br/>Priorität sw2 > sw1 > sw0"]
        CLKC["clock_core<br/>hh:mm:ss, 24 h"]
        ALC["alarm_core<br/>Weckzeit + FSM"]
        DMUX["display_mux<br/>Auswahl + bin→BCD"]
        SSDL["ssd_driver<br/>linke Anzeige"]
        SSDR["ssd_driver<br/>rechte Anzeige"]
        BUZ["buzzer<br/>1 kHz / 2 Hz Beep"]
        LEDL["LED-Logik<br/>Status / Blinken"]
    end

    subgraph OUT["Ausgänge"]
        D1["Pmod SSD links<br/>JC + JD (Stunden)"]
        D2["Pmod SSD rechts<br/>JA + JB (Minuten/Sekunden)"]
        LEDS["LD4..LD7<br/>optisches Signal"]
        SPK["Buzzer<br/>JA Pin 1 (G13)"]
    end

    CLK --> CORE
    RSTB --> SYNC --> CORE
    SW --> MODE
    BTN --> DB --> MODE

    MODE -->|set_time, +/-| CLKC
    MODE -->|set_alarm, +/-, enable, stop| ALC
    CLKC -->|hh, mm, ss| ALC
    CLKC -->|hh, mm, ss| DMUX
    ALC -->|al_hh, al_mm| DMUX
    ALC -->|ringing| BUZ
    ALC -->|ringing| LEDL

    DMUX -->|2x BCD| SSDL --> D1
    DMUX -->|2x BCD| SSDR --> D2
    LEDL --> LEDS
    BUZ --> SPK
```

## 2. Hilfsmodule (Wiederverwendung)

```mermaid
flowchart TD
    TG["tick_gen<br/>generic DIV"] --> C1["clock_core: 1 Hz"]
    TG --> C2["ssd_driver: 1 kHz Refresh"]
    TG --> C3["buzzer: Ton + Beep"]
    TG --> C4["wecker_top: 2 Hz Blinken"]
    S7["seg7_decoder"] --> C2
    PKG["clock_pkg<br/>max_nat, to_bcd2"] --> ALLE["alle Module"]
```

## 3. Automat `alarm_core`

```mermaid
stateDiagram-v2
    [*] --> IDLE
    IDLE --> RINGING : match_min = 1 und ss = 0
    RINGING --> SILENCED : stop (Tastendruck)
    RINGING --> IDLE : match_min = 0 (Minute vorbei)
    SILENCED --> IDLE : match_min = 0
    RINGING --> IDLE : enable = 0
    SILENCED --> IDLE : enable = 0

    note right of RINGING
        ringing = 1
        LEDs blinken 2 Hz
        Buzzer piept
    end note
```

`match_min = (hh = al_hh) und (mm = al_mm)`

Der Alarm klingelt höchstens eine Minute und schaltet sich dann selbst ab.
Ein Tastendruck während des Klingelns verstellt die Zeit **nicht**, sondern
quittiert nur den Alarm (Zustand `SILENCED`), bis die Weckminute vorbei ist.

## 4. Anzeige-Auswahl (`display_mux`)

| Priorität | Bedingung | linke Anzeige (JC/JD) | rechte Anzeige (JA/JB) |
|---|---|---|---|
| 1 | `sw2 = 1` | Weckzeit Stunden | Weckzeit Minuten |
| 2 | `sw1 = 1` | Stunden | Minuten |
| 3 | `sw0 = 1` | Minuten | Sekunden |
| 4 | sonst | Stunden | Minuten |

## 5. Zeitmultiplex einer Anzeige (`ssd_driver`)

```mermaid
sequenceDiagram
    participant T as tick_gen (1 kHz)
    participant S as sel (Toggle-FF)
    participant D as seg7_decoder
    participant P as Pmod SSD
    T->>S: tick
    S->>D: sel = 0 → Einerstelle
    D->>P: seg(6:0), dsel = 0
    T->>S: tick
    S->>D: sel = 1 → Zehnerstelle
    D->>P: seg(6:0), dsel = 1
```

Jede Ziffer wird mit 500 Hz aufgefrischt – deutlich über den vom Datenblatt
geforderten 50 Hz, dadurch flimmerfreie Darstellung (Persistence of Vision).
