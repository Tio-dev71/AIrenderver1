#!/usr/bin/env python3
"""Telegram Bot for Auto News Video pipeline.

Scans 5 crypto news sites every hour, uses Claude API to generate script.json,
sends to Telegram for approval, then runs the HyperFrames pipeline to render video.

Usage:
    python telegram_bot.py
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
import time
import unicodedata
import uuid
from datetime import datetime
from pathlib import Path

import feedparser
import schedule
import telebot
import urllib.request
import urllib.parse
from anthropic import Anthropic
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ─── Config ──────────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
TELEGRAM_GROUP_ID = os.environ.get("TELEGRAM_GROUP_ID", "")
TTS_PROVIDER = os.environ.get("TTS_PROVIDER", "lucylab")
ELEVENLABS_VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")
VIETNAMESE_VOICEID = os.environ.get("VIETNAMESE_VOICEID", "")
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6")
NEWS_SOURCES = os.environ.get("NEWS_SOURCES", "")
SCAN_INTERVAL_MINUTES = int(os.environ.get("SCAN_INTERVAL_MINUTES", "60"))

# TTS config (read from same .env used by the Node.js pipeline)
TTS_PROVIDER = os.environ.get("TTS_PROVIDER", "elevenlabs")
ELEVENLABS_VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")

SCANNED_URLS_FILE = ROOT / "scanned_urls.json"
OUTPUT_DIR = ROOT / "output"

bot = telebot.TeleBot(BOT_TOKEN) if BOT_TOKEN else None
client = Anthropic(api_key=ANTHROPIC_KEY) if ANTHROPIC_KEY else None

# In-memory sessions: job_id -> dict
sessions: dict[str, dict] = {}

# ─── Scanned URL persistence ────────────────────────────────────────────────

def load_scanned_urls() -> list[str]:
    if SCANNED_URLS_FILE.exists():
        try:
            with open(SCANNED_URLS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_scanned_url(url: str):
    urls = load_scanned_urls()
    if url not in urls:
        urls.append(url)
        with open(SCANNED_URLS_FILE, "w") as f:
            json.dump(urls, f, ensure_ascii=False)


# ─── Article scraping ────────────────────────────────────────────────────────

import requests

def extract_latest_links(source_url: str, max_links: int = 5) -> list[str]:
    """Extract latest article links from RSS feed or HTML page."""
    try:
        # Try RSS first
        if "feed" in source_url.lower() or "rss" in source_url.lower() or source_url.endswith(".xml"):
            # feedparser can hang, use requests to fetch the XML first
            resp = requests.get(source_url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            feed = feedparser.parse(resp.content)
            if feed.entries:
                return [entry.link for entry in feed.entries[:max_links]]

        # Fallback to HTML scraping
        resp = requests.get(
            source_url,
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7 AppleWebKit/537.36)"},
            timeout=15
        )
        html = resp.text

        soup = BeautifulSoup(html, "html.parser")
        base_domain = urllib.parse.urlparse(source_url).netloc

        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            full_url = urllib.parse.urljoin(source_url, href)

            # Filter: same domain, long enough (skip homepage/category links)
            if base_domain in full_url and len(full_url) > len(source_url) + 15:
                if "/tag/" not in full_url and "/author/" not in full_url and "/category/" not in full_url:
                    if full_url not in links:
                        links.append(full_url)
            if len(links) >= max_links:
                break
        return links
    except Exception as e:
        print(f"❌ Lỗi khi quét {source_url}: {e}")
        return []


def scrape_article(url: str) -> dict:
    """Scrape article content from URL. Returns dict with title, content, ogImage, domain."""
    try:
        resp = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7 AppleWebKit/537.36)",
                "Accept": "text/html,application/xhtml+xml",
            },
            timeout=15
        )
        resp.encoding = 'utf-8'
        html_text = resp.text
        soup = BeautifulSoup(html_text, "html.parser")

        # Extract metadata
        og_title = ""
        og_image = None
        og_desc = ""

        for meta in soup.find_all("meta"):
            prop = meta.get("property", "") or meta.get("name", "")
            content = meta.get("content", "")
            if prop.lower() in ("og:title", "twitter:title"):
                og_title = content.strip()
            elif prop.lower() in ("og:image", "twitter:image"):
                og_image = content.strip()
            elif prop.lower() in ("description", "og:description"):
                og_desc = content.strip()

        # Title fallback
        title = og_title or (soup.title.string.strip() if soup.title and soup.title.string else "Không có tiêu đề")

        # Extract text content
        # Remove script/style/nav/footer/aside to get clean text
        for tag in soup(["script", "style", "noscript", "svg", "iframe", "nav", "footer", "form", "header", "aside"]):
            tag.decompose()

        content = soup.get_text(separator=" ", strip=True)
        # Clean up
        content = re.sub(r"\s+", " ", content).strip()
        content = content[:3000]  # Cap at 3000 chars to save tokens

        domain = urllib.parse.urlparse(url).netloc

        return {
            "title": title,
            "content": content,
            "ogImage": og_image,
            "domain": domain,
            "description": og_desc,
            "url": url,
        }
    except Exception as e:
        print(f"❌ Lỗi scrape {url}: {e}")
        return {
            "title": "Lỗi khi đọc bài",
            "content": "",
            "ogImage": None,
            "domain": urllib.parse.urlparse(url).netloc,
            "description": "",
            "url": url,
        }


# ─── Slug helper ─────────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    """Create ASCII slug from Vietnamese text."""
    # Remove Vietnamese diacritics
    nfkd = unicodedata.normalize("NFKD", text)
    ascii_text = "".join(c for c in nfkd if not unicodedata.combining(c))
    ascii_text = ascii_text.replace("đ", "d").replace("Đ", "D")
    # Keep alphanumeric, replace rest with dash
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_text.lower()).strip("-")
    return slug[:40] or f"article-{int(time.time())}"


# ─── Claude API: Generate script.json ────────────────────────────────────────

SCRIPT_PROMPT = """Bạn là chuyên gia viết kịch bản video tin tức crypto ngắn (short-form 9:16) cho TikTok/YouTube Shorts.

