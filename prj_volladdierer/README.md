# Volladdierer fuer den Arty A7

Der Volladdierer addiert die drei 1-Bit-Eingaenge `x`, `y` und `cin`.
`sum` ist das Summenbit, `cout` der ausgehende Uebertrag. Es gilt:

$$
x + y + cin = sum + 2 \cdot cout
$$

## 1. Wahrheitstabelle

| x | y | cin | sum | cout |
|---|---|-----|-----|------|
| 0 | 0 | 0   | 0   | 0    |
| 0 | 0 | 1   | 1   | 0    |
| 0 | 1 | 0   | 1   | 0    |
| 0 | 1 | 1   | 0   | 1    |
| 1 | 0 | 0   | 1   | 0    |
| 1 | 0 | 1   | 0   | 1    |
| 1 | 1 | 0   | 0   | 1    |
| 1 | 1 | 1   | 1   | 1    |

Beispiel: Bei `x = 1`, `y = 1` und `cin = 1` ist die Summe dezimal 3,
also binaer `11`. Damit sind `cout = 1` und `sum = 1`.

## 2. Boolesche Gleichungen

Notation: $\neg$ bedeutet NICHT, $\land$ bedeutet UND, $\lor$ bedeutet
ODER und $\oplus$ bedeutet XOR (exklusives ODER).

Fuer jeden Ausgang werden die Zeilen mit Ausgangswert 1 als UND-Terme
aufgeschrieben und mit ODER verknuepft. Ein Eingang mit Wert 0 wird dabei
negiert. Das ergibt die disjunktive Normalform.

### Summenbit

`sum` ist fuer die Eingangskombinationen `001`, `010`, `100` und `111` gleich 1:

$$
\begin{aligned}
sum ={}& (\neg x \land \neg y \land cin) \\
       &\lor (\neg x \land y \land \neg cin) \\
       &\lor (x \land \neg y \land \neg cin) \\
       &\lor (x \land y \land cin)
\end{aligned}
$$

Der Ausgang ist genau dann 1, wenn eine ungerade Anzahl der Eingaenge 1 ist.
Das entspricht der XOR-Verknuepfung:

$$
\boxed{sum = x \oplus y \oplus cin}
$$

### Uebertrag

`cout` ist fuer die Eingangskombinationen `011`, `101`, `110` und `111` gleich 1:

$$
\begin{aligned}
cout ={}& (\neg x \land y \land cin) \\
        &\lor (x \land \neg y \land cin) \\
        &\lor (x \land y \land \neg cin) \\
        &\lor (x \land y \land cin)
\end{aligned}
$$

Der Term fuer `111` darf bei einer ODER-Verknuepfung mehrfach verwendet werden.
Durch Paarbildung mit jeder der drei anderen Zeilen entfaellt jeweils ein Eingang:

$$
\begin{aligned}
(\neg x \land y \land cin) \lor (x \land y \land cin) &= y \land cin \\
(x \land \neg y \land cin) \lor (x \land y \land cin) &= x \land cin \\
(x \land y \land \neg cin) \lor (x \land y \land cin) &= x \land y
\end{aligned}
$$

Damit folgt:

$$
\boxed{cout = (x \land y) \lor (x \land cin) \lor (y \land cin)}
$$

Der Uebertrag ist also 1, wenn mindestens zwei Eingaenge 1 sind.

## 3. Umsetzung in VHDL

Die Operatoren werden direkt uebersetzt: $\oplus$ zu `xor`, $\land$ zu `and`
und $\lor$ zu `or`. Daraus entstehen die beiden Zuweisungen in
[volladdierer.vhd](volladdierer.vhd):

```vhdl
sum  <= x xor y xor cin;
cout <= (x and y) or (x and cin) or (y and cin);
```

Die Entity in derselben Datei legt die Schnittstelle fest: `x`, `y` und `cin`
sind Eingaenge; `sum` und `cout` sind Ausgaenge. Alle Ports haben den Typ
`STD_LOGIC`. Die Schaltung ist rein kombinatorisch und benoetigt keinen Takt.

## 4. Zuordnung auf dem Arty A7

Die Datei [volladdierer.xdc](volladdierer.xdc) verbindet die Ports mit den
Schaltern und LEDs des Arty A7-35T:

| Port | Richtung | Bedienelement | FPGA-Pin |
|------|----------|---------------|----------|
| x    | Eingang  | SW0           | A8       |
| y    | Eingang  | SW1           | C11      |
| cin  | Eingang  | SW2           | C10      |
| sum  | Ausgang  | LED0          | H5       |
| cout | Ausgang  | LED1          | J5       |

In Vivado `volladdierer` als Top-Modul setzen und die XDC-Datei als Constraints
hinzufuegen. Mit den drei Schaltern lassen sich alle acht Zeilen der
Wahrheitstabelle einstellen; die LEDs zeigen das Ergebnis an.
