----------------------------------------------------------------------------------
-- Testbench : wecker_top
-- CLK_HZ ist auf 1000 verkleinert, eine Sekunde dauert damit 1000 Takte (10 us).
-- Ablauf: Weckzeit auf 00:01 stellen, Wecker scharf schalten, Alarm abwarten,
--         Alarm per Tastendruck stoppen.
----------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity tb_wecker_top is
end entity tb_wecker_top;

architecture sim of tb_wecker_top is

    constant CLK_PERIOD : time     := 10 ns;
    constant CLK_HZ_TB  : positive := 1000;        -- 1 s = 1000 Takte = 10 us

    signal clk      : std_logic := '0';
    signal ck_rst   : std_logic := '0';            -- aktiv low -> '0' = Reset
    signal sw       : std_logic_vector(3 downto 0) := (others => '0');
    signal btn      : std_logic_vector(3 downto 0) := (others => '0');
    signal led      : std_logic_vector(3 downto 0);
    signal seg_l    : std_logic_vector(6 downto 0);
    signal dsel_l   : std_logic;
    signal seg_r    : std_logic_vector(6 downto 0);
    signal dsel_r   : std_logic;
    signal buzzer_o : std_logic;

    signal buzz_any : std_logic := '0';
    signal buzz_clr : std_logic := '0';
    signal sim_done : boolean   := false;

begin

    clk <= not clk after CLK_PERIOD / 2 when not sim_done else '0';

    dut : entity work.wecker_top
        generic map (CLK_HZ => CLK_HZ_TB)
        port map (
            CLK100MHZ => clk,
            ck_rst    => ck_rst,
            sw        => sw,
            btn       => btn,
            led       => led,
            seg_l     => seg_l,
            dsel_l    => dsel_l,
            seg_r     => seg_r,
            dsel_r    => dsel_r,
            buzzer_o  => buzzer_o
        );

    -- Merkt sich, ob der Buzzer im Beobachtungsfenster aktiv war
    monitor : process (clk)
    begin
        if rising_edge(clk) then
            if buzz_clr = '1' then
                buzz_any <= '0';
            elsif buzzer_o = '1' then
                buzz_any <= '1';
            end if;
        end if;
    end process;

    stim : process

        -- Taster lange genug halten, damit die Entprellung anspricht,
        -- aber kurz genug fuer genau einen Puls (kein Auto-Repeat).
        procedure press (idx : natural; n : natural) is
        begin
            for i in 1 to n loop
                btn(idx) <= '1';
                wait for 40 * CLK_PERIOD;
                btn(idx) <= '0';
                wait for 40 * CLK_PERIOD;
            end loop;
        end procedure;

    begin
        wait for 20 * CLK_PERIOD;
        ck_rst <= '1';                                  -- Reset loesen
        wait for 20 * CLK_PERIOD;

        ----------------------------------------------------------------
        -- Weckzeit von 07:00 auf 00:01 stellen
        ----------------------------------------------------------------
        sw(2) <= '1';
        wait for 20 * CLK_PERIOD;
        press(1, 7);                                    -- Stunden 7 -> 0
        press(2, 1);                                    -- Minuten 0 -> 1
        sw(2) <= '0';

        ----------------------------------------------------------------
        -- Wecker scharf schalten, Alarm bei 00:01:00 erwarten
        ----------------------------------------------------------------
        sw(3) <= '1';

        assert buzzer_o = '0'
            report "Buzzer darf vor der Weckzeit nicht toenen" severity error;

        wait for 650 us;                                -- ca. 65 s

        buzz_clr <= '1';
        wait for 2 * CLK_PERIOD;
        buzz_clr <= '0';
        wait for 100 us;

        assert buzz_any = '1'
            report "Kein akustisches Wecksignal zur Weckzeit" severity error;

        ----------------------------------------------------------------
        -- Alarm per Tastendruck stoppen
        ----------------------------------------------------------------
        press(0, 1);
        wait for 20 * CLK_PERIOD;

        buzz_clr <= '1';
        wait for 2 * CLK_PERIOD;
        buzz_clr <= '0';
        wait for 100 us;

        assert buzz_any = '0'
            report "Alarm laesst sich nicht per Taste stoppen" severity error;

        ----------------------------------------------------------------
        -- Statusanzeige: Wecker scharf -> led(0) leuchtet
        ----------------------------------------------------------------
        assert led(0) = '1'
            report "Status-LED fuer scharfen Wecker fehlt" severity error;

        report "tb_wecker_top beendet" severity note;
        sim_done <= true;
        wait;
    end process;

end architecture sim;
