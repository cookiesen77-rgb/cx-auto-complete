@echo off
chcp 65001 >nul
title 超星学习通 Web 界面

echo.
echo   超星学习通 Web 可视化界面
echo   访问地址: http://127.0.0.1:8080
echo.

cd /d "%~dp0"

if exist "venv\Scripts\python.exe" (
    echo [*] 启动中...
    venv\Scripts\python.exe web_app.py
) else (
    echo [!] 未找到虚拟环境，正在安装...
    python -m venv venv
    venv\Scripts\pip.exe install -r requirements.txt -q
    venv\Scripts\python.exe web_app.py
)

pause
