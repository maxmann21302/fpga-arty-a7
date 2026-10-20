set script_dir [file normalize [file dirname [info script]]]
set root [file normalize "$script_dir/.."]
if {![regexp {phase_([12])$} [file tail $root] unused phase]} {
    error "Projekt muss in phase_1 oder phase_2 liegen"
}
set top "phase${phase}_top"
create_project "phase${phase}" "$root/vivado" -part xc7a35ticsg324-1L -force
add_files -fileset sources_1 [glob "$root/src/*.vhd"]
add_files -fileset sim_1 [glob "$root/sim/*.vhd"]
add_files -fileset constrs_1 "$root/constraints/arty_a7_35_ssd.xdc"
set_property file_type {VHDL 2008} [get_files *.vhd]
set_property top $top [get_filesets sources_1]
set_property top "tb_$top" [get_filesets sim_1]
set_property xsim.simulate.runtime all [get_filesets sim_1]
update_compile_order -fileset sources_1
update_compile_order -fileset sim_1
puts "Projekt erstellt: $root/vivado; Top: $top"