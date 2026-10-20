----------------------------------------------------------------------------------
-- Projekt      : Digitale Uhr / Wecker
-- Modul        : debounce
-- Beschreibung : Tasterentprellung mit Auto-Repeat fuer die +/- Eingabe
----------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

use work.clock_pkg.all;

entity debounce is
    generic (
        CLK_HZ      : positive := 100_000_000;
        DEBOUNCE_MS : positive := 10;
        REPEAT_MS   : positive := 250
    );
    port (
        clk   : in  std_logic;
        rst   : in  std_logic;
        btn   : in  std_logic;
        level : out std_logic;
        pulse : out std_logic
    );
end entity debounce;

architecture rtl of debounce is

    constant DB_MAX  : positive := max_nat(1, (CLK_HZ / 1000) * DEBOUNCE_MS);
    constant REP_MAX : positive := max_nat(1, (CLK_HZ / 1000) * REPEAT_MS);

    signal sync     : std_logic_vector(1 downto 0) := (others => '0');
    signal stable   : std_logic := '0';
    signal stable_d : std_logic := '0';
    signal db_cnt   : natural range 0 to DB_MAX  := 0;
    signal rep_cnt  : natural range 0 to REP_MAX := 0;
    signal rep_tick : std_logic := '0';

begin

    process (clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                sync     <= (others => '0');
                stable   <= '0';
                stable_d <= '0';
                db_cnt   <= 0;
                rep_cnt  <= 0;
                rep_tick <= '0';
            else
                sync     <= sync(0) & btn;
                stable_d <= stable;

                if sync(1) = stable then
                    db_cnt <= 0;
                elsif db_cnt = DB_MAX then
                    db_cnt <= 0;
                    stable <= sync(1);
                else
                    db_cnt <= db_cnt + 1;
                end if;

                if stable = '0' then
                    rep_cnt  <= 0;
                    rep_tick <= '0';
                elsif rep_cnt = REP_MAX then
                    rep_cnt  <= 0;
                    rep_tick <= '1';
                else
                    rep_cnt  <= rep_cnt + 1;
                    rep_tick <= '0';
                end if;
            end if;
        end if;
    end process;

    level <= stable;
    pulse <= (stable and not stable_d) or rep_tick;

end architecture rtl;
