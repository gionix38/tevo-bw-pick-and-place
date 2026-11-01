@echo off
rem TBW-Feeder v3.0 CLI. Usage: feeder build ^| audit ^| all ^| explode
if "%FREECAD_BIN%"=="" if exist "%LOCALAPPDATA%\Programs\FreeCAD_1_1\bin\python.exe" set "FREECAD_BIN=%LOCALAPPDATA%\Programs\FreeCAD_1_1\bin"
if "%FREECAD_BIN%"=="" if exist "%LOCALAPPDATA%\Programs\FreeCAD 1.1\bin\python.exe" set "FREECAD_BIN=%LOCALAPPDATA%\Programs\FreeCAD 1.1\bin"
if "%FREECAD_BIN%"=="" (
  echo FreeCAD python.exe not found. Set FREECAD_BIN to the FreeCAD bin directory.
  exit /b 1
)
"%FREECAD_BIN%\python.exe" -I "%~dp0tbw_feeder.py" %*
