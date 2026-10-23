----------------------------------------------------------------------------------
-- Modul        : pong_game
-- Beschreibung : Pong 1 gegen 1 auf 96x64 Pixeln. Spielzustand wird einmal pro
--                Bild (frame_tick) fortgeschrieben; pix_on liefert nach 2 Takten
--                das Pixel (weiss/schwarz) zu (x, y).
--                active = '0' haelt das Spiel im Anfangszustand.
----------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity pong_game is
    port (
        clk        : in  std_logic;
        rst        : in  std_logic;
        active     : in  std_logic;
        frame_tick : in  std_logic;
        l_up       : in  std_logic;
        l_dn       : in  std_logic;
        r_up       : in  std_logic;
        r_dn       : in  std_logic;
        x          : in  unsigned(6 downto 0);
        y          : in  unsigned(5 downto 0);
        pix_on     : out std_logic
    );
end entity pong_game;

architecture rtl of pong_game is

    constant PAD_H     : natural := 14;
    constant PAD_W     : natural := 2;
    constant PAD_LX    : natural := 4;
    constant PAD_RX    : natural := 90;
    constant PAD_SPEED : natural := 3;
    constant BALL      : natural := 3;
    constant VX_START  : natural := 2;
    constant VX_MAX    : natural := 4;
    constant WIN_SCORE : natural := 9;
    constant SERVE_FRAMES : natural := 45;
    constant OVER_FRAMES  : natural := 150;

    signal pl_y, pr_y     : integer range 0 to 63 := 25;
    signal bx             : integer range 0 to 95 := 46;
    signal by             : integer range 0 to 63 := 30;
    signal vx             : integer range -VX_MAX to VX_MAX := VX_START;
    signal vy             : integer range -2 to 2 := 1;
    signal score_l        : natural range 0 to 9 := 0;
    signal score_r        : natural range 0 to 9 := 0;
    signal serve_cnt      : natural range 0 to OVER_FRAMES := SERVE_FRAMES;
    signal over_cnt       : natural range 0 to OVER_FRAMES := 0;
    signal lfsr           : std_logic_vector(7 downto 0) := x"A5";

    -- Pixel-Pipeline
    signal s1_l, s1_r, s1_ball, s1_net : std_logic := '0';
    signal s1_dig_en  : std_logic := '0';
    signal s1_dig     : natural range 0 to 9 := 0;
    signal s1_gx      : natural range 0 to 2 := 0;
    signal s1_gy      : natural range 0 to 4 := 0;
    signal s2_dig     : std_logic := '0';

    type digit_rom_t is array (0 to 9) of std_logic_vector(0 to 14);   -- 3x5, Zeilenweise
    constant DIGITS : digit_rom_t := (
        "111101101101111", "010110010010111", "111001111100111", "111001111001111",
        "101101111001001", "111100111001111", "111100111101111", "111001001001001",
        "111101111101111", "111101111001111"
    );

    constant DIG_Y  : natural := 3;
    constant DIG_LX : natural := 35;
    constant DIG_RX : natural := 55;

    function clamp_pad (v : integer) return integer is
    begin
        if v < 0 then
            return 0;
        elsif v > 64 - PAD_H then
            return 64 - PAD_H;
        end if;
        return v;
    end function;

    function deflect (offset : integer) return integer is
    begin
        if offset < 4 then
            return -2;
        elsif offset < 7 then
            return -1;
        elsif offset < 10 then
            return 1;
        end if;
        return 2;
    end function;

    function serve_vy (r : std_logic_vector(1 downto 0)) return integer is
    begin
        case r is
            when "00"   => return -2;
            when "01"   => return -1;
            when "10"   => return 1;
            when others => return 2;
        end case;
    end function;

