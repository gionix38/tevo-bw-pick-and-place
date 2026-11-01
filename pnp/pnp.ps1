# TEVO-BW PnP model CLI. Usage: .\pnp.ps1 build | render | check | all | info  [--pose X Y Z C] [--views iso,head]
if (-not $env:FREECAD_BIN) {
    $candidates = @(
        (Join-Path $env:LOCALAPPDATA "Programs\FreeCAD_1_1\bin"),
        (Join-Path $env:LOCALAPPDATA "Programs\FreeCAD 1.1\bin")
    )
    $env:FREECAD_BIN = $candidates | Where-Object { Test-Path (Join-Path $_ "python.exe") } | Select-Object -First 1
}
if (-not $env:FREECAD_BIN) { throw "FreeCAD python.exe not found. Set FREECAD_BIN to the FreeCAD bin directory." }
& (Join-Path $env:FREECAD_BIN "python.exe") -I (Join-Path $PSScriptRoot "pnp.py") @args
exit $LASTEXITCODE