## Nhiệm vụ
Dựa trên bài báo bên dưới, hãy sinh ra một file JSON hoàn chỉnh theo đúng schema dưới đây.

## Schema bắt buộc (Zod validated)

```json
{
  "version": "1.0",
  "metadata": {
    "title": "Tiêu đề video (tiếng Việt)",
    "source": {
      "url": "<URL bài báo>",
      "domain": "<domain>",
      "image": "<URL ảnh og:image hoặc null>"
    },
    "channel": "Hedra Central"
  },
  "voice": {
    "provider": "lucylab",
    "voiceId": "${VOICE_ID}",
    "speed": 1.0
  },
  "scenes": [
    // 5-8 scenes, scene đầu type="hook", scene cuối type="outro", còn lại type="body"
  ]
}
```

## Các loại template cho templateData (chọn phù hợp nội dung):

1. **hook** (BẮT BUỘC cho scene đầu):
   ```json
   {"template": "hook", "headline": "max 40 ký tự", "subhead": "max 40 ký tự (optional)"}
   ```

2. **comparison** (khi có so sánh X vs Y):
   ```json
   {"template": "comparison", "left": {"label": "max 30", "value": "max 20", "color": "cyan"}, "right": {"label": "max 30", "value": "max 20", "color": "purple", "winner": true}}
   ```

3. **stat-hero** (khi có số liệu nổi bật):
   ```json
   {"template": "stat-hero", "value": "82.7%", "label": "max 40 ký tự", "context": "max 50 (optional)"}
   ```

4. **feature-list** (liệt kê tính năng):
   ```json
   {"template": "feature-list", "title": "max 40", "bullets": ["max 50 mỗi bullet"], "icon": "optional emoji"}
   ```

5. **callout** (cảnh báo / statement quan trọng):
   ```json
   {"template": "callout", "statement": "max 80 ký tự", "tag": "max 20 (optional)"}
   ```

6. **outro** (BẮT BUỘC cho scene cuối):
   ```json
   {"template": "outro", "ctaTop": "max 30", "channelName": "max 30", "source": "max 40"}
   ```

## Quy tắc TTS tiếng Việt (CỰC KỲ QUAN TRỌNG cho voiceText)

voiceText sẽ được AI đọc thành tiếng. SỐ VÀ KÝ HIỆU BỊ ĐỌC SAI nếu không viết phonetic:

| Dạng | SAI | ĐÚNG |
|---|---|---|
| Thập phân | GPT 5.5 | GPT năm chấm năm |
| Phần trăm | 82.7% | tám mươi hai phẩy bảy phần trăm |
| Giá USD | $5 | năm đô la |
| Giá VND | 21 triệu đồng | hai mươi mốt triệu đồng |
| Nhân | 2x | gấp đôi |
| Token | 1M | một triệu |
| Năm | 2026 | hai nghìn không trăm hai mươi sáu |

- Tên thương hiệu Anh giữ nguyên: Bitcoin, Ethereum, Apple OK
- KHÔNG emoji, KHÔNG markdown, KHÔNG URL trong voiceText
- Kết thúc mỗi câu bằng dấu chấm (.) hoặc dấu hỏi (?)
- BẮT BUỘC: Luôn mở đầu mỗi câu (đặc biệt là câu đầu tiên của scene 1) bằng các từ thuần Việt (ví dụ: 'Tin nóng', 'Thị trường', 'Mới đây', 'Hôm nay') để ElevenLabs không bị lai giọng ngoại quốc.
- templateData (text hiển thị trên màn hình) GIỮ NGUYÊN dạng số/ký hiệu gốc

