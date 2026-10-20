library ieee;
use ieee.std_logic_1164.all;
use std.env.all;

entity tb_phase2_top is
end entity;

architecture test of tb_phase2_top is
    constant SIM_CLK_HZ : positive := 1000;
    signal clk : std_logic := '0';
    signal reset_n : std_logic := '0';
    signal segments : std_logic_vector(6 downto 0);
    signal select_digit : std_logic;
    type patterns_t is array (0 to 9) of std_logic_vector(6 downto 0);
    constant patterns : patterns_t := (
        "0111111", "0000110", "1011011", "1001111", "1100110",
        "1101101", "1111101", "0000111", "1111111", "1101111"
    );
begin
    clk <= not clk after 5 ns;
    dut : entity work.phase2_top
        generic map (CLK_HZ => SIM_CLK_HZ, REFRESH_HZ => 100)
        port map (clk, reset_n, segments, select_digit);

    process
        variable expected : natural;
        variable digit : natural;
        variable seen_ones : boolean := false;
        variable seen_tens : boolean := false;
        procedure cycles(amount : positive) is
        begin
            for cycle_index in 1 to amount loop
                wait until falling_edge(clk);
            end loop;
        end procedure;
        procedure check_run(amount : positive) is
        begin
            for elapsed in 1 to amount loop
                cycles(1);
                expected := (elapsed / SIM_CLK_HZ) mod 100;
                if select_digit = '0' then
                    digit := expected mod 10;
                    seen_ones := true;
                else
                    digit := expected / 10;
                    seen_tens := true;
                end if;
                assert segments = patterns(digit)
                    report "Wrong display after cycle " & integer'image(elapsed) &
                           ", expected counter " & integer'image(expected)
                    severity failure;
            end loop;
        end procedure;
    begin
        cycles(4);
        assert segments = patterns(0) report "Reset must show zero" severity failure;
        reset_n <= '1';
        cycles(2);
        check_run(101 * SIM_CLK_HZ + 357);
        assert seen_ones and seen_tens report "Both digits must be multiplexed" severity failure;
        reset_n <= '0'; cycles(4);
        assert segments = patterns(0) report "Mid-second reset failed" severity failure;
        reset_n <= '1'; cycles(2);
        check_run(2 * SIM_CLK_HZ);
        report "PASS: phase 2 exact period, all 00..99, 09->10, 99->00, mux, reset/restart" severity note;
        finish;
    end process;
end architecture;