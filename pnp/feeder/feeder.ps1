# TBW-Feeder v3.0 CLI. Usage: .\feeder.ps1 build | audit | all | explode
if (-not $env:FREECAD_BIN) {
    $candidates = @(
        (Join-Path $env:LOCALAPPDATA "Programs\FreeCAD_1_1\bin"),
        (Join-Path $env:LOCALAPPDATA "Programs\FreeCAD 1.1\bin")
    )
    $env:FREECAD_BIN = $candidates | Where-Object { Test-Path (Join-Path $_ "python.exe") } | Select-Object -First 1
}
if (-not $env:FREECAD_BIN) { throw "FreeCAD python.exe not found. Set FREECAD_BIN to the FreeCAD bin directory." }
& (Join-Path $env:FREECAD_BIN "python.exe") -I (Join-Path $PSScriptRoot "tbw_feeder.py") @args
exit $LASTEXITCODE
