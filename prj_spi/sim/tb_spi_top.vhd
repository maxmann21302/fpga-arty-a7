----------------------------------------------------------------------------------
-- Testbench    : tb_spi_top
-- Beschreibung : SSD1331-Modell (SPI-Mode 3) empfaengt Kommandos und Pixeldaten.
--                Geprueft werden Init-Sequenz, Bildformat (96x64 RGB565) und der
--                Bildinhalt fuer alle Schalterstellungen inkl. Pong-Schlaegerbewegung.
----------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;
use std.env.all;

use work.oled_rom_pkg.all;

entity tb_spi_top is
end entity tb_spi_top;

architecture sim of tb_spi_top is

    constant WHITE : std_logic_vector(15 downto 0) := x"FFFF";
    constant BLACK : std_logic_vector(15 downto 0) := x"0000";

    signal clk  : std_logic := '0';
    signal rstn : std_logic := '0';
    signal sw   : std_logic_vector(3 downto 0) := "0000";
    signal btn  : std_logic_vector(3 downto 0) := "0000";
    signal led  : std_logic_vector(3 downto 0);

    signal oled_cs, oled_mosi, oled_sck, oled_dc : std_logic;
    signal oled_res, oled_vccen, oled_pmoden     : std_logic;

    type byte_arr is array (natural range <>) of std_logic_vector(7 downto 0);
    signal fb      : byte_arr(0 to 12287) := (others => (others => '0'));
    signal cmds    : byte_arr(0 to 255)   := (others => (others => '0'));
    signal cmd_cnt   : natural := 0;
    signal frame_cnt : natural := 0;

    impure function px (x, y : natural) return std_logic_vector is
        constant i : natural := 2 * (y * 96 + x);
    begin
        return fb(i) & fb(i + 1);
    end function;

    function rom_px (rom : rom_t; pal : pal_t; x, y : natural) return std_logic_vector is
    begin
        return pal(to_integer(unsigned(rom(y)(383 - 4 * x downto 380 - 4 * x))));
    end function;

    -- Drehwinkel-Index des Sprites, der im Sprite-Fenster angezeigt wird (-1 = keiner)
    impure function box_ang return integer is
        variable ok   : boolean;
        variable sidx : std_logic_vector(3 downto 0);
    begin
        for k in 0 to SPR_N - 1 loop
            ok := true;
            for sy in 0 to SPR_SIZE - 1 loop
                for sx in 0 to SPR_SIZE - 1 loop
                    sidx := SPR_ROM(k * SPR_SIZE + sy)(SPR_SIZE * 4 - 1 - 4 * sx downto SPR_SIZE * 4 - 4 - 4 * sx);
                    if px(SPR_X0 + sx, SPR_Y0 + sy) /= SYM_PAL(to_integer(unsigned(sidx))) then
                        ok := false;
                    end if;
                end loop;
            end loop;
            if ok then
                return k;
            end if;
        end loop;
        return -1;
    end function;

    -- Anzahl abweichender Pixel gegen die ROM-Daten (kind: 0 Bosch ohne Anker-Bereich, 1 HHN, 2 Hinweis)
    impure function mismatches (kind : natural) return natural is
        variable n : natural := 0;
        variable e : std_logic_vector(15 downto 0);
    begin
        for y in 0 to 63 loop
            for x in 0 to 95 loop
                case kind is
                    when 0      => e := rom_px(BOSCH_ROM, BOSCH_PAL, x, y);
                    when 1      => e := rom_px(HHN_ROM, HHN_PAL, x, y);
                    when others => e := rom_px(MSG_ROM, MSG_PAL, x, y);
                end case;
                if not (kind = 0 and x >= SPR_X0 and x < SPR_X0 + SPR_SIZE and
                        y >= SPR_Y0 and y < SPR_Y0 + SPR_SIZE) then
                    if px(x, y) /= e then
                        n := n + 1;
                    end if;
                end if;
            end loop;
        end loop;
        return n;
    end function;

