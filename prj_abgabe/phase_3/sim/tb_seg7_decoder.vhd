----------------------------------------------------------------------------------
-- Testbench : seg7_decoder
-- Prueft alle Ziffern 0..9 sowie die Austastung (blank)
----------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity tb_seg7_decoder is
end entity tb_seg7_decoder;

architecture sim of tb_seg7_decoder is

    signal digit : unsigned(3 downto 0) := (others => '0');
    signal blank : std_logic := '0';
    signal seg   : std_logic_vector(6 downto 0);

    type pattern_array_t is array (0 to 9) of std_logic_vector(6 downto 0);
    --                                    gfedcba
    constant EXPECTED : pattern_array_t := ("0111111", "0000110", "1011011",
                                            "1001111", "1100110", "1101101",
                                            "1111101", "0000111", "1111111",
                                            "1101111");

begin

    dut : entity work.seg7_decoder
        port map (digit => digit, blank => blank, seg => seg);

    stim : process
    begin
        for i in 0 to 9 loop
            digit <= to_unsigned(i, 4);
            wait for 10 ns;
            assert seg = EXPECTED(i)
                report "Falsches Segmentmuster fuer Ziffer " & integer'image(i)
                severity error;
        end loop;

        blank <= '1';
        wait for 10 ns;
        assert seg = "0000000"
            report "Austastung funktioniert nicht" severity error;

        report "tb_seg7_decoder beendet" severity note;
        wait;
    end process;

end architecture sim;
