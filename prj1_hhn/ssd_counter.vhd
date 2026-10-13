----------------------------------------------------------------------------------
-- Company:
-- Engineer:
--
-- Create Date: 13.10.2026
-- Design Name:
-- Module Name: ssd_counter - Behavioral
-- Project Name: prj1_hhn
-- Target Devices: Arty A7-35T
-- Tool Versions:
-- Description: Sekunden 00..59 auf Pmod SSD (JA/JB), Minuten 00..59 auf Pmod SSD (JC/JD)
--              btn0 = Reset, btn1 = Start/Pause
--
-- Dependencies:
--
-- Revision:
-- Revision 0.01 - File Created
-- Additional Comments:
--
----------------------------------------------------------------------------------


library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity ssd_counter is
    generic (
        CLK_HZ : natural := 100_000_000
    );
    Port ( CLK100MHZ : in  STD_LOGIC;
           btn0      : in  STD_LOGIC;
           btn1      : in  STD_LOGIC;
           seg_sec   : out STD_LOGIC_VECTOR (6 downto 0);
           dsel_sec  : out STD_LOGIC;
           seg_min   : out STD_LOGIC_VECTOR (6 downto 0);
           dsel_min  : out STD_LOGIC);
end ssd_counter;

architecture Behavioral of ssd_counter is

    constant SEC_MAX      : natural := CLK_HZ - 1;
    constant REFRESH_MAX  : natural := (CLK_HZ / 1000) - 1;
    constant DEBOUNCE_MAX : natural := CLK_HZ / 100;

    signal btn0_sync  : std_logic_vector(1 downto 0) := (others => '0');
    signal btn1_sync  : std_logic_vector(1 downto 0) := (others => '0');
    signal rst        : std_logic;

    signal db_cnt     : natural range 0 to DEBOUNCE_MAX := 0;
    signal btn1_deb   : std_logic := '0';
    signal btn1_deb_d : std_logic := '0';
    signal run        : std_logic := '1';

    signal sec_cnt   : unsigned(26 downto 0) := (others => '0');
    signal tick_1hz  : std_logic := '0';
    signal tick_min  : std_logic;

    signal ref_cnt   : unsigned(16 downto 0) := (others => '0');
    signal digit_sel : std_logic := '0';

    signal sec_ones  : unsigned(3 downto 0) := (others => '0');
    signal sec_tens  : unsigned(3 downto 0) := (others => '0');
    signal min_ones  : unsigned(3 downto 0) := (others => '0');
    signal min_tens  : unsigned(3 downto 0) := (others => '0');
    signal digit_s   : unsigned(3 downto 0);
    signal digit_m   : unsigned(3 downto 0);

    -- Pmod SSD: Common Cathode mit Treibertransistoren -> Segmente aktiv high
    function bcd_to_seg (d : unsigned(3 downto 0)) return std_logic_vector is
    begin
        case d is
            --                   gfedcba
            when "0000" => return "0111111";
            when "0001" => return "0000110";
            when "0010" => return "1011011";
            when "0011" => return "1001111";
            when "0100" => return "1100110";
            when "0101" => return "1101101";
            when "0110" => return "1111101";
            when "0111" => return "0000111";
            when "1000" => return "1111111";
            when "1001" => return "1101111";
            when others => return "0000000";
        end case;
    end function;

begin

    sync_proc : process (CLK100MHZ)
    begin
        if rising_edge(CLK100MHZ) then
            btn0_sync <= btn0_sync(0) & btn0;
            btn1_sync <= btn1_sync(0) & btn1;
        end if;
    end process;

    rst <= btn0_sync(1);

    -- Entprellung btn1: Pegel muss 10 ms stabil anliegen
    debounce_proc : process (CLK100MHZ)
    begin
        if rising_edge(CLK100MHZ) then
            if btn1_sync(1) = btn1_deb then
                db_cnt <= 0;
            elsif db_cnt = DEBOUNCE_MAX then
                db_cnt   <= 0;
                btn1_deb <= btn1_sync(1);
            else
                db_cnt <= db_cnt + 1;
            end if;
            btn1_deb_d <= btn1_deb;
        end if;
    end process;

    run_proc : process (CLK100MHZ)
    begin
        if rising_edge(CLK100MHZ) then
            if btn1_deb = '1' and btn1_deb_d = '0' then
                run <= not run;
            end if;
        end if;
    end process;

    sec_prescaler : process (CLK100MHZ)
    begin
        if rising_edge(CLK100MHZ) then
            if rst = '1' then
                sec_cnt  <= (others => '0');
                tick_1hz <= '0';
            elsif run = '0' then
                tick_1hz <= '0';
            elsif sec_cnt = SEC_MAX then
                sec_cnt  <= (others => '0');
                tick_1hz <= '1';
            else
                sec_cnt  <= sec_cnt + 1;
                tick_1hz <= '0';
            end if;
        end if;
    end process;

    refresh_prescaler : process (CLK100MHZ)
    begin
        if rising_edge(CLK100MHZ) then
            if ref_cnt = REFRESH_MAX then
                ref_cnt   <= (others => '0');
                digit_sel <= not digit_sel;
            else
                ref_cnt <= ref_cnt + 1;
            end if;
        end if;
    end process;

    tick_min <= '1' when tick_1hz = '1' and sec_tens = 5 and sec_ones = 9 else '0';

    sec_count_proc : process (CLK100MHZ)
    begin
        if rising_edge(CLK100MHZ) then
            if rst = '1' then
                sec_ones <= (others => '0');
                sec_tens <= (others => '0');
            elsif tick_1hz = '1' then
                if sec_ones = 9 then
                    sec_ones <= (others => '0');
                    if sec_tens = 5 then
                        sec_tens <= (others => '0');
                    else
                        sec_tens <= sec_tens + 1;
                    end if;
                else
                    sec_ones <= sec_ones + 1;
                end if;
            end if;
        end if;
    end process;

    min_count_proc : process (CLK100MHZ)
    begin
        if rising_edge(CLK100MHZ) then
            if rst = '1' then
                min_ones <= (others => '0');
                min_tens <= (others => '0');
            elsif tick_min = '1' then
                if min_ones = 9 then
                    min_ones <= (others => '0');
                    if min_tens = 5 then
                        min_tens <= (others => '0');
                    else
                        min_tens <= min_tens + 1;
                    end if;
                else
                    min_ones <= min_ones + 1;
                end if;
            end if;
        end if;
    end process;

    digit_s  <= sec_ones when digit_sel = '0' else sec_tens;
    digit_m  <= min_ones when digit_sel = '0' else min_tens;

    seg_sec  <= bcd_to_seg(digit_s);
    dsel_sec <= digit_sel;
    seg_min  <= bcd_to_seg(digit_m);
    dsel_min <= digit_sel;

end Behavioral;
