library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity phase1_top is
    generic (
        CLK_HZ : positive := 100_000_000;
        DEBOUNCE_CYCLES : positive := 1_000_000;
        REFRESH_HZ : positive := 500
    );
    port (
        CLK100MHZ : in std_logic;
        ck_rst : in std_logic;
        btn_up : in std_logic;
        seg_r : out std_logic_vector(6 downto 0);
        dsel_r : out std_logic
    );
end entity;

architecture rtl of phase1_top is
    signal reset_sync : std_logic_vector(1 downto 0) := (others => '1');
    signal button_sync : std_logic_vector(1 downto 0) := (others => '0');
    signal stable : std_logic := '0';
    signal debounce_count : natural range 0 to DEBOUNCE_CYCLES - 1 := 0;
    signal count : natural range 0 to 9 := 0;
    signal digit : unsigned(3 downto 0);
    signal selected_segments : std_logic_vector(6 downto 0);
    signal selected_digit : std_logic;
begin
    process (CLK100MHZ, ck_rst)
    begin
        if ck_rst = '0' then
            reset_sync <= (others => '1');
        elsif rising_edge(CLK100MHZ) then
            reset_sync <= reset_sync(0) & '0';
        end if;
    end process;

    process (CLK100MHZ)
    begin
        if rising_edge(CLK100MHZ) then
            if reset_sync(1) = '1' then
                button_sync <= (others => '0');
                stable <= '0';
                debounce_count <= 0;
                count <= 0;
            else
                button_sync <= button_sync(0) & btn_up;
                if button_sync(1) = stable then
                    debounce_count <= 0;
                elsif debounce_count = DEBOUNCE_CYCLES - 1 then
                    debounce_count <= 0;
                    stable <= button_sync(1);
                    if button_sync(1) = '1' then
                        if count = 9 then
                            count <= 0;
                        else
                            count <= count + 1;
                        end if;
                    end if;
                else
                    debounce_count <= debounce_count + 1;
                end if;
            end if;
        end if;
    end process;

    digit <= to_unsigned(count, 4);
    display : entity work.ssd_driver
        generic map (CLK_HZ => CLK_HZ, REFRESH_HZ => REFRESH_HZ)
        port map (
            clk => CLK100MHZ, rst => reset_sync(1),
            digit0 => digit, digit1 => to_unsigned(0, 4),
            seg => selected_segments, dsel => selected_digit
        );
    seg_r <= selected_segments when selected_digit = '0' else (others => '0');
    dsel_r <= selected_digit;
end architecture;