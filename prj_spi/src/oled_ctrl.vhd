----------------------------------------------------------------------------------
-- Modul        : oled_ctrl
-- Beschreibung : Ansteuerung des Pmod OLEDrgb (SSD1331, 96x64, RGB565) ueber SPI.
--                Ablauf: Einschalten, Reset, Init-Sequenz, danach laufend Vollbild-
--                Aufbau. Fuer jedes Pixel wird (pix_x, pix_y) ausgegeben und nach
--                PIPE_WAIT Takten das Pixel von pix_in uebernommen.
--                frame_tick = 1 Takt nach Ende jedes Bildes.
----------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity oled_ctrl is
    generic (
        T_US      : positive := 100;              -- Takte pro Mikrosekunde
        SPI_HALF  : positive := 8;                -- SCK = CLK / (2*SPI_HALF)
        PIPE_WAIT : positive := 12                -- Latenz des Pixelgenerators
    );
    port (
        clk         : in  std_logic;
        rst         : in  std_logic;
        pix_x       : out unsigned(6 downto 0);
        pix_y       : out unsigned(5 downto 0);
        pix_in      : in  std_logic_vector(15 downto 0);
        frame_tick  : out std_logic;
        oled_cs     : out std_logic;
        oled_mosi   : out std_logic;
        oled_sck    : out std_logic;
        oled_dc     : out std_logic;
        oled_res    : out std_logic;
        oled_vccen  : out std_logic;
        oled_pmoden : out std_logic
    );
end entity oled_ctrl;

architecture rtl of oled_ctrl is

    type byte_arr is array (natural range <>) of std_logic_vector(7 downto 0);

    -- Init-Sequenz laut SSD1331-Datenblatt / Digilent-Referenz
    constant INIT_CMD : byte_arr(0 to 36) := (
        x"AE",                                    -- Display aus
        x"A0", x"72",                             -- Remap: 65k Farben, RGB, Ausrichtung
        x"A1", x"00",                             -- Startzeile
        x"A2", x"00",                             -- Display-Offset
        x"A4",                                    -- normale Anzeige
        x"A8", x"3F",                             -- Multiplex 64
        x"AD", x"8E",                             -- externe VCC
        x"B0", x"0B",                             -- Power-Save aus
        x"B1", x"31",                             -- Phase-Adjust
        x"B3", x"F0",                             -- Takt-Teiler
        x"8A", x"64", x"8B", x"78", x"8C", x"64", -- Precharge A/B/C
        x"BB", x"3A",                             -- Precharge-Level
        x"BE", x"3E",                             -- VCOMH
        x"87", x"06",                             -- Master-Strom
        x"81", x"91", x"82", x"50", x"83", x"7D", -- Kontrast A/B/C
        x"2E"                                     -- Scrolling aus
    );

    -- Fenster = ganzes Display
    constant FRAME_HDR : byte_arr(0 to 5) := (x"15", x"00", x"5F", x"75", x"00", x"3F");

    type state_t is (ST_PWR, ST_WAIT, ST_RST_LOW, ST_RST_HIGH, ST_INIT, ST_VCC,
                     ST_ON, ST_HDR, ST_PIX_HI, ST_PIX_LO);
    signal state   : state_t := ST_PWR;
    signal nxt     : state_t := ST_PWR;
    signal tmr     : natural range 0 to 100_000 * T_US := 0;
    signal waiting : std_logic := '0';
    signal idx     : natural range 0 to 36 := 0;

    signal px      : natural range 0 to 95 := 0;
    signal py      : natural range 0 to 63 := 0;
    signal pix_q   : std_logic_vector(15 downto 0) := (others => '0');

    signal spi_start : std_logic := '0';
    signal spi_data  : std_logic_vector(7 downto 0) := (others => '0');
    signal spi_dc    : std_logic := '0';
    signal spi_hold  : std_logic := '0';
    signal spi_done  : std_logic;

