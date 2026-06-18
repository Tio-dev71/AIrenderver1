"""
web_fetcher.py — Web fetching module với fallback 3 lớp + error classification.
Độc lập, không phụ thuộc DeepSeek TUI.

Usage:
    from web_fetcher import fetch_content, classify_error
    result = fetch_content("https://...")
    if result["error"]:
        error_type = classify_error(result["error"])
"""

import re
import time
import trafilatura
import requests


# ── Config ───────────────────────────────────────────────────────────────────

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
TIMEOUT = 20
MAX_BYTES = 500_000


# ── Error classification ─────────────────────────────────────────────────────

ERROR_DNS = "dns_failure"
ERROR_BLOCKED = "blocked"       # Cloudflare, 403
ERROR_AUTH = "auth_required"    # 401, login page
ERROR_TIMEOUT = "timeout"       # slow / no response
ERROR_SSL = "ssl_error"
ERROR_BINARY = "binary_file"    # PDF, ZIP, image
ERROR_TOO_LARGE = "too_large"   # >500KB
ERROR_EMPTY = "empty_content"   # < 100 bytes
ERROR_UNKNOWN = "unknown"


def classify_error(error_msg: str, status_code: int = 0, content_length: int = 0) -> str:
    """Phân loại lỗi dựa vào error message và context."""
    err_lower = error_msg.lower()

    if status_code == 401:
        return ERROR_AUTH
    if status_code == 403:
        return ERROR_BLOCKED
    if status_code == 429:
        return ERROR_BLOCKED
    if status_code == 404:
        return ERROR_EMPTY

    if any(x in err_lower for x in [
        "nameresolutionerror", "gaierror", "nodename nor servname",
        "failed to resolve", "temporary failure in name resolution",
        "dns", "cannot resolve"
    ]):
        return ERROR_DNS

    if any(x in err_lower for x in [
        "sslerror", "certificate_verify_failed", "ssl",
        "certificate verify failed"
    ]):
        return ERROR_SSL

    if any(x in err_lower for x in [
        "timeout", "timed out", "connection refused",
        "connection reset", "connectionerror"
    ]):
        return ERROR_TIMEOUT

    if any(x in err_lower for x in [
        "cf-browser-verify", "cloudflare", "challenge",
        "just a moment", "checking your browser",
        "access denied", "blocked"
    ]):
        return ERROR_BLOCKED

    return ERROR_UNKNOWN


def error_hint(error_type: str) -> str:
    """Trả về hướng dẫn cho user dựa trên loại lỗi."""
    hints = {
        ERROR_DNS: "Lỗi DNS — kiểm tra internet hoặc Tailscale. Chạy: nslookup google.com",
        ERROR_BLOCKED: "Site bị chặn (Cloudflare/403) — thử --force-browser",
        ERROR_AUTH: "Site cần đăng nhập — không thể đọc tự động",
        ERROR_TIMEOUT: "Site quá chậm hoặc chặn kết nối — thử --force-browser",
        ERROR_SSL: "Lỗi SSL — site có chứng chỉ không hợp lệ",
        ERROR_BINARY: "File nhị phân — không thể đọc nội dung",
        ERROR_TOO_LARGE: "Trang quá lớn — đã cắt bớt",
        ERROR_EMPTY: "Trang rỗng — có thể URL sai hoặc site chết",
        ERROR_UNKNOWN: "Lỗi không xác định — kiểm tra kết nối",
    }
    return hints.get(error_type, "Lỗi không xác định")


# ── Fetchers ─────────────────────────────────────────────────────────────────

def fetch_trafilatura(url: str) -> tuple[str | None, str, int, float]:
    """trafilatura: nhanh, không JS. Returns (html, method, bytes, duration_ms)."""
    t0 = time.time()
    try:
        html = trafilatura.fetch_url(url)
        dur = (time.time() - t0) * 1000
        if html:
            return html, "trafilatura", len(html.encode()), dur
        return None, "trafilatura", 0, dur
    except Exception:
        return None, "trafilatura", 0, (time.time() - t0) * 1000


