## ---------------------------------------------------------------------------
## Prell-Oszilloskop - Arty A7-35T, Pmod OLEDrgb (SSD1331, SPI) an Pmod JD
## ---------------------------------------------------------------------------

set_property -dict { PACKAGE_PIN E3    IOSTANDARD LVCMOS33 } [get_ports { CLK100MHZ }];
create_clock -add -name sys_clk_pin -period 10.00 -waveform {0 5} [get_ports { CLK100MHZ }];

## RESET-Taster (aktiv low)
set_property -dict { PACKAGE_PIN C2    IOSTANDARD LVCMOS33 } [get_ports { ck_rst }];

## BTN0: Messeingang | BTN1: Loeschen | BTN2: Zeitbasis - | BTN3: Zeitbasis +
set_property -dict { PACKAGE_PIN D9    IOSTANDARD LVCMOS33 } [get_ports { btn[0] }];
set_property -dict { PACKAGE_PIN C9    IOSTANDARD LVCMOS33 } [get_ports { btn[1] }];
set_property -dict { PACKAGE_PIN B9    IOSTANDARD LVCMOS33 } [get_ports { btn[2] }];
set_property -dict { PACKAGE_PIN B8    IOSTANDARD LVCMOS33 } [get_ports { btn[3] }];

## SW0: Triggerflanke (0 steigend, 1 fallend) | SW1: Quelle (0 BTN0, 1 JA1)
set_property -dict { PACKAGE_PIN A8    IOSTANDARD LVCMOS33 } [get_ports { sw[0] }];
set_property -dict { PACKAGE_PIN C11   IOSTANDARD LVCMOS33 } [get_ports { sw[1] }];

## Externer Messeingang Pmod JA1 (max. 3,3 V!), Pull-down -> offen = 0
set_property -dict { PACKAGE_PIN G13   IOSTANDARD LVCMOS33 PULLDOWN TRUE } [get_ports { ext_in }];

## Pmod JD - Pmod OLEDrgb
set_property -dict { PACKAGE_PIN D4    IOSTANDARD LVCMOS33 } [get_ports { oled_cs }];      # JD1  CS
set_property -dict { PACKAGE_PIN D3    IOSTANDARD LVCMOS33 } [get_ports { oled_mosi }];    # JD2  MOSI
set_property -dict { PACKAGE_PIN F3    IOSTANDARD LVCMOS33 } [get_ports { oled_sck }];     # JD4  SCK
set_property -dict { PACKAGE_PIN E2    IOSTANDARD LVCMOS33 } [get_ports { oled_dc }];      # JD7  D/C
set_property -dict { PACKAGE_PIN D2    IOSTANDARD LVCMOS33 } [get_ports { oled_res }];     # JD8  RES
set_property -dict { PACKAGE_PIN H2    IOSTANDARD LVCMOS33 } [get_ports { oled_vccen }];   # JD9  VCCEN
set_property -dict { PACKAGE_PIN G2    IOSTANDARD LVCMOS33 } [get_ports { oled_pmoden }];  # JD10 PMODEN

set_property BITSTREAM.GENERAL.COMPRESS TRUE [current_design]
set_property CONFIG_VOLTAGE 3.3 [current_design]
set_property CFGBVS VCCO [current_design]
