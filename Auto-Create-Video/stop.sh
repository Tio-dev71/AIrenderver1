#!/bin/bash
# ════════════════════════════════════════════════════════════════════════════
# Auto News Video — Stop Bot
# ════════════════════════════════════════════════════════════════════════════
# Dừng bot đang chạy ngầm (background).
# ════════════════════════════════════════════════════════════════════════════

cd "$(dirname "$0")"

if [ -f ".bot.pid" ]; then
    BOT_PID=$(cat .bot.pid)
    if kill -0 "$BOT_PID" 2>/dev/null; then
        kill "$BOT_PID"
        rm -f .bot.pid
        echo "✅ Bot đã dừng (PID: $BOT_PID)"
    else
        rm -f .bot.pid
        echo "⚠️ Bot không chạy (PID $BOT_PID không tồn tại)."
    fi
else
    echo "⚠️ Không tìm thấy file .bot.pid. Bot có thể chưa chạy ngầm."
    echo "   Thử: ps aux | grep telegram_bot"
fi
