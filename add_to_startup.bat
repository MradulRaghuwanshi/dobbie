@echo off
REM Add Dobbie to Windows Startup
REM This script creates a shortcut in the startup folder

setlocal enabledelayedexpansion

REM Get the startup folder path
set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"

REM Create the shortcut
REM Using a VBScript to create the shortcut
(
    echo Set objShell = CreateObject("WScript.Shell"^)
    echo Set objLink = objShell.CreateShortcut("%STARTUP_FOLDER%\Dobbie.lnk"^)
    echo objLink.TargetPath = "c:\Users\mradu\Desktop\dobbie\run_dobbie.bat"
    echo objLink.WorkingDirectory = "c:\Users\mradu\Desktop\dobbie"
    echo objLink.Description = "Dobbie - Magical Desktop Assistant"
    echo objLink.WindowStyle = 7
    echo objLink.Save
) > "%temp%\create_shortcut.vbs"

cscript.exe "%temp%\create_shortcut.vbs"

if errorlevel 1 (
    echo.
    echo ❌ Failed to create startup shortcut
    echo.
    pause
    exit /b 1
) else (
    echo.
    echo ✓ Dobbie has been added to Windows Startup!
    echo.
    echo Dobbie will now automatically start when your PC boots up.
    echo Your browser will open to http://localhost:5000
    echo.
    echo To remove Dobbie from startup, delete the shortcut from:
    echo %STARTUP_FOLDER%
    echo.
    pause
)

del "%temp%\create_shortcut.vbs"
exit /b 0
