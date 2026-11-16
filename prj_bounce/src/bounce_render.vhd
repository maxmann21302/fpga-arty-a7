----------------------------------------------------------------------------------
-- Projekt      : Prell-Oszilloskop (Pmod OLEDrgb an JD)
-- Modul        : bounce_render
-- Beschreibung : Pixelgenerator 96x64 (RGB565), 2 Takte Latenz
--                Zeile oben : Zeitbasis, Quelle (BTN0 / JA1), Triggerflanke, Status
--                Darunter   : Raster, Triggermarke, Signalverlauf (nicht im Status WAIT)
----------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.bounce_pkg.all;

entity bounce_render is
    port (
        clk    : in  std_logic;
        x      : in  unsigned(6 downto 0);
        y      : in  unsigned(5 downto 0);
        hi_buf : in  std_logic_vector(SAMPLES - 1 downto 0);
        lo_buf : in  std_logic_vector(SAMPLES - 1 downto 0);
        armed  : in  std_logic;
        done   : in  std_logic;
        src    : in  std_logic;
        edge   : in  std_logic;
        tb_idx : in  natural range 0 to TB_COUNT - 1;
        pix    : out std_logic_vector(15 downto 0)
    );
end entity bounce_render;

architecture rtl of bounce_render is

    constant TEXT_Y  : natural := 1;
    constant LABEL_X : natural := 1;
    constant SRC_X   : natural := 42;
    constant EDGE_X  : natural := 60;
    constant STAT_X  : natural := 80;
    constant PLOT_Y  : natural := 9;
    constant Y_HI    : natural := 18;
    constant Y_LO    : natural := 54;

    constant C_BLACK : std_logic_vector(15 downto 0) := x"0000";
    constant C_GRID  : std_logic_vector(15 downto 0) := x"31A6";
    constant C_TRACE : std_logic_vector(15 downto 0) := x"07E0";
    constant C_TEXT  : std_logic_vector(15 downto 0) := x"FFFF";
    constant C_TRIG  : std_logic_vector(15 downto 0) := x"FD20";
    constant C_WAIT  : std_logic_vector(15 downto 0) := x"FFE0";
    constant C_RUN   : std_logic_vector(15 downto 0) := x"F800";
    constant C_HOLD  : std_logic_vector(15 downto 0) := x"07E0";

    -- 3x5-Zeichensatz, Zeile fuer Zeile von oben, je 3 Bit von links
    subtype glyph_t is std_logic_vector(14 downto 0);

    function glyph (c : character) return glyph_t is
    begin
        case c is
            when '0'    => return B"111_101_101_101_111";
            when '1'    => return B"010_110_010_010_111";
            when '2'    => return B"111_001_111_100_111";
            when '5'    => return B"111_100_111_001_111";
            when 'u'    => return B"000_101_101_101_111";
            when 'm'    => return B"000_111_111_101_101";
            when 's'    => return B"000_011_100_001_110";
            when '/'    => return B"001_001_010_100_100";
            when 'd'    => return B"001_001_111_101_111";
            when 'i'    => return B"010_000_010_010_010";
            when 'v'    => return B"000_101_101_101_010";
            when 'W'    => return B"101_101_111_111_101";
            when 'A'    => return B"010_101_111_101_101";
            when 'I'    => return B"111_010_010_010_111";
            when 'T'    => return B"111_010_010_010_010";
            when 'R'    => return B"110_101_110_101_101";
            when 'U'    => return B"101_101_101_101_111";
            when 'N'    => return B"110_101_101_101_101";
            when 'H'    => return B"101_101_111_101_101";
            when 'O'    => return B"010_101_101_101_010";
            when 'L'    => return B"100_100_100_100_111";
            when 'D'    => return B"110_101_101_101_110";
            when 'B'    => return B"110_101_110_101_110";
            when 'J'    => return B"001_001_001_101_010";
            when '^'    => return B"010_111_010_010_010";   -- Pfeil hoch
            when '_'    => return B"010_010_010_111_010";   -- Pfeil runter
            when others => return B"000_000_000_000_000";
        end case;
    end function;

    -- Stufe 1
    signal x1    : natural range 0 to 127 := 0;
    signal y1    : natural range 0 to 63  := 0;
    signal h1    : std_logic := '0';
    signal l1    : std_logic := '0';
    signal g1    : glyph_t := (others => '0');
    signal cx1   : natural range 0 to 3 := 0;
    signal tcol1 : std_logic_vector(15 downto 0) := C_TEXT;

