<a id="top"></a>

<div align="center">

<img src="./assets/logo.svg" alt="Auto News Video" width="120" />

# 🎬 Auto News Video

### Biến bài báo công nghệ tiếng Việt thành video TikTok 9:16 chỉ trong 60 giây

**Một câu lệnh. Không cần edit. Chất lượng motion graphic studio.**

[![Stars](https://img.shields.io/github/stars/hoquanghai/Auto-Create-Video?style=for-the-badge&logo=github&color=yellow)](https://github.com/hoquanghai/Auto-Create-Video/stargazers)
[![Forks](https://img.shields.io/github/forks/hoquanghai/Auto-Create-Video?style=for-the-badge&logo=github&color=blue)](https://github.com/hoquanghai/Auto-Create-Video/network/members)
[![License](https://img.shields.io/github/license/hoquanghai/Auto-Create-Video?style=for-the-badge&color=green)](LICENSE)
[![Node](https://img.shields.io/badge/node-22%2B-brightgreen?style=for-the-badge&logo=node.js&logoColor=white)](https://nodejs.org)
[![TypeScript](https://img.shields.io/badge/typescript-5%2B-blue?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Tests](https://github.com/hoquanghai/Auto-Create-Video/actions/workflows/test.yml/badge.svg?style=for-the-badge)](https://github.com/hoquanghai/Auto-Create-Video/actions/workflows/test.yml)
[![Typecheck](https://github.com/hoquanghai/Auto-Create-Video/actions/workflows/typecheck.yml/badge.svg?style=for-the-badge)](https://github.com/hoquanghai/Auto-Create-Video/actions/workflows/typecheck.yml)

[**🇬🇧 English**](README.md) · [**🇻🇳 Tiếng Việt**](README.vi.md) · [**📺 Xem Demo**](https://youtube.com/shorts/S24JfKxV4bo) · [**🚀 Bắt Đầu Nhanh**](#-bắt-đầu-nhanh) · [**❓ FAQ**](#-faq)

</div>

---

<div align="center">

## 🎥 Xem Demo Sản Phẩm

### 👉 [**▶️ Xem video demo trên YouTube Shorts**](https://youtube.com/shorts/S24JfKxV4bo) 👈

[![Xem Demo](https://img.youtube.com/vi/S24JfKxV4bo/maxresdefault.jpg)](https://youtube.com/shorts/S24JfKxV4bo)

[![Xem trên YouTube](https://img.shields.io/badge/▶️_Xem_trên_YouTube-FF0000?style=for-the-badge&logo=youtube&logoColor=white)](https://youtube.com/shorts/S24JfKxV4bo)

*Video này được tạo **hoàn toàn** bằng pipeline này — Vietnamese TTS + HyperFrames + GSAP animations, không edit thủ công.*

</div>

---

## 🤔 Tại sao có dự án này?

Việc tạo video tin tức ngắn rất **tốn thời gian và lặp đi lặp lại**:

- ⏰ Viết kịch bản thủ công → 30 phút mỗi video
- 🎨 Chọn visual + animation → 1 tiếng mỗi video
- 🎙️ Thu hoặc tìm voice → 30 phút
- ✂️ Edit trên CapCut / Premiere → 1 tiếng
- 📱 **Tổng: ~3 tiếng cho 1 video 60 giây**

**Auto News Video chỉ cần 5 phút. Paste URL là xong.**

| | Cách thủ công | Auto News Video |
|---|---|---|
| ⏱️ Thời gian | ~3 tiếng | **~5 phút** |
| 🎓 Kỹ năng cần | Editor video | **Không cần** |
| 🎯 Độ ổn định | Phụ thuộc người làm | **Studio-grade mọi video** |
| 💰 Chi phí | $50–200 (freelancer) | **~$0.10 (API)** |
| 🇻🇳 Giọng tiếng Việt | Khó tìm | **Sẵn (LucyLab cloning)** |

---

## 🚀 Bắt Đầu Nhanh

```bash
# 1. Clone & cài dependencies
git clone https://github.com/hoquanghai/Auto-Create-Video.git
cd Auto-Create-Video
npm install

# 2. Cấu hình TTS API key
cp .env.example .env.local
# → mở .env.local, set TTS_PROVIDER + key (LucyLab hoặc ElevenLabs)
```

Sau đó chọn 1 trong 2 cách:

**Cách A — Có Claude Code (khuyến nghị, setup 30 giây):**

1. Cài Claude Code: `npm install -g @anthropic-ai/claude-code`
2. Trong thư mục project, chạy `claude`, rồi gõ:
   ```
   /create-news-video https://vnexpress.net/some-article
   ```

**Cách B — Không có Claude Code (tự viết script):**

```bash
# Edit script.json thủ công theo src/render/script-schema.ts
npm run pipeline -- output/my-video/script.json
```

Cả 2 cách: sau ~3–5 phút bạn sẽ có `output/<slug>/video.mp4` — file 1080×1920 sẵn sàng cho TikTok / Shorts / Reels.

> 💡 **Cần chi tiết?** Xem [Cài đặt đầy đủ](#-cài-đặt-đầy-đủ) · [Cấu hình](#-cấu-hình) · [Sử dụng](#-sử-dụng)

---

## ✨ Tính năng

<table>
<tr>
<td width="33%" align="center">
<h3>🎨 12 Template thông minh</h3>
<sub>hook · comparison · stat-hero · feature-list · callout · outro · quote-card · icon-grid · timeline · big-text · chart-bars · kinetic-quote</sub>
</td>
<td width="33%" align="center">
<h3>🎤 Đa nhà cung cấp TTS</h3>
<sub>LucyLab (giọng Việt cloning + SRT free) hoặc ElevenLabs (30+ ngôn ngữ)</sub>
</td>
<td width="33%" align="center">
<h3>🤖 Claude Code Skill</h3>
<sub>Một câu lệnh duy nhất:<br/><code>/create-news-video &lt;url&gt;</code><br/>(input URL / .txt / .md)</sub>
</td>
</tr>
<tr>
<td width="33%" align="center">
<h3>🎬 Phong cách HeyGen</h3>
<sub>Studio shell + grain texture + GSAP animations + 6 theme palettes (tech-blue, growth-green, finance-gold, warning-red, creator-purple, news-mono)</sub>
</td>
<td width="33%" align="center">
<h3>🔊 Auto SFX Mixing</h3>
<sub>Smart 3-tier picker (override → semantic → default) với anti-repetition + anti-overlap guards</sub>
</td>
<td width="33%" align="center">
<h3>🧪 Production Ready</h3>
<sub>44 unit tests, Zod schema validation, full TypeScript ESM, GitHub Actions CI</sub>
</td>
</tr>
<tr>
<td width="33%" align="center">
<h3>📱 9:16 Native</h3>
<sub>1080×1920 @ 30fps, sẵn cho TikTok / Shorts / Reels</sub>
</td>
<td width="33%" align="center">
<h3>♻️ TTS idempotent</h3>
<sub>Skip re-TTS nếu đã có voice file — tiết kiệm quota qua các lần re-render</sub>
</td>
<td width="33%" align="center">
<h3>🖼️ Auto Thumbnail</h3>
<sub>Gemini 2.5 Flash Image sinh cover 9:16, embed vào MP4 (không re-encode)</sub>
</td>
</tr>
<tr>
<td width="33%" align="center">
<h3>🎯 Voice-Text Sync</h3>
<sub><code>voiceChunks</code> per scene → beats fire ĐÚNG lúc voice nhắc đến từng element</sub>
</td>
<td width="33%" align="center">
<h3>✅ Quality Gates</h3>
<sub>Pre-render <code>lint</code> + <code>validate</code> (WCAG contrast) + <code>inspect</code> (text overflow / off-canvas)</sub>
</td>
<td width="33%" align="center">
<h3>📝 Thân thiện CapCut</h3>
<sub>Xuất kèm <code>script.txt</code> + <code>voice.mp3</code> + <code>sns_post.txt</code> cho auto-caption + caption mạng xã hội</sub>
</td>
</tr>
</table>

---

## 🧠 Cách hoạt động

```mermaid
flowchart LR
    A[📰 URL / .txt / .md] -->|/create-news-video| B[Claude Code]
    B -->|fetch + analyze| C[Sinh script.json]
    C -->|Zod validate| D{Template Picker}
    D -->|12 variants| E[Loại Scene]
    E -->|TTS từng scene<br/>hoặc từng chunk| F[LucyLab / ElevenLabs]
    F -->|voice.mp3<br/>+ SFX mix<br/>+ beat SFX| G[HyperFrames]
    G -.->|lint<br/>validate<br/>inspect| G
    G -->|Puppeteer + GSAP| H[1800 frames @ 30fps]
    H -->|FFmpeg encode| I[video.mp4 1080×1920]
    I -->|attach cover| J[Gemini Thumbnail]
    J -->|🎬 video.mp4 + thumbnail.png| K[Done]

    style A fill:#0f172a,color:#fff
    style K fill:#10b981,color:#fff
    style B fill:#6366f1,color:#fff
    style F fill:#f59e0b,color:#fff
    style G fill:#ec4899,color:#fff
    style J fill:#8b5cf6,color:#fff
```

Pipeline tách bạch rõ: **AI lo phần sáng tạo** (Claude viết kịch bản) và **code deterministic lo phần production** (Node/TS/FFmpeg render pixel) — cùng input → frames giống hệt nhau mỗi lần.

---

## 🛠️ Công nghệ sử dụng

| Lớp | Công nghệ |
|---|---|
| **Runtime** | Node.js ≥ 22, TypeScript 6+, ESM |
| **Render engine** | [HyperFrames](https://hyperframes.heygen.com) ^0.4.34 (Puppeteer + GSAP + FFmpeg) |
| **Quality gates** | `hyperframes lint` (errors block) → `validate` (WCAG contrast) → `inspect` (text overflow / off-canvas) — chạy trước khi render |
| **TTS providers** | [LucyLab.io](https://lucylab.io) (JSON-RPC async, Vietnamese cloning) hoặc [ElevenLabs](https://elevenlabs.io) (REST sync, multilingual) |
| **Image generation** | [Gemini 2.5 Flash Image](https://aistudio.google.com) — sinh thumbnail 9:16, embed làm cover MP4 |
| **Schema validation** | [Zod](https://zod.dev) ^4 discriminated unions (12 template variants) |
| **HTTP** | axios ^1.15 + nock (test mocking) |
| **Concurrency** | [p-limit](https://github.com/sindresorhus/p-limit) ^7 (rate-limit TTS theo provider) |
| **Testing** | [Vitest](https://vitest.dev) ^4 — ESM-native, kèm @vitest/coverage-v8 |
| **Audio processing** | FFmpeg + ffprobe (mix, concat with silence, attach cover image) |
| **AI orchestration** | [Claude Code](https://docs.claude.com/en/docs/claude-code/overview) skill (`/create-news-video`) |
| **Visual blocks** | HyperFrames registry: `grain-overlay`, `shimmer-sweep`, `tiktok-follow` |
| **Brand spec** | Xem [`design.md`](design.md) — palette, layout density, motion principles |
| **Fonts** | Manrope (body) + Anton (display) + Lora (italic serif cho quotes) — Google Fonts |

---

## 🔬 Đi sâu vào các công nghệ chính

### 🎞️ HyperFrames — trái tim của render engine

[HyperFrames](https://hyperframes.heygen.com) là framework HTML-to-video do **HeyGen** phát triển và mã nguồn mở. Khác với After Effects hay Premiere, HyperFrames cho phép bạn **viết video bằng HTML/CSS/JS** rồi render thành MP4 chất lượng cao một cách **deterministic** (cùng input → cùng output frame-by-frame).

**Cách nó hoạt động trong dự án:**
1. Pipeline sinh ra một file `index.html` chứa toàn bộ scenes + GSAP timeline
2. HyperFrames spawn headless Chrome (Puppeteer) để load file đó
3. Capture từng frame ở đúng timestamp (30fps × 60s = 1800 frames)
4. Encode tất cả frames + audio thành MP4 dùng FFmpeg

**Tại sao chọn HyperFrames?**
- ✅ **Có sẵn 50+ pre-built blocks** trong registry (transitions, social cards, kinetic typography...)
- ✅ **GSAP timeline** đã được tích hợp sẵn cho animations mượt mà
- ✅ **AI-agent friendly** — Claude/GPT có thể tự sinh composition HTML
- ✅ **Quality gates built-in** (`lint` / `validate` / `inspect`) — pipeline chạy cả 3 trước khi render để bắt lỗi rẻ nhất
- ✅ **Aspect ratio 9:16 native** — sinh ra cho short-form video

### 🎤 LucyLab vs ElevenLabs — chọn cái nào?

| Tiêu chí | LucyLab | ElevenLabs |
|---|---|---|
| **Giọng tiếng Việt** | ⭐⭐⭐⭐⭐ Tự nhiên (voice cloning) | ⭐⭐⭐⭐ Tốt (multilingual) |
| **Chi phí** | Rẻ (~25k VND / 1M ký tự) | Đắt hơn (~$5 / 30k ký tự) |
| **Voice library** | Tự clone giọng | 1000+ voices có sẵn |
| **API style** | JSON-RPC async (poll) | REST sync (instant) |
| **SRT subtitle** | ✅ Free, kèm theo response | ❌ Không có |
| **Concurrency** | 1 export/account | Parallel OK |
| **Ngôn ngữ khác** | ❌ Chỉ tiếng Việt | ✅ 30+ ngôn ngữ |

**Khuyến nghị:**
- 🇻🇳 **Chỉ làm video tiếng Việt** → chọn **LucyLab** (rẻ + giọng tự nhiên + có SRT)
- 🌍 **Đa ngôn ngữ hoặc cần voice library lớn** → chọn **ElevenLabs**
- 🔄 **Không chắc** → bắt đầu với LucyLab, đổi sang ElevenLabs sau (chỉ cần đổi `TTS_PROVIDER` trong `.env.local`)

### 🛡️ Zod — schema validation an toàn

[Zod](https://zod.dev) là TypeScript-first schema library. Trong project này, Zod đảm bảo `script.json` (do Claude sinh) **luôn đúng cấu trúc** trước khi pipeline chạy.

```ts
// Discriminated union: 12 loại template, mỗi loại có data shape khác nhau
const TemplateData = z.discriminatedUnion("template", [
  // v1 — core 6
  HookData, ComparisonData, StatHeroData, FeatureListData, CalloutData, OutroData,
  // v3 — composition expansion
  QuoteCardData, IconGridData, TimelineData,
  // v3.1 — dramatic impact
  BigTextData, ChartBarsData, KineticQuoteData,
]);
```

Lợi ích:
- Phát hiện ngay nếu Claude sinh script sai (vd: `template: "stat"` không tồn tại) — fail Step 1 với error message rõ ràng
- TypeScript types được suy ra tự động từ Zod schema → composer không cần khai báo type lại
- Schema = source of truth cho cả validation runtime + type compile-time

---

## 📋 Yêu cầu hệ thống

| Mục | Phiên bản | Ghi chú |
|---|---|---|
| **Node.js** | ≥ 22 | `node --version` |
| **FFmpeg + ffprobe** | bất kỳ phiên bản hiện đại | trong PATH (`ffmpeg -version`) |
| **Chrome / Chromium** | bất kỳ | HyperFrames Puppeteer auto-download lần đầu chạy |
| **Claude Code CLI** | latest | [cài tại đây](https://docs.claude.com/en/docs/claude-code/overview) |
| **Tài khoản TTS** | một trong hai | LucyLab.io HOẶC ElevenLabs |

---

## 🔧 Cài đặt đầy đủ

```bash
# 1. Clone repo
git clone https://github.com/hoquanghai/Auto-Create-Video.git
cd Auto-Create-Video

# 2. Cài dependencies
npm install

# 3. Tạo file env và điền API key
cp .env.example .env.local
# → mở .env.local, set TTS_PROVIDER + API key (xem phần Cấu hình bên dưới)

# 4. Verify cài đặt
node --version       # ≥ 22
ffmpeg -version      # in version OK
ffprobe -version
npm test             # all 44 tests should pass
```

### Cài FFmpeg

| OS | Lệnh |
|---|---|
| **Windows** | `winget install Gyan.FFmpeg` |
| **macOS** | `brew install ffmpeg` |
| **Ubuntu/Debian** | `sudo apt install ffmpeg` |

---

## ⚙️ Cấu hình

Mở `.env.local` và chọn **một trong hai provider**:

### Option 1 — LucyLab.io (khuyến nghị cho tiếng Việt)

```env
TTS_PROVIDER=lucylab
VIETNAMESE_API_KEY=sk_live_xxxxxxxxxxxxxxxxxxxx
VIETNAMESE_VOICEID=22charvoiceiduuidhere
```

- ✅ Giọng Việt tự nhiên (voice cloning), trả kèm file SRT subtitle miễn phí
- ⚠️ Chỉ 1 export/account đồng thời (pipeline tự xử lý)
- 🔗 Đăng ký: https://lucylab.io

### Option 2 — ElevenLabs

```env
TTS_PROVIDER=elevenlabs
ELEVENLABS_API_KEY=sk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ELEVENLABS_VOICE_ID=EXAVITQu4vr4xnSDxMaL
ELEVENLABS_MODEL_ID=eleven_multilingual_v2
```

- ✅ Đa ngôn ngữ (30+), thư viện voice phong phú, chất lượng cao
- ⚠️ Đắt hơn LucyLab, không có SRT đi kèm
- 🔗 Lấy key: https://elevenlabs.io/app/settings/api-keys · Browse voices: https://elevenlabs.io/app/voice-library

### TikTok follow card (tùy chọn, defaults work)

```env
TIKTOK_DISPLAY_NAME=Quẹp Làm IT
TIKTOK_HANDLE=@haiquep
TIKTOK_FOLLOWERS=11.5k followers
TIKTOK_AVATAR_URL=https://example.com/your-avatar.jpg   # tùy chọn
```

Để đổi avatar: thay file `assets/avatar.png` bằng ảnh của bạn (vuông, ≥256×256), **hoặc** set `TIKTOK_AVATAR_URL` để pipeline tự download mỗi lần render.

### Option 3 — Gemini thumbnail (tùy chọn, skip mượt mà nếu không có key)

Nếu set, pipeline sinh thumbnail 9:16 cho mỗi video và embed làm cover image của MP4 — Windows Explorer / Finder / TikTok / YouTube uploader hiển thị ảnh đó trước khi play frame đầu. Không có key, step bị skip im lặng (video vẫn render bình thường).

```env
GEMINI_API_KEY=YOUR_GEMINI_API_KEY_HERE
GEMINI_IMAGE_MODEL=gemini-2.5-flash-image    # default; ~7s mỗi call
```

🔗 Lấy key free tại: https://aistudio.google.com/apikey

### Pipeline tuning (tùy chọn)

```env
TTS_CONCURRENCY=1    # 1 cho LucyLab (giới hạn API). Tăng cho ElevenLabs để parallel.
```

---

## 🎬 Sử dụng

### Cách 1 — Trong Claude Code (khuyến nghị)

Mở Claude Code trong thư mục project và gõ:

```
/create-news-video https://vnexpress.net/iphone-17-200mp
```

Hoặc với file local (`.txt` hoặc `.md`):

```
/create-news-video news/my-article.md
```

Sau ~3–5 phút:

```
✓ Video:  output/<slug>-<timestamp>/video.mp4    ← video cuối
✓ Audio:  output/<slug>-<timestamp>/voice.mp3    ← để import CapCut
✓ Script: output/<slug>-<timestamp>/script.txt   ← cho CapCut auto-caption
```

### Cách 2 — Chạy pipeline trực tiếp (advanced)

Nếu đã có sẵn `script.json` (debug hoặc tự viết kịch bản):

```bash
npm run pipeline -- output/<slug>-<timestamp>/script.json
```

### Cách 3 — Re-render visual không cần TTS (tiết kiệm quota)

Nếu đã có voice files trong `voice/` và muốn render lại visual:

```bash
npm run rerender -- output/<slug>-<timestamp>
```

---

## 📁 Cấu trúc output

```
output/<slug>-<timestamp>/
├── script.json                # Input JSON (Claude sinh hoặc bạn viết tay)
├── script.txt                 # Plain text cho CapCut auto-caption
├── sns_post.txt               # Caption tiếng Việt cho TikTok / Reels (skill sinh ra)
├── images/bg.jpg              # og:image đã tải (nếu có)
├── voice/
│   ├── scene-hook.mp3         # TTS từng scene (idempotent — skip nếu đã có)
│   ├── scene-hook.srt         # SRT subtitle (chỉ LucyLab)
│   ├── scene-body-1.mp3
│   ├── scene-body-1-chunk-0.mp3   # voiceChunks: file TTS từng element riêng
│   └── scene-body-1-chunk-1.mp3   # dùng để compute beat timing chính xác
├── voice-raw.mp3              # Voice concat, chưa mix SFX (intermediate)
├── voice.mp3                  # Final audio đã mix SFX + beat SFX (cho CapCut)
├── tiktok-avatar.png          # Copy avatar bundled (hoặc download từ URL)
├── logo.svg                   # Copy logo bundled
├── index.html                 # HyperFrames composition
├── styles.css                 # Template CSS (self-contained)
├── animations.js              # GSAP timeline (self-contained)
├── hyperframes.json           # HyperFrames manifest
├── meta.json                  # HyperFrames metadata
├── thumbnail.png              # Cover 9:16 do Gemini sinh (nếu GEMINI_API_KEY set)
└── video.mp4                  # 🎉 Output cuối — 1080×1920 @ 30fps + cover embed
```

---

## 🎨 Visual System

Mỗi video gồm **persistent shell** xuyên suốt (header brand icon + tên channel + tag, footer handle TikTok, grain texture, gradient background) cộng với 4–18 scene Claude tự pick theo nội dung. Base palette luôn là **cream editorial (light)** để giữ brand identity nhất quán; field `theme` trên `script.metadata` đổi accent color:

| Theme | Khi nào dùng |
|---|---|
| `tech-blue` *(default)* | AI, code, dev tools, software |
| `growth-green` | Marketing, SaaS, customer growth |
| `finance-gold` | Money, pricing, ROI, fundraising |
| `warning-red` | Risk, controversy, failure stories |
| `creator-purple` | Founder stories, design, art, indie |
| `news-mono` | Serious news, journalism, reports |

### 12 templates (Claude tự pick theo nội dung)

**v1 — core 6:**

| Template | Khi nào pick | Ví dụ |
|---|---|---|
| `hook` | Scene đầu tiên (3–5s) | "GPT 5.5" + "AI mạnh nhất!" trên ảnh og:image với Ken Burns + shimmer |
| `comparison` | Có "X vs Y" / "vượt xa" / "so với" | 2 cards: "GPT 5.4 75.1%" cyan vs "GPT 5.5 82.7%" purple (winner) |
| `stat-hero` | Có số/% nổi bật | "1M" giant gradient + "Tokens / cửa sổ ngữ cảnh" |
| `feature-list` | Liệt kê tính năng | Card với tối đa 4 bullets, accent glow dots |
| `callout` | Statement / cảnh báo / quote | Glow card với "Cảnh báo: AI tự chủ cần cân nhắc" |
| `outro` | Scene cuối (3–5s) | "Theo dõi ngay" pill + tên channel + underline gradient |

**v3 — composition expansion:**

| Template | Khi nào pick | Ví dụ |
|---|---|---|
| `quote-card` | Pull quote / statement contemplative | Italic Lora serif, attribution dòng dưới |
| `icon-grid` | 3–6 tính năng / capability | Cells icon emoji + label, staggered reveal |
| `timeline` | Nhiều giai đoạn tiến trình | Hàng when/label, slide-right cascade |

**v3.1 — dramatic impact:**

| Template | Khi nào pick | Ví dụ |
|---|---|---|
| `big-text` | Một từ/cụm dramatic duy nhất | Anton display khổng lồ, có thể `hideShell` để full-bleed |
| `chart-bars` | 2–5 thanh số liệu | Heights normalize 100%, slide-up reveal kèm ding |
| `kinetic-quote` | Kinetic typography 3–12 từ | Words reveal tuần tự, accent ở từ highlight |

### Per-scene timing & motion

- **Beats** — tối đa 12 keyed animations mỗi scene (8 effects: `bounce-in`, `scale-pop`, `slide-up/-left/-right`, `fade-in`, `glow-pulse`, `shake`). Defaults derive theo template, override qua `scene.beats`, hoặc dùng `voiceChunks` để timing chính xác theo voice.
- **`voiceChunks`** — chia voice thành 2–8 câu kèm `target` element + optional `effect` + `sfx`. Pipeline TTS từng chunk riêng, đo duration thực, fire beats ĐÚNG lúc voice nhắc đến từng element. Khử lỗi "visual leak ahead of voice".
- **Transitions** — 8 loại (`cut`, `fade`, `slide-up/-down/-left/-right`, `scale-out`, `blur`). Defaults theo cặp from→to scene-type (vd `hook→body`=fade 0.4s, `body→outro`=scale-out 0.5s); override qua `scene.transition`.

### Sound Effects (auto-mix theo template)

| Template | Default category (fallback) | Khi nào nghe |
|---|---|---|
| `hook` | `transition` → `cinematic` | Đầu video, entrance dramatic |
| `comparison` | `transition` → `emphasis` | Khi 2 cards xuất hiện |
| `stat-hero` | `emphasis` → `success` | Lúc số/% xuất hiện |
| `feature-list` | `transition` → `emphasis` | Mỗi bullet appear |
| `callout` | `alert` → `drumroll` | Statement quan trọng / cảnh báo |
| `outro` | `outro` → `success` | Ending signature |
| `quote-card` | `cinematic` → `drumroll` | Pull quote contemplative |
| `icon-grid` | `transition` → `emphasis` | Multi-element reveal |
| `timeline` | `countdown` → `emphasis` | Tiến trình các stage |
| `big-text` | `cinematic` → `success` | Dramatic impact |
| `chart-bars` | `emphasis` → `success` | Bar reveal cascade |
| `kinetic-quote` | `cinematic` → `drumroll` | Typographic reveal |

Smart 3-tier picker (trong [`src/assets/sfx-selector.ts`](src/assets/sfx-selector.ts)) chọn theo thứ tự:

1. **`scene.sfx`** override (set `"none"` để disable SFX cho scene đó)
2. **Semantic match** trên `voiceText` (Việt + Anh) — vd `cảnh báo|warning|risk` → `alert`, `kỷ lục|record|breakthrough` → `success`, `ra mắt|launch|reveal` → `reveal`, `thất bại|fail|crash` → `fail`
3. **Template default** category (kèm fallback chain)

Trong cùng category, file được pick **deterministic** bằng hash scene id (cùng script → cùng SFX, nhưng các scene khác nhau lấy file khác nhau). Hai lớp bảo vệ thêm chạy trong mixer:

- **Anti-repetition**: sliding window 2 scene gần nhất ngăn không cho cùng file SFX phát 2 lần liên tiếp.
- **Anti-overlap guard**: beat SFX firing trong khoảng ±0.4s quanh SFX chính của scene bị skip (tránh "tick + ding clash" ở scene boundary). Beat SFX lặp lại liên tiếp giữa 2 scene bị duck volume 35%.

---

## 🎥 Showcase

<table>
<tr>
<td width="33%" align="center">
<a href="https://youtube.com/shorts/S24JfKxV4bo">
<img src="https://img.youtube.com/vi/S24JfKxV4bo/0.jpg" alt="iPhone 17 - 200MP camera" />
</a>
<br/>
<sub><b>iPhone 17 — 200MP camera</b><br/>Source: VnExpress</sub>
</td>
<td width="33%" align="center">
<i>Video của bạn ở đây?</i><br/><br/>
<sub>Mở issue gửi output của bạn, mình sẽ feature.</sub>
</td>
<td width="33%" align="center">
<i>Video của bạn ở đây?</i><br/><br/>
<sub>Mở issue gửi output của bạn, mình sẽ feature.</sub>
</td>
</tr>
</table>

> 🎬 **Làm được video hay?** Gửi qua [issue](https://github.com/hoquanghai/Auto-Create-Video/issues/new) — mình sẽ feature ở đây.

---

## ❓ FAQ

<details>
<summary><b>Có dùng được cho ngôn ngữ khác ngoài tiếng Việt không?</b></summary>

Có. Đổi `TTS_PROVIDER=elevenlabs` trong `.env.local` — ElevenLabs hỗ trợ 30+ ngôn ngữ (Anh, Trung, Nhật...).

Lưu ý: skill Claude Code hiện đang optimize cho tiếng Việt. Với ngôn ngữ khác bạn nên chỉnh prompt trong `.claude/skills/create-news-video/SKILL.md`.
</details>

<details>
<summary><b>Mỗi video tốn bao nhiêu tiền?</b></summary>

Khoảng **$0.05–0.15 mỗi video**, tùy provider:

- LucyLab: ~$0.02 / video (rẻ nhất, chỉ tiếng Việt)
- ElevenLabs: ~$0.10 / video (đa ngôn ngữ)
- Claude API (sinh script): ~$0.03 / video
</details>

<details>
<summary><b>Chạy được không cần Claude Code không?</b></summary>

Có — dùng **Cách 2** (`npm run pipeline -- script.json`) với `script.json` viết tay. Skill Claude Code chỉ lo phần "sáng tạo" (viết script tiếng Việt + pick template). Pipeline thuần Node.js — xem [`src/pipeline.ts`](src/pipeline.ts).
</details>

<details>
<summary><b>Sao không chọn Remotion mà lại chọn HyperFrames?</b></summary>

HyperFrames được purpose-built cho short-form video — 9:16 native, 50+ blocks social media (TikTok cards, kinetic typography, data viz), AI-agent friendly (Claude có thể tự sinh HTML composition mà không cần React boilerplate).

Remotion là tool tuyệt vời với scope rộng hơn — long-form content, composition phức tạp, full React ecosystem. Tool khác nhau cho job khác nhau.

Bọn mình vẫn mượn các ý tưởng tốt từ design của Remotion:

- Frame-deterministic timeline
- Declarative scene timing ([`src/render/timing.ts`](src/render/timing.ts))
- Hệ thống transitions built-in ([`src/render/transition-profiles.ts`](src/render/transition-profiles.ts))
</details>

<details>
<summary><b>Video output bị câm / audio bị méo. Sao vậy?</b></summary>

Khả năng cao FFmpeg chưa cài hoặc không trong PATH. Chạy `ffmpeg -version` để verify.

- Windows: `winget install Gyan.FFmpeg`
- macOS: `brew install ffmpeg`
- Ubuntu: `sudo apt install ffmpeg`

Sau đó restart terminal và chạy lại.
</details>

<details>
<summary><b>TTS đọc sai số. Fix thế nào?</b></summary>

TTS Việt đọc số kiểu chữ. Spell out trong `voiceText` (text trên màn hình `templateData` giữ nguyên dạng số):

| Trong `voiceText` (TTS-friendly) | Trên màn hình (`templateData`) |
|---|---|
| `năm chấm năm` | `5.5` |
| `tám mươi hai phẩy bảy phần trăm` | `82.7%` |
| `một triệu token` | `1M tokens` |
| `hai trăm megapixel` | `200MP` |

Skill Claude Code tự handle cái này khi sinh script. Xem [`SKILL.md`](.claude/skills/create-news-video/SKILL.md) để có ruleset đầy đủ.
</details>

<details>
<summary><b>Customize visual (màu, font) được không?</b></summary>

Được — sửa [`src/render/templates/styles.css`](src/render/templates/styles.css). Template dùng CSS variables (theme accent + base palette) nên thay đổi propagate qua cả 12 scene types và cả 6 themes. Animation timing trong [`src/render/templates/animations.js`](src/render/templates/animations.js). Brand spec rationale ở [`design.md`](design.md).
</details>

<details>
<summary><b>Force re-TTS một scene cụ thể như nào?</b></summary>

Step TTS là idempotent — chỉ synthesize scene chưa có mp3. Force 1 scene: xóa file của nó:

```bash
rm output/<slug>/voice/scene-hook.mp3
npm run pipeline -- output/<slug>/script.json
```

Re-render visual mà giữ tất cả voice: dùng `npm run rerender -- output/<slug>`.
</details>

<details>
<summary><b>Video dài tối đa được bao nhiêu?</b></summary>

Pipeline support **45–180 giây**. Heuristic trong [`SKILL.md`](.claude/skills/create-news-video/SKILL.md):

| Source words | Script words | Scenes | Duration |
|---|---|---|---|
| < 500 | ~110 | 4–5 | ~45–55s |
| 500–1500 | ~150–200 | 5–8 | ~60–80s |
| 1500–3000 | ~250–350 | 8–12 | ~100–140s |
| > 3000 | ~400–500 | 12–18 | ~150–180s |
</details>

---

## 🧪 Testing

```bash
npm test                 # 44 unit tests (~6s)
npm run test:watch       # watch mode
npx tsc --noEmit         # type-check không build
```

Tests cover Zod schema validation (12 templates), TTS clients cho cả LucyLab + ElevenLabs (với `nock` HTTP mocking — không gọi API thật), audio tools (với fixture mp3 sine waves), beat profiles + chunk-derived beats, timing computation, transition profiles, SFX selector (3-tier + anti-repetition), Gemini thumbnail prompt builder, và HTML composer snapshots. CI chạy mỗi push (xem badges đầu trang).

---

## 🐛 Troubleshooting

| Lỗi | Cách khắc phục |
|---|---|
| `Missing VIETNAMESE_API_KEY` / `Missing ELEVENLABS_API_KEY` | Kiểm tra `.env.local` đã có và đúng `TTS_PROVIDER` |
| `hyperframes render failed` | Chạy `npx hyperframes render --help` verify CLI; Chrome cài chưa? |
| `LucyLab polling timeout` | Tăng `LUCYLAB_POLL_TIMEOUT_MS` trong `.env.local` (default 120000ms) |
| `ElevenLabs 401 Invalid API key` | Verify key trên dashboard ElevenLabs, paste lại vào `.env.local` |
| `Total duration outside [45, 180]s` | Pipeline chỉ **warns** — re-trigger skill hoặc chỉnh `script.json` viết dài/ngắn hơn. Heuristic ở [`SKILL.md`](.claude/skills/create-news-video/SKILL.md). |
| `ffprobe: command not found` | Cài FFmpeg (xem phần [Cấu hình](#-cấu-hình)) |
| `Thumbnail skipped: GEMINI_API_KEY not set` | Step tùy chọn. Thêm key vào `.env.local` (free tại https://aistudio.google.com/apikey) hoặc bỏ qua — video vẫn render bình thường. |
| `hyperframes lint failed` | Quality gate phát hiện composition error. Đọc message và sửa `index.html` / `animations.js` trong output dir, rồi chạy lại `rerender`. |

---

## 🗺️ Roadmap

- [x] ~~Auto thumbnail generation (cover image)~~ — đã ship qua Gemini 2.5 Flash Image
- [x] ~~Voice-text sync per element~~ — đã ship qua `voiceChunks`
- [x] ~~Quality gates trước render~~ — đã ship qua hyperframes lint/validate/inspect
- [ ] Caption burned-in (forced alignment với Whisper)
- [ ] Auto-select background music theo mood
- [ ] Multi-news compilation mode (`digest`)
- [ ] AI-generated background images cho hook scene (Gemini / Flux khi không có og:image)
- [ ] Auto-upload TikTok / YouTube Shorts / Reels qua API
- [ ] Multi-language script generation (English, Chinese, Japanese)
- [ ] Web UI standalone (không cần Claude Code)

Có yêu cầu tính năng? [Mở issue](https://github.com/hoquanghai/Auto-Create-Video/issues/new).

---

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=hoquanghai/Auto-Create-Video&type=Date)](https://star-history.com/#hoquanghai/Auto-Create-Video&Date)

---

## 🤝 Contributing

PRs welcome! Với thay đổi lớn, mở issue trước để discuss.

```bash
# Fork → clone → branch
git checkout -b feature/my-improvement

# Make changes, ensure tests pass
npm test
npx tsc --noEmit

# Commit theo Conventional Commits
git commit -m "feat: add Google TTS provider support"

# Push và mở PR
git push origin feature/my-improvement
```

Commit prefixes: `feat:` (tính năng mới) · `fix:` (bug) · `docs:` · `refactor:` · `test:` · `chore:`

---

## 📜 License

[MIT](LICENSE) — sử dụng tự do, fork tự do, đóng góp PR tự do.

---

## 🙏 Acknowledgements

Dự án này đứng trên vai những người khổng lồ:

- [HyperFrames by HeyGen](https://hyperframes.heygen.com) — framework HTML-to-video làm cho dự án này khả thi
- [LucyLab.io](https://lucylab.io) — API voice cloning tiếng Việt
- [ElevenLabs](https://elevenlabs.io) — TTS đa ngôn ngữ
- [Anthropic Claude](https://www.anthropic.com/claude) — LLM viết script qua Claude Code skill
- [Remotion](https://www.remotion.dev) — inspiration cho HTML-based video rendering

---

## 💖 Ủng hộ dự án

Nếu dự án giúp bạn tiết kiệm thời gian, hãy:

- ⭐ **[Star repo này](https://github.com/hoquanghai/Auto-Create-Video)** — giúp dự án nhiều người biết đến hơn
- 🐦 [Share trên Twitter / X](https://twitter.com/intent/tweet?text=Check%20out%20Auto%20News%20Video%20%E2%80%94%20one-command%20Vietnamese%20short-form%20video%20generator&url=https://github.com/hoquanghai/Auto-Create-Video)
- 💬 Giới thiệu cho bạn bè làm content
- 🐛 [Report bug hoặc đề xuất tính năng](https://github.com/hoquanghai/Auto-Create-Video/issues)

<div align="center">

**[⬆ Lên đầu trang](#top)**

Made with ❤️ by [Ho Quang Hai](https://github.com/hoquanghai) tại 🇻🇳 Vietnam

</div>
