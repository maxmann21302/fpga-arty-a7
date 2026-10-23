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

### Uebertrag in XOR-Form (Loesung des Professors)

Die Mehrheitsform oben ist nicht die einzige Darstellung. Aus derselben KDNF
laesst sich auch die XOR-Form herleiten, indem man die Terme anders gruppiert.

#### Schritt 1: Terme zusammenfassen

Die Zeilen `110` und `111` unterscheiden sich nur in `cin`.
Deshalb faellt `cin` beim Zusammenfassen weg:

$$
(x \land y \land \neg cin) \lor (x \land y \land cin)
= x \land y \land (\neg cin \lor cin)
= x \land y
$$

#### Schritt 2: cin ausklammern

Bei den verbleibenden Zeilen `011` und `101` ist `cin` jeweils 1.
Man kann es ausklammern:

$$
(\neg x \land y \land cin) \lor (x \land \neg y \land cin)
= cin \land \bigl((\neg x \land y) \lor (x \land \neg y)\bigr)
$$

#### Schritt 3: XOR erkennen

Der Ausdruck in der Klammer ist genau die Definition von XOR:
Er ist 1, wenn `x` und `y` unterschiedlich sind.

$$
(\neg x \land y) \lor (x \land \neg y) = x \oplus y
$$

Die ODER-Verknuepfung beider Gruppen ergibt daher:

$$
\boxed{cout = (x \land y) \lor \bigl(cin \land (x \oplus y)\bigr)}
$$

Anschaulich gibt es zwei Faelle fuer einen Uebertrag:

- `x` und `y` sind beide 1: Schon ihre Addition erzeugt einen Uebertrag,
  unabhaengig von `cin`.
- Genau einer der Eingaenge `x` und `y` ist 1: Ein Uebertrag entsteht nur,
  wenn auch `cin` gleich 1 ist.

Der Term `cin and (x xor y)` allein erfasst nur den zweiten Fall.
Beide vereinfachten Formen sind fuer die binaeren Werte 0 und 1 gleichwertig;
sie sind keine KDNF mehr, da ihre UND-Terme nicht alle Eingaenge enthalten
beziehungsweise XOR verwendet wird.

## 3. Umsetzung in VHDL

Die Operatoren werden direkt uebersetzt: $\oplus$ zu `xor`, $\land$ zu `and`
und $\lor$ zu `or`. Daraus entstehen die beiden Zuweisungen in
[volladdierer.vhd](volladdierer.vhd):

```vhdl
sum  <= x xor y xor cin;
cout <= (x and y) or (x and cin) or (y and cin);
```

Alternativ kann die Zuweisung fuer `cout` durch die hergeleitete XOR-Form
ersetzt werden. Dies ist die Loesung des Professors:

```vhdl
cout <= (x and y) or (cin and (x xor y));
```

Beide Varianten liefern fuer alle acht Zeilen der Wahrheitstabelle dieselben
Ausgaenge. Die vorhandene VHDL-Datei verwendet weiterhin die Mehrheitsform.

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
