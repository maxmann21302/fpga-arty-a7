library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use std.env.all;

entity tb_phase1_top is
end entity;

architecture test of tb_phase1_top is
    constant BLANK : integer := -1;
    signal clk : std_logic := '0';
    signal reset_n : std_logic := '0';
    signal sw : std_logic_vector(3 downto 0) := "0000";
    signal btn : std_logic_vector(3 downto 0) := "0000";
    signal segments : std_logic_vector(6 downto 0);
    signal select_digit : std_logic;
    type patterns_t is array (0 to 9) of std_logic_vector(6 downto 0);
    constant patterns : patterns_t := (
        "0111111", "0000110", "1011011", "1001111", "1100110",
        "1101101", "1111101", "0000111", "1111111", "1101111"
    );

    function pattern_of(digit : integer) return std_logic_vector is
    begin
        if digit < 0 then
            return "0000000";
        end if;
        return patterns(digit);
    end function;
begin
    clk <= not clk after 5 ns;
    dut : entity work.phase1_top
        generic map (CLK_HZ => 100, DEBOUNCE_CYCLES => 4, REFRESH_HZ => 10)
        port map (
            CLK100MHZ => clk, ck_rst => reset_n, sw => sw, btn => btn,
            seg_r => segments, dsel_r => select_digit
        );

    process
        variable count : natural := 0;
        variable bin_value : unsigned(3 downto 0) := "0000";
        variable target : unsigned(3 downto 0);

        procedure cycles(amount : positive) is
        begin
            for cycle_index in 1 to amount loop
                wait until falling_edge(clk);
            end loop;
        end procedure;

        procedure expect_display(tens, ones : integer; what : string) is
            variable seen_left, seen_right : boolean := false;
        begin
            for cycle_index in 1 to 24 loop
                wait until falling_edge(clk);
                if select_digit = '0' then
                    assert segments = pattern_of(ones)
                        report what & ": wrong right digit, expected " & integer'image(ones) severity failure;
                    seen_right := true;
                else
                    assert segments = pattern_of(tens)
                        report what & ": wrong left digit, expected " & integer'image(tens) severity failure;
                    seen_left := true;
                end if;
            end loop;
            assert seen_left and seen_right report what & ": both slots must be observed" severity failure;
        end procedure;

        procedure expect_number(value : natural; what : string) is
        begin
            if value >= 10 then
                expect_display(value / 10, value mod 10, what & " " & integer'image(value));
            else
                expect_display(BLANK, value, what & " " & integer'image(value));
            end if;
        end procedure;

        procedure press(index : natural) is
        begin
            btn(index) <= '1'; cycles(10);
            btn(index) <= '0'; cycles(10);
        end procedure;

        procedure set_switches(value : std_logic_vector(3 downto 0)) is
        begin
            sw <= value;
            cycles(4);
        end procedure;
    begin
        cycles(4);
        reset_n <= '1';
        cycles(4);

        -- kein Schalter: Anzeige dunkel
        expect_display(BLANK, BLANK, "no switch");

        -- SW0: Zaehler, Startwert 0, untere Grenze
        set_switches("0001");
        expect_number(0, "start");
        press(1); expect_number(0, "0 - 1 clamps");
        press(3); expect_number(0, "0 - 10 clamps");

        -- Prellen: 1-Takt-Pulse loesen nichts aus
        btn(0) <= '1'; cycles(1);
        btn(0) <= '0'; cycles(1);
        btn(0) <= '1'; cycles(1);
        btn(0) <= '0'; cycles(10);
        expect_number(0, "bounce");

        -- Halten zaehlt genau einmal, Loslassen zaehlt nicht
        btn(0) <= '1'; cycles(10);
        expect_number(1, "press");
        cycles(100);
        expect_number(1, "hold");
        btn(0) <= '0'; cycles(10);
        expect_number(1, "release");

        -- +1 ueber den gesamten Bereich, 99 + 1 -> 0
        count := 1;
        for step in 2 to 100 loop
            press(0);
            count := (count + 1) mod 100;
            expect_number(count, "+1");
        end loop;

        -- +10 / -10 / -1 und Begrenzungen
        press(2); expect_number(10, "+10");
        press(2); expect_number(20, "+10");
        press(1); expect_number(19, "-1");
        press(3); expect_number(9, "-10");
        press(3); expect_number(0, "9 - 10 clamps");
        for step in 1 to 9 loop
            press(2);
        end loop;
        expect_number(90, "9x +10");
        for step in 1 to 5 loop
            press(0);
        end loop;
        expect_number(95, "+5");
        press(2); expect_number(0, "95 + 10 overflow");
        for step in 1 to 4 loop
            press(2);
        end loop;
        press(0); press(0);
        expect_number(42, "count kept");

        -- SW1 / SW2: Matrikelnummern, Tasten ohne Wirkung
        set_switches("0010");
        expect_number(91, "SW1 Mark");
        press(0); press(2);
        expect_number(91, "SW1 ignores buttons");
        set_switches("0100");
        expect_number(93, "SW2 Maxi");
        press(1); press(3);
        expect_number(93, "SW2 ignores buttons");
        set_switches("0001");
        expect_number(42, "counter unchanged by other modes");

        -- SW3: BTNi toggelt Bit i, alle Werte 0..15
        set_switches("1000");
        expect_number(0, "SW3 start");
        for value in 0 to 15 loop
            target := to_unsigned(value, 4);
            for bit_index in 0 to 3 loop
                if target(bit_index) /= bin_value(bit_index) then
                    press(bit_index);
                end if;
            end loop;
            bin_value := target;
            expect_number(value, "SW3 binary");
        end loop;
        press(3); expect_number(7, "SW3 toggle bit 3 off");

        set_switches("0001");
        expect_number(42, "counter unchanged by binary mode");

        -- mehrere Schalter: Anzeige dunkel
        set_switches("0011"); expect_display(BLANK, BLANK, "SW0+SW1");
        set_switches("0101"); expect_display(BLANK, BLANK, "SW0+SW2");
        set_switches("1100"); expect_display(BLANK, BLANK, "SW2+SW3");
        set_switches("1111"); expect_display(BLANK, BLANK, "all switches");
        press(0);
        set_switches("1000");
        expect_number(7, "binary value kept");

        -- Reset loescht Zaehler und Binaerwert
        reset_n <= '0'; cycles(4);
        reset_n <= '1'; cycles(4);
        expect_number(0, "reset binary");
        set_switches("0001");
        expect_number(0, "reset counter");

        report "PASS: phase 1 modes SW0 counter (+1/-1/+10/-10, clamp 0, 99->0), SW1 91, SW2 93, SW3 binary, invalid switches blank, bounce, hold, reset" severity note;
        finish;
    end process;
end architecture;