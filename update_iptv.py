import urllib.request
import re
import concurrent.futures

# Sayt sahibinə təbii görünmək və bloklanmamaq üçün brauzər başlığı
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

def fetch_custom_site(url, channel_name, country_code):
    # Xüsusi saytlardan gizli və təbii şəkildə axın linkini çəkmək üçün funksiya
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=5) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
            # Saytın kodları içində m3u8 axın ünvanını axtarırıq
            m3u8_matches = re.findall(r'https?://[^\s<>"]+?\.m3u8[^\s<>"]*', html)
            if m3u8_matches:
                stream_url = m3u8_matches[0]
                clean_name = clean_channel_name(channel_name)
                final_name = f"[{country_code}] {clean_name}"
                return (final_name, stream_url)
    except Exception as e:
        print(f"Xüsusi saytdan çəkilə bilmədi {url}: {e}")
    return None

def main():
    all_channels = []
    
    # Bütün kanalları çəkmək istədiyin xüsusi saytların siyahısı
    # Format: ("Sayt Linki", "Kanal Adı", "Ölkə Kodu [AZ, TR, RU]")
    custom_sites = [
        ("https://tv.canlitvvolo.com/cbc-sport-az-izle/", "CBC Sport", "AZ"),
        # Əlavə etmək istədiyin digər saytları bura alt-alta yaza bilərsən:
        # ("https://ornek-sayt.com/kanal", "Kanal Adi", "TR"),
    ]
    
    print("Xüsusi saytlardan axın linkləri çəkilir...")
    for site_url, name, code in custom_sites:
        custom_channel = fetch_custom_site(site_url, name, code)
        if custom_channel:
            all_channels.append(custom_channel)

    print(f"Ümumi {len(all_channels)} kanal tapıldı. İşləmə testləri aparılır...")

    # İşlək olmayan linkləri filtrdən keçir
    valid_channels = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_to_channel = {executor.submit(test_link, ch[1]): ch for ch in all_channels}
        for future in concurrent.futures.as_completed(future_to_channel):
            ch = future_to_channel[future]
            if future.result():
                valid_channels.append(ch)

    print(f"Testlər tamamlandı. İşlək kanal sayı: {len(valid_channels)}")

    # "w" rejimi köhnə faylı tamamilə silib hər dəfə sıfırdan təzə siyahı yazır
    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for name, url in valid_channels:
            f.write(f'#EXTINF:-1,{name}\n')
            f.write(f'{url}\n')

    print("playlist.m3u sıfırdan uğurla yeniləndi!")

if __name__ == "__main__":
    main()
