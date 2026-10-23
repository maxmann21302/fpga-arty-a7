----------------------------------------------------------------------------------
-- Projekt      : Pmod OLEDrgb (SPI) an JD
-- Modul        : spi_top
--
-- Bedienung (genau EIN Schalter oben, sonst Hinweis "Waehle einen Schalter")
--   sw0 : Bosch-Logo
--   sw1 : Bosch-Logo mit rotierendem Anker
--   sw2 : HHN-Logo
--   sw3 : Pong 1 gegen 1   btn0/btn1 = links hoch/runter, btn2/btn3 = rechts hoch/runter
--   RESET-Taster : Display neu initialisieren
----------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity spi_top is
    generic (
        CLK_HZ   : positive := 100_000_000;
        SPI_HALF : positive := 8
    );
    port (
        CLK100MHZ   : in  std_logic;
        ck_rst      : in  std_logic;                  -- RESET-Taster, aktiv low
        sw          : in  std_logic_vector(3 downto 0);
        btn         : in  std_logic_vector(3 downto 0);
        led         : out std_logic_vector(3 downto 0);
        oled_cs     : out std_logic;                  -- JD1
        oled_mosi   : out std_logic;                  -- JD2
        oled_sck    : out std_logic;                  -- JD4
        oled_dc     : out std_logic;                  -- JD7
        oled_res    : out std_logic;                  -- JD8
        oled_vccen  : out std_logic;                  -- JD9
        oled_pmoden : out std_logic                   -- JD10
    );
end entity spi_top;

architecture structural of spi_top is

    constant DB_CYCLES : positive := (CLK_HZ / 1000) * 10;

    signal rst_sync   : std_logic_vector(1 downto 0) := (others => '1');
    signal rst        : std_logic;
    signal sw_f       : std_logic_vector(3 downto 0);
    signal btn_f      : std_logic_vector(3 downto 0);
    signal pix_x      : unsigned(6 downto 0);
    signal pix_y      : unsigned(5 downto 0);
    signal pix        : std_logic_vector(15 downto 0);
    signal frame_tick : std_logic;

begin

    process (CLK100MHZ)
    begin
        if rising_edge(CLK100MHZ) then
            rst_sync <= rst_sync(0) & (not ck_rst);
        end if;
    end process;

    rst <= rst_sync(1);

    g_in : for i in 0 to 3 generate
        u_sw : entity work.input_filter
            generic map (DEBOUNCE_CYCLES => DB_CYCLES)
            port map (clk => CLK100MHZ, rst => rst, d => sw(i), q => sw_f(i));
        u_btn : entity work.input_filter
            generic map (DEBOUNCE_CYCLES => DB_CYCLES)
            port map (clk => CLK100MHZ, rst => rst, d => btn(i), q => btn_f(i));
    end generate g_in;

    led <= sw_f;

    u_render : entity work.oled_render
        port map (
            clk        => CLK100MHZ,
            rst        => rst,
            x          => pix_x,
            y          => pix_y,
            frame_tick => frame_tick,
            sw         => sw_f,
            btn        => btn_f,
            pix        => pix
        );

    u_ctrl : entity work.oled_ctrl
        generic map (
            T_US     => CLK_HZ / 1_000_000,
            SPI_HALF => SPI_HALF
        )
        port map (
            clk         => CLK100MHZ,
            rst         => rst,
            pix_x       => pix_x,
            pix_y       => pix_y,
            pix_in      => pix,
            frame_tick  => frame_tick,
            oled_cs     => oled_cs,
            oled_mosi   => oled_mosi,
            oled_sck    => oled_sck,
            oled_dc     => oled_dc,
            oled_res    => oled_res,
            oled_vccen  => oled_vccen,
            oled_pmoden => oled_pmoden
        );

end architecture structural;
