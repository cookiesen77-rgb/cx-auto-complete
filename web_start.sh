#!/bin/bash

cd "$(dirname "$0")"

echo ""
echo "  超星学习通 Web 可视化界面"
echo "  访问地址: http://127.0.0.1:7002"
echo ""

if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "[*] 创建虚拟环境..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt -q
fi

echo "[*] 启动中..."
python web_app.py
