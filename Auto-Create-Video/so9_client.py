import os
import time
import uuid
import requests

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

def upload_temp_video(file_path: str) -> str:
    url = "https://tmpfiles.org/api/v1/upload"
    with open(file_path, "rb") as f:
        files = {'file': f}
        resp = requests.post(url, files=files)
        resp.raise_for_status()
        data = resp.json().get("data", {})
        return data.get("url", "").replace("tmpfiles.org/", "tmpfiles.org/dl/")

def publish_post(app_id: str, app_secret: str, channel_ids: list, content: str, video_file_path: str) -> dict:
    # 1. Upload video to get public URL
    video_url = upload_temp_video(video_file_path)
    if not video_url:
        raise Exception("Failed to upload temporary video.")
    
    # 2. Get token
    token = get_access_token(app_id, app_secret)
    
    # 3. Create post
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
        "tiktok_setting": {
            # Tiktok mặc định upload video ok
        },
        "media": {
            "type": 2, # 2 = video
            "video": {
                "url": video_url
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
