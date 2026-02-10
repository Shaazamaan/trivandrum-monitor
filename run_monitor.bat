@echo off
cd /d "%~dp0"
echo Starting Google Maps Monitor...
echo Press Ctrl+C to stop.
:loop
python main.py
echo Monitor crashed or stopped. Restarting in 10 seconds...
timeout /t 10
goto loop
