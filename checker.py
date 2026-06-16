import urllib.request
import concurrent.futures
import os

TIMEOUT = 4  # Số giây chờ tối đa để check link sống/chết

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
    
    with open(input_file, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    if not lines:
        print(f"❌ Bỏ qua: File '{input_file}' trống rỗng!")
        return

    channels = []
    current_info = None
    # Kiểm tra xem có phải định dạng M3U không
    is_m3u = any(line.strip().startswith("#EXTM3U") for line in lines[:5])

    if is_m3u:
        # Xử lý cấu trúc file .m3u
        for line in lines:
            line_str = line.strip()
            if line_str.startswith("#EXTM3U"): continue
            if line_str.startswith("#EXTINF"):
                current_info = line
                continue
            if line_str and not line_str.startswith("#"):
                if current_info:
                    channels.append({"info": current_info, "url": line_str, "type": "m3u"})
                    current_info = None
    else:
        # Xử lý cấu trúc file .txt (Tên,Link)
        for line in lines:
            line_str = line.strip()
            if not line_str or "#genre#" in line_str: continue
            if "," in line_str:
                parts = line_str.split(",", 1)
                name = parts[0].strip()
                url = parts[1].strip()
                if url.startswith("http"):
                    channels.append({"name": name, "url": url, "type": "txt"})

    print(f"Tổng số link cần kiểm tra trong '{input_file}': {len(channels)}")
    if len(channels) == 0:
        print("-> Không tìm thấy link hợp lệ nào để check.")
        return

    live_channels = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        future_to_channel = {executor.submit(check_link, ch["url"]): ch for ch in channels}
        counter = 0
        for future in concurrent.futures.as_completed(future_to_channel):
            ch = future_to_channel[future]
            counter += 1
            if counter % 50 == 0 or counter == len(channels):
                print(f"[{input_file}] Đã check: {counter}/{len(channels)}")
            try:
                if future.result():
                    live_channels.append(ch)
            except Exception:
                pass

    print(f"Kiểm tra xong! File '{input_file}' còn sống: {len(live_channels)}")
    
    # Ghi file kết quả sạch ra
    with open(output_file, "w", encoding="utf-8") as f:
        if is_m3u:
            f.write("#EXTM3U\n")
            for ch in live_channels:
                f.write(ch["info"])
                f.write(ch["url"] + "\n")
        else:
            for ch in live_channels:
                f.write(f"{ch['name']},{ch['url']}\n")
                
    print(f"🎉 Đã xuất file sạch thành công: {output_file}")

def main():
    # TỰ ĐỘNG QUÉT TẤT CẢ FILE TRONG THƯ MỤC
    all_files = os.listdir(".")
    
    for file_name in all_files:
        # Chỉ check các file có đuôi .m3u hoặc .txt
        # Bỏ qua các file cấu hình hệ thống và file kết quả "live_" để không bị check vòng lặp
        if (file_name.endswith(".m3u") or file_name.endswith(".txt")) \
           and not file_name.startswith("live_") \
           and file_name != "requirements.txt":
            
            # Tự động đặt tên file sạch là live_ + tên file cũ
            # Ví dụ: list.m3u -> live_list.m3u | CCTV5.txt -> live_CCTV5.txt
            output_name = f"live_{file_name}"
            process_file(file_name, output_name)

if __name__ == "__main__":
    main()
