----------------------------------------------------------------------------------
-- Projekt      : Labor 7-Segment-Anzeige, Phase II
-- Modul        : phase2_top
-- Beschreibung : Betriebsarten ueber SW0..SW2 (genau ein Schalter aktiv)
--                SW0: Sekundenzaehler 00..99, rechtes SSD (JA/JB), linkes SSD aus
--                SW1: Sekundenzaehler 0000..9999 ueber beide SSD (JC/JD links)
--                SW2: Stoppuhr, links Sekunden 00..99, rechts Hundertstel 00..99
--                     BTN0 Start, BTN1 Stopp, BTN2 Nullen (nur im Stopp)
--                sonst (kein / mehrere Schalter, SW3): beide Anzeigen dunkel
--                Alle Zaehler laufen unabhaengig von der Betriebsart weiter.
----------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.clock_pkg.all;

entity phase2_top is
    generic (
        CLK_HZ          : positive := 100_000_000;
        DEBOUNCE_CYCLES : positive := 1_000_000;
        REFRESH_HZ      : positive := 500
    );
    port (
        CLK100MHZ : in  std_logic;
        ck_rst    : in  std_logic;
        sw        : in  std_logic_vector(3 downto 0);
        btn       : in  std_logic_vector(3 downto 0);
        seg_r     : out std_logic_vector(6 downto 0);
        dsel_r    : out std_logic;
        seg_l     : out std_logic_vector(6 downto 0);
        dsel_l    : out std_logic
    );
end entity phase2_top;

architecture rtl of phase2_top is

    constant MODE_SEC99   : std_logic_vector(3 downto 0) := "0001";
    constant MODE_SEC9999 : std_logic_vector(3 downto 0) := "0010";
    constant MODE_STOP    : std_logic_vector(3 downto 0) := "0100";

    constant CS_DIV : positive := max_nat(1, CLK_HZ / 100);

    signal reset_sync : std_logic_vector(1 downto 0) := (others => '1');
    signal rst        : std_logic;
    signal sw_meta    : std_logic_vector(3 downto 0) := (others => '0');
    signal sw_sync    : std_logic_vector(3 downto 0) := (others => '0');
    signal press      : std_logic_vector(2 downto 0);

    signal tick_sec   : std_logic;
    signal tick_cs    : std_logic;

    signal cnt_a      : natural range 0 to 99 := 0;
    signal cnt_b_lo   : natural range 0 to 99 := 0;
    signal cnt_b_hi   : natural range 0 to 99 := 0;

    signal running    : std_logic := '0';
    signal sw_start   : std_logic;
    signal sw_stop    : std_logic;
    signal sw_zero    : std_logic;
    signal stop_cs    : natural range 0 to 99 := 0;
    signal stop_s     : natural range 0 to 99 := 0;

    signal val_l      : natural range 0 to 99;
    signal val_r      : natural range 0 to 99;
    signal show_l     : std_logic;
    signal show_r     : std_logic;
    signal blank_l    : std_logic;
    signal blank_r    : std_logic;
    signal bcd_l      : bcd2_t;
    signal bcd_r      : bcd2_t;