begin

    ------------------------------------------------------------------
    -- Zufallszahl fuer den Aufschlagwinkel
    ------------------------------------------------------------------
    process (clk)
    begin
        if rising_edge(clk) then
            lfsr <= lfsr(6 downto 0) & (lfsr(7) xor lfsr(5) xor lfsr(4) xor lfsr(3));
        end if;
    end process;

    ------------------------------------------------------------------
    -- Spiellogik, einmal pro Bild
    ------------------------------------------------------------------
    process (clk)
        variable nx, ny : integer;
        variable left_out : boolean;
    begin
        if rising_edge(clk) then
            if rst = '1' or active = '0' then
                pl_y      <= 25;
                pr_y      <= 25;
                bx        <= 46;
                by        <= 30;
                vx        <= VX_START;
                vy        <= 1;
                score_l   <= 0;
                score_r   <= 0;
                serve_cnt <= SERVE_FRAMES;
                over_cnt  <= 0;
            elsif frame_tick = '1' then

                -- Schlaeger
                if l_up = '1' and l_dn = '0' then
                    pl_y <= clamp_pad(pl_y - PAD_SPEED);
                elsif l_dn = '1' and l_up = '0' then
                    pl_y <= clamp_pad(pl_y + PAD_SPEED);
                end if;
                if r_up = '1' and r_dn = '0' then
                    pr_y <= clamp_pad(pr_y - PAD_SPEED);
                elsif r_dn = '1' and r_up = '0' then
                    pr_y <= clamp_pad(pr_y + PAD_SPEED);
                end if;

                if over_cnt > 0 then              -- Spielende: Anzeige halten, dann neu
                    over_cnt <= over_cnt - 1;
                    if over_cnt = 1 then
                        score_l   <= 0;
                        score_r   <= 0;
                        serve_cnt <= SERVE_FRAMES;
                    end if;
                elsif serve_cnt > 0 then          -- Pause vor dem Aufschlag
                    serve_cnt <= serve_cnt - 1;
                else
                    nx := bx + vx;
                    ny := by + vy;

                    if ny < 0 then
                        ny := 0;
                        vy <= -vy;
                    elsif ny > 64 - BALL then
                        ny := 64 - BALL;
                        vy <= -vy;
                    end if;

                    if vx < 0 and nx <= PAD_LX + PAD_W - 1 and nx + BALL - 1 >= PAD_LX
                       and ny + BALL > pl_y and ny < pl_y + PAD_H then
                        -- Treffer links
                        nx := PAD_LX + PAD_W;
                        if -vx < VX_MAX then
                            vx <= -vx + 1;
                        else
                            vx <= VX_MAX;
                        end if;
                        vy <= deflect(ny + 1 - pl_y);
                    elsif vx > 0 and nx + BALL - 1 >= PAD_RX and nx <= PAD_RX + PAD_W - 1
                       and ny + BALL > pr_y and ny < pr_y + PAD_H then
                        -- Treffer rechts
                        nx := PAD_RX - BALL;
                        if vx < VX_MAX then
                            vx <= -(vx + 1);
                        else
                            vx <= -VX_MAX;
                        end if;
                        vy <= deflect(ny + 1 - pr_y);
                    end if;

                    if nx <= 0 or nx + BALL >= 96 then
                        -- Punkt: Ball zurueck in die Mitte, Aufschlag zum Verlierer
                        left_out := nx <= 0;
                        nx := 46;
                        ny := 30;
                        vy <= serve_vy(lfsr(1 downto 0));
                        serve_cnt <= SERVE_FRAMES;
                        if left_out then
                            vx <= -VX_START;
                            score_r <= score_r + 1;
                            if score_r + 1 = WIN_SCORE then
                                over_cnt <= OVER_FRAMES;
                            end if;
                        else
                            vx <= VX_START;
                            score_l <= score_l + 1;
                            if score_l + 1 = WIN_SCORE then
                                over_cnt <= OVER_FRAMES;
                            end if;
                        end if;
                    end if;

                    bx <= nx;
                    by <= ny;
                end if;
            end if;
        end if;
    end process;

    ------------------------------------------------------------------
    -- Pixelausgabe (2 Pipeline-Stufen)
    ------------------------------------------------------------------
    process (clk)
        variable xi, yi : integer;
        variable rx, ry : integer;
    begin
        if rising_edge(clk) then
            xi := to_integer(x);
            yi := to_integer(y);

            if xi >= PAD_LX and xi < PAD_LX + PAD_W and yi >= pl_y and yi < pl_y + PAD_H then
                s1_l <= '1';
            else
                s1_l <= '0';
            end if;

            if xi >= PAD_RX and xi < PAD_RX + PAD_W and yi >= pr_y and yi < pr_y + PAD_H then
                s1_r <= '1';
            else
                s1_r <= '0';
            end if;

            if xi >= bx and xi < bx + BALL and yi >= by and yi < by + BALL then
                s1_ball <= '1';
            else
                s1_ball <= '0';
            end if;

            if xi = 47 and y(2) = '0' then
                s1_net <= '1';
            else
                s1_net <= '0';
            end if;

            s1_dig_en <= '0';
            s1_dig    <= 0;
            s1_gx     <= 0;
            s1_gy     <= 0;
            ry := yi - DIG_Y;
            if ry >= 0 and ry < 10 then
                rx := xi - DIG_LX;
                if rx >= 0 and rx < 6 then
                    s1_dig_en <= '1';
                    s1_dig    <= score_l;
                    s1_gx     <= rx / 2;
                    s1_gy     <= ry / 2;
                end if;
                rx := xi - DIG_RX;
                if rx >= 0 and rx < 6 then
                    s1_dig_en <= '1';
                    s1_dig    <= score_r;
                    s1_gx     <= rx / 2;
                    s1_gy     <= ry / 2;
                end if;
            end if;

            s2_dig <= s1_dig_en and DIGITS(s1_dig)(s1_gy * 3 + s1_gx);
            pix_on <= s1_l or s1_r or s1_ball or s1_net or s2_dig;
        end if;
    end process;

end architecture rtl;
