library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity phase2_top is
    generic (
        CLK_HZ : positive := 100_000_000;
        REFRESH_HZ : positive := 500
    );
    port (
        CLK100MHZ : in std_logic;
        ck_rst : in std_logic;
        seg_r : out std_logic_vector(6 downto 0);
        dsel_r : out std_logic
    );
end entity;

architecture rtl of phase2_top is
    signal reset_sync : std_logic_vector(1 downto 0) := (others => '1');
    signal divider : natural range 0 to CLK_HZ - 1 := 0;
    signal count : natural range 0 to 99 := 0;
    signal ones : unsigned(3 downto 0);
    signal tens : unsigned(3 downto 0);
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
                divider <= 0;
                count <= 0;
            elsif divider = CLK_HZ - 1 then
                divider <= 0;
                if count = 99 then
                    count <= 0;
                else
                    count <= count + 1;
                end if;
            else
                divider <= divider + 1;
            end if;
        end if;
    end process;

    ones <= to_unsigned(count mod 10, 4);
    tens <= to_unsigned(count / 10, 4);
    display : entity work.ssd_driver
        generic map (CLK_HZ => CLK_HZ, REFRESH_HZ => REFRESH_HZ)
        port map (
            clk => CLK100MHZ, rst => reset_sync(1),
            digit0 => ones, digit1 => tens, seg => seg_r, dsel => dsel_r
        );
end architecture;