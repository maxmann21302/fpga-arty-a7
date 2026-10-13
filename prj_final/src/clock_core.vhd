----------------------------------------------------------------------------------
-- Projekt      : Digitale Uhr / Wecker
-- Modul        : clock_core
-- Beschreibung : Zeitbasis 24 h. Im Stellmodus steht die Uhr und die Sekunden
--                werden auf 0 gesetzt (uebliches Verhalten beim Zeitstellen).
----------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity clock_core is
    generic (
        CLK_HZ : positive := 100_000_000
    );
    port (
        clk      : in  std_logic;
        rst      : in  std_logic;
        set_mode : in  std_logic;
        inc_h    : in  std_logic;
        dec_h    : in  std_logic;
        inc_m    : in  std_logic;
        dec_m    : in  std_logic;
        hours    : out unsigned(5 downto 0);
        minutes  : out unsigned(5 downto 0);
        seconds  : out unsigned(5 downto 0);
        tick_1hz : out std_logic
    );
end entity clock_core;

architecture rtl of clock_core is

    signal h, m, s : unsigned(5 downto 0) := (others => '0');
    signal tick    : std_logic;
    signal run     : std_logic;

begin

    run <= not set_mode;

    u_sec : entity work.tick_gen
        generic map (DIV => CLK_HZ)
        port map (clk => clk, rst => rst, en => run, clr => set_mode, tick => tick);

    process (clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                h <= (others => '0');
                m <= (others => '0');
                s <= (others => '0');
            elsif set_mode = '1' then
                s <= (others => '0');

                if inc_h = '1' then
                    if h = 23 then
                        h <= (others => '0');
                    else
                        h <= h + 1;
                    end if;
                elsif dec_h = '1' then
                    if h = 0 then
                        h <= to_unsigned(23, h'length);
                    else
                        h <= h - 1;
                    end if;
                end if;

                -- Minutenstellen erzeugt bewusst keinen Uebertrag auf die Stunden
                if inc_m = '1' then
                    if m = 59 then
                        m <= (others => '0');
                    else
                        m <= m + 1;
                    end if;
                elsif dec_m = '1' then
                    if m = 0 then
                        m <= to_unsigned(59, m'length);
                    else
                        m <= m - 1;
                    end if;
                end if;

            elsif tick = '1' then
                if s = 59 then
                    s <= (others => '0');
                    if m = 59 then
                        m <= (others => '0');
                        if h = 23 then
                            h <= (others => '0');
                        else
                            h <= h + 1;
                        end if;
                    else
                        m <= m + 1;
                    end if;
                else
                    s <= s + 1;
                end if;
            end if;
        end if;
    end process;

    hours    <= h;
    minutes  <= m;
    seconds  <= s;
    tick_1hz <= tick;

end architecture rtl;