def fetch_requests(url: str) -> tuple[str | None, str, int, float, int]:
    """requests: giả trình duyệt. Returns (html, method, bytes, duration_ms, status_code)."""
    t0 = time.time()
    try:
        r = requests.get(url, headers={
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }, timeout=TIMEOUT, allow_redirects=True)
        dur = (time.time() - t0) * 1000
        if r.status_code == 200:
            html = r.text
            # Check content type
            ct = r.headers.get("Content-Type", "").lower()
            if "application/pdf" in ct:
                return None, "requests", 0, dur, r.status_code
            return html, "requests", len(r.text.encode()), dur, r.status_code
        return None, "requests", 0, dur, r.status_code
    except requests.Timeout:
        return None, "requests", 0, (time.time() - t0) * 1000, 0
    except requests.exceptions.SSLError:
        return None, "requests", 0, (time.time() - t0) * 1000, -3  # SSL
    except requests.ConnectionError as e:
        err = str(e)
        if "NameResolutionError" in err or "gaierror" in err or "nodename" in err:
            return None, "requests", 0, (time.time() - t0) * 1000, -1  # DNS
        if "Connection refused" in err or "Connection reset" in err:
            return None, "requests", 0, (time.time() - t0) * 1000, -2  # Refused
        return None, "requests", 0, (time.time() - t0) * 1000, 0
    except requests.RequestException:
        return None, "requests", 0, (time.time() - t0) * 1000, 0


def fetch_playwright(url: str) -> tuple[str | None, str, int, float]:
    """Playwright: JS render, Cloudflare bypass. Returns (html, method, bytes, duration_ms)."""
    t0 = time.time()
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent=UA)
            page.goto(url, wait_until="networkidle", timeout=TIMEOUT * 1000)
            html = page.content()
            dur = (time.time() - t0) * 1000
            browser.close()
            return html, "playwright", len(html.encode()), dur
    except Exception:
        return None, "playwright", 0, (time.time() - t0) * 1000


def detect_blocked(html: str) -> bool:
    """Detect Cloudflare / bot protection (chỉ match HTML/meta, không match text content)."""
    # Chỉ scan trong <head> và <script> để tránh false positive từ nội dung bài viết
    head = html.lower()
    # Lấy phần head + script tags để scan
    body_start = head.find("<body")
    scan_zone = head[:body_start] if body_start > 0 else head
    
    signals = [
        "cf-browser-verify", "challenge-form", "js-challenge",
        "Please enable JavaScript", "enable_cookies",
        "Just a moment", "Checking your browser",
        "Access Denied", "blocked", "captcha",
        "Attention Required", "DDoS protection",
    ]
    return any(s in scan_zone for s in signals)


def detect_auth_page(html: str) -> bool:
    """Detect login/sign-in page."""
    signals = ["sign in", "log in", "đăng nhập", "login",
               "authentication required", "this page requires"]
    return any(s in html.lower() for s in signals)


def extract_metadata(html: str, url: str) -> dict:
    """Extract title, domain, og:image từ HTML."""
    from urllib.parse import urlparse

    meta = {
        "title": "",
        "domain": urlparse(url).netloc,
        "og_image": "",
        "description": "",
    }

    # og:title (ưu tiên)
    m = re.search(
        r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']*)["\']',
        html, re.I
    )
    if m:
        meta["title"] = m.group(1).strip()
    else:
        m = re.search(r'<title[^>]*>(.*?)</title>', html, re.I | re.S)
        if m:
            meta["title"] = m.group(1).strip()

    # og:image
    m = re.search(
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']*)["\']',
        html, re.I
    )
    if m:
        meta["og_image"] = m.group(1).strip()

    # description
    for pattern in [
        r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']*)["\']',
        r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']*)["\']',
    ]:
        m = re.search(pattern, html, re.I)
        if m:
            meta["description"] = m.group(1).strip()
            break

    return meta


