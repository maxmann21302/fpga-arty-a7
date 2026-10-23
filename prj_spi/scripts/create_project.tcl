# Vivado-Projekt fuer Pmod OLEDrgb (SPI) erzeugen
#   vivado -mode batch -source scripts/create_project.tcl
#   vivado -mode gui   -source scripts/create_project.tcl
# Bitmaps neu erzeugen: python scripts/gen_rom.py

set script_dir [file normalize [file dirname [info script]]]
set root       [file normalize "$script_dir/.."]

set proj_name "spi_oled"
set part      "xc7a35ticsg324-1L"

create_project $proj_name "$root/vivado" -part $part -force

add_files -fileset sources_1 [glob "$root/src/*.vhd"]
add_files -fileset sim_1     [glob "$root/sim/*.vhd"]
add_files -fileset constrs_1 "$root/constraints/arty_a7_35_oled.xdc"

set_property file_type {VHDL 2008} [get_files -of_objects [get_filesets sources_1] *.vhd]
set_property file_type {VHDL 2008} [get_files -of_objects [get_filesets sim_1] *.vhd]

set_property top spi_top    [get_filesets sources_1]
set_property top tb_spi_top [get_filesets sim_1]

update_compile_order -fileset sources_1
update_compile_order -fileset sim_1

puts "Projekt '$proj_name' angelegt unter $root/vivado"
