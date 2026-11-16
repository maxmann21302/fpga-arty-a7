----------------------------------------------------------------------------------
-- Projekt      : Prell-Oszilloskop (Pmod OLEDrgb an JD)
-- Modul        : bounce_top
-- Bedienung    : BTN0  Messeingang (nur synchronisiert, NICHT entprellt)
--                SW0   Triggerflanke: 0 = steigend (Druecken), 1 = fallend (Loslassen)
--                SW1   Messeingang: 0 = BTN0, 1 = Pmod JA1 (interner Pull-down)
--                BTN1  Aufnahme loeschen, neu scharf schalten
--                BTN2  Zeitbasis kleiner (min. 1 us/div), loescht die Aufnahme
--                BTN3  Zeitbasis groesser (max. 10 ms/div), loescht die Aufnahme
--                Umschalten von SW0/SW1 loescht die Aufnahme ebenfalls
--                RESET alles zuruecksetzen, Display neu initialisieren
----------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.bounce_pkg.all;

entity bounce_top is
    generic (
        DEBOUNCE_CYCLES : positive := 1_000_000;
        SPI_HALF        : positive := 8
    );
    port (
        CLK100MHZ   : in  std_logic;
        ck_rst      : in  std_logic;
        btn         : in  std_logic_vector(3 downto 0);
        sw          : in  std_logic_vector(1 downto 0);
        ext_in      : in  std_logic;
        oled_cs     : out std_logic;
        oled_mosi   : out std_logic;
        oled_sck    : out std_logic;
        oled_dc     : out std_logic;
        oled_res    : out std_logic;
        oled_vccen  : out std_logic;
        oled_pmoden : out std_logic
    );
end entity bounce_top;

architecture rtl of bounce_top is

    signal reset_sync : std_logic_vector(1 downto 0) := (others => '1');
    signal rst        : std_logic;
    signal btn0_sync  : std_logic_vector(1 downto 0) := (others => '0');
    signal ext_sync   : std_logic_vector(1 downto 0) := (others => '0');
    signal sw_meta    : std_logic_vector(1 downto 0) := (others => '0');
    signal sw_sync    : std_logic_vector(1 downto 0) := (others => '0');
    signal sw_prev    : std_logic_vector(1 downto 0) := (others => '0');
    signal sig        : std_logic;
    signal press      : std_logic_vector(3 downto 1);
    signal clear      : std_logic;

    signal tb_idx     : natural range 0 to TB_COUNT - 1 := TB_DEFAULT;
    signal period     : period_t := TB_PERIOD(TB_DEFAULT);

    signal hi_buf     : std_logic_vector(SAMPLES - 1 downto 0);
    signal lo_buf     : std_logic_vector(SAMPLES - 1 downto 0);
    signal armed      : std_logic;
    signal done       : std_logic;

    signal pix_x      : unsigned(6 downto 0);
    signal pix_y      : unsigned(5 downto 0);
    signal pix        : std_logic_vector(15 downto 0);

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
            btn0_sync <= btn0_sync(0) & btn(0);
            ext_sync  <= ext_sync(0) & ext_in;
            sw_meta   <= sw;
            sw_sync   <= sw_meta;
            sw_prev   <= sw_sync;
        end if;
    end process;

    sig <= ext_sync(1) when sw_sync(1) = '1' else btn0_sync(1);

    gen_btn : for i in 1 to 3 generate
        u_btn : entity work.btn_debounce
            generic map (DEBOUNCE_CYCLES => DEBOUNCE_CYCLES)
            port map (clk => CLK100MHZ, rst => rst, btn_i => btn(i), press_o => press(i));
    end generate;

    process (CLK100MHZ)
    begin
        if rising_edge(CLK100MHZ) then
            if rst = '1' then
                tb_idx <= TB_DEFAULT;
            elsif press(2) = '1' and tb_idx > 0 then
                tb_idx <= tb_idx - 1;
            elsif press(3) = '1' and tb_idx < TB_COUNT - 1 then
                tb_idx <= tb_idx + 1;
            end if;
            period <= TB_PERIOD(tb_idx);
        end if;
    end process;

    -- alte Aufnahme passt nicht mehr zu neuer Zeitbasis / Quelle / Flanke
    clear <= '1' when press /= "000" or sw_sync /= sw_prev else '0';

    u_capture : entity work.bounce_capture
        port map (
            clk    => CLK100MHZ,
            rst    => rst,
            clear  => clear,
            sig    => sig,
            edge   => sw_sync(0),
            period => period,
            hi_buf => hi_buf,
            lo_buf => lo_buf,
            armed  => armed,
            done   => done
        );

    u_render : entity work.bounce_render
        port map (
            clk    => CLK100MHZ,
            x      => pix_x,
            y      => pix_y,
            hi_buf => hi_buf,
            lo_buf => lo_buf,
            armed  => armed,
            done   => done,
            src    => sw_sync(1),
            edge   => sw_sync(0),
            tb_idx => tb_idx,
            pix    => pix
        );

    u_ctrl : entity work.oled_ctrl
        generic map (T_US => 100, SPI_HALF => SPI_HALF)
        port map (
            clk         => CLK100MHZ,
            rst         => rst,
            pix_x       => pix_x,
            pix_y       => pix_y,
            pix_in      => pix,
            frame_tick  => open,
            oled_cs     => oled_cs,
            oled_mosi   => oled_mosi,
            oled_sck    => oled_sck,
            oled_dc     => oled_dc,
            oled_res    => oled_res,
            oled_vccen  => oled_vccen,
            oled_pmoden => oled_pmoden
        );

end architecture rtl;
