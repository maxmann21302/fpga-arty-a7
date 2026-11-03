# VHDL: Entity, Architecture und Volladdierer

## 1. Entity und Architecture

Eine VHDL-Schaltung besteht meistens aus einer **Entity** und einer
**Architecture**:

- Die `entity` beschreibt die Schnittstelle der Schaltung.
- Die `architecture` beschreibt die innere Funktion oder Struktur.

### `generic` und `port`

In einer Entity werden zwei wichtige Bereiche unterschieden:

- `generic`: Konfigurationsparameter, die normalerweise zur
  Compile-/Elaborationszeit festgelegt werden.
- `port`: Ein- und Ausgaenge der Schaltung, ueber die im Betrieb Signale
  uebertragen werden.

```vhdl
entity beispiel is
    generic (
        WIDTH : positive := 8
    );
    port (
        clk : in  std_logic;
        q   : out std_logic_vector(WIDTH - 1 downto 0)
    );
end entity beispiel;
```

`generic` beschreibt also einstellbare Eigenschaften, waehrend `port` die
elektrische Schnittstelle beschreibt.

## 2. OR-Gatter mit zwei Eingaengen

```vhdl
library ieee;
use ieee.std_logic_1164.all;

entity or2 is
    port (
        a : in  std_logic;
        b : in  std_logic;
        y : out std_logic
    );
end entity or2;

architecture rtl of or2 is
begin
    y <= a or b;
end architecture rtl;
```

Der Ausgang `y` ist `1`, sobald mindestens einer der beiden Eingaenge `a` oder
`b` `1` ist.

## 3. Half Adder

Ein Half Adder addiert zwei einzelne Bits. Er besitzt keinen Eingang fuer
einen vorherigen Uebertrag.

```vhdl
library ieee;
use ieee.std_logic_1164.all;

entity half_adder is
    port (
        a     : in  std_logic;
        b     : in  std_logic;
        sum   : out std_logic;
        carry : out std_logic
    );
end entity half_adder;

architecture rtl of half_adder is
begin
    sum   <= a xor b;
    carry <= a and b;
end architecture rtl;
```

| a | b | sum | carry |
|---|---|-----|-------|
| 0 | 0 | 0   | 0     |
| 0 | 1 | 1   | 0     |
| 1 | 0 | 1   | 0     |
| 1 | 1 | 0   | 1     |

- `sum` ist `1`, wenn genau einer der Eingaenge `1` ist.
- `carry` ist `1`, wenn beide Eingaenge `1` sind.
- Beide Zuweisungen sind nebenlaeufig und beschreiben kombinatorische Logik.

## 4. Volladdierer

Ein Volladdierer addiert drei Bits:

- `a` und `b`: die beiden aktuellen Bits
- `cin`: der Uebertrag von der vorherigen Bitstelle
- `sum`: Summenbit
- `cout`: Uebertrag zur naechsten Bitstelle

Die logischen Gleichungen lauten:

```text
sum  = a xor b xor cin
cout = (a and b) or (a and cin) or (b and cin)
```

Alternativ kann der Uebertrag auch so geschrieben werden:

```text
cout = (a and b) or (cin and (a xor b))
```

Der Volladdierer erzeugt einen Uebertrag, wenn mindestens zwei der drei
Eingaenge `1` sind.

## 5. Volladdierer aus zwei Half Adders und einem OR2

Der strukturelle Aufbau ist:

```text
HA1: a + b             -> sum1, carry1
HA2: sum1 + cin        -> sum,  carry2
OR2: carry1 or carry2  -> cout
```

### Komponentenbasierte Beschreibung

