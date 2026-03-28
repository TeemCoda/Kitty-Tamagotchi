@echo off
:: Desktop Cat — Install dependencies and launch
echo Installing dependencies...
pip install -r requirements.txt --quiet
echo Done!
echo.
echo Launching Desktop Cat... (look for the cat in the corner and the tray icon!)
start "" pythonw main.py
