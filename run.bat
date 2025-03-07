@echo off
REM filepath: /d:/Code/rok/scanData/roktrackerRemake/run_roktracker.bat
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing required packages...
python setup.py

echo Starting RokTracker...
python main.py


pause