## Nội dung tập trung CRYPTO / BLOCKCHAIN
- Ưu tiên biến động giá, phần trăm thay đổi, market cap
- Hook phải có số liệu hoặc claim gây tò mò, KHÔNG dùng câu chung chung
- Giọng điệu: chuyên nghiệp, dễ hiểu, như MC truyền hình tài chính
- Câu ngắn gọn, súc tích, max 30 từ/câu

## Cấu trúc scenes (5-8 scenes)
- Scene 1: type="hook", template="hook" — câu gây tò mò, có số liệu
- Scene 2-N: type="body" — đa dạng template (stat-hero, comparison, feature-list, callout)
- Scene cuối: type="outro", template="outro"

## Quan trọng
- Trả về ĐÚNG 1 JSON object, không markdown, không giải thích
- voiceText tổng ~150-200 từ → ~55-65 giây
- Mỗi scene voiceText 1-3 câu ngắn

## Bài báo gốc
Tiêu đề: {title}
Domain: {domain}
Ảnh: {og_image}
Nội dung: {content}
"""

REWRITE_PROMPT = """Bạn là chuyên gia viết kịch bản video tin tức crypto.

Dưới đây là script.json hiện tại. Hãy VIẾT LẠI các voiceText cho mượt mà, chuyên nghiệp, tự nhiên khi đọc to.
Giữ nguyên cấu trúc JSON, metadata, template types. Chỉ thay đổi voiceText.
Tuân thủ quy tắc TTS tiếng Việt: viết phonetic cho tất cả số/ký hiệu.
BẮT BUỘC: Luôn mở đầu mỗi câu bằng các từ thuần Việt để AI không bị đọc lai giọng ngoại quốc.

Trả về ĐÚNG 1 JSON object hoàn chỉnh, không markdown, không giải thích.

Script hiện tại:
{script_json}
"""

REWRITE_CUSTOM_PROMPT = """Bạn là chuyên gia viết kịch bản video tin tức crypto.

Dưới đây là script.json hiện tại. Người dùng vừa gửi yêu cầu CHỈNH SỬA kịch bản này như sau:
"{instruction}"

Hãy VIẾT LẠI script.json theo đúng yêu cầu trên.
Giữ nguyên cấu trúc JSON, metadata, template types. Chỉ thay đổi nội dung cần thiết.
Tuân thủ quy tắc TTS tiếng Việt: viết phonetic cho tất cả số/ký hiệu.
BẮT BUỘC: Luôn mở đầu mỗi câu bằng các từ thuần Việt để AI không bị đọc lai giọng ngoại quốc.

Trả về ĐÚNG 1 JSON object hoàn chỉnh, không markdown, không giải thích.

