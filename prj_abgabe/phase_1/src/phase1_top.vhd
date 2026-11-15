----------------------------------------------------------------------------------
-- Projekt      : Labor 7-Segment-Anzeige, Phase I
-- Modul        : phase1_top
-- Beschreibung : Betriebsarten ueber SW0..SW3 (genau ein Schalter aktiv)
--                SW0: Zaehler 0..99, BTN0 +1, BTN1 -1, BTN2 +10, BTN3 -10
--                SW1: Matrikelnummer Mark (91)
--                SW2: Matrikelnummer Maxi (93)
--                SW3: Binaereingabe, BTNi toggelt Bit i (0..15)
--                sonst (kein / mehrere Schalter): Anzeige dunkel
----------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity phase1_top is
    generic (
        CLK_HZ          : positive := 100_000_000;
        DEBOUNCE_CYCLES : positive := 1_000_000;
        REFRESH_HZ      : positive := 500
    );
    port (
        CLK100MHZ : in  std_logic;
        ck_rst    : in  std_logic;
        sw        : in  std_logic_vector(3 downto 0);
        btn       : in  std_logic_vector(3 downto 0);
        seg_r     : out std_logic_vector(6 downto 0);
        dsel_r    : out std_logic
    );
end entity phase1_top;

architecture rtl of phase1_top is

    constant MODE_COUNT  : std_logic_vector(3 downto 0) := "0001";
    constant MODE_MARK   : std_logic_vector(3 downto 0) := "0010";
    constant MODE_MAXI   : std_logic_vector(3 downto 0) := "0100";
    constant MODE_BINARY : std_logic_vector(3 downto 0) := "1000";

    constant MATR_MARK : natural := 91;
    constant MATR_MAXI : natural := 93;

    signal reset_sync : std_logic_vector(1 downto 0) := (others => '1');
    signal rst        : std_logic;
    signal sw_meta    : std_logic_vector(3 downto 0) := (others => '0');
    signal sw_sync    : std_logic_vector(3 downto 0) := (others => '0');
    signal press      : std_logic_vector(3 downto 0);

    signal count      : natural range 0 to 99 := 0;
    signal bin_value  : unsigned(3 downto 0) := (others => '0');

    signal value      : natural range 0 to 99;
    signal show       : std_logic;
    signal show_tens  : std_logic;
    signal tens       : unsigned(3 downto 0);
    signal ones       : unsigned(3 downto 0);

    signal driver_seg : std_logic_vector(6 downto 0);
    signal driver_sel : std_logic;

begin

    -- Reset: asynchron anfordern (ck_rst aktiv Low), synchron freigeben
    process (CLK100MHZ, ck_rst)
    begin
        if ck_rst = '0' then
            reset_sync <= (others => '1');
        elsif rising_edge(CLK100MHZ) then
            reset_sync <= reset_sync(0) & '0';
        end if;
    end process;

    rst <= reset_sync(1);

    process (CLK100MHZ)
    begin
        if rising_edge(CLK100MHZ) then
            sw_meta <= sw;
            sw_sync <= sw_meta;
        end if;
    end process;

    gen_btn : for i in 0 to 3 generate
        u_btn : entity work.btn_debounce
            generic map (DEBOUNCE_CYCLES => DEBOUNCE_CYCLES)
            port map (clk => CLK100MHZ, rst => rst, btn_i => btn(i), press_o => press(i));
    end generate;

    -- Tasten wirken nur in der jeweils aktiven Betriebsart; Werte bleiben sonst erhalten
    process (CLK100MHZ)
    begin
        if rising_edge(CLK100MHZ) then
            if rst = '1' then
                count     <= 0;
                bin_value <= (others => '0');
            elsif sw_sync = MODE_COUNT then
                if press(0) = '1' then
                    if count = 99 then
                        count <= 0;
                    else
                        count <= count + 1;
                    end if;
                elsif press(1) = '1' then
                    if count >= 1 then
                        count <= count - 1;
                    end if;
                elsif press(2) = '1' then
                    if count >= 90 then
                        count <= 0;
                    else
                        count <= count + 10;
                    end if;
                elsif press(3) = '1' then
                    if count >= 10 then
                        count <= count - 10;
                    else
                        count <= 0;
                    end if;
                end if;
            elsif sw_sync = MODE_BINARY then
                bin_value <= bin_value xor unsigned(press);
            end if;
        end if;
    end process;

    process (sw_sync, count, bin_value)
    begin
        value <= 0;
        show  <= '0';
        case sw_sync is
            when MODE_COUNT  => value <= count;                  show <= '1';
            when MODE_MARK   => value <= MATR_MARK;              show <= '1';
            when MODE_MAXI   => value <= MATR_MAXI;              show <= '1';
            when MODE_BINARY => value <= to_integer(bin_value);  show <= '1';
            when others      => null;
        end case;
    end process;

    tens <= to_unsigned(value / 10, 4);
    ones <= to_unsigned(value mod 10, 4);

    -- fuehrende Null wird unterdrueckt
    show_tens <= '1' when show = '1' and value >= 10 else '0';

    display : entity work.ssd_driver
        generic map (CLK_HZ => CLK_HZ, REFRESH_HZ => REFRESH_HZ)
        port map (
            clk    => CLK100MHZ,
            rst    => rst,
            digit0 => ones,
            digit1 => tens,
            seg    => driver_seg,
            dsel   => driver_sel
        );

    seg_r <= driver_seg when (driver_sel = '0' and show = '1') or (driver_sel = '1' and show_tens = '1')
             else (others => '0');
    dsel_r <= driver_sel;

end architecture rtl;