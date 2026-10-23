param([string]$Ghdl = 'ghdl')
$ErrorActionPreference = 'Stop'
$root  = Split-Path $PSScriptRoot -Parent
$build = Join-Path $root 'sim/build'
New-Item -ItemType Directory -Force $build | Out-Null
Push-Location $build
try {
    $src = 'oled_rom_pkg','input_filter','spi_tx','oled_ctrl','pong_game','oled_render','spi_top' | ForEach-Object { "$root/src/$_.vhd" }
    & $Ghdl -a --std=08 @src "$root/sim/tb_spi_top.vhd"
    if ($LASTEXITCODE -ne 0) { throw 'VHDL-Analyse fehlgeschlagen' }
    & $Ghdl --elab-run --std=08 tb_spi_top --assert-level=error
    if ($LASTEXITCODE -ne 0) { throw 'Simulation fehlgeschlagen' }
} finally {
    Pop-Location
}
