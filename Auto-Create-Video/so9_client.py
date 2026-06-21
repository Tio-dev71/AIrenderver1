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
    """Extract a thumbnail frame at 0.28s for a nicer social media grid preview."""
    video_path_str = str(video_path)
    thumb_path = video_path_str + ".jpg"
    cmd = ["ffmpeg", "-ss", "0.28", "-i", video_path_str, "-vframes", "1", "-y", thumb_path]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return thumb_path

def publish_post(app_id: str, app_secret: str, channel_ids: list, content: str, video_file_path: str, title: str = "") -> dict:
    if not title:
        title = content.split('\n')[0][:95]
    # 1. Upload video to get public URL
    video_url = upload_temp_file(video_file_path)
    if not video_url:
        raise Exception("Failed to upload temporary video.")
    
    # 2. Upload thumbnail
    thumb_path = generate_thumbnail(video_file_path)
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
            "thumbnail_offset": 0.28
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
