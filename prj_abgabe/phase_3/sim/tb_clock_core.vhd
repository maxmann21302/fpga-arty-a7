----------------------------------------------------------------------------------
-- Testbench : clock_core
-- CLK_HZ ist auf 100 verkleinert, eine Sekunde dauert damit 100 Takte (1 us).
----------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity tb_clock_core is
end entity tb_clock_core;

architecture sim of tb_clock_core is

    constant CLK_PERIOD : time     := 10 ns;
    constant CLK_HZ_TB  : positive := 100;          -- 1 s = 100 Takte = 1 us

    signal clk      : std_logic := '0';
    signal rst      : std_logic := '1';
    signal set_mode : std_logic := '0';
    signal inc_h    : std_logic := '0';
    signal dec_h    : std_logic := '0';
    signal inc_m    : std_logic := '0';
    signal dec_m    : std_logic := '0';
    signal hours    : unsigned(5 downto 0);
    signal minutes  : unsigned(5 downto 0);
    signal seconds  : unsigned(5 downto 0);
    signal tick_1hz : std_logic;

    signal sim_done : boolean := false;

begin

    clk <= not clk after CLK_PERIOD / 2 when not sim_done else '0';

    dut : entity work.clock_core
        generic map (CLK_HZ => CLK_HZ_TB)
        port map (
            clk      => clk,
            rst      => rst,
            set_mode => set_mode,
            inc_h    => inc_h,
            dec_h    => dec_h,
            inc_m    => inc_m,
            dec_m    => dec_m,
            hours    => hours,
            minutes  => minutes,
            seconds  => seconds,
            tick_1hz => tick_1hz
        );

    stim : process

        procedure press (signal s : out std_logic; n : natural) is
        begin
            for i in 1 to n loop
                s <= '1';
                wait until rising_edge(clk);
                s <= '0';
                wait until rising_edge(clk);
            end loop;
        end procedure;

    begin
        wait for 5 * CLK_PERIOD;
        rst <= '0';
        wait until rising_edge(clk);

        assert hours = 0 and minutes = 0 and seconds = 0
            report "Reset setzt die Uhr nicht auf 00:00:00" severity error;

        ----------------------------------------------------------------
        -- 1) Sekunden laufen, Uebertrag auf die Minute nach 60 s
        ----------------------------------------------------------------
        wait for 10.5 us;                     -- 10 s (halber Takt Versatz)
        assert seconds = 10 and minutes = 0
            report "Sekundenzaehler laeuft falsch" severity error;

        wait for 51 us;                       -- insgesamt 61 s
        assert minutes = 1 and seconds = 1
            report "Uebertrag Sekunde -> Minute fehlerhaft" severity error;

        ----------------------------------------------------------------
        -- 2) Stellmodus friert die Uhr ein und setzt die Sekunden auf 0
        ----------------------------------------------------------------
        set_mode <= '1';
        wait for 20 us;
        assert seconds = 0
            report "Sekunden werden im Stellmodus nicht genullt" severity error;
        assert minutes = 1
            report "Uhr laeuft im Stellmodus weiter" severity error;

        ----------------------------------------------------------------
        -- 3) Zeit auf 23:59 stellen, danach Tagesuebergang pruefen
        ----------------------------------------------------------------
        press(inc_h, 23);
        press(inc_m, 58);                     -- 1 + 58 = 59
        assert hours = 23 and minutes = 59
            report "Zeitstellen liefert falschen Wert" severity error;

        set_mode <= '0';
        wait for 61 us;                       -- 61 s
        assert hours = 0 and minutes = 0
            report "Tagesuebergang 23:59 -> 00:00 fehlerhaft" severity error;

        ----------------------------------------------------------------
        -- 4) Minuten herunterzaehlen ohne Uebertrag auf die Stunden
        ----------------------------------------------------------------
        set_mode <= '1';
        wait until rising_edge(clk);
        press(dec_m, 1);
        assert minutes = 59 and hours = 0
            report "Minuten-Dekrement darf die Stunden nicht veraendern" severity error;

        press(dec_h, 1);
        assert hours = 23
            report "Stunden-Dekrement mit Unterlauf fehlerhaft" severity error;

        report "tb_clock_core beendet" severity note;
        sim_done <= true;
        wait;
    end process;

end architecture sim;
