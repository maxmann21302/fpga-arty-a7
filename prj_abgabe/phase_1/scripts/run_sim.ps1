param([string]$Ghdl = 'ghdl')
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$phase = Split-Path $root -Leaf
if ($phase -notmatch '^phase_([12])$') { throw 'Unbekannte Phase' }
$top = 'phase' + $Matches[1] + '_top'
$build = Join-Path $root 'sim/build'
New-Item -ItemType Directory -Force $build | Out-Null
Push-Location $build
try {
    & $Ghdl -a --std=08 "$root/src/clock_pkg.vhd" "$root/src/tick_gen.vhd" "$root/src/seg7_decoder.vhd" "$root/src/ssd_driver.vhd" "$root/src/$top.vhd" "$root/sim/tb_$top.vhd"
    if ($LASTEXITCODE -ne 0) { throw 'VHDL-Analyse fehlgeschlagen' }
    & $Ghdl --elab-run --std=08 "tb_$top" --assert-level=error --wave=simulation.ghw
    if ($LASTEXITCODE -ne 0) { throw 'Simulation fehlgeschlagen' }
} finally {
    Pop-Location
}