Script hiện tại:
{script_json}
"""


def generate_script_json(article: dict) -> tuple[dict | None, dict | None]:
    """Use Claude API to generate script.json matching Auto-Create-Video Zod schema."""
    if not client:
        print("⚠️ Chưa có ANTHROPIC_API_KEY, không thể sinh script.")
        return None, None

    prompt = SCRIPT_PROMPT.replace("{title}", article["title"]) \
                          .replace("{domain}", article["domain"]) \
                          .replace("{og_image}", article["ogImage"] or "null") \
                          .replace("{content}", article["content"][:2000])

    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()

        # Extract JSON block robustly
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            text = text[start_idx:end_idx+1]
        else:
            print("⚠️ Không tìm thấy JSON block trong response.")
            return None

        script = json.loads(text)

        # Validate basic structure
        if "version" not in script or "scenes" not in script:
            print("⚠️ AI sinh script thiếu version/scenes.")
            return None

        scenes = script.get("scenes", [])
        if len(scenes) < 5 or len(scenes) > 8:
            print(f"⚠️ AI sinh {len(scenes)} scenes (cần 5-8). Giữ nguyên.")

        if scenes[0].get("type") != "hook":
            print("⚠️ Scene đầu không phải hook, sửa lại.")
            scenes[0]["type"] = "hook"

        if scenes[-1].get("type") != "outro":
            print("⚠️ Scene cuối không phải outro, sửa lại.")
            scenes[-1]["type"] = "outro"

        # Đảm bảo các field thỏa mãn độ dài của Zod (chống crash Node.js)
        script = enforce_schema_limits(script)

        print(f"✅ Claude đã sinh script.json ({len(scenes)} scenes)")
        
        # Lấy thông tin usage tokens
        usage = {
            "input_tokens": response.usage.input_tokens if hasattr(response.usage, 'input_tokens') else 0,
            "output_tokens": response.usage.output_tokens if hasattr(response.usage, 'output_tokens') else 0
        }
        return script, usage

    except json.JSONDecodeError as e:
        print(f"❌ Lỗi parse JSON từ Claude: {e}")
        return None, None
    except Exception as e:
        print(f"❌ Lỗi Claude API: {e}")
        return None, None


def rewrite_script_json(script: dict, instruction: str = None) -> tuple[dict, dict | None]:
    """Use Claude API to rewrite voiceText in script.json."""
    if not client:
        return script, None

    if instruction:
        prompt = REWRITE_CUSTOM_PROMPT.replace("{instruction}", instruction).replace("{script_json}", json.dumps(script, ensure_ascii=False, indent=2))
    else:
        prompt = REWRITE_PROMPT.replace("{script_json}", json.dumps(script, ensure_ascii=False, indent=2))

    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            text = text[start_idx:end_idx+1]
        else:
            print("⚠️ Không tìm thấy JSON block khi viết lại.")
            return script

        new_script = json.loads(text)
        usage = {
            "input_tokens": response.usage.input_tokens if hasattr(response.usage, 'input_tokens') else 0,
            "output_tokens": response.usage.output_tokens if hasattr(response.usage, 'output_tokens') else 0
        }
        
        if "scenes" in new_script and len(new_script["scenes"]) >= 5:
            new_script = enforce_schema_limits(new_script)
            print("✅ Claude đã viết lại script.json")
            return new_script, usage
        else:
            print("⚠️ AI trả về script không hợp lệ. Giữ bản cũ.")
            return script, usage
    except Exception as e:
        print(f"❌ Lỗi rewrite: {e}")
        return script, None


# ─── Zod Schema Normalizer ───────────────────────────────────────────────────

def enforce_schema_limits(script: dict) -> dict:
    """Ensure generated script matches Zod limits to prevent Node.js crashes."""
    if not isinstance(script, dict):
        return script
        
    if "voice" not in script or not isinstance(script["voice"], dict):
        script["voice"] = {}
    script["voice"]["provider"] = TTS_PROVIDER
    script["voice"]["voiceId"] = ELEVENLABS_VOICE_ID if TTS_PROVIDER == "elevenlabs" else VIETNAMESE_VOICEID
    if "speed" not in script["voice"]:
        script["voice"]["speed"] = 1.0
        
    def _trunc(val, limit: int, fallback: str = "N/A") -> str:
        if not val or not isinstance(val, str):
            return fallback
        return val[:limit]

    for i, scene in enumerate(script.get("scenes", [])):
        if "id" not in scene:
            scene["id"] = f"scene-{i+1}"
        if "type" not in scene:
            scene["type"] = "hook" if i == 0 else "body"
        if "voiceText" not in scene:
            scene["voiceText"] = "Tin tức tiền điện tử hôm nay."
            
        td = scene.get("templateData", {})
        tpl = td.get("template")
        
        if tpl == "hook":
            td["headline"] = _trunc(td.get("headline"), 25, "Tin tức Crypto")
            if "subhead" in td:
                td["subhead"] = _trunc(td.get("subhead"), 30)
        elif tpl == "comparison":
            left = td.get("left", {})
            left["label"] = _trunc(left.get("label"), 30, "Lựa chọn 1")
            left["value"] = _trunc(left.get("value"), 15, "???")
            td["left"] = left
            right = td.get("right", {})
            right["label"] = _trunc(right.get("label"), 30, "Lựa chọn 2")
            right["value"] = _trunc(right.get("value"), 15, "???")
            td["right"] = right
        elif tpl == "stat-hero":
            td["label"] = _trunc(td.get("label"), 30, "Chỉ số quan trọng")
            td["value"] = _trunc(td.get("value"), 15, "0%")
            if "context" in td:
                td["context"] = _trunc(td.get("context"), 40)
        elif tpl == "feature-list":
            td["title"] = _trunc(td.get("title"), 30, "Điểm nổi bật")
            bullets = td.get("bullets", [])
            if not isinstance(bullets, list) or not bullets:
                bullets = ["Không có thông tin"]
            td["bullets"] = [_trunc(b, 40, "Mục") for b in bullets[:4]]
        elif tpl == "callout":
            td["statement"] = _trunc(td.get("statement"), 50, "Cần lưu ý quan trọng")
            if "tag" in td:
                td["tag"] = _trunc(td.get("tag"), 20)
        elif tpl == "outro":
            # Sometimes Claude returns "cta" instead of "ctaTop"
            cta = td.get("ctaTop") or td.get("cta") or "Theo dõi ngay"
            td["ctaTop"] = _trunc(cta, 30, "Theo dõi ngay")
            td["channelName"] = _trunc(td.get("channelName"), 30, "Hedra Central")
            td["source"] = _trunc(td.get("source"), 40, "Nguồn tham khảo")
            if "cta" in td:
                del td["cta"]
                
    return script

# ─── Telegram message formatting ─────────────────────────────────────────────

def format_script_preview(script: dict) -> str:
    """Format script.json into readable Telegram message."""
    title = script.get("metadata", {}).get("title", "Không có tiêu đề")
    source_url = script.get("metadata", {}).get("source", {}).get("url", "")
    scenes = script.get("scenes", [])

    lines = [f"📰 *{_escape_md(title)}*"]
    if source_url:
        lines.append(f"🔗 Nguồn: {_escape_md(source_url)}")
    lines.append("")
    lines.append(f"🎬 *Kịch bản ({len(scenes)} scenes):*")
    lines.append("")

    for i, scene in enumerate(scenes):
        scene_type = scene.get("type", "body")
        template = scene.get("templateData", {}).get("template", "unknown")
        voice = scene.get("voiceText", "")

        icon = {"hook": "🎯", "body": "📝", "outro": "👋"}.get(scene_type, "📝")
        lines.append(f"{icon} *Scene {i+1}* \\[{_escape_md(template)}\\]")
        lines.append(f"_{_escape_md(voice[:120])}{'...' if len(voice) > 120 else ''}_")
        lines.append("")

    return "\n".join(lines)


def _escape_md(text: str) -> str:
    """Escape special chars for Telegram MarkdownV2."""
    special = r"_*[]()~`>#+-=|{}.!"
    return "".join(f"\\{c}" if c in special else c for c in str(text))


# ─── Telegram handlers ───────────────────────────────────────────────────────

@bot.message_handler(commands=["start", "help", "id"])
def send_welcome(message):
    chat_id = message.chat.id
    text = (
        f"🤖 *Auto News Video Bot*\n\n"
        f"🆔 ID của chat này: `{chat_id}`\n\n"
        f"*Lệnh có sẵn:*\n"
        f"/scan — Quét thủ công 5 trang báo ngay\n"
        f"/status — Xem trạng thái bot\n\n"
        f"Hoặc gửi 1 đường link bài báo, bot sẽ tạo kịch bản video cho bạn duyệt\\!"
    )
    bot.reply_to(message, text, parse_mode="MarkdownV2")


@bot.message_handler(commands=["scan"])
def manual_scan(message):
    bot.reply_to(message, "🔄 Đang quét 5 trang báo...")
    threading.Thread(target=scan_news_job, args=(message.chat.id,), daemon=True).start()


@bot.message_handler(commands=["status"])
def show_status(message):
    scanned = load_scanned_urls()
    sources = [s.strip() for s in NEWS_SOURCES.split(",") if s.strip()]
    text = (
        f"📊 *Trạng thái Bot*\n\n"
        f"🔗 Nguồn tin: {len(sources)} trang\n"
        f"📰 Đã quét: {len(scanned)} bài\n"
        f"⏰ Quét tự động: mỗi {SCAN_INTERVAL_MINUTES} phút\n"
        f"🎤 TTS: {TTS_PROVIDER}\n"
        f"🧠 AI Model: {CLAUDE_MODEL}\n"
        f"📂 Đang chờ duyệt: {len(sessions)} job"
    )
    bot.reply_to(message, text, parse_mode="Markdown")


@bot.message_handler(func=lambda message: message.text and re.search(r"(https?://[^\s]+)", message.text))
def handle_url(message):
    """Handle direct URL submission from user."""
    chat_id = message.chat.id
    match = re.search(r"(https?://[^\s]+)", message.text)
    if not match:
        return
    url = match.group(1)

    msg = bot.send_message(chat_id, "⏳ Đang bóc tách bài viết và tạo kịch bản AI...", reply_to_message_id=message.message_id)

    def process():
        try:
            article = scrape_article(url)
            if not article["content"]:
                bot.edit_message_text("❌ Không đọc được nội dung bài viết. Thử link khác nhé.", chat_id, msg.message_id)
                return

            script, usage = generate_script_json(article)
            if not script:
                bot.edit_message_text("❌ AI không thể tạo kịch bản. Thử lại sau.", chat_id, msg.message_id)
                return

            job_id = str(uuid.uuid4())[:8]
            sessions[job_id] = {
                "chat_id": chat_id,
                "message_id": msg.message_id,
                "article": article,
                "script": script,
                "usage": usage,
                "url": url,
            }
            send_script_approval(job_id)
            save_scanned_url(url)
        except Exception as e:
            bot.edit_message_text(f"❌ Lỗi: {e}", chat_id, msg.message_id)

    threading.Thread(target=process, daemon=True).start()


@bot.message_handler(func=lambda message: message.reply_to_message is not None)
def handle_reply(message):
    reply_msg_id = message.reply_to_message.message_id
    chat_id = message.chat.id
    
    target_job_id = None
    for jid, session in sessions.items():
        if session.get("message_id") == reply_msg_id:
            target_job_id = jid
            break
            
    if not target_job_id:
        return
        
    instruction = message.text
    bot.reply_to(message, "⏳ Đã nhận yêu cầu sửa kịch bản. Đang xử lý...")
    
    def do_custom_rewrite():
        session = sessions[target_job_id]
        new_script, new_usage = rewrite_script_json(session["script"], instruction)
        session["script"] = new_script
        
        if new_usage:
            old_usage = session.get("usage", {"input_tokens": 0, "output_tokens": 0})
            session["usage"] = {
                "input_tokens": old_usage.get("input_tokens", 0) + new_usage.get("input_tokens", 0),
                "output_tokens": old_usage.get("output_tokens", 0) + new_usage.get("output_tokens", 0),
            }
        
        msg = bot.send_message(chat_id, "⏳ Đang cập nhật kịch bản mới...")
        session["message_id"] = msg.message_id
        send_script_approval(target_job_id, header=f"🔄 *Kịch Bản Đã Sửa:* _{_escape_md(instruction)}_")

    threading.Thread(target=do_custom_rewrite, daemon=True).start()


# ─── Script approval UI ──────────────────────────────────────────────────────

def send_script_approval(job_id: str, header: str = "📝 *Kịch Bản Đề Xuất:*"):
    session = sessions.get(job_id)
    if not session:
        return

    chat_id = session["chat_id"]
    msg_id = session["message_id"]
    script = session["script"]

    text = f"{header}\n\n{format_script_preview(script)}"

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("✅ Duyệt & Render Video", callback_data=f"render_{job_id}"),
        InlineKeyboardButton("🔄 Viết lại (AI)", callback_data=f"rewrite_{job_id}"),
    )
    markup.add(InlineKeyboardButton("❌ Feed backup update", callback_data=f"cancel_{job_id}"))

    try:
        bot.edit_message_text(text, chat_id, msg_id, reply_markup=markup, parse_mode="MarkdownV2")
    except Exception:
        # Fallback without MarkdownV2 if escaping fails
        plain_text = f"📝 Kịch Bản Đề Xuất:\n\n"
        for i, scene in enumerate(script.get("scenes", [])):
            plain_text += f"Scene {i+1} [{scene.get('templateData', {}).get('template', '?')}]:\n"
            plain_text += f"  {scene.get('voiceText', '')[:120]}\n\n"

        bot.edit_message_text(plain_text, chat_id, msg_id, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    data_parts = call.data.split("_", 1)
    action = data_parts[0]
    job_id = data_parts[1] if len(data_parts) > 1 else None

    if not job_id or job_id not in sessions:
        bot.answer_callback_query(call.id, "⚠️ Session hết hạn hoặc đã xử lý xong.")
        return

    if action == "cancel":
        bot.edit_message_text("❌ Đã feed backup update.", chat_id, call.message.message_id)
        del sessions[job_id]

    elif action == "rewrite":
        bot.answer_callback_query(call.id, "🔄 AI đang viết lại...")
        bot.edit_message_text("⏳ Claude AI đang viết lại kịch bản cho mượt hơn...", chat_id, call.message.message_id)

        def do_rewrite():
            session = sessions[job_id]
            new_script, new_usage = rewrite_script_json(session["script"])
            session["script"] = new_script
            
            if new_usage:
                old_usage = session.get("usage", {"input_tokens": 0, "output_tokens": 0})
                session["usage"] = {
                    "input_tokens": old_usage.get("input_tokens", 0) + new_usage.get("input_tokens", 0),
                    "output_tokens": old_usage.get("output_tokens", 0) + new_usage.get("output_tokens", 0),
                }
            # Need a new message since we can't edit back with buttons easily
            msg = bot.send_message(chat_id, "⏳ Đang cập nhật...")
            session["message_id"] = msg.message_id
            send_script_approval(job_id, header="🔄 *Kịch Bản Đã Viết Lại:*")

        threading.Thread(target=do_rewrite, daemon=True).start()

    elif action == "render":
        bot.answer_callback_query(call.id, "⚙️ Bắt đầu render...")
        bot.edit_message_text(
            "⏳ Đang render video...\n\n"
            "⚙️ Step 1: Validate script\n"
            "⚙️ Step 2-4: TTS voice generation\n"
            "⚙️ Step 5-6: HTML composition\n"
            "⚙️ Step 7: HyperFrames render\n\n"
            "⏱️ Ước tính: 3-5 phút. Anh chờ xíu nhé!",
            chat_id, call.message.message_id
        )
        threading.Thread(target=render_video_task, args=(job_id, call.message.message_id), daemon=True).start()


# ─── Video render task ────────────────────────────────────────────────────────

def render_video_task(job_id: str, message_id: int):
    session = sessions.get(job_id)
    if not session:
        return

    chat_id = session["chat_id"]
    script = session["script"]
    article = session["article"]

    try:
        # 1. Create output directory
        slug = slugify(article.get("title", "video"))
        timestamp = datetime.now().strftime("%Y%m%d-%H%M")
        output_name = f"{slug}-{timestamp}"
        output_path = OUTPUT_DIR / output_name
        output_path.mkdir(parents=True, exist_ok=True)

        # 2. Write script.json
        script_file = output_path / "script.json"
        with open(script_file, "w", encoding="utf-8") as f:
            json.dump(script, f, ensure_ascii=False, indent=2)
        print(f"📝 script.json written to {script_file}")

        # 3. Run the Node.js pipeline
        bot.edit_message_text(
            "⏳ Pipeline đang chạy...\n\n"
            "▶️ npm run pipeline -- " + str(script_file.relative_to(ROOT)),
            chat_id, message_id
        )

        result = subprocess.run(
            ["npm", "run", "pipeline", "--", str(script_file)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout
        )

        if result.returncode != 0:
            error_msg = result.stderr[-500:] if result.stderr else result.stdout[-500:]
            bot.edit_message_text(
                f"❌ Pipeline lỗi (exit code {result.returncode}):\n\n"
                f"```\n{error_msg}\n```\n\n"
                f"📂 Output dir: {output_path}",
                chat_id, message_id, parse_mode="Markdown"
            )
            return

        # 4. Find and send video
        video_file = output_path / "video.mp4"
        if video_file.exists():
            file_size_mb = video_file.stat().st_size / (1024 * 1024)
            
            # Tính chi phí
            usage = session.get("usage", {"input_tokens": 0, "output_tokens": 0})
            in_tokens = usage.get("input_tokens", 0)
            out_tokens = usage.get("output_tokens", 0)
            
            # Claude 3.5 Sonnet: $3/1M input, $15/1M output
            claude_cost = (in_tokens / 1_000_000) * 3.0 + (out_tokens / 1_000_000) * 15.0
            
            # TTS Cost (ElevenLabs: ~$0.30 per 1000 chars)
            total_chars = sum(len(scene.get("voiceText", "")) for scene in script.get("scenes", []))
            tts_cost = 0
            if TTS_PROVIDER == "elevenlabs":
                tts_cost = (total_chars / 1000) * 0.30
                
            total_cost = claude_cost + tts_cost
            
            bot.edit_message_text(
                f"✅ Video render thành công!\n"
                f"📦 Kích thước: {file_size_mb:.1f} MB\n"
                f"💰 Phí dự kiến: ${total_cost:.4f}\n"
                f"📤 Đang upload lên Telegram...",
                chat_id, message_id
            )

            # Telegram limit: 50MB for bots
            if file_size_mb > 50:
                bot.send_message(
                    chat_id,
                    f"⚠️ Video quá lớn ({file_size_mb:.1f} MB) để gửi qua Telegram.\n"
                    f"📂 File tại: `{video_file}`",
                    parse_mode="Markdown", reply_to_message_id=message_id
                )
            else:
                with open(video_file, "rb") as f:
                    bot.send_video(
                        chat_id, f,
                        width=1080, height=1920,
                        caption=(
                            f"🎬 {article.get('title', 'Video')}\n\n"
                            f"🔗 Tham gia ngay: https://okx.com/join/HEDRATIKTOK\n"
                            f"📰 Nguồn: {article.get('url', '')}\n\n"
                            f"#TheBeautifulGame #OKX\n"
                            f"💰 Phí: ${total_cost:.4f} | 📦 {file_size_mb:.1f} MB"
                        ),
                        reply_to_message_id=message_id,
                        timeout=300,
                    )
        else:
            bot.edit_message_text(
                f"❌ Không tìm thấy video.mp4 sau khi render.\n"
                f"📂 Kiểm tra: {output_path}",
                chat_id, message_id
            )

    except subprocess.TimeoutExpired:
        bot.edit_message_text("❌ Pipeline timeout (>10 phút). Thử lại sau.", chat_id, message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ Lỗi render: {e}", chat_id, message_id)
    finally:
        if job_id in sessions:
            del sessions[job_id]


# ─── News scanner (cron job) ─────────────────────────────────────────────────

def scan_news_job(manual_chat_id=None):
    """Scan all news sources for new articles."""
    target_chat = manual_chat_id or TELEGRAM_GROUP_ID
    if not target_chat:
        print("⚠️ Chưa cấu hình TELEGRAM_GROUP_ID, bỏ qua quét.")
        return

    sources = [s.strip() for s in NEWS_SOURCES.split(",") if s.strip()]
    if not sources:
        print("⚠️ Chưa cấu hình NEWS_SOURCES.")
        return

    print(f"🔄 Đang quét {len(sources)} nguồn tin tức...")
    scanned = load_scanned_urls()
    new_count = 0

    for source in sources:
        links = extract_latest_links(source, max_links=3)
        for url in links:
            if url in scanned:
                continue

            print(f"📰 Tin mới: {url}")
            try:
                article = scrape_article(url)
                if not article["content"]:
                    print(f"  ⚠️ Không đọc được nội dung, bỏ qua.")
                    save_scanned_url(url)
                    continue

                script = generate_script_json(article)
                if not script:
                    print(f"  ⚠️ AI không thể tạo kịch bản, bỏ qua.")
                    save_scanned_url(url)
                    continue

                job_id = str(uuid.uuid4())[:8]

                # Send to Telegram
                msg = bot.send_message(target_chat, f"🚨 *TIN MỚI PHÁT HIỆN*\n\n⏳ Đang tạo kịch bản...", parse_mode="Markdown")

                sessions[job_id] = {
                    "chat_id": target_chat,
                    "message_id": msg.message_id,
                    "article": article,
                    "script": script,
                    "url": url,
                }

                send_script_approval(job_id, header="🚨 *TIN MỚI PHÁT HIỆN:*")
                save_scanned_url(url)
                new_count += 1

                # Small delay between processing articles
                time.sleep(2)

            except Exception as e:
                print(f"❌ Lỗi xử lý {url}: {e}")
                save_scanned_url(url)  # Mark as scanned to avoid retry loops

    if manual_chat_id and new_count == 0:
        bot.send_message(
            manual_chat_id,
            "✅ Đã quét xong 5 trang báo. Hiện tại *chưa có bài viết nào mới* (tất cả đều đã quét rồi).",
            parse_mode="Markdown"
        )
    elif new_count > 0:
        print(f"✅ Quét xong: {new_count} bài mới.")


def run_scheduler():
    """Run the background scheduler thread."""
    schedule.every(SCAN_INTERVAL_MINUTES).minutes.do(scan_news_job)
    print(f"⏰ Scheduler: quét mỗi {SCAN_INTERVAL_MINUTES} phút")
    while True:
        schedule.run_pending()
        time.sleep(1)


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not BOT_TOKEN:
        print("❌ Vui lòng cấu hình TELEGRAM_BOT_TOKEN trong file .env!")
        sys.exit(1)

    if not ANTHROPIC_KEY:
        print("⚠️ Chưa có ANTHROPIC_API_KEY — bot sẽ không thể tạo kịch bản AI.")

    print("=" * 60)
    print("🚀 Auto News Video — Telegram Bot")
    print("=" * 60)
    print(f"  🤖 Bot Token: ...{BOT_TOKEN[-8:]}")
    print(f"  📱 Group ID: {TELEGRAM_GROUP_ID}")
    print(f"  🧠 AI Model: {CLAUDE_MODEL}")
    print(f"  🎤 TTS: {TTS_PROVIDER}")
    print(f"  ⏰ Scan interval: {SCAN_INTERVAL_MINUTES} phút")
    print(f"  📰 Sources: {len([s for s in NEWS_SOURCES.split(',') if s.strip()])} trang")
    print("=" * 60)

    # Start scheduler thread
    threading.Thread(target=run_scheduler, daemon=True).start()

    # Notify on startup
    if TELEGRAM_GROUP_ID:
        try:
            bot.send_message(
                TELEGRAM_GROUP_ID,
                "🤖 *Auto News Video Bot* đã khởi động\\!\n\n"
                f"⏰ Tự động quét mỗi {SCAN_INTERVAL_MINUTES} phút\n"
                f"🎤 TTS: {_escape_md(TTS_PROVIDER)}\n"
                f"🧠 AI: {_escape_md(CLAUDE_MODEL)}\n\n"
                "Gõ /scan để quét ngay, hoặc gửi link bài báo\\.",
                parse_mode="MarkdownV2"
            )
        except Exception as e:
            print(f"⚠️ Không thể gửi tin vào Group {TELEGRAM_GROUP_ID}: {e}")

    print("\n🟢 Bot đang chạy... Nhấn Ctrl+C để dừng.\n")
    bot.infinity_polling()
