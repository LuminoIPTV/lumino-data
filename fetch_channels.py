import re
import urllib.request

# Güncellenecek kanallar ve resmi canlı yayın web sayfaları
CHANNELS = [
    {
        "name": "ATV",
        "logo": "https://raw.githubusercontent.com/LuminoIPTV/lumino-data/ana/TR/atv.png",
        "group": "TR | Ulusal",
        "url": "https://www.atv.com.tr/canli-yayin"
    },
    {
        "name": "TRT 1",
        "logo": "https://raw.githubusercontent.com/LuminoIPTV/lumino-data/ana/TR/trt1.png",
        "group": "TR | Ulusal",
        "url": "https://www.trt1.com.tr/canli-izle"
    }
]

def get_m3u8_link(page_url):
    try:
        req = urllib.request.Request(
            page_url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
            # HTML kaynak kodunda .m3u8 ile biten linki yakalar
            match = re.search(r'(https?://[^\s\'"]+\.m3u8[^\s\'"]*)', html)
            if match:
                return match.group(1)
    except Exception as e:
        print(f"Hata ({page_url}): {e}")
    return None

def generate_m3u():
    m3u_content = "#EXTM3U\n"
    for ch in CHANNELS:
        print(f"{ch['name']} için link aranıyor...")
        stream_url = get_m3u8_link(ch['url'])
        if stream_url:
            m3u_content += f'#EXTINF:-1 tvg-logo="{ch["logo"]}" group-title="{ch["group"]}",{ch["name"]}\n'
            m3u_content += f'{stream_url}\n'
            print(f"✓ {ch['name']} linki bulundu!")
        else:
            print(f"✗ {ch['name']} linki bulunamadı.")

    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write(m3u_content)

if __name__ == "__main__":
    generate_m3u()
