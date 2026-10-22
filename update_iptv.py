import urllib.request
import re
import concurrent.futures

# Standart iptv-org mənbələri və əlavə etmək istədiyin xüsusi saytlar/linklər buraya yazılacaq
SOURCES = {
    "AZ": "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/az.m3u",
    "TR": "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/tr.m3u",
    "RU": "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/ru.m3u"
}

# Sayt sahibini narahat etməmək və əsl brauzer kimi görünmək üçün User-Agent başlığı
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7'
}

def clean_channel_name(name):
    # Köşeli, süslü və normal parantez içindəki hər şeyi təmizlə: [], {}, ()
    name = re.sub(r'\[.*?\]|\{.*?\}|\(.*?\)', '', name)
    
    # İstənməyən çözünürlük və sözləri təmizlə
    patterns = [
        r'\b1440p\b', r'\b1080p\b', r'\b720p\b', r'\b576p\b', r'\b480p\b', 
        r'\b4K\b', r'\bHD\b', r'\bSD\b', r'\bFHD\b', r'\bHEVC\b',
        r'\b7/24\b', r'\bGeo\s*Blocked\b', r'\bNot\b', r'\|'
    ]
    
    for pattern in patterns:
        name = re.sub(pattern, '', name, flags=re.IGNORECASE)
        
    name = re.sub(r'\s*-\s*', ' - ', name)
    return ' '.join(name.split())

def test_link(url):
    # Linkin işləyib-işləmədiyini təbii şəkildə yoxla (3 saniyə zaman aşımı)
    try:
        req = urllib.request.Request(url, headers=HEADERS)
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

def fetch_custom_site(url, channel_name, country_code):
    # Xüsusi saytlardan (məsələn canlitvvolo) gizli və təbii şəkildə axın linkini çəkmək üçün funksiya
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=5) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
            # Saytın kodları içində m3u8 axın ünvanını axtarırıq
            m3u8_matches = re.findall(r'https?://[^\s<>"]+?\.m3u8[^\s<>"]*', html)
            if m3u8_matches:
                stream_url = m3u8_matches[0]
                final_name = f"[{country_code}] {channel_name}"
                return (final_name, stream_url)
    except Exception as e:
        print(f"Xüsusi saytdan çəkilə bilmədi {url}: {e}")
    return None

def main():
    all_channels = []
    
    # 1. Standart mənbələri endir
    for code in ["AZ", "TR", "RU"]:
        url = SOURCES[code]
        print(f"{code} listəsi endirilir...")
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req) as response:
                content = response.read().decode('utf-8')
                parsed = parse_m3u(content, code)
                all_channels.extend(parsed)
        except Exception as e:
            print(f"{code} endirilə bilmədi: {e}")

    # 2. Əlavə etmək istədiyin xüsusi saytları burada manual olaraq əlavə edə bilərik
    # Məsələn: CBC Sport üçün
    custom_sites = [
        ("https://tv.canlitvvolo.com/cbc-sport-az-izle/", "CBC Sport", "AZ")
    ]
    
    for site_url, name, code in custom_sites:
        print(f"Xüsusi sayt yoxlanılır: {name}...")
        custom_channel = fetch_custom_site(site_url, name, code)
        if custom_channel:
            all_channels.append(custom_channel)

    print(f"Ümumi {len(all_channels)} kanal tapıldı. İşləmə testləri aparılır...")

    # 3. İşlək olmayan linkləri filtrdən keçir
    valid_channels = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_to_channel = {executor.submit(test_link, ch[1]): ch for ch in all_channels}
        for future in concurrent.futures.as_completed(future_to_channel):
            ch = future_to_channel[future]
            if future.result():
                valid_channels.append(ch)

    print(f"Testlər tamamlandı. İşlək kanal sayı: {len(valid_channels)}")

    # 4. playlist.m3u faylına yaz
    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for name, url in valid_channels:
            f.write(f'#EXTINF:-1,{name}\n')
            f.write(f'{url}\n')

    print("playlist.m3u uğurla yeniləndi!")

if __name__ == "__main__":
    main()
