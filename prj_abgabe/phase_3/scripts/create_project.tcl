# Vivado-Projekt fuer die digitale Uhr / Wecker erzeugen
#   vivado -mode batch -source scripts/create_project.tcl
#   vivado -mode gui   -source scripts/create_project.tcl

set script_dir [file normalize [file dirname [info script]]]
set root       [file normalize "$script_dir/.."]

set proj_name "wecker"
set part      "xc7a35ticsg324-1L"

create_project $proj_name "$root/vivado" -part $part -force

add_files -fileset sources_1 [glob "$root/src/*.vhd"]
add_files -fileset sim_1     [glob "$root/sim/*.vhd"]
add_files -fileset constrs_1 "$root/constraints/arty_a7_35_wecker.xdc"

set_property file_type {VHDL} [get_files -of_objects [get_filesets sources_1] *.vhd]
set_property file_type {VHDL} [get_files -of_objects [get_filesets sim_1] *.vhd]

set_property top wecker_top    [get_filesets sources_1]
set_property top tb_wecker_top [get_filesets sim_1]

update_compile_order -fileset sources_1
update_compile_order -fileset sim_1

puts "Projekt '$proj_name' angelegt unter $root/vivado"
