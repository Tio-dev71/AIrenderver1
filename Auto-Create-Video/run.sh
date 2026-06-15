#!/bin/bash
# ════════════════════════════════════════════════════════════════════════════
# Auto News Video — Run Bot
# ════════════════════════════════════════════════════════════════════════════
# Khởi động Telegram Bot. Tự activate venv và chạy bot.
#
# Cách dùng:
#   ./run.sh              — Chạy bot bình thường
#   ./run.sh --background — Chạy ngầm (nohup)
# ════════════════════════════════════════════════════════════════════════════

cd "$(dirname "$0")"
PROJECT_DIR="$(pwd)"

# Kiểm tra .venv
if [ ! -d ".venv" ]; then
    echo "❌ Chưa setup! Chạy ./setup.sh trước."
    exit 1
fi

# Kiểm tra .env
if [ ! -f ".env" ]; then
    echo "❌ Chưa có file .env! Copy từ .env.example và điền API keys."
    exit 1
fi

# Activate venv
source .venv/bin/activate

if [ "$1" = "--background" ] || [ "$1" = "-bg" ]; then
    # Chạy ngầm
    echo "🚀 Khởi động bot chạy ngầm (background)..."
    nohup python telegram_bot.py > bot.log 2>&1 &
    BOT_PID=$!
    echo $BOT_PID > .bot.pid
    echo ""
    echo "✅ Bot đang chạy ngầm!"
    echo "   PID: $BOT_PID"
    echo "   Log: tail -f bot.log"
    echo "   Dừng: ./stop.sh"
    echo ""
else
    # Chạy foreground
    echo ""
    echo "🚀 Khởi động Telegram Bot..."
    echo "   Nhấn Ctrl+C để dừng."
    echo ""
    python telegram_bot.py
fi
