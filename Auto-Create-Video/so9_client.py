import os
import time
import uuid
import requests
import subprocess

SO9_API_BASE = "https://open-api.so9.vn/api/v1"

_cached_token = None
_token_expiry = 0

def get_access_token(app_id: str, app_secret: str) -> str:
    global _cached_token, _token_expiry
    if _cached_token and time.time() < _token_expiry:
        return _cached_token
    
    url = f"{SO9_API_BASE}/oauth"
    payload = {
        "app_id": app_id,
        "app_secret": app_secret
    }
    resp = requests.post(url, json=payload)
    resp.raise_for_status()
    data = resp.json().get("data", {})
    
    _cached_token = data.get("access_token")
    expires_in = data.get("access_token_expires_in", 900)
    _token_expiry = time.time() + expires_in - 60 # buffer 60s
    return _cached_token

def upload_temp_file(file_path: str) -> str:
    url = "https://tmpfiles.org/api/v1/upload"
    with open(file_path, "rb") as f:
        files = {'file': f}
        resp = requests.post(url, files=files)
        resp.raise_for_status()
        data = resp.json().get("data", {})
        return data.get("url", "").replace("tmpfiles.org/", "tmpfiles.org/dl/")

def draw_thumbnail_text(image_path: str, title: str) -> str:
    """Draw text on the thumbnail image following the Hedra production style.
    - Dark overlay (36% opacity)
    - Cyan top text, Yellow bottom text with black stroke
    - Wraps text to fit within 1080px width
    """
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageOps
        import textwrap
        
        img = Image.open(image_path).convert("RGBA")
        
        # Fit and crop center
        img = ImageOps.fit(img, (1080, 1920), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
        
        # Overlay black 36%
        overlay = Image.new("RGBA", img.size, (0, 0, 0, int(255 * 0.36)))
        img = Image.alpha_composite(img, overlay)
        
        draw = ImageDraw.Draw(img)
        font_path = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
        try:
            font = ImageFont.truetype(font_path, 60)
        except Exception:
            font = ImageFont.load_default()
            
        parts = title.split(": ", 1)
        if len(parts) == 1:
            parts = title.split("- ", 1)
            
        line1 = parts[0] if len(parts) == 2 else ""
        line2 = parts[1] if len(parts) == 2 else title

        def draw_wrapped(text, y_start, color):
            # Wrap text to ~28 chars per line for font size 60
            wrapped_lines = textwrap.wrap(text, width=28)
            y = y_start
            for line in wrapped_lines:
                bbox = draw.textbbox((0, 0), line, font=font)
                w = bbox[2] - bbox[0]
                h = bbox[3] - bbox[1]
                x = (img.width - w) / 2
                # Stroke
                draw.text((x, y), line, font=font, fill=color, stroke_width=4, stroke_fill="black")
                y += h + 20
            return y

        # Start drawing slightly above center
        start_y = img.height / 2 - 150
        
        if line1:
            next_y = draw_wrapped(line1, start_y, "#00FFFF") # Cyan
            draw_wrapped(line2, next_y + 40, "#FFFF00") # Yellow
        else:
            draw_wrapped(line2, start_y, "#FFFF00")
            
        out_path = image_path.replace(".jpg", ".png")
        img.convert("RGB").save(out_path)
        return out_path
    except Exception as e:
        print(f"⚠️ PIL text drawing failed: {e}")
        return image_path


def generate_thumbnail(video_path, title: str = "") -> str:
    """Capture the first frame (0.1s) and apply custom text overlay.
    
    Extracting at 0.1s avoids pure black frames, then we draw the text
    overlay according to the Hedra production guide.
    """
    video_path_str = str(video_path)
    thumb_path = video_path_str + ".jpg"
    if os.path.exists(thumb_path):
        os.remove(thumb_path)

    cmd = [
        "ffmpeg",
        "-ss", "0.1",
        "-i", video_path_str,
        "-vf", "scale=1080:1920",
        "-frames:v", "1",
        "-q:v", "2",
        "-y", thumb_path,
    ]
    result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if result.returncode != 0 or not os.path.exists(thumb_path):
        raise Exception("Failed to capture thumbnail frame at 0.1s.")
        
    print("📸 Thumbnail captured at 0.1s")
    
    if title:
        # Draw the text overlay on the image and return the new PNG path
        thumb_path = draw_thumbnail_text(thumb_path, title)
        
    return thumb_path


def prepare_social_video(video_path, thumbnail_path: str) -> str:
    """Prepend a 0.28s still frame of the thumbnail to the video for SO9 upload.

    Facebook/Instagram Reels don't support custom thumbnails via API —
    they auto-pick a cover frame from the video.  By placing a bright,
    text-visible thumbnail image at the very start (0.28s), the auto-picked
    cover will look correct on every platform.
    """
    video_path_str = str(video_path)
    social_path = video_path_str.replace(".mp4", ".so9.mp4")
    if os.path.exists(social_path):
        os.remove(social_path)

    # Probe the original video to get fps and audio sample-rate so the
    # concat filter produces a seamless result.
    probe = subprocess.run(
        ["ffprobe", "-v", "error",
         "-select_streams", "v:0",
         "-show_entries", "stream=r_frame_rate",
         "-of", "csv=p=0", video_path_str],
        capture_output=True, text=True
    )
    fps = "30"  # default fallback
    if probe.returncode == 0 and "/" in probe.stdout.strip():
        parts = probe.stdout.strip().split("/")
        try:
            fps = str(round(int(parts[0]) / int(parts[1])))
        except Exception:
            pass

    # Build an FFmpeg command that:
    #   input 0 = thumbnail image → 0.28s video clip at matching fps/size
    #   input 1 = original video
    # Then concat them together with the original audio stream.
    cmd = [
        "ffmpeg",
        # Input 0: thumbnail still → 0.28s video
        "-loop", "1",
        "-framerate", fps,
        "-t", "0.28",
        "-i", thumbnail_path,
        # Input 1: original video
        "-i", video_path_str,
        # Concat filter: scale thumbnail to match, then join video streams.
        # Generate 0.28s silence for the thumbnail clip so audio stays in sync.
        "-filter_complex",
        f"[0:v]scale=1080:1920:force_original_aspect_ratio=disable,setsar=1,fps={fps},format=yuv420p[thumb];"
        f"[1:v]fps={fps},format=yuv420p[main];"
        f"[thumb][main]concat=n=2:v=1:a=0[vout];"
        f"anullsrc=r=44100:cl=stereo[silence];"
        f"[silence]atrim=0:0.28[sil];"
        f"[sil][1:a]concat=n=2:v=0:a=1[aout]",
        "-map", "[vout]",
        "-map", "[aout]",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "18",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        "-y", social_path,
    ]
    result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0 or not os.path.exists(social_path):
        print(f"⚠️ prepare_social_video FFmpeg error: {result.stderr[-500:]}")
        raise Exception("Failed to prepend thumbnail frame to SO9 video.")
    return social_path

def publish_post(app_id: str, app_secret: str, channel_ids: list, content: str, video_file_path: str, title: str = "", project_id: str = "") -> dict:
    if not title:
        title = content.split('\n')[0][:95]
    # 1. Capture thumbnail and create a SO9-specific video copy.
    thumb_path = generate_thumbnail(video_file_path, title)
    social_video_path = prepare_social_video(video_file_path, thumb_path)

    # 2. Upload video + thumbnail to get public URLs
    video_url = upload_temp_file(social_video_path)
    if not video_url:
        raise Exception("Failed to upload temporary video.")
    
    thumb_url = upload_temp_file(thumb_path)
    if not thumb_url:
        raise Exception("Failed to upload temporary thumbnail.")
    
    # 3. Get token
    token = get_access_token(app_id, app_secret)
    
    # 4. Create post
    url = f"{SO9_API_BASE}/posts/store"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    payload = {
        "channel_ids": channel_ids,
        "content": content,
        "id_thirdparty": str(uuid.uuid4()),
        "share_post_to_story": False,
        "facebook_setting": {
            "type": "reel"  # SO9 docs: feed, reel, story
        },
        "youtube_setting": {
            "type": "short",  # SO9 docs: video, short
            "title": title,
            "category": "28",  # Science & Technology
            "privacy_status": "public",
            "privacyStatus": "public",
            "status": "public"
        },
        "tiktok_setting": {
            "thumbnail_offset": 0  # 0ms = first frame of the 0.28s prepended thumbnail still
        },
        "instagram_setting": {
            "type": "reel"  # SO9 docs: feed, reel, story
        },
        "zalo_setting": {
            "title": title,
            "description": content,
            "comment_state": "show",
            "article_state": "show"
        },
        "pinterest_setting": {
            "title": title
        },
        "media": {
            "type": 2, # 2 = video
            "video": {
                "url": video_url,
                "thumbnail_url": thumb_url
            }
        }
    }
    
    resp = requests.post(url, headers=headers, json=payload)
    if not resp.ok:
        try:
            err = resp.json()
        except:
            err = resp.text
        raise Exception(f"SO9 API Error ({resp.status_code}): {err}")
    result = resp.json()

    # 5. Set Facebook custom thumbnail via SO9 internal API
    post_id = result.get("data", "")
    if post_id and project_id:
        try:
            set_facebook_thumbnail(token, project_id, post_id, thumb_path)
        except Exception as e:
            print(f"⚠️ Failed to set Facebook thumbnail: {e}")
    
    return result


# ─── SO9 Internal API: Custom Thumbnail for Facebook ─────────────────────────

SO9_UPLOAD_BASE = "https://upload.so9.vn/api/v1"
SO9_INTERNAL_BASE = "https://i.so9.vn/api/v1"

PLATFORM_FACEBOOK = 5  # from DevTools network capture


def upload_to_so9(token: str, project_id: str, image_path: str) -> str:
    """Upload an image to SO9's permanent storage (asset.so9.vn).
    
    Returns the permanent URL like:
      https://asset.so9.vn/do-space/{project_id}/post-{hash}...
    """
    url = f"{SO9_UPLOAD_BASE}/upload/image"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    with open(image_path, "rb") as f:
        files = {"image": (os.path.basename(image_path), f, "image/jpeg")}
        data = {
            "projectId": project_id,
            "folder": "post"
        }
        resp = requests.post(url, headers=headers, files=files, data=data)
    
    if not resp.ok:
        raise Exception(f"SO9 upload error ({resp.status_code}): {resp.text[:200]}")
    
    result = resp.json()
    image_url = result.get("data", {}).get("url", "")
    if not image_url:
        raise Exception(f"SO9 upload returned no URL: {result}")
    print(f"✅ Thumbnail uploaded to SO9: {image_url[:80]}...")
    return image_url


def get_platform_posts(token: str, project_id: str, post_id: str) -> list:
    """Get platform-specific sub-posts for a given SO9 post ID.
    
    Returns list of dicts like:
      [{"_id": "...", "platform": 5, ...}, ...]
    """
    url = f"{SO9_INTERNAL_BASE}/projects/{project_id}/note-posts/list"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    params = {
        "post_id": post_id,
        "is_open": 0,
        "menu": "dashboard"
    }
    resp = requests.get(url, headers=headers, params=params)
    if not resp.ok:
        raise Exception(f"SO9 get platform posts error ({resp.status_code}): {resp.text[:200]}")
    
    result = resp.json()
    # Response may be {"data": [...]} or {"data": {"data": [...]}}
    data = result.get("data", [])
    if isinstance(data, dict):
        data = data.get("data", [])
    return data if isinstance(data, list) else []


def set_facebook_thumbnail(token: str, project_id: str, post_id: str, thumb_path: str):
    """Set custom thumbnail for Facebook Reels via SO9 internal API.
    
    Flow:
    1. Upload thumbnail to SO9's permanent storage
    2. Get platform-specific post IDs
    3. Call edit-social-post for Facebook platform
    """
    # 1. Upload thumbnail to SO9
    thumb_url = upload_to_so9(token, project_id, thumb_path)
    
    # 2. Wait for SO9 to finish processing the post across platforms
    print("⏳ Waiting 15s for SO9 to process post across platforms...")
    time.sleep(15)
    
    # 3. Get platform-specific post IDs
    platform_posts = get_platform_posts(token, project_id, post_id)
    if not platform_posts:
        print("⚠️ No platform posts found — post may still be processing.")
        return
    
    # 4. Find Facebook platform post and set thumbnail
    fb_count = 0
    for pp in platform_posts:
        platform = pp.get("platform")
        platform_post_id = pp.get("_id", "")
        
        if platform == PLATFORM_FACEBOOK and platform_post_id:
            edit_url = f"{SO9_INTERNAL_BASE}/projects/{project_id}/posts/edit-social-post"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            body = {
                "platform_post_id": platform_post_id,
                "platform": PLATFORM_FACEBOOK,
                "info": {
                    "thumb": thumb_url
                },
                "menu": "dashboard"
            }
            resp = requests.put(edit_url, headers=headers, json=body)
            if resp.ok:
                print(f"✅ Facebook thumbnail set for platform_post {platform_post_id}")
                fb_count += 1
            else:
                print(f"⚠️ Failed to set FB thumbnail ({resp.status_code}): {resp.text[:200]}")
    
    if fb_count == 0:
        print(f"⚠️ No Facebook platform post found. Available platforms: {[p.get('platform') for p in platform_posts]}")
    else:
        print(f"✅ Facebook thumbnail set for {fb_count} post(s)")


if __name__ == "__main__":
    # Test only, won't execute when imported
    pass

