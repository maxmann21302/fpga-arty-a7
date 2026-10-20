## Arty A7-35T: SW0 = x, SW1 = y, SW2 = cin
set_property -dict { PACKAGE_PIN A8  IOSTANDARD LVCMOS33 } [get_ports { x }]
set_property -dict { PACKAGE_PIN C11 IOSTANDARD LVCMOS33 } [get_ports { y }]
set_property -dict { PACKAGE_PIN C10 IOSTANDARD LVCMOS33 } [get_ports { cin }]

## LED0 = sum, LED1 = cout
set_property -dict { PACKAGE_PIN H5 IOSTANDARD LVCMOS33 } [get_ports { sum }]
set_property -dict { PACKAGE_PIN J5 IOSTANDARD LVCMOS33 } [get_ports { cout }]

set_property CONFIG_VOLTAGE 3.3 [current_design]
set_property CFGBVS VCCO [current_design]