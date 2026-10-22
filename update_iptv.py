import re
import time
from playwright.sync_api import sync_playwright

# Avtomatik link çəkiləcək saytların siyahısı
# Format: ("Sayt Linki", "Kanal Adı", "Ölkə Kodu")
TARGET_SITES = [
    ("https://tv.canlitvvolo.com/cbc-sport-az-izle/", "CBC Sport", "AZ"),
    # Başqa kanalları buraya əlavə edə bilərsən:
    # ("https://tv.canlitvvolo.com/ictimai-tv-izle/", "İctimai TV", "AZ"),
    # ("https://tv.canlitvvolo.com/xezer-tv-canli-izle/", "Xəzər TV", "AZ"),
]

def clean_channel_name(name):
    # Parantez içindəki hər şeyi təmizlə: [], {}, ()
    name = re.sub(r'\[.*?\]|\{.*?\}|\(.*?\)', '', name)
    
    # Lazımsız sözləri və çözünürlükləri təmizlə
    patterns = [
        r'\b1440p\b', r'\b1080p\b', r'\b720p\b', r'\b576p\b', r'\b480p\b', 
        r'\b4K\b', r'\bHD\b', r'\bSD\b', r'\bFHD\b', r'\bHEVC\b',
        r'\b7/24\b', r'\bGeo\s*Blocked\b', r'\bNot\b', r'\|',
        r'\bcanlı\b', r'\bizle\b', r'\bcanli\b', r'\btv\b'
    ]
    for pattern in patterns:
        name = re.sub(pattern, '', name, flags=re.IGNORECASE)
        
    name = re.sub(r'\s*-\s*', ' ', name)
    return ' '.join(name.split()).strip().title()

def capture_stream_from_site(page, url):
    captured_links = []

    # Şəbəkə trafikini (Network) izləyən funksiya (API və M3U8 tutucu)
    def handle_response(response):
        req_url = response.url
        # Həm birbaşa m3u8 linklərini, həm də axın ehtiva edən API sorğularını yoxla
        if ".m3u8" in req_url or "stream" in req_url or "playlist" in req_url:
            if not req_url.endswith(".ts") and req_url not in captured_links:
                # Əgər cavab JSON formatındadırsa, içindəki linki oxumağa çalış
                try:
                    if "application/json" in response.headers.get("content-type", ""):
                        data = response.json()
                        # JSON içində link ola biləcək açarları yoxla
                        for key in ["url", "stream", "file", "link", "src"]:
                            if key in data and isinstance(data[key], str) and ".m3u8" in data[key]:
                                if data[key] not in captured_links:
                                    captured_links.append(data[key])
                except:
                    pass
                
                # Əgər birbaşa m3u8 linkidirsə əlavə et
                if ".m3u8" in req_url and req_url not in captured_links:
                    captured_links.append(req_url)

    page.on("response", handle_response)

    try:
        # Sayta real brauzer kimi daxil ol
        page.goto(url, wait_until="networkidle", timeout=20000)
        # Pleyerin tam yüklənməsi və API sorğularının işə düşməsi üçün qısa gözləmə
        page.wait_for_timeout(6000)
        
        # Əgər şəbəkədən birbaşa tutulmadısa, səhifənin mənbə kodunu skan et
        if not captured_links:
            content = page.content()
            matches = re.findall(r'https?://[^\s"\'<>]+?\.m3u8[^\s"\'<>]*', content)
            for m in matches:
                clean_m = m.replace('\\/', '/')
                if clean_m not in captured_links:
                    captured_links.append(clean_m)
                    
    except Exception as e:
        print(f"Xəta baş verdi ({url}): {e}")

    page.remove_listener("response", handle_response)
    return captured_links[0] if captured_links else None

def main():
    valid_channels = []

    with sync_playwright() as p:
        # Sayt tərəfindən bot kimi tanınmamaq üçün gizli brauzer konfiqurasiyası
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1366, "height": 768}
        )
        page = context.new_page()

        print(f"Ümumi {len(TARGET_SITES)} sayt taranır...")
        
        for site_url, raw_name, code in TARGET_SITES:
            clean_name = clean_channel_name(raw_name)
            if not clean_name:
                clean_name = "Kanal"
            
            print(f"Yoxlanılır: [{code}] {clean_name} -> {site_url}")
            stream_url = capture_stream_from_site(page, site_url)
            
            if stream_url:
                print(f"  [+] Uğurlu! Link tapıldı: {stream_url}")
                final_name = f"[{code}] {clean_name}"
                valid_channels.append((final_name, stream_url, site_url))
            else:
                print(f"  [-] Link tapılmadı: {site_url}")

            time.sleep(2) # Sayt serverini yormamaq üçün təbii fasilə

        browser.close()

    # Köhnə siyahını tamamilə təmizləyib ("w" rejimi) tapılan yenilərini yazırıq
    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for name, stream_url, ref_url in valid_channels:
            f.write(f'#EXTINF:-1,{name}\n')
            f.write(f'#EXTVLCOPT:http-referrer={ref_url}\n')
            f.write(f'{stream_url}\n')

    print(f"Proses tamamlandı! {len(valid_channels)} kanal playlist.m3u faylına yazıldı.")

if __name__ == "__main__":
    main()
