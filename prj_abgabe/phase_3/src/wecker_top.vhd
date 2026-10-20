----------------------------------------------------------------------------------
-- Projekt      : Digitale Uhr / Wecker (Arty A7-35T + 2x Pmod SSD)
-- Modul        : wecker_top (Top-Level, struktureller Aufbau)
--
-- Bedienung
--   RESET-Taster : Uhr auf 00:00:00, Weckzeit auf 07:00
--   sw0          : Anzeige MM:SS statt HH:MM
--   sw1          : Zeit stellen
--   sw2          : Weckzeit stellen (hat Vorrang vor sw1)
--   sw3          : Wecker scharf
--   btn0/btn1    : Stunden +/-        btn2/btn3 : Minuten +/-
--   Bei Alarm stoppt jeder Tastendruck den Wecker (kein Verstellen).
----------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

use work.clock_pkg.all;

entity wecker_top is
    generic (
        CLK_HZ : positive := 100_000_000
    );
    port (
        CLK100MHZ : in  std_logic;
        ck_rst    : in  std_logic;                      -- RESET-Taster, aktiv low
        sw        : in  std_logic_vector(3 downto 0);
        btn       : in  std_logic_vector(3 downto 0);
        led       : out std_logic_vector(3 downto 0);
        seg_l     : out std_logic_vector(6 downto 0);
        dsel_l    : out std_logic;
        seg_r     : out std_logic_vector(6 downto 0);
        dsel_r    : out std_logic;
        buzzer_o  : out std_logic
    );
end entity wecker_top;

architecture structural of wecker_top is

    constant BLINK_DIV : positive := max_nat(1, CLK_HZ / 4);   -- 2 Hz Blinken

    signal rst_sync  : std_logic_vector(1 downto 0) := (others => '1');
    signal rst       : std_logic;

    signal btn_level : std_logic_vector(3 downto 0);
    signal btn_pulse : std_logic_vector(3 downto 0);

    signal show_sec  : std_logic;
    signal set_time  : std_logic;
    signal set_alarm : std_logic;
    signal alarm_en  : std_logic;

    signal adj_en    : std_logic;
    signal inc_h     : std_logic;
    signal dec_h     : std_logic;
    signal inc_m     : std_logic;
    signal dec_m     : std_logic;
    signal any_pulse : std_logic;
    signal stop      : std_logic;

    signal hours     : unsigned(5 downto 0);
    signal minutes   : unsigned(5 downto 0);
    signal seconds   : unsigned(5 downto 0);
    signal al_hours  : unsigned(5 downto 0);
    signal al_min    : unsigned(5 downto 0);
    signal tick_1hz  : std_logic;
    signal ringing   : std_logic;

    signal l_tens, l_ones : unsigned(3 downto 0);
    signal r_tens, r_ones : unsigned(3 downto 0);

    signal blink_tick : std_logic;
    signal blink      : std_logic := '0';
    signal heartbeat  : std_logic := '0';
    signal led_normal : std_logic_vector(3 downto 0);
    signal led_blink  : std_logic_vector(3 downto 0);

