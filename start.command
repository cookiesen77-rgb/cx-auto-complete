#!/bin/bash
# ============================================
#   超星学习通助手 - macOS 启动脚本
#   双击此文件即可启动应用
# ============================================

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

clear
echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║      超星学习通助手 - 启动中...              ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════╝${NC}"
echo ""

# 检查 Python3
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
        echo -e "${GREEN}✓${NC} Python3 已安装"
        return 0
    elif command -v python &> /dev/null; then
        if python --version 2>&1 | grep -q "Python 3"; then
            PYTHON_CMD="python"
            echo -e "${GREEN}✓${NC} Python3 已安装"
            return 0
        fi
    fi
    
    echo -e "${RED}✗${NC} 未检测到 Python3"
    echo ""
    echo -e "${YELLOW}请先安装 Python3:${NC}"
    echo "  访问 https://www.python.org/downloads/"
    echo "  下载并安装 Python 3.9 或更高版本"
    echo ""
    read -p "按回车键退出..."
    exit 1
}

# 检查并创建虚拟环境
setup_venv() {
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}→${NC} 首次运行，创建虚拟环境..."
        $PYTHON_CMD -m venv venv
        if [ $? -ne 0 ]; then
            echo -e "${RED}✗${NC} 创建虚拟环境失败"
            read -p "按回车键退出..."
            exit 1
        fi
        echo -e "${GREEN}✓${NC} 虚拟环境已创建"
    fi
}

# 激活虚拟环境
activate_venv() {
    source venv/bin/activate
    echo -e "${GREEN}✓${NC} 虚拟环境已激活"
}

# 安装依赖
install_deps() {
    if [ ! -f "venv/.deps_installed" ]; then
        echo -e "${YELLOW}→${NC} 安装依赖中，请稍候..."
        pip install --upgrade pip -q 2>/dev/null
        pip install -r requirements.txt -q 2>/dev/null
        if [ $? -ne 0 ]; then
            echo -e "${RED}✗${NC} 依赖安装失败，请检查网络"
            read -p "按回车键退出..."
            exit 1
        fi
        touch venv/.deps_installed
        echo -e "${GREEN}✓${NC} 依赖安装完成"
    else
        echo -e "${GREEN}✓${NC} 依赖已就绪"
    fi
}

# 启动应用
start_app() {
    echo ""
    echo -e "${BLUE}══════════════════════════════════════════════${NC}"
    echo ""
    echo -e "  ${GREEN}应用已启动！${NC}"
    echo ""
    echo -e "  访问地址: ${YELLOW}http://127.0.0.1:7002${NC}"
    echo ""
    echo -e "  ${RED}关闭此窗口将停止应用${NC}"
    echo ""
    echo -e "${BLUE}══════════════════════════════════════════════${NC}"
    echo ""
    
    # 打开浏览器
    sleep 1
    open "http://127.0.0.1:7002"
    
    # 启动服务
    $PYTHON_CMD web_app.py
}

# 主流程
main() {
    check_python
    setup_venv
    activate_venv
    install_deps
    start_app
}

main

