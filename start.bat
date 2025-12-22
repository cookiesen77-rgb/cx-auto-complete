@echo off
chcp 65001 >nul
title 超星学习通助手 - Web界面

cd /d "%~dp0"

echo.
echo ╔══════════════════════════════════════════════╗
echo ║      超星学习通助手 - 启动中...              ║
echo ╚══════════════════════════════════════════════╝
echo.

:: 检查 Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] 未检测到 Python
    echo.
    echo 请先安装 Python3:
    echo   访问 https://www.python.org/downloads/
    echo   下载并安装 Python 3.9 或更高版本
    echo.
    pause
    exit /b 1
)

echo [√] Python 已安装

:: 检查虚拟环境
if not exist "venv\Scripts\python.exe" (
    echo [→] 首次运行，创建虚拟环境...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [X] 创建虚拟环境失败
        pause
        exit /b 1
    )
    echo [√] 虚拟环境已创建
)

:: 激活虚拟环境
call venv\Scripts\activate.bat
echo [√] 虚拟环境已激活

:: 安装依赖
if not exist "venv\.deps_installed" (
    echo [→] 安装依赖中，请稍候...
    pip install --upgrade pip -q 2>nul
    pip install -r requirements.txt -q 2>nul
    if %errorlevel% neq 0 (
        echo [X] 依赖安装失败，请检查网络
        pause
        exit /b 1
    )
    echo. > venv\.deps_installed
    echo [√] 依赖安装完成
) else (
    echo [√] 依赖已就绪
)

echo.
echo ══════════════════════════════════════════════
echo.
echo   应用已启动！
echo.
echo   访问地址: http://127.0.0.1:7002
echo.
echo   关闭此窗口将停止应用
echo.
echo ══════════════════════════════════════════════
echo.

:: 打开浏览器
start http://127.0.0.1:7002

:: 启动服务
python web_app.py

pause
