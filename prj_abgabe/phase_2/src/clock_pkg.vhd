----------------------------------------------------------------------------------
-- Projekt      : Digitale Uhr / Wecker (Labor Digitale Schaltungstechnik)
-- Modul        : clock_pkg
-- Beschreibung : Gemeinsame Typen und Hilfsfunktionen
----------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

package clock_pkg is

    subtype bcd_t is unsigned(3 downto 0);

    type bcd2_t is record
        tens : bcd_t;
        ones : bcd_t;
    end record;

    function max_nat (a : natural; b : natural) return natural;
    function to_bcd2 (v : unsigned) return bcd2_t;

end package clock_pkg;


package body clock_pkg is

    function max_nat (a : natural; b : natural) return natural is
    begin
        if a > b then
            return a;
        else
            return b;
        end if;
    end function;

    -- Division durch die Konstante 10 wird von der Synthese als Logik aufgeloest
    function to_bcd2 (v : unsigned) return bcd2_t is
        variable n : natural;
        variable r : bcd2_t;
    begin
        n      := to_integer(v);
        r.tens := to_unsigned((n / 10) mod 10, 4);
        r.ones := to_unsigned(n mod 10, 4);
        return r;
    end function;

end package body clock_pkg;
