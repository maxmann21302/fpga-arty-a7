----------------------------------------------------------------------------------
-- Projekt      : Prell-Oszilloskop (Pmod OLEDrgb an JD)
-- Modul        : bounce_capture
-- Beschreibung : Zeichnet ein (synchronisiertes) Signal als Min/Max-Abtastung auf.
--                Pro Abtastintervall wird gespeichert, ob '1' (hi) und/oder '0' (lo)
--                vorkam - so bleiben auch Pulse kuerzer als ein Intervall sichtbar.
--                Scharf -> erste steigende Flanke -> PRE Werte davor, N-PRE danach
--                -> eingefroren bis clear.
--                Spalte k (0 = links) liegt in buf(N-1-k).
----------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

use work.bounce_pkg.all;

entity bounce_capture is
    generic (
        N   : positive := SAMPLES;
        PRE : positive := PRE_TRIG
    );
    port (
        clk    : in  std_logic;
        rst    : in  std_logic;
        clear  : in  std_logic;
        sig    : in  std_logic;
        period : in  period_t;               -- Takte pro Abtastwert
        hi_buf : out std_logic_vector(N - 1 downto 0);
        lo_buf : out std_logic_vector(N - 1 downto 0);
        armed  : out std_logic;
        done   : out std_logic
    );
end entity bounce_capture;

architecture rtl of bounce_capture is

    type state_t is (S_ARMED, S_RUN, S_DONE);

    signal state  : state_t := S_ARMED;
    signal sig_d  : std_logic := '0';
    signal tmr    : natural range 1 to period_t'high := 1;
    signal hi_acc : std_logic := '0';
    signal lo_acc : std_logic := '0';
    signal hi_sr  : std_logic_vector(N - 1 downto 0) := (others => '0');
    signal lo_sr  : std_logic_vector(N - 1 downto 0) := (others => '0');
    signal post   : natural range 0 to N - PRE := 0;

begin

    process (clk)
        variable hi_v : std_logic;
        variable lo_v : std_logic;
    begin
        if rising_edge(clk) then
            sig_d <= sig;
            hi_v  := hi_acc or sig;
            lo_v  := lo_acc or not sig;

            if rst = '1' or clear = '1' then
                state  <= S_ARMED;
                tmr    <= 1;
                hi_acc <= '0';
                lo_acc <= '0';
                hi_sr  <= (others => '0');
                lo_sr  <= (others => '0');
                post   <= 0;

            elsif state = S_ARMED and sig = '1' and sig_d = '0' then
                -- Intervall vor dem Trigger abschliessen; Triggerspalte enthaelt die Flanke
                hi_sr  <= hi_sr(N - 2 downto 0) & hi_acc;
                lo_sr  <= lo_sr(N - 2 downto 0) & lo_acc;
                hi_acc <= '1';
                lo_acc <= '1';
                tmr    <= 2;
                state  <= S_RUN;

            elsif state /= S_DONE then
                if tmr >= period then
                    hi_sr  <= hi_sr(N - 2 downto 0) & hi_v;
                    lo_sr  <= lo_sr(N - 2 downto 0) & lo_v;
                    -- Grenztakt zaehlt auch ins naechste Intervall, sonst gingen Flanken genau an der Grenze verloren
                    hi_acc <= sig;
                    lo_acc <= not sig;
                    tmr    <= 1;
                    if state = S_RUN then
                        if post = N - PRE - 1 then
                            state <= S_DONE;
                        else
                            post <= post + 1;
                        end if;
                    end if;
                else
                    hi_acc <= hi_v;
                    lo_acc <= lo_v;
                    tmr    <= tmr + 1;
                end if;
            end if;
        end if;
    end process;

    hi_buf <= hi_sr;
    lo_buf <= lo_sr;
    armed  <= '1' when state = S_ARMED else '0';
    done   <= '1' when state = S_DONE  else '0';

end architecture rtl;
