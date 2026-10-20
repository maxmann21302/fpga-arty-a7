# Blockschaltbild - Wecker (vereinfacht)

Das Blockschaltbild zeigt die wesentlichen Funktionseinheiten des gesamten
Weckers und ihre Signalverbindungen. Mehrere VHDL-Module sind jeweils zu einem
Funktionsblock zusammengefasst.

Eine bearbeitbare Version des Blockschaltbilds ist in
[blockschaltbild_simple.drawio](./blockschaltbild_simple.drawio) verfügbar.

```mermaid
%%{init: {"flowchart": {"curve": "linear"}}}%%
flowchart LR
    INPUT["Taster und Schalter"]
    CLK["100-MHz-Takt und Reset"]

    subgraph FPGA["FPGA - Digitaler Wecker"]
        CTRL["Bedienung und Steuerung"]
        CLOCK["Uhr<br/>Stunden, Minuten, Sekunden"]
        ALARM["Wecklogik<br/>Weckzeit speichern und vergleichen"]
        DISPLAY["Anzeigeaufbereitung"]
        SIGNAL["Signalisierung<br/>Ton und LED-Ansteuerung"]
    end

    SSD["2 x zweistellige<br/>7-Segment-Anzeige"]
    BUZZER["Buzzer"]
    LED["Status- und Alarm-LEDs"]

    INPUT -->|Bedieneingaben| CTRL
    CLK -->|gemeinsam fuer alle Funktionsbloecke| FPGA
    CTRL -->|Uhrzeit stellen| CLOCK
    CTRL -->|Weckzeit stellen, aktivieren, quittieren| ALARM
    CLOCK -->|aktuelle Uhrzeit| ALARM
    CLOCK -->|aktuelle Uhrzeit| DISPLAY
    ALARM -->|Weckzeit| DISPLAY
    CTRL -->|Anzeigemodus| DISPLAY
    ALARM -->|Alarm aktiv| CTRL
    ALARM -->|Alarm aktiv| SIGNAL
    CTRL -->|Betriebsstatus| SIGNAL
    CLOCK -->|Sekundentakt| SIGNAL
    DISPLAY -->|Segment- und Stellensignale| SSD
    SIGNAL -->|Tonsignal| BUZZER
    SIGNAL -->|LED-Signale| LED
```

Die Umrandung kennzeichnet die FPGA-Systemgrenze; die aeusseren Bloecke stellen
Ein- und Ausgabeelemente dar. Die Pfeile zeigen den Signalfluss, keinen zeitlichen
Programmablauf. Takt und Reset versorgen alle internen Funktionsbloecke; ihre
einzelnen Verbindungen sind zur besseren Uebersicht zusammengefasst.

Die Anzeige gibt je nach Betriebsart Uhrzeit, Minuten/Sekunden oder Weckzeit aus.
Bei einem Alarm steuert die Signalisierung Buzzer und blinkende LEDs an. Die
Rueckmeldung an die Steuerung sorgt dafuer, dass ein Tastendruck den Alarm
quittiert, ohne dabei die Uhr- oder Weckzeit zu verstellen.