def html_to_text_simple(html: str) -> str:
    """HTML → text đơn giản (không có trafilatura)."""
    from html.parser import HTMLParser
    class TextExtract(HTMLParser):
        def __init__(self):
            super().__init__()
            self.parts = []
            self.skip = False
        def handle_starttag(self, tag, attrs):
            if tag in ("script", "style"):
                self.skip = True
        def handle_endtag(self, tag):
            if tag in ("script", "style"):
                self.skip = False
        def handle_data(self, data):
            if not self.skip:
                self.parts.append(data)
    ex = TextExtract()
    ex.feed(html)
    text = " ".join(p.strip() for p in ex.parts if p.strip()).strip()
    return re.sub(r'\s+', ' ', text)


def extract_article(html: str) -> str:
    """Extract article content (dùng trafilatura, fallback HTML parser)."""
    result = trafilatura.extract(html, output_format='markdown',
                                 include_links=True, favor_precision=True)
    if result:
        return result
    # Fallback: simple extraction
    text = html_to_text_simple(html)
    if len(text) > 200:
        return text[:MAX_BYTES]
    return text


# ── Main entry ───────────────────────────────────────────────────────────────

def fetch_content(url: str, force_browser: bool = False) -> dict:
    """
    Fetch URL content với fallback 3 lớp.
    
    Returns:
        {
            "url": str,
            "success": bool,
            "content": str (markdown),
            "method": str,
            "bytes": int,
            "duration_ms": int,
            "error": str or "",
            "error_type": str or "",
            "error_hint": str or "",
            "truncated": bool,
        }
    """
    result = {
        "url": url,
        "success": False,
        "content": "",
        "method": "none",
        "bytes": 0,
        "duration_ms": 0,
        "error": "",
        "error_type": "",
        "error_hint": "",
        "truncated": False,
    }

    html = None
    method = "none"
    byte_count = 0
    duration_ms = 0

    if force_browser:
        html, method, byte_count, duration_ms = fetch_playwright(url)
        method = "playwright (forced)"
    else:
        # Level 1: trafilatura
        html, method, byte_count, duration_ms = fetch_trafilatura(url)
        if html:
            method = "trafilatura"
        else:
            # Level 2: requests
            html, method, byte_count, duration_ms, status = fetch_requests(url)
            if html:
                method = "requests"
            elif status == 401:
                result["error"] = "HTTP 401: site requires authentication"
                result["error_type"] = ERROR_AUTH
                result["error_hint"] = error_hint(ERROR_AUTH)
                return result
            elif status == 404:
                result["error"] = f"HTTP 404: page not found"
                result["error_type"] = ERROR_EMPTY
                result["error_hint"] = error_hint(ERROR_EMPTY)
                return result
            elif status == 403 or (isinstance(status, int) and status > 0 and status != 404):
                # Level 3: Playwright for blocked sites
                html, method, byte_count, duration_ms = fetch_playwright(url)
                if html:
                    method = "playwright (bypass 403)"
                else:
                    result["error"] = f"HTTP {status}: site blocked"
                    result["error_type"] = ERROR_BLOCKED
                    result["error_hint"] = error_hint(ERROR_BLOCKED)
                    return result
            elif status == -1:
                result["error"] = "DNS resolution failed"
                result["error_type"] = ERROR_DNS
                result["error_hint"] = error_hint(ERROR_DNS)
                return result
            else:
                # Level 3: Playwright for everything else
                html, method, byte_count, duration_ms = fetch_playwright(url)
                if html:
                    method = "playwright (fallback)"

    if not html:
        result["error"] = f"Cannot fetch: {url}"
        result["error_type"] = ERROR_UNKNOWN
        result["error_hint"] = error_hint(ERROR_UNKNOWN)
        return result

    # Check content
    if len(html.strip()) < 100:
        result["error"] = "Empty or minimal content"
        result["error_type"] = ERROR_EMPTY
        result["error_hint"] = error_hint(ERROR_EMPTY)
        return result

    # Detect blocked
    if detect_blocked(html) and "playwright" not in method:
        html2, _, _, _ = fetch_playwright(url)
        if html2 and not detect_blocked(html2):
            html = html2
            method = "playwright (bypass)"
            byte_count = len(html.encode())

    # Truncate if too large
    truncated = False
    if byte_count > MAX_BYTES:
        html = extract_article(html)
        byte_count = len(html.encode())
        truncated = True

    # Convert to text
    content = extract_article(html)
    if not content:
        content = html_to_text_simple(html)

    if not content.strip():
        result["error"] = "Could not extract content from page"
        result["error_type"] = ERROR_EMPTY
        return result

    result["success"] = True
    result["content"] = content.strip()
    result["method"] = method
    result["bytes"] = byte_count
    result["duration_ms"] = int(duration_ms)
    result["truncated"] = truncated
    result["raw_html"] = html  # raw HTML cho metadata extraction
    return result


