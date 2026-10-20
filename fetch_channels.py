import re
import urllib.request

# Hedef kanallar, M3U içindeki isimleri ve çekilecek web siteleri
TARGETS = [
    {"name": "ATV AVRUPA", "url": "https://www.atvavrupa.tv/webtv/canli-yayin"},
    {"name": "ATV", "url": "https://www.atv.com.tr/canli-yayin"},
    {"name": "STAR TV", "url": "https://www.startv.com.tr/canli-yayin"},
    {"name": "EUROSTAR TV", "url": "https://www.eurostartv.com.tr/canli-izle"},
    {"name": "TGRT Belgesel", "url": "https://www.tgrtbelgesel.com.tr/canli-yayin?play=1"}
]

def fetch_m3u8(url):
    """Web sitesinin HTML kaynak kodundan m3u8 linkini arar."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': '*/*'
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            # m3u8 içeren URL'leri yakala
            found = re.findall(r'(https?://[^\s\'"]+\.m3u8[^\s\'"]*)', html)
            if found:
                return found[0]
    except Exception as e:
        print(f"Hata ({url}): {e}")
    return None

def main():
    file_path = "playlist.m3u"
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"{file_path} bulunamadı!")
        return

    # Canlı linkleri önceden toplayalım
    live_links = {}
    for t in TARGETS:
        print(f"🔍 {t['name']} için web sitesi taranıyor...")
        link = fetch_m3u8(t['url'])
        if link:
            live_links[t['name']] = link
            print(f"   ✓ Bulundu: {link}")
        else:
            print(f"   ✗ Bulunamadı!")

    new_lines = []
    skip_next = False

    for i, line in enumerate(lines):
        if skip_next:
            skip_next = False
            continue

        new_lines.append(line)

        if line.startswith("#EXTINF"):
            for name, new_url in live_links.items():
                # Kanal adının satır sonunda veya virgül sonrasında geçtiğini doğrula
                if line.strip().endswith(name) or f",{name}" in line or f", {name}" in line:
                    # Bir sonraki satır linktir, onu yeni linkle değiştir
                    if i + 1 < len(lines):
                        new_lines.append(f"{new_url}\n")
                        skip_next = True
                        print(f"⚡ M3U Güncellendi: {name}")
                    break

    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

if __name__ == "__main__":
    main()
