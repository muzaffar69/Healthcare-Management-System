@echo off
echo Building Medical Practice Management executable...
echo.
pyinstaller medical_practice.spec --clean
echo.
echo Build complete! Check the 'dist' folder for the executable.
pause