```vhdl
library ieee;
use ieee.std_logic_1164.all;

entity full_adder is
    port (
        a    : in  std_logic;
        b    : in  std_logic;
        cin  : in  std_logic;
        sum  : out std_logic;
        cout : out std_logic
    );
end entity full_adder;

architecture structural of full_adder is

    component half_adder is
        port (
            a     : in  std_logic;
            b     : in  std_logic;
            sum   : out std_logic;
            carry : out std_logic
        );
    end component;

    component or2 is
        port (
            a : in  std_logic;
            b : in  std_logic;
            y : out std_logic
        );
    end component;

    signal sum1   : std_logic;
    signal carry1 : std_logic;
    signal carry2 : std_logic;

begin
    HA1 : half_adder
        port map (
            a     => a,
            b     => b,
            sum   => sum1,
            carry => carry1
        );

    HA2 : half_adder
        port map (
            a     => sum1,
            b     => cin,
            sum   => sum,
            carry => carry2
        );

    OR1 : or2
        port map (
            a => carry1,
            b => carry2,
            y => cout
        );
end architecture structural;
```

Die `component`-Deklarationen geben an, welche Module verwendet werden
koennen. Mit `HA1`, `HA2` und `OR1` werden diese Komponenten instanziiert und
ueber `port map` verbunden.

## 6. Drei Beschreibungsmodelle im Vergleich

### Datenflussmodell

Das Datenflussmodell beschreibt die logischen Gleichungen direkt mit
nebenlaeufigen Signalzuweisungen:

```vhdl
architecture dataflow of full_adder is
begin
    sum  <= a xor b xor cin;
    cout <= (a and b) or (a and cin) or (b and cin);
end architecture dataflow;
```

Es ist kurz und gut fuer einfache kombinatorische Logik geeignet. Die
einzelnen Module oder Gatter sind dabei nicht sichtbar.

### Strukturmodell

Das Strukturmodell beschreibt den Aufbau aus vorhandenen Modulen. Beim
Volladdierer werden zwei Half Adder und ein OR2 miteinander verbunden.

Es zeigt die Hardware-Hierarchie und ist besonders nuetzlich, wenn Module
wiederverwendet oder groessere Schaltungen aus Teilmodulen aufgebaut werden.

### Verhaltensmodell

Das Verhaltensmodell beschreibt, **was** die Schaltung macht, ohne ihren
inneren Aufbau vorzugeben:

```vhdl
architecture behavioral of full_adder is
begin
    process(a, b, cin)
        variable value : std_logic_vector(1 downto 0);
    begin
        value := ('0' & a) + ('0' & b) + ('0' & cin);
        sum    <= value(0);
        cout   <= value(1);
    end process;
end architecture behavioral;
```

Alternativ kann ein `case`-Statement verwendet werden, um alle Zeilen der
Wahrheitstabelle einzeln zu beschreiben.

## 7. Gesamtvergleich

| Modell | Beschreibung | Typische Verwendung |
|---|---|---|
| Datenfluss | Logische Gleichungen | Einfache kombinatorische Logik |
| Struktur | Zusammenschaltung von Modulen/Gattern | Hierarchische und wiederverwendbare Hardware |
| Verhalten | Funktion mit `process`, `if` oder `case` | Komplexere Logik und Algorithmen |

Alle drei Modelle koennen dieselbe Hardware-Funktion beschreiben. Der
Unterschied liegt in der Darstellung: Datenfluss zeigt Gleichungen,
Struktur zeigt Verbindungen und Verhalten zeigt die gewuenschte Funktion.

## 8. Wahrheitstabelle des Volladdierers

| a | b | cin | sum | cout |
|---|---|-----|-----|------|
| 0 | 0 | 0   | 0   | 0    |
| 0 | 0 | 1   | 1   | 0    |
| 0 | 1 | 0   | 1   | 0    |
| 0 | 1 | 1   | 0   | 1    |
| 1 | 0 | 0   | 1   | 0    |
| 1 | 0 | 1   | 0   | 1    |
| 1 | 1 | 0   | 0   | 1    |
| 1 | 1 | 1   | 1   | 1    |

Ein Half Adder reicht nur fuer die erste Bitstelle ohne Eingangscarry. Fuer
weitere Bitstellen wird ein Volladdierer benoetigt, weil er den Uebertrag der
vorherigen Stelle mitverarbeitet.
