----------------------------------------------------------------------------------
-- Projekt      : Prell-Oszilloskop (Pmod OLEDrgb an JD)
-- Modul        : btn_debounce
-- Beschreibung : 2-FF-Synchronisation + Entprellung, liefert pro Tastendruck
--                genau einen 1-Takt-Puls (kein Auto-Repeat)
----------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity btn_debounce is
    generic (
        DEBOUNCE_CYCLES : positive := 1_000_000
    );
    port (
        clk     : in  std_logic;
        rst     : in  std_logic;
        btn_i   : in  std_logic;
        press_o : out std_logic
    );
end entity btn_debounce;

architecture rtl of btn_debounce is
    signal sync   : std_logic_vector(1 downto 0) := (others => '0');
    signal stable : std_logic := '0';
    signal cnt    : natural range 0 to DEBOUNCE_CYCLES - 1 := 0;
    signal press  : std_logic := '0';
begin

    process (clk)
    begin
        if rising_edge(clk) then
            press <= '0';
            if rst = '1' then
                sync   <= (others => '0');
                stable <= '0';
                cnt    <= 0;
            else
                sync <= sync(0) & btn_i;
                if sync(1) = stable then
                    cnt <= 0;
                elsif cnt = DEBOUNCE_CYCLES - 1 then
                    cnt    <= 0;
                    stable <= sync(1);
                    -- nur die akzeptierte Low->High-Flanke erzeugt einen Puls
                    press  <= sync(1);
                else
                    cnt <= cnt + 1;
                end if;
            end if;
        end if;
    end process;

    press_o <= press;

end architecture rtl;
