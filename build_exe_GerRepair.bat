@echo off
setlocal
cd /d "%~dp0"

echo.
echo Baue GerRepair SPD Raw Dumper Alpha...
echo.

py -3 -m pip install --upgrade pyinstaller
if errorlevel 1 goto :fail

py -3 -m PyInstaller --onefile --windowed --name "GerRepair_SPD_RAW_Dumper_Alpha" --icon "GerRepair_icon.ico" "SPD_Read_GerRepair_Alpha.py"
if errorlevel 1 goto :fail

echo.
echo Kopiere Treiberdateien, falls vorhanden...
if exist inpoutx64.dll copy /Y inpoutx64.dll dist\
if exist InpOutx64.dll copy /Y InpOutx64.dll dist\
if exist WinRing0x64.dll copy /Y WinRing0x64.dll dist\
if exist WinRing0x64.sys copy /Y WinRing0x64.sys dist\

echo.
echo Fertig:
echo "%~dp0dist\GerRepair_SPD_RAW_Dumper_Alpha.exe"
pause
exit /b 0

:fail
echo.
echo Build fehlgeschlagen.
pause
exit /b 1
