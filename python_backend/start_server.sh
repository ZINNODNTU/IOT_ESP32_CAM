#!/bin/bash

# ===============================================
# AttendAI IoT Server Startup Script
# Dành cho AWS EC2 Ubuntu/Linux
# ===============================================

set -e  # Exit on error

echo "=========================================="
echo "  AttendAI IoT Server - Starting..."
echo "=========================================="

# Màu sắc cho output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Kiểm tra Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 chưa được cài đặt!${NC}"
    echo "Chạy: sudo apt install python3 python3-pip python3-venv"
    exit 1
fi

echo -e "${GREEN}✅ Python3 found: $(python3 --version)${NC}"

# Kiểm tra virtual environment
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment chưa tồn tại. Đang tạo...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

# Kích hoạt virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Kiểm tra và cài đặt dependencies
if [ ! -f "venv/installed.flag" ]; then
    echo "📦 Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    touch venv/installed.flag
    echo -e "${GREEN}✅ Dependencies installed${NC}"
else
    echo -e "${GREEN}✅ Dependencies already installed${NC}"
fi

# Kiểm tra các thư mục cần thiết
echo "📁 Checking directories..."
mkdir -p known_faces
mkdir -p templates
echo -e "${GREEN}✅ Directories ready${NC}"

# Kiểm tra file cấu hình
if [ ! -f "config.py" ]; then
    echo -e "${RED}❌ config.py không tồn tại!${NC}"
    exit 1
fi

# Lấy Public IP (nếu trên AWS)
echo "🌐 Detecting public IP..."
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "localhost")
echo -e "${GREEN}✅ Public IP: $PUBLIC_IP${NC}"

# Export environment variables
export PUBLIC_HOST=${PUBLIC_HOST:-$PUBLIC_IP}
export PORT=${PORT:-3000}

echo ""
echo "=========================================="
echo "  Configuration Summary"
echo "=========================================="
echo "Public Host: $PUBLIC_HOST"
echo "Port: $PORT"
echo "Working Directory: $(pwd)"
echo "=========================================="
echo ""

# Chạy server
echo "🚀 Starting AttendAI server..."
echo ""

python websockets_stream.py

# Cleanup khi thoát
trap 'echo -e "\n${YELLOW}🛑 Server stopped${NC}"' EXIT
