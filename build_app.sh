#!/bin/bash

echo "=========================================="
echo "  超星学习通 - 应用打包脚本 (macOS)"
echo "=========================================="
echo ""

cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
    echo "[*] 创建虚拟环境..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt -q
    pip install pyinstaller -q
else
    source venv/bin/activate
fi

echo "[*] 清理旧的构建文件..."
rm -rf build dist

echo "[*] 开始打包应用..."
pyinstaller cx_app.spec --clean

if [ -d "dist/超星学习通" ]; then
    echo ""
    echo "=========================================="
    echo "  ✅ 打包成功！"
    echo "=========================================="
    echo ""
    echo "应用位置: dist/超星学习通/"
    echo ""
    echo "运行方式:"
    echo "  cd dist/超星学习通"
    echo "  ./超星学习通"
    echo ""
    echo "浏览器访问: http://127.0.0.1:8080"
    echo ""
else
    echo ""
    echo "❌ 打包失败，请检查错误信息"
    exit 1
fi
