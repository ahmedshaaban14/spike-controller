@echo off
setlocal
cd /d "%~dp0"
set "SPIKE_PYTHON=python"
if exist "C:\Python311\python.exe" set "SPIKE_PYTHON=C:\Python311\python.exe"
"%SPIKE_PYTHON%" -c "import sys; assert sys.version_info[:2] == (3, 11), 'Python 3.11 required for building'"
if errorlevel 1 goto failed
"%SPIKE_PYTHON%" -m pip install -r requirements.txt
if errorlevel 1 goto failed
"%SPIKE_PYTHON%" -m pip install pyinstaller==6.22.3
if errorlevel 1 goto failed
"%SPIKE_PYTHON%" -m PyInstaller --noconfirm "SPIKE Controller.spec"
if errorlevel 1 goto failed
copy /y README.md "dist\SPIKE Controller\README.md" >nul
echo Build complete: dist\SPIKE Controller\SPIKE Controller.exe
exit /b 0
:failed
echo Build failed. Review the error above.
exit /b 1
