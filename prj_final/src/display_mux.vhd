----------------------------------------------------------------------------------
-- Projekt      : Digitale Uhr / Wecker
-- Modul        : display_mux
-- Beschreibung : Auswahl der Anzeige und Wandlung binaer -> BCD
--                Prioritaet: Weckzeit > Zeit stellen > Sekunden > Normalanzeige
----------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

use work.clock_pkg.all;

entity display_mux is
    port (
        show_seconds : in  std_logic;
        set_time     : in  std_logic;
        set_alarm    : in  std_logic;
        hours        : in  unsigned(5 downto 0);
        minutes      : in  unsigned(5 downto 0);
        seconds      : in  unsigned(5 downto 0);
        al_hours     : in  unsigned(5 downto 0);
        al_minutes   : in  unsigned(5 downto 0);
        left_tens    : out unsigned(3 downto 0);
        left_ones    : out unsigned(3 downto 0);
        right_tens   : out unsigned(3 downto 0);
        right_ones   : out unsigned(3 downto 0)
    );
end entity display_mux;

architecture rtl of display_mux is

    signal left_val  : unsigned(5 downto 0);
    signal right_val : unsigned(5 downto 0);
    signal left_bcd  : bcd2_t;
    signal right_bcd : bcd2_t;

begin

    left_val  <= al_hours   when set_alarm    = '1' else
                 hours      when set_time     = '1' else
                 minutes    when show_seconds = '1' else
                 hours;

    right_val <= al_minutes when set_alarm    = '1' else
                 minutes    when set_time     = '1' else
                 seconds    when show_seconds = '1' else
                 minutes;

    left_bcd  <= to_bcd2(left_val);
    right_bcd <= to_bcd2(right_val);

    left_tens  <= left_bcd.tens;
    left_ones  <= left_bcd.ones;
    right_tens <= right_bcd.tens;
    right_ones <= right_bcd.ones;

end architecture rtl;
