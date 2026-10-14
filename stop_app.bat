@echo off
cd /d "%~dp0"
title CS2 Highlights Studio - Shutdown
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\stop_app.ps1"
