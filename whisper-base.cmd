@echo on
REM Change to the project directory
cd U:\voothi\20250228230803-whisper

REM Pause to see the results
@REM pause

REM Activate the virtual environment
.\venv\Scripts\python.exe .\whisper.py --clipboard --timestamp --model "base" --tray