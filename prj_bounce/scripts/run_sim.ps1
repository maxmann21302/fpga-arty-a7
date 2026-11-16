param([string]$Ghdl = 'ghdl')
$ErrorActionPreference = 'Stop'
$root  = Split-Path $PSScriptRoot -Parent
$build = Join-Path $root 'sim/build'
New-Item -ItemType Directory -Force $build | Out-Null
Push-Location $build
try {
    $src = 'bounce_pkg','btn_debounce','spi_tx','oled_ctrl','bounce_capture','bounce_render','bounce_top' | ForEach-Object { "$root/src/$_.vhd" }
    & $Ghdl -a --std=08 @src "$root/sim/tb_bounce_capture.vhd"
    if ($LASTEXITCODE -ne 0) { throw 'VHDL-Analyse fehlgeschlagen' }
    & $Ghdl -e --std=08 bounce_top
    if ($LASTEXITCODE -ne 0) { throw 'Elaboration bounce_top fehlgeschlagen' }
    & $Ghdl --elab-run --std=08 tb_bounce_capture --assert-level=error
    if ($LASTEXITCODE -ne 0) { throw 'Simulation fehlgeschlagen' }
} finally {
    Pop-Location
}