begin

    process (clk)
        variable xi   : natural range 0 to 127;
        variable col  : natural range 0 to 127;
        variable lbl  : string(1 to 9);
        variable stat : string(1 to 4);
        variable ch   : character;
        variable d    : natural range 0 to 63;
        variable p    : std_logic_vector(15 downto 0);
    begin
        if rising_edge(clk) then
            -- Stufe 1: Abtastwert der Spalte und Zeichen holen
            xi := to_integer(x);
            x1 <= xi;
            y1 <= to_integer(y);

            if xi < SAMPLES then
                h1 <= hi_buf(SAMPLES - 1 - xi);
                l1 <= lo_buf(SAMPLES - 1 - xi);
            else
                h1 <= '0';
                l1 <= '0';
            end if;

            ch    := ' ';
            cx1   <= 0;
            tcol1 <= C_TEXT;
            if xi >= LABEL_X and xi < LABEL_X + 4 * 9 then
                col := xi - LABEL_X;
                lbl := TB_LABEL(tb_idx);
                ch  := lbl(col / 4 + 1);
                cx1 <= col mod 4;
            elsif xi >= SRC_X and xi < SRC_X + 4 * 4 then
                col := xi - SRC_X;
                if src = '1' then
                    stat := "JA1 ";
                else
                    stat := "BTN0";
                end if;
                ch  := stat(col / 4 + 1);
                cx1 <= col mod 4;
            elsif xi >= EDGE_X and xi < EDGE_X + 4 then
                if edge = '1' then
                    ch := '_';
                else
                    ch := '^';
                end if;
                tcol1 <= C_TRIG;
                cx1   <= xi - EDGE_X;
            elsif xi >= STAT_X and xi < STAT_X + 4 * 4 then
                col := xi - STAT_X;
                if armed = '1' then
                    stat  := "WAIT";
                    tcol1 <= C_WAIT;
                elsif done = '1' then
                    stat  := "HOLD";
                    tcol1 <= C_HOLD;
                else
                    stat  := "RUN ";
                    tcol1 <= C_RUN;
                end if;
                ch  := stat(col / 4 + 1);
                cx1 <= col mod 4;
            end if;
            g1 <= glyph(ch);

            -- Stufe 2: Pixel zusammensetzen
            p := C_BLACK;
            if y1 >= TEXT_Y and y1 < TEXT_Y + 5 then
                if cx1 < 3 and g1(14 - ((y1 - TEXT_Y) * 3 + cx1)) = '1' then
                    p := tcol1;
                end if;
            elsif y1 >= PLOT_Y then
                if (x1 mod DIV_PX = PRE_TRIG mod DIV_PX and y1 mod 2 = 0)
                   or ((y1 = Y_HI or y1 = Y_LO) and x1 mod 2 = 0) then
                    p := C_GRID;
                end if;

                d := y1 - PLOT_Y;
                if d < 3 and x1 + (2 - d) >= PRE_TRIG and x1 <= PRE_TRIG + (2 - d) then
                    p := C_TRIG;
                end if;

                if armed = '0' then
                    if h1 = '1' and l1 = '1' and y1 >= Y_HI and y1 <= Y_LO then
                        p := C_TRACE;
                    elsif h1 = '1' and l1 = '0' and y1 = Y_HI then
                        p := C_TRACE;
                    elsif h1 = '0' and l1 = '1' and y1 = Y_LO then
                        p := C_TRACE;
                    end if;
                end if;
            end if;
            pix <= p;
        end if;
    end process;

end architecture rtl;
