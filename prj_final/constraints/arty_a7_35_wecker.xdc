## ---------------------------------------------------------------------------
## Digitale Uhr / Wecker - Arty A7-35T (Rev. D/E)
## Pin-Constraints, abgeleitet vom Digilent Arty-A7-35-Master.xdc
##
## Pmod SSD #1 (links, Stunden)  : JA + JB, jeweils UNTERE Reihe (Pins 7-10)
## Pmod SSD #2 (rechts, Minuten) : JC + JD, jeweils UNTERE Reihe (Pins 7-10)
## Buzzer                        : JA Pin 1 (obere Reihe ist frei)
## ---------------------------------------------------------------------------

## Clock signal (100 MHz)
set_property -dict { PACKAGE_PIN E3    IOSTANDARD LVCMOS33 } [get_ports { CLK100MHZ }]; #IO_L12P_T1_MRCC_35 Sch=gclk[100]
create_clock -add -name sys_clk_pin -period 10.00 -waveform {0 5} [get_ports { CLK100MHZ }];

## RESET-Taster (aktiv low)
set_property -dict { PACKAGE_PIN C2    IOSTANDARD LVCMOS33 } [get_ports { ck_rst }]; #IO_L16P_T2_35 Sch=ck_rst

## Switches
## sw0 = Sekundenanzeige, sw1 = Zeit stellen, sw2 = Weckzeit stellen, sw3 = Wecker scharf
set_property -dict { PACKAGE_PIN A8    IOSTANDARD LVCMOS33 } [get_ports { sw[0] }]; #IO_L12N_T1_MRCC_16 Sch=sw[0]
set_property -dict { PACKAGE_PIN C11   IOSTANDARD LVCMOS33 } [get_ports { sw[1] }]; #IO_L13P_T2_MRCC_16 Sch=sw[1]
set_property -dict { PACKAGE_PIN C10   IOSTANDARD LVCMOS33 } [get_ports { sw[2] }]; #IO_L13N_T2_MRCC_16 Sch=sw[2]
set_property -dict { PACKAGE_PIN A10   IOSTANDARD LVCMOS33 } [get_ports { sw[3] }]; #IO_L14P_T2_SRCC_16 Sch=sw[3]

## Buttons
## btn0 = Stunden +, btn1 = Stunden -, btn2 = Minuten +, btn3 = Minuten -
set_property -dict { PACKAGE_PIN D9    IOSTANDARD LVCMOS33 } [get_ports { btn[0] }]; #IO_L6N_T0_VREF_16 Sch=btn[0]
set_property -dict { PACKAGE_PIN C9    IOSTANDARD LVCMOS33 } [get_ports { btn[1] }]; #IO_L11P_T1_SRCC_16 Sch=btn[1]
set_property -dict { PACKAGE_PIN B9    IOSTANDARD LVCMOS33 } [get_ports { btn[2] }]; #IO_L11N_T1_SRCC_16 Sch=btn[2]
set_property -dict { PACKAGE_PIN B8    IOSTANDARD LVCMOS33 } [get_ports { btn[3] }]; #IO_L12P_T1_MRCC_16 Sch=btn[3]

## LEDs (optische Weck-Signalisierung / Statusanzeige)
set_property -dict { PACKAGE_PIN H5    IOSTANDARD LVCMOS33 } [get_ports { led[0] }]; #IO_L24N_T3_35 Sch=led[4]
set_property -dict { PACKAGE_PIN J5    IOSTANDARD LVCMOS33 } [get_ports { led[1] }]; #IO_25_35 Sch=led[5]
set_property -dict { PACKAGE_PIN T9    IOSTANDARD LVCMOS33 } [get_ports { led[2] }]; #IO_L24P_T3_A01_D17_14 Sch=led[6]
set_property -dict { PACKAGE_PIN T10   IOSTANDARD LVCMOS33 } [get_ports { led[3] }]; #IO_L24N_T3_A00_D16_14 Sch=led[7]

