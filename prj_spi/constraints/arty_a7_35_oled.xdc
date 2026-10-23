## ---------------------------------------------------------------------------
## Pmod OLEDrgb (SSD1331, SPI) an Pmod JD - Arty A7-35T
##
## Pmod-Pinbelegung des OLEDrgb (12-polig, passt 1:1 auf JD):
##   obere Reihe  : 1 CS | 2 MOSI | 3 NC | 4 SCK | 5 GND | 6 VCC (3V3)
##   untere Reihe : 7 D/C | 8 RES | 9 VCCEN | 10 PMODEN | 11 GND | 12 VCC (3V3)
## Beim direkten Aufstecken liegen GND auf GND und VCC auf VCC (JD Pin 5/11 = GND,
## Pin 6/12 = 3V3). Bei Kabelverbindung: Pin 5 + 11 -> GND, Pin 6 + 12 -> 3V3.
## ---------------------------------------------------------------------------

## Clock signal (100 MHz)
set_property -dict { PACKAGE_PIN E3    IOSTANDARD LVCMOS33 } [get_ports { CLK100MHZ }]; #IO_L12P_T1_MRCC_35 Sch=gclk[100]
create_clock -add -name sys_clk_pin -period 10.00 -waveform {0 5} [get_ports { CLK100MHZ }];

## RESET-Taster (aktiv low)
set_property -dict { PACKAGE_PIN C2    IOSTANDARD LVCMOS33 } [get_ports { ck_rst }]; #IO_L16P_T2_35 Sch=ck_rst

## Switches: sw0 = Bosch, sw1 = Bosch drehend, sw2 = HHN, sw3 = Pong
set_property -dict { PACKAGE_PIN A8    IOSTANDARD LVCMOS33 } [get_ports { sw[0] }]; #IO_L12N_T1_MRCC_16 Sch=sw[0]
set_property -dict { PACKAGE_PIN C11   IOSTANDARD LVCMOS33 } [get_ports { sw[1] }]; #IO_L13P_T2_MRCC_16 Sch=sw[1]
set_property -dict { PACKAGE_PIN C10   IOSTANDARD LVCMOS33 } [get_ports { sw[2] }]; #IO_L13N_T2_MRCC_16 Sch=sw[2]
set_property -dict { PACKAGE_PIN A10   IOSTANDARD LVCMOS33 } [get_ports { sw[3] }]; #IO_L14P_T2_SRCC_16 Sch=sw[3]

## Buttons (Pong): btn0/btn1 = links hoch/runter, btn2/btn3 = rechts hoch/runter
set_property -dict { PACKAGE_PIN D9    IOSTANDARD LVCMOS33 } [get_ports { btn[0] }]; #IO_L6N_T0_VREF_16 Sch=btn[0]
set_property -dict { PACKAGE_PIN C9    IOSTANDARD LVCMOS33 } [get_ports { btn[1] }]; #IO_L11P_T1_SRCC_16 Sch=btn[1]
set_property -dict { PACKAGE_PIN B9    IOSTANDARD LVCMOS33 } [get_ports { btn[2] }]; #IO_L11N_T1_SRCC_16 Sch=btn[2]
set_property -dict { PACKAGE_PIN B8    IOSTANDARD LVCMOS33 } [get_ports { btn[3] }]; #IO_L12P_T1_MRCC_16 Sch=btn[3]

## LEDs: Spiegel der Schalter
set_property -dict { PACKAGE_PIN H5    IOSTANDARD LVCMOS33 } [get_ports { led[0] }]; #IO_L24N_T3_35 Sch=led[4]
set_property -dict { PACKAGE_PIN J5    IOSTANDARD LVCMOS33 } [get_ports { led[1] }]; #IO_25_35 Sch=led[5]
set_property -dict { PACKAGE_PIN T9    IOSTANDARD LVCMOS33 } [get_ports { led[2] }]; #IO_L24P_T3_A01_D17_14 Sch=led[6]
set_property -dict { PACKAGE_PIN T10   IOSTANDARD LVCMOS33 } [get_ports { led[3] }]; #IO_L24N_T3_A00_D16_14 Sch=led[7]

## Pmod JD - Pmod OLEDrgb
set_property -dict { PACKAGE_PIN D4    IOSTANDARD LVCMOS33 } [get_ports { oled_cs }];      #IO_L11N_T1_SRCC_35 Sch=jd[1]   CS
set_property -dict { PACKAGE_PIN D3    IOSTANDARD LVCMOS33 } [get_ports { oled_mosi }];    #IO_L12N_T1_MRCC_35 Sch=jd[2]   MOSI
set_property -dict { PACKAGE_PIN F3    IOSTANDARD LVCMOS33 } [get_ports { oled_sck }];     #IO_L13N_T2_MRCC_35 Sch=jd[4]   SCK
set_property -dict { PACKAGE_PIN E2    IOSTANDARD LVCMOS33 } [get_ports { oled_dc }];      #IO_L14P_T2_SRCC_35 Sch=jd[7]   D/C
set_property -dict { PACKAGE_PIN D2    IOSTANDARD LVCMOS33 } [get_ports { oled_res }];     #IO_L14N_T2_SRCC_35 Sch=jd[8]   RES
set_property -dict { PACKAGE_PIN H2    IOSTANDARD LVCMOS33 } [get_ports { oled_vccen }];   #IO_L15P_T2_DQS_35 Sch=jd[9]    VCCEN
set_property -dict { PACKAGE_PIN G2    IOSTANDARD LVCMOS33 } [get_ports { oled_pmoden }];  #IO_L15N_T2_DQS_35 Sch=jd[10]   PMODEN

## Konfiguration
set_property BITSTREAM.GENERAL.COMPRESS TRUE [current_design]
set_property CONFIG_VOLTAGE 3.3 [current_design]
set_property CFGBVS VCCO [current_design]
