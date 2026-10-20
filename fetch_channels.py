import re
import urllib.request

# Web sitelerinden güncellenecek kanallar ve M3U içindeki tam isimleri
TARGET_CHANNELS = {
    "ATV AVRUPA": "https://www.atvavrupa.tv/webtv/canli-yayin",
    "ATV": "https://www.atv.com.tr/canli-yayin",
    "STAR TV": "https://www.startv.com.tr/canli-yayin",
    "EUROSTAR TV": "https://www.eurostartv.com.tr/canli-izle",
    "TGRT Belgesel": "https://www.tgrtbelgesel.com.tr/canli-yayin?play=1"
}

def get_live_m3u8(url):
    """Web sitesinin kaynak kodundan güncel m3u8 linkini çeker."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as response:
            html = response.read().decode('utf-8', errors='ignore')
            matches = re.findall(r'(https?://[^\s\'"]+\.m3u8[^\s\'"]*)', html)
            if matches:
                return matches[0]
    except Exception as e:
        print(f"Hata ({url}): {e}")
    return None

def update_m3u_file(file_path="playlist.m3u"):
    """Mevcut playlist.m3u dosyasını okur, hedef kanalların linkini yeniler."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"{file_path} dosyası bulunamadı!")
        return

    updated_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        updated_lines.append(line)
        
        # #EXTINF satırlarında hedef kanal ismini kontrol et
        if line.startswith("#EXTINF"):
            for channel_name, web_url in TARGET_CHANNELS.items():
                # Virgül sonrası kanal ismini esnek eşleştirme
                if f",{channel_name}" in line or f", {channel_name}" in line:
                    print(f"➜ {channel_name} bulundu, güncel link aranıyor...")
                    new_link = get_live_m3u8(web_url)
                    
                    if new_link and (i + 1) < len(lines):
                        # Bir sonraki satır yayın linkidir, yenisiyle değiştir
                        print(f"✓ {channel_name} güncellendi: {new_link}")
                        updated_lines.append(f"{new_link}\n")
                        i += 1  # Eski link satırını atla
                    else:
                        print(f"✗ {channel_name} için yeni link alınamadı, eski link korundu.")
                    break
        i += 1

    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(updated_lines)

if __name__ == "__main__":
    update_m3u_file()
