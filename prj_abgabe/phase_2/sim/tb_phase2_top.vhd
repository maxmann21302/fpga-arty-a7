library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use std.env.all;

entity tb_phase2_top is
end entity;

architecture test of tb_phase2_top is
    -- beschleunigt: 1 s = 1000 Takte, 10 ms = 10 Takte, 5 Takte je Ziffer
    constant SIM_CLK_HZ : positive := 1000;
    constant SEC        : positive := SIM_CLK_HZ;
    constant CS         : positive := SIM_CLK_HZ / 100;
    constant DARK       : integer := -1;
    constant WINDOW     : positive := 12;

    signal clk     : std_logic := '0';
    signal reset_n : std_logic := '0';
    signal sw      : std_logic_vector(3 downto 0) := "0000";
    signal btn     : std_logic_vector(3 downto 0) := "0000";
    signal seg_r   : std_logic_vector(6 downto 0);
    signal seg_l   : std_logic_vector(6 downto 0);
    signal dsel_r  : std_logic;
    signal dsel_l  : std_logic;
    signal cyc     : natural := 0;

    type patterns_t is array (0 to 9) of std_logic_vector(6 downto 0);
    constant patterns : patterns_t := (
        "0111111", "0000110", "1011011", "1001111", "1100110",
        "1101101", "1111101", "0000111", "1111111", "1101111"
    );

    -- -1 = dunkel, -2 = ungueltiges Muster
    function digit_of(p : std_logic_vector(6 downto 0)) return integer is
    begin
        if p = "0000000" then
            return DARK;
        end if;
        for d in 0 to 9 loop
            if p = patterns(d) then
                return d;
            end if;
        end loop;
        return -2;
    end function;

    -- -2 = nur eine Ziffer dunkel (nicht erlaubt)
    function combine(tens, ones : integer) return integer is
    begin
        if tens = DARK and ones = DARK then
            return DARK;
        elsif tens = DARK or ones = DARK then
            return -2;
        end if;
        return tens * 10 + ones;
    end function;

    function img(v : integer) return string is
    begin
        return integer'image(v);
    end function;
