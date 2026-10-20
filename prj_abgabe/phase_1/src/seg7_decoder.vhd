----------------------------------------------------------------------------------
-- Projekt      : Digitale Uhr / Wecker
-- Modul        : seg7_decoder
-- Beschreibung : BCD-Ziffer -> 7-Segment, Pmod SSD ist Common Cathode (aktiv high)
----------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity seg7_decoder is
    port (
        digit : in  unsigned(3 downto 0);
        blank : in  std_logic := '0';
        seg   : out std_logic_vector(6 downto 0)
    );
end entity seg7_decoder;

architecture rtl of seg7_decoder is
    signal pattern : std_logic_vector(6 downto 0);
begin

    with digit select
        --         gfedcba
        pattern <= "0111111" when "0000",
                   "0000110" when "0001",
                   "1011011" when "0010",
                   "1001111" when "0011",
                   "1100110" when "0100",
                   "1101101" when "0101",
                   "1111101" when "0110",
                   "0000111" when "0111",
                   "1111111" when "1000",
                   "1101111" when "1001",
                   "1000000" when others;   -- ungueltig: Mittelstrich

    seg <= (others => '0') when blank = '1' else pattern;

end architecture rtl;
