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
    # Try tmpfiles.org first
    try:
        url = "https://tmpfiles.org/api/v1/upload"
        with open(file_path, "rb") as f:
            files = {'file': f}
            resp = requests.post(url, files=files, timeout=30)
            resp.raise_for_status()
            data = resp.json().get("data", {})
            return data.get("url", "").replace("tmpfiles.org/", "tmpfiles.org/dl/")
    except Exception as e:
        print(f"⚠️ tmpfiles.org failed ({e}), falling back to catbox.moe...")
        # Fallback to catbox.moe
        catbox_url = "https://catbox.moe/user/api.php"
        with open(file_path, 'rb') as f:
            files = {'fileToUpload': f}
            data = {'reqtype': 'fileupload'}
            resp2 = requests.post(catbox_url, files=files, data=data, timeout=60)
            resp2.raise_for_status()
            return resp2.text.strip()

def generate_thumbnail(video_path, title: str = "") -> str:
    """Capture a content-rich frame at 32% of video duration for thumbnail.

    YouTube auto-picks a visually interesting frame from the middle of
    the video — that's why its thumbnails show colorful charts/data.
    TikTok/FB/Insta just take the first frame.  By extracting at 32%
    of total duration (the Hedra standard) we get the same rich content
    frame and prepend it so every platform shows it.
    """
    video_path_str = str(video_path)
    thumb_path = video_path_str + ".jpg"
    if os.path.exists(thumb_path):
        os.remove(thumb_path)

    # 1. Get video duration via ffprobe
    probe = subprocess.run(
        ["ffprobe", "-v", "error",
         "-show_entries", "format=duration",
         "-of", "csv=p=0", video_path_str],
        capture_output=True, text=True
    )
    thumb_time = 3.0  # fallback ~3s if probe fails
    if probe.returncode == 0:
        try:
            duration = float(probe.stdout.strip())
            thumb_time = duration * 0.32
        except (ValueError, TypeError):
            pass

    # 2. Extract the frame (accurate seek: -ss AFTER -i)
    cmd = [
        "ffmpeg",
        "-i", video_path_str,
        "-ss", str(thumb_time),
        "-vf", "scale=1080:1920",
        "-frames:v", "1",
        "-q:v", "2",
        "-y", thumb_path,
    ]
    result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if result.returncode != 0 or not os.path.exists(thumb_path):
        raise Exception(f"Failed to capture thumbnail frame at {thumb_time:.1f}s.")

    print(f"📸 Thumbnail captured at {thumb_time:.1f}s (32% of {duration:.1f}s duration)")

    return thumb_path


def prepare_social_video(video_path, thumbnail_path: str) -> str:
    """Prepend a 0.28s still frame of the thumbnail to the video for SO9 upload.

    Facebook/Instagram/TikTok Reels don't support custom thumbnails via API —
    they auto-pick a cover frame from the video.  By placing a bright,
    text-visible thumbnail image at the very start (0.28s), the auto-picked
    cover will look correct on every platform.
    """
    video_path_str = str(video_path)
    social_path = video_path_str.replace(".mp4", ".so9.mp4")
    if os.path.exists(social_path):
        os.remove(social_path)

    # Probe the original video to get fps
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

    # Build an FFmpeg command mimicking Hedra Dev's exact filter graph
    cmd = [
        "ffmpeg",
        # Input 0: original video
        "-i", video_path_str,
        # Input 1: thumbnail still → 0.28s video
        "-loop", "1",
        "-t", "0.28",
        "-i", thumbnail_path,
        # Input 2: 0.28s silence
        "-f", "lavfi",
        "-t", "0.28",
        "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
        
        "-filter_complex",
        (
            f"[1:v]scale=1080:1920:force_original_aspect_ratio=disable,setsar=1,fps={fps},format=yuv420p[vcover]; "
            f"[2:a]aresample=48000[acover]; "
            f"[0:v]fps={fps},format=yuv420p[vmain]; "
            f"[0:a]aresample=48000[amain]; "
            f"[vcover][acover][vmain][amain]concat=n=2:v=1:a=1[vout][aout]"
        ),
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