begin

    clk <= not clk after 5 ns;

    dut : entity work.spi_top
        generic map (CLK_HZ => 1_000_000, SPI_HALF => 2)
        port map (
            CLK100MHZ   => clk,
            ck_rst      => rstn,
            sw          => sw,
            btn         => btn,
            led         => led,
            oled_cs     => oled_cs,
            oled_mosi   => oled_mosi,
            oled_sck    => oled_sck,
            oled_dc     => oled_dc,
            oled_res    => oled_res,
            oled_vccen  => oled_vccen,
            oled_pmoden => oled_pmoden
        );

    ------------------------------------------------------------------
    -- SSD1331-Modell
    ------------------------------------------------------------------
    process (oled_sck, oled_cs)
        variable sh   : std_logic_vector(7 downto 0) := (others => '0');
        variable bits : natural := 0;
        variable dcnt : natural := 0;
        variable ccnt : natural := 0;
    begin
        if oled_cs = '1' then
            bits := 0;
        elsif rising_edge(oled_sck) then
            sh   := sh(6 downto 0) & oled_mosi;
            bits := bits + 1;
            if bits = 8 then
                bits := 0;
                if oled_dc = '0' then
                    if ccnt = 0 then
                        assert oled_pmoden = '1' and oled_res = '1'
                            report "Erstes Kommando ohne PMODEN/RES" severity error;
                    end if;
                    if sh = x"AF" then
                        assert oled_vccen = '1' report "Display ein ohne VCCEN" severity error;
                    end if;
                    cmds(ccnt) <= sh;
                    ccnt    := ccnt + 1;
                    cmd_cnt <= ccnt;
                else
                    fb(dcnt) <= sh;
                    dcnt := dcnt + 1;
                    if dcnt = 12288 then
                        dcnt := 0;
                        frame_cnt <= frame_cnt + 1;
                    end if;
                end if;
            end if;
        end if;
    end process;

    ------------------------------------------------------------------
    -- Stimulus und Pruefungen
    ------------------------------------------------------------------
    process
        variable f      : natural;
        variable a      : integer;
        variable a_max  : integer;
        variable found  : boolean;
    begin
        wait for 100 ns;
        rstn <= '1';

        -- Bild 1: kein Schalter -> Hinweis
        wait until frame_cnt = 1;
        assert cmds(0) = x"AE" report "Init: erstes Kommando /= AE" severity error;
        assert cmds(37) = x"AF" report "Init: Display-ein fehlt" severity error;
        assert cmd_cnt = 44 report "Anzahl Kommandos Bild 1: " & integer'image(cmd_cnt) severity error;
        assert cmds(38) = x"15" and cmds(39) = x"00" and cmds(40) = x"5F" and
               cmds(41) = x"75" and cmds(42) = x"00" and cmds(43) = x"3F"
            report "Fenster-Kommandos falsch" severity error;
        assert mismatches(2) = 0 report "Hinweisbild (kein Schalter) falsch" severity error;
        report "Bild 1 (kein Schalter): OK";

        -- sw0: Bosch-Logo
        sw <= "0001";
        found := false;
        f := frame_cnt;
        for k in 1 to 4 loop
            wait until frame_cnt = f + k;
            if mismatches(0) = 0 and box_ang = 0 then
                found := true;
                exit;
            end if;
        end loop;
        assert found report "sw0: Bosch-Logo nicht angezeigt" severity error;
        report "sw0 (Bosch): OK";

        -- sw1: Sprite-Winkel muss laufen und der Rest des Bildes gleich bleiben
        sw <= "0010";
        a_max := 0;
        for k in 1 to 20 loop
            f := frame_cnt;
            wait until frame_cnt = f + 1;
            a := box_ang;
            assert a >= 0 report "sw1: Sprite-Fenster passt zu keinem Drehwinkel" severity error;
            assert mismatches(0) = 0 report "sw1: Bosch-Schriftzug falsch" severity error;
            if a > a_max then
                a_max := a;
            end if;
        end loop;
        assert a_max >= 5
            report "sw1: Anker dreht sich nicht (max. Winkel-Index " & integer'image(a_max) & ")"
            severity error;
        report "sw1 (Bosch drehend): OK";

        -- sw2: HHN-Logo
        sw <= "0100";
        found := false;
        f := frame_cnt;
        for k in 1 to 4 loop
            wait until frame_cnt = f + k;
            if mismatches(1) = 0 then
                found := true;
                exit;
            end if;
        end loop;
        assert found report "sw2: HHN-Logo nicht angezeigt" severity error;
        report "sw2 (HHN): OK";

        -- sw3: Pong
        sw <= "1000";
        found := false;
        f := frame_cnt;
        for k in 1 to 4 loop
            wait until frame_cnt = f + k;
            if px(4, 30) = WHITE and px(0, 0) = BLACK then
                found := true;
                exit;
            end if;
        end loop;
        assert found report "sw3: Pong nicht angezeigt" severity error;
        assert px(91, 30) = WHITE and px(10, 10) = BLACK and px(47, 31) = WHITE
            report "sw3: Schlaeger/Ball falsch" severity error;
        assert px(4, 24) = BLACK and px(4, 39) = BLACK
            report "sw3: Schlaegerhoehe falsch" severity error;

        -- btn0 gedrueckt: linker Schlaeger 4 Bilder lang um 3 Pixel nach oben
        btn <= "0001";
        f := frame_cnt;
        wait until frame_cnt = f + 5;
        assert px(4, 14) = WHITE and px(4, 12) = BLACK and px(4, 26) = WHITE and px(4, 28) = BLACK
            report "sw3: btn0 bewegt linken Schlaeger falsch" severity error;
        assert px(91, 30) = WHITE and px(91, 24) = BLACK
            report "sw3: rechter Schlaeger bewegt sich ohne Taste" severity error;
        btn <= "0000";
        report "sw3 (Pong): OK";

        -- mehrere Schalter -> Hinweis
        sw <= "0101";
        found := false;
        f := frame_cnt;
        for k in 1 to 4 loop
            wait until frame_cnt = f + k;
            if mismatches(2) = 0 then
                found := true;
                exit;
            end if;
        end loop;
        assert found report "mehrere Schalter: Hinweisbild fehlt" severity error;
        report "mehrere Schalter: OK";

        report "ALLE TESTS ABGESCHLOSSEN";
        finish;
    end process;

    process
    begin
        wait for 500 ms;
        report "Timeout" severity failure;
    end process;

end architecture sim;