begin
    clk <= not clk after 5 ns;

    process (clk)
    begin
        if rising_edge(clk) then
            cyc <= cyc + 1;
        end if;
    end process;

    dut : entity work.phase2_top
        generic map (CLK_HZ => SIM_CLK_HZ, DEBOUNCE_CYCLES => 4, REFRESH_HZ => 100)
        port map (
            CLK100MHZ => clk, ck_rst => reset_n, sw => sw, btn => btn,
            seg_r => seg_r, dsel_r => dsel_r, seg_l => seg_l, dsel_l => dsel_l
        );

    process
        variable offset : integer := 0;
        variable lval, rval : integer;
        variable v, v2  : integer;
        variable k      : natural;
        variable guard  : natural;

        procedure cycles(amount : natural) is
        begin
            for i in 1 to amount loop
                wait until falling_edge(clk);
            end loop;
        end procedure;

        -- beide Anzeigen ueber WINDOW Takte lesen; jede Ziffer muss stabil sein
        procedure read_ssd(variable l_out, r_out : out integer; what : string) is
            type slots_t is array (0 to 3) of integer;
            variable slot : slots_t := (others => -3);
            variable idx  : natural;
            variable d    : integer;
        begin
            for i in 1 to WINDOW loop
                wait until falling_edge(clk);
                d := digit_of(seg_r);
                assert d /= -2 report what & ": invalid pattern on right SSD" severity failure;
                if dsel_r = '0' then idx := 0; else idx := 1; end if;
                if slot(idx) = -3 then
                    slot(idx) := d;
                else
                    assert slot(idx) = d report what & ": right SSD unstable" severity failure;
                end if;
                d := digit_of(seg_l);
                assert d /= -2 report what & ": invalid pattern on left SSD" severity failure;
                if dsel_l = '0' then idx := 2; else idx := 3; end if;
                if slot(idx) = -3 then
                    slot(idx) := d;
                else
                    assert slot(idx) = d report what & ": left SSD unstable" severity failure;
                end if;
            end loop;
            for i in 0 to 3 loop
                assert slot(i) /= -3 report what & ": digit slot not observed" severity failure;
            end loop;
            r_out := combine(slot(1), slot(0));
            l_out := combine(slot(3), slot(2));
            assert r_out /= -2 and l_out /= -2 report what & ": partially dark SSD" severity failure;
        end procedure;

        procedure expect(l_exp, r_exp : integer; what : string) is
            variable l, r : integer;
        begin
            read_ssd(l, r, what);
            assert l = l_exp and r = r_exp
                report what & ": expected " & img(l_exp) & " | " & img(r_exp) &
                       ", got " & img(l) & " | " & img(r) severity failure;
        end procedure;

        procedure read_stopwatch(variable value : out integer; what : string) is
            variable l, r : integer;
        begin
            read_ssd(l, r, what);
            assert l >= 0 and r >= 0 report what & ": stopwatch display dark" severity failure;
            value := l * 100 + r;
        end procedure;

        -- wartet bis zur Mitte von Sekunde n (gezaehlt ab Reset)
        procedure wait_second(n : natural) is
        begin
            if n * SEC + offset > cyc + 100 then
                wait for (n * SEC + offset - cyc - 50) * 10 ns;
            end if;
            loop
                wait until falling_edge(clk);
                exit when (cyc - offset) / SEC = n
                      and (cyc - offset) mod SEC >= 300
                      and (cyc - offset) mod SEC <= 600;
            end loop;
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
        cycles(2);

        -- P2-01 / P2-02: Startzustand
        expect(DARK, DARK, "no switch");
        set_switches("0001");
        expect(DARK, 0, "SW0 start");
        set_switches("0010");
        expect(0, 0, "SW1 start");
        set_switches("0100");
        expect(0, 0, "SW2 start");
        set_switches("0001");

        -- erste Sekundenflanke bestimmt die Phase des Sekundentakts
        guard := 0;
        loop
            wait until falling_edge(clk);
            exit when dsel_r = '0' and seg_r = patterns(1);
            guard := guard + 1;
            assert guard < 2 * SEC report "no first second tick" severity failure;
        end loop;
        offset := cyc - SEC;

        -- P2-03 / P2-04 / P2-05: SW0 zaehlt jede Sekunde, 99 -> 00, links dunkel
        for n in 1 to 102 loop
            wait_second(n);
            expect(DARK, n mod 100, "SW0 second " & img(n));
        end loop;

        -- P2-06: SW1 vierstellig ueber beide SSD, fuehrende Nullen
        set_switches("0010");
        wait_second(103); expect(1, 3, "SW1 0103");
        wait_second(104); expect(1, 4, "SW1 0104");

        -- P2-08: beide Zaehler laufen unabhaengig von der Betriebsart
        set_switches("0001");
        wait_second(105); expect(DARK, 5, "SW0 after SW1");

        -- P2-02: ungueltige Schalterstellungen
        set_switches("0011"); expect(DARK, DARK, "SW0+SW1");
        set_switches("0101"); expect(DARK, DARK, "SW0+SW2");
        set_switches("0110"); expect(DARK, DARK, "SW1+SW2");
        set_switches("1000"); expect(DARK, DARK, "SW3");
        set_switches("1111"); expect(DARK, DARK, "all switches");

        -- P2-07: SW1 9999 -> 0000
        set_switches("0010");
        wait_second(9998);  expect(99, 98, "SW1 9998");
        wait_second(9999);  expect(99, 99, "SW1 9999");
        wait_second(10000); expect(0, 0, "SW1 overflow 0000");
        wait_second(10001); expect(0, 1, "SW1 0001");
        set_switches("0001");
        wait_second(10002); expect(DARK, 2, "SW0 at 10002 s");

        -- P2-09: Stoppuhr steht nach Reset, Start/Stopp in 10-ms-Schritten
        set_switches("0100");
        expect(0, 0, "SW2 idle");
        press(0);
        cycles(2000);
        press(1);
        read_stopwatch(v, "SW2 after 2 s");
        assert v >= 200 and v <= 205 report "SW2 2 s run: got " & img(v) severity failure;

        -- P2-10: Stand bleibt im Stopp erhalten
        cycles(3000);
        read_stopwatch(v2, "SW2 hold");
        assert v2 = v report "SW2 hold: value changed while stopped" severity failure;

        -- P2-11: Nullen waehrend des Laufs ohne Wirkung
        press(0);
        cycles(500);
        press(2);
        cycles(500);
        press(1);
        read_stopwatch(v2, "SW2 zero while running");
        assert v2 >= v + 100 and v2 <= v + 110
            report "SW2 zero while running: expected about " & img(v + 104) & ", got " & img(v2) severity failure;
        v := v2;

        -- P2-13: Tasten ausserhalb von SW2 ohne Wirkung
        set_switches("0001");
        press(0); press(2);
        cycles(500);
        set_switches("0010");
        press(0); press(2);
        cycles(500);
        set_switches("0100");
        read_stopwatch(v2, "SW2 buttons outside SW2");
        assert v2 = v report "buttons outside SW2 changed the stopwatch" severity failure;

        -- P2-11: Nullen im Stopp
        press(2);
        expect(0, 0, "SW2 zero");

        -- P2-14: Stoppuhr laeuft im Hintergrund weiter
        press(0);
        set_switches("0001");
        cycles(3000);
        set_switches("0100");
        press(1);
        read_stopwatch(v, "SW2 background");
        assert v >= 300 and v <= 310 report "SW2 background run: got " & img(v) severity failure;

        -- P2-12: 99.99 -> 00.00, Stoppuhr laeuft weiter
        press(2);
        expect(0, 0, "SW2 zero before overflow");
        press(0);
        cycles(100 * SEC + 50 * CS);
        press(1);
        read_stopwatch(v, "SW2 overflow");
        assert v >= 45 and v <= 60 report "SW2 overflow: expected 00.5x, got " & img(v) severity failure;

        -- P2-08: Zaehler SW1 lief waehrend der Stoppuhr-Tests weiter
        set_switches("0010");
        k := (cyc - offset) / SEC + 1;
        wait_second(k);
        expect((k / 100) mod 100, k mod 100, "SW1 still running at " & img(k));

        -- P2-15: Reset setzt alle Zaehler und die Stoppuhr zurueck
        set_switches("0100");
        press(0);
        cycles(200);
        reset_n <= '0'; cycles(4);
        reset_n <= '1'; cycles(4);
        expect(0, 0, "reset stopwatch");
        cycles(500);
        expect(0, 0, "stopwatch stopped after reset");
        set_switches("0010");
        expect(0, 0, "reset SW1");
        set_switches("0001");
        expect(DARK, 0, "reset SW0");

        report "PASS: phase 2 SW0 00..99 (1 s, 99->00, left dark), SW1 0000..9999 (9999->0000), " &
               "SW2 stopwatch (start/stop/zero, 10 ms, 99.99->00.00, background), buttons only in SW2, " &
               "invalid switches dark, reset" severity note;
        finish;
    end process;
end architecture;
