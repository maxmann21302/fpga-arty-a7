----------------------------------------------------------------------------------
-- Projekt      : Digitale Uhr / Wecker
-- Modul        : ssd_driver
-- Beschreibung : Zeitmultiplex fuer ein Pmod SSD (2 Ziffern, gemeinsame Segmente)
----------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

use work.clock_pkg.all;

entity ssd_driver is
    generic (
        CLK_HZ     : positive := 100_000_000;
        REFRESH_HZ : positive := 500
    );
    port (
        clk    : in  std_logic;
        rst    : in  std_logic;
        digit0 : in  unsigned(3 downto 0);   -- Einerstelle (rechts)
        digit1 : in  unsigned(3 downto 0);   -- Zehnerstelle (links)
        blank  : in  std_logic := '0';
        seg    : out std_logic_vector(6 downto 0);
        dsel   : out std_logic
    );
end entity ssd_driver;

architecture rtl of ssd_driver is

    constant DIV : positive := max_nat(1, CLK_HZ / (2 * REFRESH_HZ));

    signal tick : std_logic;
    signal sel  : std_logic := '0';
    signal mux  : unsigned(3 downto 0);

begin

    u_tick : entity work.tick_gen
        generic map (DIV => DIV)
        port map (clk => clk, rst => rst, tick => tick);

    process (clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                sel <= '0';
            elsif tick = '1' then
                sel <= not sel;
            end if;
        end if;
    end process;

    mux <= digit0 when sel = '0' else digit1;

    u_dec : entity work.seg7_decoder
        port map (digit => mux, blank => blank, seg => seg);

    dsel <= sel;

end architecture rtl;
