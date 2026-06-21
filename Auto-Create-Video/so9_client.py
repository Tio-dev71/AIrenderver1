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
    """Prepend a 0.5s still frame of the thumbnail to the video for SO9 upload.

    Facebook/Instagram Reels don't support custom thumbnails via API —
    they auto-pick a cover frame from the video.  By placing a bright,
    text-visible thumbnail image at the very start (0.5s), the auto-picked
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
    #   input 0 = thumbnail image → 0.5s video clip at matching fps/size
    #   input 1 = original video
    # Then concat them together with the original audio stream.
    cmd = [
        "ffmpeg",
        # Input 0: thumbnail still → 0.5s video
        "-loop", "1",
        "-framerate", fps,
        "-t", "0.5",
        "-i", thumbnail_path,
        # Input 1: original video
        "-i", video_path_str,
        # Concat filter: scale thumbnail to match, then join video streams.
        # Generate 0.5s silence for the thumbnail clip so audio stays in sync.
        "-filter_complex",
        f"[0:v]scale=1080:1920:force_original_aspect_ratio=disable,setsar=1,fps={fps},format=yuv420p[thumb];"
        f"[1:v]fps={fps},format=yuv420p[main];"
        f"[thumb][main]concat=n=2:v=1:a=0[vout];"
        f"anullsrc=r=44100:cl=stereo[silence];"
        f"[silence]atrim=0:0.5[sil];"
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
            "thumbnail_offset": 300  # 300ms = inside the 0.5s prepended thumbnail still
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
    return resp.json()

if __name__ == "__main__":
    # Test only, won't execute when imported
    pass
