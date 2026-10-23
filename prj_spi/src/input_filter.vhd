----------------------------------------------------------------------------------
-- Modul        : input_filter
-- Beschreibung : 2-FF-Synchronisierer mit Entprellung fuer Schalter und Taster
----------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity input_filter is
    generic (
        DEBOUNCE_CYCLES : positive := 1_000_000   -- 10 ms bei 100 MHz
    );
    port (
        clk : in  std_logic;
        rst : in  std_logic;
        d   : in  std_logic;
        q   : out std_logic
    );
end entity input_filter;

architecture rtl of input_filter is
    signal sync  : std_logic_vector(1 downto 0) := (others => '0');
    signal stable : std_logic := '0';
    signal cnt   : natural range 0 to DEBOUNCE_CYCLES := 0;
begin

    process (clk)
    begin
        if rising_edge(clk) then
            sync <= sync(0) & d;
            if rst = '1' then
                stable <= '0';
                cnt    <= 0;
            elsif sync(1) = stable then
                cnt <= 0;
            elsif cnt = DEBOUNCE_CYCLES then
                cnt    <= 0;
                stable <= sync(1);
            else
                cnt <= cnt + 1;
            end if;
        end if;
    end process;

    q <= stable;

end architecture rtl;