## Pmod Header JA - Pin 1: Buzzer, Pins 7-10: Pmod SSD #1 Header J1 (AA..AD)
set_property -dict { PACKAGE_PIN G13   IOSTANDARD LVCMOS33 } [get_ports { buzzer_o }]; #IO_0_15 Sch=ja[1]
set_property -dict { PACKAGE_PIN D13   IOSTANDARD LVCMOS33 } [get_ports { seg_l[0] }]; #IO_L6N_T0_VREF_15 Sch=ja[7]   AA
set_property -dict { PACKAGE_PIN B18   IOSTANDARD LVCMOS33 } [get_ports { seg_l[1] }]; #IO_L10P_T1_AD11P_15 Sch=ja[8]  AB
set_property -dict { PACKAGE_PIN A18   IOSTANDARD LVCMOS33 } [get_ports { seg_l[2] }]; #IO_L10N_T1_AD11N_15 Sch=ja[9]  AC
set_property -dict { PACKAGE_PIN K16   IOSTANDARD LVCMOS33 } [get_ports { seg_l[3] }]; #IO_25_15 Sch=ja[10]            AD

## Pmod Header JB - Pins 7-10: Pmod SSD #1 Header J2 (AE, AF, AG, C)
set_property -dict { PACKAGE_PIN J17   IOSTANDARD LVCMOS33 } [get_ports { seg_l[4] }]; #IO_L23P_T3_FOE_B_15 Sch=jb_p[3]  AE
set_property -dict { PACKAGE_PIN J18   IOSTANDARD LVCMOS33 } [get_ports { seg_l[5] }]; #IO_L23N_T3_FWE_B_15 Sch=jb_n[3]  AF
set_property -dict { PACKAGE_PIN K15   IOSTANDARD LVCMOS33 } [get_ports { seg_l[6] }]; #IO_L24P_T3_RS1_15 Sch=jb_p[4]    AG
set_property -dict { PACKAGE_PIN J15   IOSTANDARD LVCMOS33 } [get_ports { dsel_l }];   #IO_L24N_T3_RS0_15 Sch=jb_n[4]    C

## Pmod Header JC - Pins 7-10: Pmod SSD #2 Header J1 (AA..AD)
set_property -dict { PACKAGE_PIN U14   IOSTANDARD LVCMOS33 } [get_ports { seg_r[0] }]; #IO_L22P_T3_A05_D21_14 Sch=jc_p[3]  AA
set_property -dict { PACKAGE_PIN V14   IOSTANDARD LVCMOS33 } [get_ports { seg_r[1] }]; #IO_L22N_T3_A04_D20_14 Sch=jc_n[3]  AB
set_property -dict { PACKAGE_PIN T13   IOSTANDARD LVCMOS33 } [get_ports { seg_r[2] }]; #IO_L23P_T3_A03_D19_14 Sch=jc_p[4]  AC
set_property -dict { PACKAGE_PIN U13   IOSTANDARD LVCMOS33 } [get_ports { seg_r[3] }]; #IO_L23N_T3_A02_D18_14 Sch=jc_n[4]  AD

## Pmod Header JD - Pins 7-10: Pmod SSD #2 Header J2 (AE, AF, AG, C)
set_property -dict { PACKAGE_PIN E2    IOSTANDARD LVCMOS33 } [get_ports { seg_r[4] }]; #IO_L14P_T2_SRCC_35 Sch=jd[7]   AE
set_property -dict { PACKAGE_PIN D2    IOSTANDARD LVCMOS33 } [get_ports { seg_r[5] }]; #IO_L14N_T2_SRCC_35 Sch=jd[8]   AF
set_property -dict { PACKAGE_PIN H2    IOSTANDARD LVCMOS33 } [get_ports { seg_r[6] }]; #IO_L15P_T2_DQS_35 Sch=jd[9]    AG
set_property -dict { PACKAGE_PIN G2    IOSTANDARD LVCMOS33 } [get_ports { dsel_r }];   #IO_L15N_T2_DQS_35 Sch=jd[10]   C

## Konfiguration
set_property BITSTREAM.GENERAL.COMPRESS TRUE [current_design]
set_property CONFIG_VOLTAGE 3.3 [current_design]
set_property CFGBVS VCCO [current_design]
