import urllib.request
import re
import concurrent.futures

# Kaynak m3u linkleri (Ham/Raw formatlar)
SOURCES = {
    "AZ": "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/az.m3u",
    "TR": "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/tr.m3u",
    "RU": "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/ru.m3u"
}

def clean_channel_name(name):
    # 1. Köşeli parantez, süslü parantez ve normal parantez içindekileri tamamen kaldır: [], {}, ()
    name = re.sub(r'\[.*?\]|\{.*?\}|\(.*?\)', '', name)
    
    # 2. Kaldırılacak kelimeler ve çözünürlük kalıpları (Büyük/küçük harf duyarsız)
    patterns = [
        r'\b1440p\b', r'\b1080p\b', r'\b720p\b', r'\b576p\b', r'\b480p\b', 
        r'\b4K\b', r'\bHD\b', r'\bSD\b', r'\bFHD\b', r'\bHEVC\b',
        r'\b7/24\b', r'\bGeo\s*Blocked\b', r'\bNot\b', r'\|'
    ]
    
    for pattern in patterns:
        name = re.sub(pattern, '', name, flags=re.IGNORECASE)
        
    # 3. Kalan fazlalık tire, nokta veya boşlukları düzenle
    name = re.sub(r'\s*-\s*', ' - ', name) # Tire etrafındaki boşlukları dengele
    return ' '.join(name.split())

def test_link(url):
    # Linkin çalışıp çalışmadığını test et (3 saniye zaman aşımı)
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as response:
            if response.status == 200:
                return True
    except:
        pass
    return False

def parse_m3u(content, country_code):
    lines = content.splitlines()
    channels = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF:"):
            parts = line.split(',', 1)
            if len(parts) > 1:
                raw_name = parts[1]
                clean_name = clean_channel_name(raw_name)
                final_name = f"[{country_code}] {clean_name}"
                
                if i + 1 < len(lines):
                    url_line = lines[i + 1].strip()
                    if not url_line.startswith("#"):
                        channels.append((final_name, url_line))
        i += 1
    return channels

def main():
    all_channels = []
    
    for code in ["AZ", "TR", "RU"]:
        url = SOURCES[code]
        print(f"{code} listesi indiriliyor...")
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                content = response.read().decode('utf-8')
                parsed = parse_m3u(content, code)
                all_channels.extend(parsed)
        except Exception as e:
            print(f"{code} indirilemedi: {e}")

    print(f"Toplam {len(all_channels)} kanal bulundu. Çalışma testleri yapılıyor...")

    valid_channels = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_to_channel = {executor.submit(test_link, ch[1]): ch for ch in all_channels}
        for future in concurrent.futures.as_completed(future_to_channel):
            ch = future_to_channel[future]
            if future.result():
                valid_channels.append(ch)

    print(f"Testler tamamlandı. Çalışan kanal sayısı: {len(valid_channels)}")

    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for name, url in valid_channels:
            f.write(f'#EXTINF:-1,{name}\n')
            f.write(f'{url}\n')

    print("playlist.m3u başarıyla güncellendi!")

if __name__ == "__main__":
    main()
