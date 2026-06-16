import urllib.request
import concurrent.futures
import re

# Tên file gốc và file kết quả
INPUT_FILE = "list.m3u"
OUTPUT_FILE = "live.m3u"
TIMEOUT = 4  # Số giây tối đa để chờ phản hồi từ link (quá 4s coi như chết)

def check_link(url):
    """Kiểm tra xem link còn sống hay không"""
    try:
        # Sử dụng phương pháp HEAD thay vì GET để check cho nhanh, tránh tải cả luồng video
        req = urllib.request.Request(url, method="HEAD", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            if response.status in [200, 206, 301, 302]:
                return True
    except Exception:
        # Thử lại bằng GET nếu HEAD bị chặn (một số server chặn HEAD)
        try:
            req = urllib.request.Request(url, method="GET", headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
                if response.status in [200, 206, 301, 302]:
                    return True
        except Exception:
            pass
    return False

def main():
    print("Đang đọc file m3u...")
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    header = ""
    channels = []
    current_info = None

    for line in lines:
        line_str = line.strip()
        if line_str.startswith("#EXTM3U"):
            header = line
            continue
        if line_str.startswith("#EXTINF"):
            current_info = line
            continue
        if line_str and not line_str.startswith("#"):
            if current_info:
                channels.append({"info": current_info, "url": line_str})
                current_info = None

    print(lines[0].strip() if lines else "")
    print(f"Tổng số link cần kiểm tra: {len(channels)}")

    live_channels = []
    
    # Sử dụng ThreadPoolExecutor để kiểm tra đa luồng (chạy song song nhiều link cùng lúc cho nhanh)
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        # Gửi các luồng check
        future_to_channel = {executor.submit(check_link, ch["url"]): ch for ch in channels}
        
        counter = 0
        for future in concurrent.futures.as_completed(future_to_channel):
            ch = future_to_channel[future]
            counter += 1
            if counter % 10 == 0:
                print(f"Đã check: {counter}/{len(channels)}")
            try:
                if future.result():
                    live_channels.append(ch)
            except Exception:
                pass

    # Ghi ra file mới chỉ chứa các link sống
    print(f"Kiểm tra xong! Số lượng link còn sống: {len(live_channels)}")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for ch in live_channels:
            f.write(ch["info"])
            f.write(ch["url"] + "\n")

if __name__ == "__main__":
    main()
