library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use std.env.all;

use work.bounce_pkg.all;

entity tb_bounce_capture is
end entity;

architecture test of tb_bounce_capture is
    constant P : positive := 4;
    signal clk    : std_logic := '0';
    signal rst    : std_logic := '1';
    signal clear  : std_logic := '0';
    signal sig    : std_logic := '0';
    signal period : period_t := P;
    signal hi_buf : std_logic_vector(SAMPLES - 1 downto 0);
    signal lo_buf : std_logic_vector(SAMPLES - 1 downto 0);
    signal armed  : std_logic;
    signal done   : std_logic;

    signal px     : unsigned(6 downto 0) := (others => '0');
    signal py     : unsigned(5 downto 0) := (others => '0');
    signal pix    : std_logic_vector(15 downto 0);
begin
    clk <= not clk after 5 ns;

    dut : entity work.bounce_capture
        port map (clk => clk, rst => rst, clear => clear, sig => sig, period => period,
                  hi_buf => hi_buf, lo_buf => lo_buf, armed => armed, done => done);

    u_render : entity work.bounce_render
        port map (clk => clk, x => px, y => py, hi_buf => hi_buf, lo_buf => lo_buf,
                  armed => armed, done => done, tb_idx => TB_DEFAULT, pix => pix);

    process
        procedure cycles(n : positive) is
        begin
            for i in 1 to n loop
                wait until falling_edge(clk);
            end loop;
        end procedure;

        -- Spalte k: "1" = nur high, "0" = nur low, "X" = beides, "-" = leer
        function col(h, l : std_logic) return character is
        begin
            if h = '1' and l = '1' then return 'X';
            elsif h = '1' then return '1';
            elsif l = '1' then return '0';
            else return '-';
            end if;
        end function;

        procedure expect_col(k : natural; c : character; what : string) is
            variable got : character;
        begin
            got := col(hi_buf(SAMPLES - 1 - k), lo_buf(SAMPLES - 1 - k));
            assert got = c
                report what & ": Spalte " & integer'image(k) & " = " & got & ", erwartet " & c
                severity failure;
        end procedure;

        procedure expect_pix(x, y : natural; c : std_logic_vector(15 downto 0); what : string) is
        begin
            px <= to_unsigned(x, 7);
            py <= to_unsigned(y, 6);
            cycles(3);
            assert pix = c report what & ": falsches Pixel" severity failure;
        end procedure;
    begin
        cycles(3);
        rst <= '0';
        cycles(SAMPLES * P + 10);                       -- Vorlauf komplett mit '0' fuellen
        assert armed = '1' and done = '0' report "nach Reset nicht scharf" severity failure;

        -- Prellen: 1-Takt-Puls (kuerzer als ein Abtastintervall) loest aus
        sig <= '1'; cycles(1);
        sig <= '0'; cycles(3 * P);
        assert armed = '0' report "Trigger nicht erkannt" severity failure;
        sig <= '1'; cycles(2);
        sig <= '0'; cycles(2 * P);
        sig <= '1';                                     -- danach stabil gedrueckt
        wait until done = '1';
        cycles(2);

        for k in 0 to PRE_TRIG - 1 loop
            expect_col(k, '0', "Vorlauf");
        end loop;
        expect_col(PRE_TRIG, 'X', "Triggerspalte");
        expect_col(SAMPLES - 1, '1', "Ende stabil high");

        -- Aufnahme bleibt eingefroren
        sig <= '0'; cycles(20 * P);
        sig <= '1'; cycles(20 * P);
        assert done = '1' report "HOLD verlassen" severity failure;
        expect_col(SAMPLES - 1, '1', "eingefroren");

        -- Darstellung: Flanke als senkrechte Linie, Vorlauf unten, Ende oben
        expect_pix(PRE_TRIG, 31, x"07E0", "Flanke senkrecht");
        expect_pix(5, 54, x"07E0", "Vorlauf low");
        expect_pix(5, 18, x"0000", "Vorlauf nicht high");
        expect_pix(95, 18, x"07E0", "Ende high");
        expect_pix(80, 1, x"07E0", "HOLD-Text gruen");

        -- BTN1: loeschen -> leer und wieder scharf
        sig <= '0';
        wait until falling_edge(clk);
        clear <= '1'; cycles(1);
        clear <= '0'; cycles(1);
        assert armed = '1' and done = '0' report "Loeschen schaltet nicht scharf" severity failure;
        expect_col(PRE_TRIG, '-', "geloescht");
        expect_col(SAMPLES - 1, '-', "geloescht");
        expect_pix(PRE_TRIG, 31, x"0000", "geloescht keine Kurve");
        expect_pix(80, 1, x"FFE0", "WAIT-Text gelb");

        report "PASS: bounce_capture Trigger, Min/Max-Glitch, HOLD, Loeschen, Darstellung" severity note;
        finish;
    end process;
end architecture;
