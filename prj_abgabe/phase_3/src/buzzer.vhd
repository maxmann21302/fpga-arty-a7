----------------------------------------------------------------------------------
-- Projekt      : Digitale Uhr / Wecker
-- Modul        : buzzer
-- Beschreibung : Akustische Signalausgabe, Rechteckton im Beep-Rhythmus
----------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

use work.clock_pkg.all;

entity buzzer is
    generic (
        CLK_HZ  : positive := 100_000_000;
        TONE_HZ : positive := 1000;
        BEEP_HZ : positive := 2
    );
    port (
        clk    : in  std_logic;
        rst    : in  std_logic;
        enable : in  std_logic;
        buzz   : out std_logic
    );
end entity buzzer;

architecture rtl of buzzer is

    constant TONE_DIV : positive := max_nat(1, CLK_HZ / (2 * TONE_HZ));
    constant BEEP_DIV : positive := max_nat(1, CLK_HZ / (2 * BEEP_HZ));

    signal tone_tick : std_logic;
    signal beep_tick : std_logic;
    signal tone      : std_logic := '0';
    signal beep      : std_logic := '1';

begin

    u_tone : entity work.tick_gen
        generic map (DIV => TONE_DIV)
        port map (clk => clk, rst => rst, tick => tone_tick);

    u_beep : entity work.tick_gen
        generic map (DIV => BEEP_DIV)
        port map (clk => clk, rst => rst, tick => beep_tick);

    process (clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                tone <= '0';
                beep <= '1';
            else
                if tone_tick = '1' then
                    tone <= not tone;
                end if;
                if beep_tick = '1' then
                    beep <= not beep;
                end if;
            end if;
        end if;
    end process;

    buzz <= enable and tone and beep;

end architecture rtl;
