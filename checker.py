import urllib.request
import concurrent.futures
import os

# DANH SÁCH CÁC FILE CẦN CHECK VÀ FILE KẾT QUẢ TƯƠNG ỨNG
# Bạn có thể thêm bao nhiêu file tùy thích vào đây theo đúng định dạng: "File_Gốc": "File_Sạch"
TASKS = {
    "list.m3u": "live.m3u",
    "kenh china.m3u": "live_china.m3u",
    "List tong hop The thao va HBO.m3u": "live_thethao.m3u"
}

TIMEOUT = 4  # Số giây chờ tối đa

def check_link(url):
    try:
        req = urllib.request.Request(url, method="HEAD", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            if response.status in [200, 206, 301, 302]:
                return True
    except Exception:
        try:
            req = urllib.request.Request(url, method="GET", headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
                if response.status in [200, 206, 301, 302]:
                    return True
        except Exception:
            pass
    return False

def process_file(input_file, output_file):
    print(f"\n--- Đang xử lý file: {input_file} ---")
    if not os.path.exists(input_file):
        print(f"❌ Bỏ qua: Không tìm thấy file '{input_file}' trên GitHub.")
        return

    with open(input_file, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    if not lines:
        print(f"❌ Bỏ qua: File '{input_file}' trống rỗng!")
        return

    channels = []
    current_info = None

    for line in lines:
        line_str = line.strip()
        if line_str.startswith("#EXTM3U"):
            continue
        if line_str.startswith("#EXTINF"):
            current_info = line
            continue
        if line_str and not line_str.startswith("#"):
            if current_info:
                channels.append({"info": current_info, "url": line_str})
                current_info = None

    print(f"Tổng số link cần kiểm tra: {len(channels)}")
    live_channels = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        future_to_channel = {executor.submit(check_link, ch["url"]): ch for ch in channels}
        counter = 0
        for future in concurrent.futures.as_completed(future_to_channel):
            ch = future_to_channel[future]
            counter += 1
            if counter % 20 == 0:
                print(f"[{input_file}] Đã check: {counter}/{len(channels)}")
            try:
                if future.result():
                    live_channels.append(ch)
            except Exception:
                pass

    print(f"Kiểm tra xong '{input_file}'! Còn sống: {len(live_channels)}")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for ch in live_channels:
            f.write(ch["info"])
            f.write(ch["url"] + "\n")
    print(f"🎉 Đã xuất file sạch: {output_file}")

def main():
    for input_file, output_file in TASKS.items():
        process_file(input_file, output_file)

if __name__ == "__main__":
    main()