begin

    u_spi : entity work.spi_tx
        generic map (HALF => SPI_HALF)
        port map (
            clk   => clk,
            rst   => rst,
            start => spi_start,
            data  => spi_data,
            dc_in => spi_dc,
            hold  => spi_hold,
            done  => spi_done,
            cs_n  => oled_cs,
            sck   => oled_sck,
            mosi  => oled_mosi,
            dc    => oled_dc
        );

    pix_x <= to_unsigned(px, 7);
    pix_y <= to_unsigned(py, 6);

    process (clk)
        variable last : boolean;
    begin
        if rising_edge(clk) then
            spi_start  <= '0';
            frame_tick <= '0';

            if rst = '1' then
                state       <= ST_PWR;
                waiting     <= '0';
                idx         <= 0;
                px          <= 0;
                py          <= 0;
                oled_res    <= '1';
                oled_vccen  <= '0';
                oled_pmoden <= '0';
            else
                case state is

                    when ST_WAIT =>
                        if tmr = 0 then
                            state <= nxt;
                        else
                            tmr <= tmr - 1;
                        end if;

                    when ST_PWR =>                -- Logikversorgung des Moduls, 20 ms warten
                        oled_pmoden <= '1';
                        tmr   <= 20_000 * T_US;
                        nxt   <= ST_RST_LOW;
                        state <= ST_WAIT;

                    when ST_RST_LOW =>
                        oled_res <= '0';
                        tmr   <= 100 * T_US;
                        nxt   <= ST_RST_HIGH;
                        state <= ST_WAIT;

                    when ST_RST_HIGH =>
                        oled_res <= '1';
                        tmr   <= 3_000 * T_US;
                        nxt   <= ST_INIT;
                        state <= ST_WAIT;

                    when ST_INIT =>
                        if waiting = '0' then
                            spi_data  <= INIT_CMD(idx);
                            spi_dc    <= '0';
                            spi_hold  <= '0';
                            spi_start <= '1';
                            waiting   <= '1';
                        elsif spi_done = '1' then
                            waiting <= '0';
                            if idx = INIT_CMD'high then
                                idx   <= 0;
                                state <= ST_VCC;
                            else
                                idx <= idx + 1;
                            end if;
                        end if;

                    when ST_VCC =>                -- Panelspannung (13 V) einschalten
                        oled_vccen <= '1';
                        tmr   <= 25_000 * T_US;
                        nxt   <= ST_ON;
                        state <= ST_WAIT;

                    when ST_ON =>                 -- Display ein
                        if waiting = '0' then
                            spi_data  <= x"AF";
                            spi_dc    <= '0';
                            spi_hold  <= '0';
                            spi_start <= '1';
                            waiting   <= '1';
                        elsif spi_done = '1' then
                            waiting <= '0';
                            tmr     <= 100_000 * T_US;
                            nxt     <= ST_HDR;
                            state   <= ST_WAIT;
                        end if;

                    when ST_HDR =>
                        if waiting = '0' then
                            spi_data  <= FRAME_HDR(idx);
                            spi_dc    <= '0';
                            spi_hold  <= '0';
                            spi_start <= '1';
                            waiting   <= '1';
                        elsif spi_done = '1' then
                            waiting <= '0';
                            if idx = FRAME_HDR'high then
                                idx   <= 0;
                                tmr   <= PIPE_WAIT;
                                nxt   <= ST_PIX_HI;
                                state <= ST_WAIT;
                            else
                                idx <= idx + 1;
                            end if;
                        end if;

                    when ST_PIX_HI =>
                        if waiting = '0' then
                            pix_q     <= pix_in;
                            spi_data  <= pix_in(15 downto 8);
                            spi_dc    <= '1';
                            spi_hold  <= '1';
                            spi_start <= '1';
                            waiting   <= '1';
                        elsif spi_done = '1' then
                            waiting <= '0';
                            state   <= ST_PIX_LO;
                        end if;

                    when ST_PIX_LO =>
                        last := (px = 95) and (py = 63);
                        if waiting = '0' then
                            spi_data  <= pix_q(7 downto 0);
                            spi_dc    <= '1';
                            if last then
                                spi_hold <= '0';
                            else
                                spi_hold <= '1';
                            end if;
                            spi_start <= '1';
                            waiting   <= '1';
                        elsif spi_done = '1' then
                            waiting <= '0';
                            if px = 95 then
                                px <= 0;
                                if py = 63 then
                                    py         <= 0;
                                    frame_tick <= '1';
                                else
                                    py <= py + 1;
                                end if;
                            else
                                px <= px + 1;
                            end if;
                            if last then
                                state <= ST_HDR;
                            else
                                tmr   <= PIPE_WAIT;
                                nxt   <= ST_PIX_HI;
                                state <= ST_WAIT;
                            end if;
                        end if;

                end case;
            end if;
        end if;
    end process;

end architecture rtl;