# ── File-based caching ───────────────────────────────────────────────────────

from pathlib import Path


def _url_to_filename(url: str) -> str:
    """Convert URL to a safe filename."""
    safe = re.sub(r'[^a-zA-Z0-9]+', '_', url)[:80].strip('_')
    return safe + '.txt'


def fetch_and_save(url: str, output_dir: str | Path | None = None,
                   force_browser: bool = False, cache_ttl: int = 3600) -> dict:
    """
    Fetch URL và lưu content vào file.
    
    Args:
        url: URL to fetch
        output_dir: thư mục lưu file (mặc định: ~/prompt-test/input/)
        force_browser: dùng Playwright
        cache_ttl: thời gian cache (giây), mặc định 1h
    
    Returns:
        dict với các field: url, success, filepath, content, method, bytes, ...
    """
    output_dir = Path(output_dir or Path.home() / "prompt-test" / "input")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filename = _url_to_filename(url)
    filepath = output_dir / filename
    
    # Nếu file còn mới, đọc từ cache
    if filepath.exists():
        age = time.time() - filepath.stat().st_mtime
        if age < cache_ttl:
            text = filepath.read_text(encoding='utf-8', errors='replace').strip()
            if text and len(text) > 100:
                return {
                    "url": url, "success": True, "method": "cache",
                    "bytes": len(text.encode()), "filepath": str(filepath),
                    "content": text, "truncated": False,
                    "error": "", "error_type": "", "error_hint": "",
                }
    
    # Fetch mới
    result = fetch_content(url, force_browser)
    if result["success"]:
        # Ghi atomic: ghi vào file tạm → rename
        tmp = filepath.with_suffix('.tmp')
        try:
            tmp.write_text(result["content"], encoding='utf-8')
            tmp.rename(filepath)
        except Exception:
            pass
        result["filepath"] = str(filepath)
    elif filepath.exists() and filepath.stat().st_size > 100:
        # Fetch lỗi nhưng có file cũ → dùng tạm
        text = filepath.read_text(encoding='utf-8', errors='replace').strip()
        if text and len(text) > 100:
            result["success"] = True
            result["method"] = "cache (stale)"
            result["content"] = text
            result["bytes"] = len(text.encode())
            result["filepath"] = str(filepath)
            result["warning"] = f"Dùng cache cũ (fetch mới thất bại: {result['error']})"
    
    return result


def read_fetched(filepath: str | Path) -> str | None:
    """Đọc content từ file đã fetch. Trả về None nếu file không tồn tại."""
    path = Path(filepath)
    if not path.exists():
        return None
    text = path.read_text(encoding='utf-8', errors='replace').strip()
    return text if text and len(text) > 100 else None


def ensure_fetched(url: str, output_dir: str | Path | None = None,
                   force_browser: bool = False, cache_ttl: int = 3600) -> str | None:
    """
    Đảm bảo URL đã được fetch về local file.
    - Nếu file tồn tại và còn hạn → đọc từ file
    - Nếu không → fetch mới
    Trả về content string hoặc None nếu cả fetch và cache đều thất bại.
    """
    result = fetch_and_save(url, output_dir, force_browser, cache_ttl)
    if result["success"]:
        return result["content"]
    return None
