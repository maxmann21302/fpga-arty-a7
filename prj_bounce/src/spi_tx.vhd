----------------------------------------------------------------------------------
-- Modul        : spi_tx
-- Beschreibung : SPI-Master (nur Senden), Mode 3 (SCK-Ruhepegel high, Daten werden
--                mit steigender Flanke uebernommen), MSB zuerst.
--                SCK-Periode = 2*HALF Takte. hold='1' laesst CS nach dem Byte aktiv.
----------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity spi_tx is
    generic (
        HALF : positive := 8                      -- 100 MHz / 16 = 6,25 MHz
    );
    port (
        clk   : in  std_logic;
        rst   : in  std_logic;
        start : in  std_logic;
        data  : in  std_logic_vector(7 downto 0);
        dc_in : in  std_logic;
        hold  : in  std_logic;
        done  : out std_logic;
        cs_n  : out std_logic;
        sck   : out std_logic;
        mosi  : out std_logic;
        dc    : out std_logic
    );
end entity spi_tx;

architecture rtl of spi_tx is
    type state_t is (S_IDLE, S_LEAD, S_LOW, S_HIGH, S_TRAIL);
    signal state  : state_t := S_IDLE;
    signal tmr    : natural range 0 to HALF - 1 := 0;
    signal bits   : natural range 0 to 7 := 0;
    signal sh     : std_logic_vector(7 downto 0) := (others => '0');
    signal hold_q : std_logic := '0';
begin

    process (clk)
    begin
        if rising_edge(clk) then
            done <= '0';
            if rst = '1' then
                state <= S_IDLE;
                cs_n  <= '1';
                sck   <= '1';
                mosi  <= '0';
                dc    <= '0';
            else
                case state is
                    when S_IDLE =>
                        if start = '1' then
                            cs_n   <= '0';
                            dc     <= dc_in;
                            sh     <= data;
                            hold_q <= hold;
                            bits   <= 0;
                            tmr    <= 0;
                            state  <= S_LEAD;
                        end if;

                    when S_LEAD =>                -- CS/DC-Vorlauf
                        if tmr = HALF - 1 then
                            tmr   <= 0;
                            sck   <= '0';
                            mosi  <= sh(7);
                            state <= S_LOW;
                        else
                            tmr <= tmr + 1;
                        end if;

                    when S_LOW =>
                        if tmr = HALF - 1 then
                            tmr   <= 0;
                            sck   <= '1';
                            state <= S_HIGH;
                        else
                            tmr <= tmr + 1;
                        end if;

                    when S_HIGH =>
                        if tmr = HALF - 1 then
                            tmr <= 0;
                            if bits = 7 then
                                state <= S_TRAIL;
                            else
                                sck   <= '0';
                                mosi  <= sh(6);
                                sh    <= sh(6 downto 0) & '0';
                                bits  <= bits + 1;
                                state <= S_LOW;
                            end if;
                        else
                            tmr <= tmr + 1;
                        end if;

                    when S_TRAIL =>
                        if hold_q = '0' then
                            cs_n <= '1';
                        end if;
                        done  <= '1';
                        state <= S_IDLE;
                end case;
            end if;
        end if;
    end process;

end architecture rtl;
