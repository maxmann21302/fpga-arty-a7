library ieee;
use ieee.std_logic_1164.all;
use std.env.all;

entity tb_phase1_top is
end entity;

architecture test of tb_phase1_top is
    signal clk : std_logic := '0';
    signal reset_n : std_logic := '0';
    signal button : std_logic := '0';
    signal segments : std_logic_vector(6 downto 0);
    signal select_digit : std_logic;
    type patterns_t is array (0 to 9) of std_logic_vector(6 downto 0);
    constant patterns : patterns_t := (
        "0111111", "0000110", "1011011", "1001111", "1100110",
        "1101101", "1111101", "0000111", "1111111", "1101111"
    );
begin
    clk <= not clk after 5 ns;
    dut : entity work.phase1_top
        generic map (CLK_HZ => 100, DEBOUNCE_CYCLES => 4, REFRESH_HZ => 10)
        port map (clk, reset_n, button, segments, select_digit);

    process
        procedure cycles(amount : positive) is
        begin
            for cycle_index in 1 to amount loop
                wait until falling_edge(clk);
            end loop;
        end procedure;
        procedure expect_digit(value : natural) is
        begin
            for cycle_index in 1 to 24 loop
                wait until falling_edge(clk);
                if select_digit = '0' then
                    assert segments = patterns(value)
                        report "Wrong digit: expected " & integer'image(value) severity failure;
                else
                    assert segments = "0000000"
                        report "Left digit must be blank" severity failure;
                end if;
            end loop;
        end procedure;
    begin
        cycles(4);
        reset_n <= '1';
        cycles(4);
        expect_digit(0);
        button <= '1'; cycles(1);
        button <= '0'; cycles(1);
        button <= '1'; cycles(1);
        button <= '0'; cycles(10);
        expect_digit(0);
        button <= '1'; cycles(10);
        expect_digit(1);
        cycles(100);
        expect_digit(1);
        button <= '0'; cycles(10);
        expect_digit(1);
        for press_index in 2 to 10 loop
            button <= '1'; cycles(10);
            expect_digit(press_index mod 10);
            button <= '0'; cycles(10);
        end loop;
        button <= '1'; cycles(10);
        expect_digit(1);
        reset_n <= '0'; cycles(4);
        button <= '0'; reset_n <= '1'; cycles(10);
        expect_digit(0);
        report "PASS: phase 1 startup, bounce, hold, release, wrap, reset" severity note;
        finish;
    end process;
end architecture;