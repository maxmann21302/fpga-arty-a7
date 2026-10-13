----------------------------------------------------------------------------------
-- Projekt      : Digitale Uhr / Wecker
-- Modul        : alarm_core
-- Beschreibung : Weckzeit-Register und Weck-Automat
--                IDLE -> RINGING (Weckzeit erreicht) -> SILENCED (Taste) -> IDLE
----------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity alarm_core is
    port (
        clk      : in  std_logic;
        rst      : in  std_logic;
        set_mode : in  std_logic;
        inc_h    : in  std_logic;
        dec_h    : in  std_logic;
        inc_m    : in  std_logic;
        dec_m    : in  std_logic;
        enable   : in  std_logic;
        stop     : in  std_logic;
        cur_h    : in  unsigned(5 downto 0);
        cur_m    : in  unsigned(5 downto 0);
        cur_s    : in  unsigned(5 downto 0);
        al_h     : out unsigned(5 downto 0);
        al_m     : out unsigned(5 downto 0);
        ringing  : out std_logic
    );
end entity alarm_core;

architecture rtl of alarm_core is

    type alarm_state_t is (IDLE, RINGING_ST, SILENCED);

    signal state     : alarm_state_t := IDLE;
    signal ah        : unsigned(5 downto 0) := to_unsigned(7, 6);
    signal am        : unsigned(5 downto 0) := (others => '0');
    signal match_min : std_logic;

begin

    match_min <= '1' when (cur_h = ah and cur_m = am) else '0';

    set_proc : process (clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                ah <= to_unsigned(7, ah'length);   -- Default-Weckzeit 07:00
                am <= (others => '0');
            elsif set_mode = '1' then
                if inc_h = '1' then
                    if ah = 23 then
                        ah <= (others => '0');
                    else
                        ah <= ah + 1;
                    end if;
                elsif dec_h = '1' then
                    if ah = 0 then
                        ah <= to_unsigned(23, ah'length);
                    else
                        ah <= ah - 1;
                    end if;
                end if;

                if inc_m = '1' then
                    if am = 59 then
                        am <= (others => '0');
                    else
                        am <= am + 1;
                    end if;
                elsif dec_m = '1' then
                    if am = 0 then
                        am <= to_unsigned(59, am'length);
                    else
                        am <= am - 1;
                    end if;
                end if;
            end if;
        end if;
    end process;

    fsm_proc : process (clk)
    begin
        if rising_edge(clk) then
            if rst = '1' or enable = '0' then
                state <= IDLE;
            else
                case state is

                    when IDLE =>
                        if match_min = '1' and cur_s = 0 then
                            state <= RINGING_ST;
                        end if;

                    when RINGING_ST =>
                        if stop = '1' then
                            state <= SILENCED;
                        elsif match_min = '0' then
                            state <= IDLE;
                        end if;

                    when SILENCED =>
                        if match_min = '0' then
                            state <= IDLE;
                        end if;

                end case;
            end if;
        end if;
    end process;

    al_h    <= ah;
    al_m    <= am;
    ringing <= '1' when state = RINGING_ST else '0';

end architecture rtl;
