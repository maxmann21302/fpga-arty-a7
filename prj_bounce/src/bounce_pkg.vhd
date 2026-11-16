----------------------------------------------------------------------------------
-- Projekt      : Prell-Oszilloskop (Pmod OLEDrgb an JD)
-- Modul        : bounce_pkg
-- Beschreibung : Gemeinsame Konstanten, Zeitbasis-Tabelle (fuer 100 MHz)
----------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

package bounce_pkg is

    constant SAMPLES  : positive := 96;      -- ein Abtastwert pro Displayspalte
    constant PRE_TRIG : positive := 10;      -- Displayspalte des Triggers
    constant DIV_PX   : positive := 10;      -- Pixel pro Rasterteilung

    subtype period_t is natural range 2 to 100_000;

    constant TB_COUNT   : positive := 13;
    constant TB_DEFAULT : natural  := 9;     -- 1 ms/div

    type period_arr_t is array (0 to TB_COUNT - 1) of period_t;
    type label_arr_t  is array (0 to TB_COUNT - 1) of string(1 to 9);

    -- Takte pro Abtastwert = (Zeit pro Teilung / DIV_PX) / 10 ns
    constant TB_PERIOD : period_arr_t := (
        10, 20, 50, 100, 200, 500, 1_000, 2_000, 5_000, 10_000, 20_000, 50_000, 100_000
    );

    constant TB_LABEL : label_arr_t := (
        "1us/div  ", "2us/div  ", "5us/div  ", "10us/div ", "20us/div ", "50us/div ",
        "100us/div", "200us/div", "500us/div", "1ms/div  ", "2ms/div  ", "5ms/div  ",
        "10ms/div "
    );

end package bounce_pkg;
