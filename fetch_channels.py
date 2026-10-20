import re
import urllib.request

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
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7'
        }
        req = urllib.request.Request(page_url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
            # .m3u8 veya master playlist yakalama deseni
            matches = re.findall(r'(https?://[^\s\'"]+\.m3u8[^\s\'"]*)', html)
            if matches:
                # Bulunan ilk veya en uygun m3u8 adresini döndür
                return matches[0]
    except Exception as e:
        print(f"Hata ({page_url}): {e}")
    return None

def generate_m3u():
    m3u_content = "#EXTM3U\n"
    for ch in CHANNELS:
        print(f"{ch['name']} için link taranıyor...")
        stream_url = get_m3u8_link(ch['url'])
        
        if stream_url:
            m3u_content += f'#EXTINF:-1 tvg-logo="{ch["logo"]}" group-title="{ch["group"]}",{ch["name"]}\n'
            m3u_content += f'{stream_url}\n'
            print(f"✓ {ch['name']} linki bulundu: {stream_url}")
        else:
            print(f"✗ {ch['name']} linki bulunamadı.")

    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write(m3u_content)

if __name__ == "__main__":
    generate_m3u()
