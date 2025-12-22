@echo off
chcp 65001 >nul
title 超星学习通 命令行版

cd /d "%~dp0"

if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe main.py %*
) else (
    echo [*] 创建虚拟环境...
    python -m venv venv
    venv\Scripts\pip.exe install -r requirements.txt -q
    venv\Scripts\python.exe main.py %*
)

pause
