@echo off
chcp 65001 >nul
cd /d "%~dp0"
title CS2 Highlights Studio — Launcher

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start_app.ps1"
