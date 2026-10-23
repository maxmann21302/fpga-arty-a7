----------------------------------------------------------------------------------
-- Modul        : oled_render
-- Beschreibung : Pixelgenerator. Waehlt anhand der Schalter das Bild:
--                  sw0 = Bosch-Logo           sw1 = Bosch-Logo, Anker dreht sich
--                  sw2 = HHN-Logo             sw3 = Pong (1 gegen 1)
--                  sonst (keiner/mehrere)     = Hinweis "Waehle einen Schalter"
--                Der Modus wird nur am Bildende uebernommen (kein Tearing).
--                Das Bosch-Symbol (Ring + Anker) kommt aus 32 Dreh-Sprites, die im
--                Sprite-Fenster das Bitmap ersetzen.
--                pix ist 5 Takte nach (x, y) gueltig; x/y muessen so lange stabil sein.
----------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

use work.oled_rom_pkg.all;

entity oled_render is
    generic (
        ROT_FRAMES : positive := 2                -- Bilder pro Drehschritt (5,6 Grad)
    );
    port (
        clk        : in  std_logic;
        rst        : in  std_logic;
        x          : in  unsigned(6 downto 0);
        y          : in  unsigned(5 downto 0);
        frame_tick : in  std_logic;
        sw         : in  std_logic_vector(3 downto 0);
        btn        : in  std_logic_vector(3 downto 0);
        pix        : out std_logic_vector(15 downto 0)
    );
end entity oled_render;

architecture rtl of oled_render is

    type mode_t is (M_MSG, M_BOSCH, M_ROT, M_HHN, M_PONG);
    signal mode : mode_t := M_MSG;

    signal ang       : natural range 0 to SPR_N - 1 := 0;
    signal ang_div   : natural range 0 to ROT_FRAMES - 1 := 0;

    -- Stufe 1
    signal row1      : std_logic_vector(383 downto 0) := (others => '0');
    signal x1        : unsigned(6 downto 0) := (others => '0');
    signal in_box1   : std_logic := '0';
    signal sx1       : natural range 0 to SPR_SIZE - 1 := 0;
    signal sidx1     : natural range 0 to SPR_N * SPR_SIZE - 1 := 0;
    -- Stufe 2
    signal idx2      : std_logic_vector(3 downto 0) := (others => '0');
    signal srow2     : std_logic_vector(SPR_SIZE * 4 - 1 downto 0) := (others => '0');
    signal in_box2   : std_logic := '0';
    signal sx2       : natural range 0 to SPR_SIZE - 1 := 0;
    -- Stufe 3
    signal col3      : std_logic_vector(15 downto 0) := (others => '0');
    signal sym3      : std_logic_vector(3 downto 0) := (others => '0');
    signal in_box3   : std_logic := '0';
    -- Stufe 4
    signal col4      : std_logic_vector(15 downto 0) := (others => '0');
    signal sym4      : std_logic_vector(15 downto 0) := (others => '0');
    signal in_box4   : std_logic := '0';

    signal pong_on   : std_logic;
    signal active    : std_logic;

    function decode (s : std_logic_vector(3 downto 0)) return mode_t is
    begin
        case s is
            when "0001" => return M_BOSCH;
            when "0010" => return M_ROT;
            when "0100" => return M_HHN;
            when "1000" => return M_PONG;
            when others => return M_MSG;
        end case;
    end function;

    function get_px (row : std_logic_vector(383 downto 0); xp : unsigned(6 downto 0))
        return std_logic_vector is
        variable r : std_logic_vector(3 downto 0) := "0000";
    begin
        for i in 0 to 95 loop
            if to_integer(xp) = i then
                r := row(383 - 4 * i downto 380 - 4 * i);
            end if;
        end loop;
        return r;
    end function;

    function get_spx (row : std_logic_vector(SPR_SIZE * 4 - 1 downto 0); xp : natural)
        return std_logic_vector is
        variable r : std_logic_vector(3 downto 0) := "0000";
    begin
        for i in 0 to SPR_SIZE - 1 loop
            if xp = i then
                r := row(SPR_SIZE * 4 - 1 - 4 * i downto SPR_SIZE * 4 - 4 - 4 * i);
            end if;
        end loop;
        return r;
    end function;

begin

    active <= '1' when mode = M_PONG else '0';

    ------------------------------------------------------------------
    -- Modus und Drehwinkel nur am Bildende fortschreiben
    ------------------------------------------------------------------
    process (clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                mode    <= M_MSG;
                ang     <= 0;
                ang_div <= 0;
            elsif frame_tick = '1' then
                mode <= decode(sw);
                if mode = M_ROT then
                    if ang_div = ROT_FRAMES - 1 then
                        ang_div <= 0;
                        ang     <= (ang + 1) mod SPR_N;
                    else
                        ang_div <= ang_div + 1;
                    end if;
                else
                    ang     <= 0;
                    ang_div <= 0;
                end if;
            end if;
        end if;
    end process;

    u_pong : entity work.pong_game
        port map (
            clk        => clk,
            rst        => rst,
            active     => active,
            frame_tick => frame_tick,
            l_up       => btn(0),
            l_dn       => btn(1),
            r_up       => btn(2),
            r_dn       => btn(3),
            x          => x,
            y          => y,
            pix_on     => pong_on
        );

    ------------------------------------------------------------------
    -- Pixel-Pipeline
    ------------------------------------------------------------------
    process (clk)
        variable sx, sy : integer;
    begin
        if rising_edge(clk) then
            -- Stufe 1: Bitmap-Zeile holen, Lage im Sprite-Fenster bestimmen
            case mode is
                when M_HHN  => row1 <= HHN_ROM(to_integer(y));
                when M_MSG  => row1 <= MSG_ROM(to_integer(y));
                when others => row1 <= BOSCH_ROM(to_integer(y));
            end case;
            x1 <= x;
            sx := to_integer(x) - SPR_X0;
            sy := to_integer(y) - SPR_Y0;
            if sx >= 0 and sx < SPR_SIZE and sy >= 0 and sy < SPR_SIZE then
                in_box1 <= '1';
                sx1     <= sx;
                sidx1   <= ang * SPR_SIZE + sy;
            else
                in_box1 <= '0';
                sx1     <= 0;
                sidx1   <= 0;
            end if;

            -- Stufe 2: Pixel bzw. Sprite-Zeile auswaehlen
            idx2    <= get_px(row1, x1);
            srow2   <= SPR_ROM(sidx1);
            in_box2 <= in_box1;
            sx2     <= sx1;

            -- Stufe 3: Palette, Sprite-Pixel
            case mode is
                when M_HHN  => col3 <= HHN_PAL(to_integer(unsigned(idx2)));
                when M_MSG  => col3 <= MSG_PAL(to_integer(unsigned(idx2)));
                when others => col3 <= BOSCH_PAL(to_integer(unsigned(idx2)));
            end case;
            sym3    <= get_spx(srow2, sx2);
            in_box3 <= in_box2;

            -- Stufe 4: Sprite-Palette
            col4    <= col3;
            sym4    <= SYM_PAL(to_integer(unsigned(sym3)));
            in_box4 <= in_box3;

            -- Stufe 5: Ausgabe
            if mode = M_PONG then
                if pong_on = '1' then
                    pix <= x"FFFF";
                else
                    pix <= x"0000";
                end if;
            elsif in_box4 = '1' and (mode = M_BOSCH or mode = M_ROT) then
                pix <= sym4;
            else
                pix <= col4;
            end if;
        end if;
    end process;

end architecture rtl;
