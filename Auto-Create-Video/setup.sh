#!/bin/bash
# ════════════════════════════════════════════════════════════════════════════
# Auto News Video — Setup Script
# ════════════════════════════════════════════════════════════════════════════
# Chạy 1 lần duy nhất trên máy mới để cài đặt toàn bộ dependencies.
#
# Cách dùng:
#   chmod +x setup.sh
#   ./setup.sh
# ════════════════════════════════════════════════════════════════════════════

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo ""
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  🎬 Auto News Video — Setup${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo ""

cd "$(dirname "$0")"
PROJECT_DIR="$(pwd)"

# ── 1. Kiểm tra Node.js ──────────────────────────────────────────────────
echo -e "${YELLOW}[1/6]${NC} Kiểm tra Node.js..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "  ${GREEN}✓${NC} Node.js $NODE_VERSION"
else
    echo -e "  ${RED}✗ Node.js chưa cài!${NC}"
    echo -e "  Cài bằng: ${CYAN}brew install node${NC} (macOS) hoặc tải từ https://nodejs.org"
    exit 1
fi

# ── 2. Kiểm tra Python 3 ─────────────────────────────────────────────────
echo -e "${YELLOW}[2/6]${NC} Kiểm tra Python 3..."
if command -v python3 &> /dev/null; then
    PY_VERSION=$(python3 --version)
    echo -e "  ${GREEN}✓${NC} $PY_VERSION"
else
    echo -e "  ${RED}✗ Python 3 chưa cài!${NC}"
    echo -e "  Cài bằng: ${CYAN}brew install python3${NC} (macOS)"
    exit 1
fi

# ── 3. Kiểm tra FFmpeg ───────────────────────────────────────────────────
echo -e "${YELLOW}[3/6]${NC} Kiểm tra FFmpeg..."
if command -v ffmpeg &> /dev/null; then
    echo -e "  ${GREEN}✓${NC} FFmpeg đã cài"
else
    echo -e "  ${RED}✗ FFmpeg chưa cài!${NC}"
    echo -e "  Cài bằng: ${CYAN}brew install ffmpeg${NC} (macOS)"
    echo -e "  FFmpeg cần thiết để render video."
    exit 1
fi

# ── 4. Cài Node.js dependencies ──────────────────────────────────────────
echo -e "${YELLOW}[4/6]${NC} Cài đặt Node.js dependencies..."
if [ -d "node_modules" ]; then
    echo -e "  ${GREEN}✓${NC} node_modules đã tồn tại, skip. (Chạy 'npm install' thủ công nếu cần update)"
else
    npm install
    echo -e "  ${GREEN}✓${NC} npm install thành công"
fi

# ── 5. Tạo Python venv + cài dependencies ────────────────────────────────
echo -e "${YELLOW}[5/6]${NC} Tạo Python virtual environment..."
if [ -d ".venv" ]; then
    echo -e "  ${GREEN}✓${NC} .venv đã tồn tại, skip."
else
    python3 -m venv .venv
    echo -e "  ${GREEN}✓${NC} .venv đã tạo"
fi

echo -e "${YELLOW}[5/6]${NC} Cài đặt Python dependencies..."
source .venv/bin/activate
pip install -q -r requirements.txt
echo -e "  ${GREEN}✓${NC} Python packages đã cài"

# ── 6. Tạo file .env nếu chưa có ─────────────────────────────────────────
echo -e "${YELLOW}[6/6]${NC} Kiểm tra file .env..."
if [ -f ".env" ]; then
    echo -e "  ${GREEN}✓${NC} .env đã tồn tại"
else
    cp .env.example .env
    echo -e "  ${YELLOW}⚠${NC} Đã tạo .env từ .env.example"
    echo -e "  ${YELLOW}→ Hãy mở file .env và điền API keys trước khi chạy!${NC}"
fi

echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ Setup hoàn tất!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  Bước tiếp theo:"
echo -e "  1. Mở file ${CYAN}.env${NC} và điền API keys (nếu chưa)"
echo -e "  2. Chạy bot:  ${CYAN}./run.sh${NC}"
echo ""
