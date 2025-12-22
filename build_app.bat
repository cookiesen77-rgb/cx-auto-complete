@echo off
chcp 65001 >nul
title 超星学习通 - 应用打包

echo ==========================================
echo   超星学习通 - 应用打包脚本 (Windows)
echo ==========================================
echo.

cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo [*] 创建虚拟环境...
    python -m venv venv
    venv\Scripts\pip.exe install -r requirements.txt -q
    venv\Scripts\pip.exe install pyinstaller -q
)

call venv\Scripts\activate.bat

echo [*] 清理旧的构建文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo [*] 开始打包应用...
pyinstaller cx_app.spec --clean

if exist "dist\超星学习通" (
    echo.
    echo ==========================================
    echo   ✅ 打包成功！
    echo ==========================================
    echo.
    echo 应用位置: dist\超星学习通\
    echo.
    echo 运行方式:
    echo   cd dist\超星学习通
    echo   超星学习通.exe
    echo.
    echo 浏览器访问: http://127.0.0.1:8080
    echo.
) else (
    echo.
    echo ❌ 打包失败，请检查错误信息
    pause
    exit /b 1
)

pause