begin

    ------------------------------------------------------------------
    -- Reset (Arty RESET-Taster ist aktiv low) einsynchronisieren
    ------------------------------------------------------------------
    process (CLK100MHZ)
    begin
        if rising_edge(CLK100MHZ) then
            rst_sync <= rst_sync(0) & (not ck_rst);
        end if;
    end process;

    rst <= rst_sync(1);

    ------------------------------------------------------------------
    -- Tastereingaben
    ------------------------------------------------------------------
    g_btn : for i in 0 to 3 generate
        u_db : entity work.debounce
            generic map (CLK_HZ => CLK_HZ)
            port map (
                clk   => CLK100MHZ,
                rst   => rst,
                btn   => btn(i),
                level => btn_level(i),
                pulse => btn_pulse(i)
            );
    end generate g_btn;

    ------------------------------------------------------------------
    -- Betriebsart
    ------------------------------------------------------------------
    show_sec  <= sw(0);
    set_alarm <= sw(2);
    set_time  <= sw(1) and not sw(2);
    alarm_en  <= sw(3);

    any_pulse <= btn_pulse(0) or btn_pulse(1) or btn_pulse(2) or btn_pulse(3);
    stop      <= any_pulse and ringing;
    adj_en    <= not ringing;

    inc_h <= btn_pulse(0) and adj_en;
    dec_h <= btn_pulse(1) and adj_en;
    inc_m <= btn_pulse(2) and adj_en;
    dec_m <= btn_pulse(3) and adj_en;

    ------------------------------------------------------------------
    -- Uhr und Wecker
    ------------------------------------------------------------------
    u_clock : entity work.clock_core
        generic map (CLK_HZ => CLK_HZ)
        port map (
            clk      => CLK100MHZ,
            rst      => rst,
            set_mode => set_time,
            inc_h    => inc_h,
            dec_h    => dec_h,
            inc_m    => inc_m,
            dec_m    => dec_m,
            hours    => hours,
            minutes  => minutes,
            seconds  => seconds,
            tick_1hz => tick_1hz
        );

    u_alarm : entity work.alarm_core
        port map (
            clk      => CLK100MHZ,
            rst      => rst,
            set_mode => set_alarm,
            inc_h    => inc_h,
            dec_h    => dec_h,
            inc_m    => inc_m,
            dec_m    => dec_m,
            enable   => alarm_en,
            stop     => stop,
            cur_h    => hours,
            cur_m    => minutes,
            cur_s    => seconds,
            al_h     => al_hours,
            al_m     => al_min,
            ringing  => ringing
        );

    ------------------------------------------------------------------
    -- Anzeige
    ------------------------------------------------------------------
    u_mux : entity work.display_mux
        port map (
            show_seconds => show_sec,
            set_time     => set_time,
            set_alarm    => set_alarm,
            hours        => hours,
            minutes      => minutes,
            seconds      => seconds,
            al_hours     => al_hours,
            al_minutes   => al_min,
            left_tens    => l_tens,
            left_ones    => l_ones,
            right_tens   => r_tens,
            right_ones   => r_ones
        );

    u_ssd_left : entity work.ssd_driver
        generic map (CLK_HZ => CLK_HZ)
        port map (
            clk    => CLK100MHZ,
            rst    => rst,
            digit0 => l_ones,
            digit1 => l_tens,
            seg    => seg_l,
            dsel   => dsel_l
        );

    u_ssd_right : entity work.ssd_driver
        generic map (CLK_HZ => CLK_HZ)
        port map (
            clk    => CLK100MHZ,
            rst    => rst,
            digit0 => r_ones,
            digit1 => r_tens,
            seg    => seg_r,
            dsel   => dsel_r
        );

    ------------------------------------------------------------------
    -- Signalausgabe optisch / akustisch
    ------------------------------------------------------------------
    u_blink : entity work.tick_gen
        generic map (DIV => BLINK_DIV)
        port map (clk => CLK100MHZ, rst => rst, tick => blink_tick);

    process (CLK100MHZ)
    begin
        if rising_edge(CLK100MHZ) then
            if rst = '1' then
                blink     <= '0';
                heartbeat <= '0';
            else
                if blink_tick = '1' then
                    blink <= not blink;
                end if;
                if tick_1hz = '1' then
                    heartbeat <= not heartbeat;
                end if;
            end if;
        end if;
    end process;

    led_normal <= heartbeat & set_alarm & set_time & alarm_en;
    led_blink  <= blink & blink & blink & blink;
    led        <= led_blink when ringing = '1' else led_normal;

    u_buzz : entity work.buzzer
        generic map (CLK_HZ => CLK_HZ)
        port map (clk => CLK100MHZ, rst => rst, enable => ringing, buzz => buzzer_o);

end architecture structural;