begin

    -- Reset: asynchron anfordern (ck_rst aktiv Low), synchron freigeben
    process (CLK100MHZ, ck_rst)
    begin
        if ck_rst = '0' then
            reset_sync <= (others => '1');
        elsif rising_edge(CLK100MHZ) then
            reset_sync <= reset_sync(0) & '0';
        end if;
    end process;

    rst <= reset_sync(1);

    process (CLK100MHZ)
    begin
        if rising_edge(CLK100MHZ) then
            sw_meta <= sw;
            sw_sync <= sw_meta;
        end if;
    end process;

    gen_btn : for i in 0 to 2 generate
        u_btn : entity work.btn_debounce
            generic map (DEBOUNCE_CYCLES => DEBOUNCE_CYCLES)
            port map (clk => CLK100MHZ, rst => rst, btn_i => btn(i), press_o => press(i));
    end generate;

    -- Tasten wirken nur in der Betriebsart Stoppuhr
    sw_start <= '1' when sw_sync = MODE_STOP and press(0) = '1' else '0';
    sw_stop  <= '1' when sw_sync = MODE_STOP and press(1) = '1' else '0';
    sw_zero  <= '1' when sw_sync = MODE_STOP and press(2) = '1' and running = '0' else '0';

    u_tick_sec : entity work.tick_gen
        generic map (DIV => CLK_HZ)
        port map (clk => CLK100MHZ, rst => rst, tick => tick_sec);

    -- Vorteiler haelt im Stopp seinen Stand, Nullen setzt ihn mit zurueck
    u_tick_cs : entity work.tick_gen
        generic map (DIV => CS_DIV)
        port map (clk => CLK100MHZ, rst => rst, en => running, clr => sw_zero, tick => tick_cs);

    process (CLK100MHZ)
    begin
        if rising_edge(CLK100MHZ) then
            if rst = '1' then
                cnt_a    <= 0;
                cnt_b_lo <= 0;
                cnt_b_hi <= 0;
            elsif tick_sec = '1' then
                if cnt_a = 99 then
                    cnt_a <= 0;
                else
                    cnt_a <= cnt_a + 1;
                end if;

                if cnt_b_lo = 99 then
                    cnt_b_lo <= 0;
                    if cnt_b_hi = 99 then
                        cnt_b_hi <= 0;
                    else
                        cnt_b_hi <= cnt_b_hi + 1;
                    end if;
                else
                    cnt_b_lo <= cnt_b_lo + 1;
                end if;
            end if;
        end if;
    end process;

    process (CLK100MHZ)
    begin
        if rising_edge(CLK100MHZ) then
            if rst = '1' then
                running <= '0';
                stop_cs <= 0;
                stop_s  <= 0;
            else
                if sw_start = '1' then
                    running <= '1';
                elsif sw_stop = '1' then
                    running <= '0';
                end if;

                if sw_zero = '1' then
                    stop_cs <= 0;
                    stop_s  <= 0;
                elsif tick_cs = '1' then
                    if stop_cs = 99 then
                        stop_cs <= 0;
                        if stop_s = 99 then
                            stop_s <= 0;
                        else
                            stop_s <= stop_s + 1;
                        end if;
                    else
                        stop_cs <= stop_cs + 1;
                    end if;
                end if;
            end if;
        end if;
    end process;

    process (sw_sync, cnt_a, cnt_b_lo, cnt_b_hi, stop_cs, stop_s)
    begin
        val_l  <= 0;
        val_r  <= 0;
        show_l <= '0';
        show_r <= '0';
        case sw_sync is
            when MODE_SEC99 =>
                val_r <= cnt_a;    show_r <= '1';
            when MODE_SEC9999 =>
                val_l <= cnt_b_hi; show_l <= '1';
                val_r <= cnt_b_lo; show_r <= '1';
            when MODE_STOP =>
                val_l <= stop_s;   show_l <= '1';
                val_r <= stop_cs;  show_r <= '1';
            when others =>
                null;
        end case;
    end process;

    bcd_l   <= to_bcd2(to_unsigned(val_l, 7));
    bcd_r   <= to_bcd2(to_unsigned(val_r, 7));
    blank_l <= not show_l;
    blank_r <= not show_r;

    display_r : entity work.ssd_driver
        generic map (CLK_HZ => CLK_HZ, REFRESH_HZ => REFRESH_HZ)
        port map (
            clk    => CLK100MHZ,
            rst    => rst,
            digit0 => bcd_r.ones,
            digit1 => bcd_r.tens,
            blank  => blank_r,
            seg    => seg_r,
            dsel   => dsel_r
        );

    display_l : entity work.ssd_driver
        generic map (CLK_HZ => CLK_HZ, REFRESH_HZ => REFRESH_HZ)
        port map (
            clk    => CLK100MHZ,
            rst    => rst,
            digit0 => bcd_l.ones,
            digit1 => bcd_l.tens,
            blank  => blank_l,
            seg    => seg_l,
            dsel   => dsel_l
        );

end architecture rtl;
