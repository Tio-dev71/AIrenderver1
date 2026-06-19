import os
import requests
from dotenv import load_dotenv

load_dotenv(".env")

APP_ID = os.environ.get("SO9_APP_ID", "")
APP_SECRET = os.environ.get("SO9_APP_SECRET", "")
BASE_URL = "https://open-api.so9.vn/api/v1"

if not APP_ID or not APP_SECRET:
    print("❌ Vui lòng điền SO9_APP_ID và SO9_APP_SECRET vào file .env trước!")
    exit(1)

print("🔄 Đang lấy Token từ SO9...")
try:
    res = requests.post(f"{BASE_URL}/oauth", json={"app_id": APP_ID, "app_secret": APP_SECRET}).json()
    token = res.get("data", {}).get("access_token")
    if not token:
        print("❌ Lấy token thất bại:", res)
        exit(1)
        
    print("✅ Đã lấy Token! Đang tải danh sách kênh...")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Thử gọi API lấy danh sách kênh
    endpoints = ["/channels", "/channel/list", "/channels/list"]
    success = False
    
    for ep in endpoints:
        channel_res = requests.get(f"{BASE_URL}{ep}", headers=headers)
        if channel_res.ok:
            data = channel_res.json()
            channels = data.get("data", {}).get("items", []) if isinstance(data.get("data"), dict) else data.get("data", [])
            print("\n" + "="*40)
            print("📋 DANH SÁCH CHANNEL ID CỦA BẠN")
            print("="*40)
            if not channels:
                print("Chưa tìm thấy kênh nào (hoặc kết quả API rỗng).")
                print("RAW Data:", data)
            for c in channels:
                name = c.get('name', 'Unknown')
                cid = c.get('id', c.get('_id', 'Unknown ID'))
                platform = c.get('platform', 'Unknown platform')
                print(f"🔹 Tên kênh: {name} ({platform})")
                print(f"   ID: {cid}")
                print("-" * 40)
            success = True
            break
            
    if not success:
        print("❌ Không thể lấy danh sách kênh tự động (Endpoint không chuẩn).")
        
except Exception as e:
    print(f"❌ Lỗi: {e}")
