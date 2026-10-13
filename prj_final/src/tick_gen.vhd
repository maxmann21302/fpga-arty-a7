----------------------------------------------------------------------------------
-- Projekt      : Digitale Uhr / Wecker
-- Modul        : tick_gen
-- Beschreibung : Generischer Vorteiler, erzeugt alle DIV Takte einen 1-Takt-Puls
----------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity tick_gen is
    generic (
        DIV : positive := 100_000_000
    );
    port (
        clk  : in  std_logic;
        rst  : in  std_logic := '0';
        en   : in  std_logic := '1';
        clr  : in  std_logic := '0';
        tick : out std_logic
    );
end entity tick_gen;

architecture rtl of tick_gen is
    signal cnt : natural range 0 to DIV - 1 := 0;
begin

    process (clk)
    begin
        if rising_edge(clk) then
            if rst = '1' or clr = '1' then
                cnt  <= 0;
                tick <= '0';
            elsif en = '1' then
                if cnt = DIV - 1 then
                    cnt  <= 0;
                    tick <= '1';
                else
                    cnt  <= cnt + 1;
                    tick <= '0';
                end if;
            else
                tick <= '0';
            end if;
        end if;
    end process;

end architecture rtl;
