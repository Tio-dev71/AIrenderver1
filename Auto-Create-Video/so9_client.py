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

def generate_thumbnail(video_path) -> str:
    """Capture the actual rendered video frame at ~0.05s, like CapCut thumbnail capture."""
    video_path_str = str(video_path)
    thumb_path = video_path_str + ".jpg"
    if os.path.exists(thumb_path):
        os.remove(thumb_path)
    cmd = [
        "ffmpeg",
        "-i", video_path_str,
        "-vf", "select='gte(t,0.05)',scale=1080:1920",
        "-frames:v", "1",
        "-q:v", "2",
        "-y", thumb_path,
    ]
    result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if result.returncode != 0 or not os.path.exists(thumb_path):
        raise Exception("Failed to capture thumbnail frame at 0.05s.")
    return thumb_path


def prepare_social_video(video_path, thumbnail_path: str) -> str:
    """Create a SO9 upload copy whose first visible frame is the chosen thumbnail."""
    video_path_str = str(video_path)
    social_path = video_path_str.replace(".mp4", ".so9.mp4")
    if os.path.exists(social_path):
        os.remove(social_path)

    cmd = [
        "ffmpeg",
        "-i", video_path_str,
        "-loop", "1",
        "-i", thumbnail_path,
        "-filter_complex", "[0:v][1:v]overlay=enable='lt(t,0.05)',format=yuv420p[v]",
        "-map", "[v]",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "18",
        "-c:a", "copy",
        "-movflags", "+faststart",
        "-shortest",
        "-y", social_path,
    ]
    result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if result.returncode != 0 or not os.path.exists(social_path):
        raise Exception("Failed to prepare SO9 social video with thumbnail first frame.")
    return social_path

def publish_post(app_id: str, app_secret: str, channel_ids: list, content: str, video_file_path: str, title: str = "") -> dict:
    if not title:
        title = content.split('\n')[0][:95]
    # 1. Capture thumbnail and create a SO9-specific video copy.
    # YouTube can use thumbnail_url, but TikTok/Facebook/Instagram often use the
    # first video frame, so the SO9 upload copy starts with the chosen thumbnail.
    thumb_path = generate_thumbnail(video_file_path)
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
        "facebook_setting": {
            "type": "reel"  # Video ngắn thường nên để Reel
        },
        "youtube_setting": {
            "type": "short",
            "title": title,
            "privacy_status": "public",
            "privacyStatus": "public",
            "status": "public"
        },
        "tiktok_setting": {
            "thumbnail_offset": 0
        },
        "instagram_setting": {
            "type": "reel"
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
    return resp.json()

if __name__ == "__main__":
    # Test only, won't execute when imported
    pass
