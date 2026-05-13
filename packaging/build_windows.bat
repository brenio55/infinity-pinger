@echo off
echo ===================================================
echo  InfinityPinger - Gerador de Executavel (Windows)
echo ===================================================

echo.
echo 1. Instalando PyInstaller...
pip install pyinstaller

echo.
echo 2. Compilando o executavel standalone...
cd ..
pyinstaller --noconfirm --onedir --windowed ^
  --icon "icon.ico" ^
  --add-data "icon.ico;." ^
  --add-data "logo.png;." ^
  --name "InfinityPinger" ^
  --distpath "packaging\dist" ^
  --workpath "packaging\temp" ^
  "main.py"
cd packaging

echo.
echo 3. Verificando Inno Setup Compiler (ISCC)...
set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

if not exist %ISCC% goto NO_INNO

echo    Inno Setup encontrado! Compilando o instalador Final...
if not exist "..\releases" mkdir "..\releases"
%ISCC% "windows_installer.iss"
echo.
echo ===================================================
echo  Concluido! Instalador gerado na pasta "releases"
echo ===================================================
goto END_INNO

:NO_INNO
echo.
echo ===================================================
echo  [AVISO] Inno Setup nao foi encontrado no sistema.
echo  O executavel isolado (sem instalador) foi gerado em:
echo  "packaging\dist\InfinityPinger\"
echo.
echo  Para gerar um .exe instalavel, instale o Inno Setup
echo  e execute este script novamente.
echo ===================================================

:END_INNO
pause
