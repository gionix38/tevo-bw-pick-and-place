@echo off
rem TEVO-BW PnP model CLI. Usage: pnp build ^| render ^| check ^| all ^| info  [--pose X Y Z C] [--views iso,head]
if "%FREECAD_BIN%"=="" if exist "%LOCALAPPDATA%\Programs\FreeCAD_1_1\bin\python.exe" set "FREECAD_BIN=%LOCALAPPDATA%\Programs\FreeCAD_1_1\bin"
if "%FREECAD_BIN%"=="" if exist "%LOCALAPPDATA%\Programs\FreeCAD 1.1\bin\python.exe" set "FREECAD_BIN=%LOCALAPPDATA%\Programs\FreeCAD 1.1\bin"
if "%FREECAD_BIN%"=="" (
  echo FreeCAD python.exe not found. Set FREECAD_BIN to the FreeCAD bin directory.
  exit /b 1
)
"%FREECAD_BIN%\python.exe" -I "%~dp0pnp.py" %*
