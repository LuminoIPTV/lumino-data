import re
import time
from playwright.sync_api import sync_playwright

# Çəkiləcək kanalların siyahısı: ("Sayt Linki", "Kanal Adı", "Ölkə Kodu")
# Buraya istədiyin qədər kanal səhifəsi əlavə edə bilərsən
CUSTOM_CHANNELS = [
    ("https://tv.canlitvvolo.com/cbc-sport-az-izle/", "CBC Sport", "AZ"),
    # Başqa kanalları bura alt-alta əlavə edə bilərsən:
    # ("https://tv.canlitvvolo.com/ictimai-tv-izle/", "İctimai TV", "AZ"),
    # ("https://tv.canlitvvolo.com/xezer-tv-canli-izle/", "Xəzər TV", "AZ"),
]

# Əgər saytın bir kateqoriya səhifəsindəki bütün kanalları avtomatik axtarmaq istəyirsənsə:
CATEGORY_URLS = [
    ("https://tv.canlitvvolo.com/azerbaycan-kanallari/", "AZ")
]

def clean_channel_name(name):
    # Parantez içindəki hər şeyi sil: [], {}, ()
    name = re.sub(r'\[.*?\]|\{.*?\}|\(.*?\)', '', name)
    
    # İstənməyən ifadələri sil
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

def extract_m3u8_from_page(page, url):
    found_m3u8 = []

    # Şəbəkə (Network) trafikini dinləyən funksiya (HLS Downloader məntiqi)
    def handle_request(request):
        req_url = request.url
        if ".m3u8" in req_url and not req_url.endswith(".ts"):
            if req_url not in found_m3u8:
                found_m3u8.append(req_url)

    page.on("request", handle_request)

    try:
        # Sayta daxil ol və şəbəkə sorğularının düşməsi üçün gözlə
        page.goto(url, wait_until="domcontentloaded", timeout=15000)
        
        # Bəzi pleyerlər klikləmədən və ya iframe yüklənmədən m3u8 vermir, 5 saniyə gözləyirik
        page.wait_for_timeout(5000)
        
        # Əgər hələ də tapılmayıbsa, səhifənin HTML və iframe kodlarında axtar
        if not found_m3u8:
            content = page.content()
            matches = re.findall(r'https?://[^\s"\'<>]+?\.m3u8[^\s"\'<>]*', content)
            for m in matches:
                found_m3u8.append(m.replace('\\/', '/'))
                
            for frame in page.frames:
                try:
                    f_content = frame.content()
                    f_matches = re.findall(r'https?://[^\s"\'<>]+?\.m3u8[^\s"\'<>]*', f_content)
                    for m in f_matches:
                        found_m3u8.append(m.replace('\\/', '/'))
                except:
                    pass
    except Exception as e:
        print(f"Səhifə yüklənərkən xəta ({url}): {e}")

    page.remove_listener("request", handle_request)
    return found_m3u8[0] if found_m3u8 else None

def main():
    valid_channels = []
    visited_urls = set()

    with sync_playwright() as p:
        # Sayt sahibinin botu hiss etməməsi üçün gerçək brauzer parametrləri
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1366, "height": 768}
        )
        page = context.new_page()

        # 1. Kateqoriya səhifələrindən kanal linklərini avtomatik toplamağa çalış
        for cat_url, code in CATEGORY_URLS:
            print(f"Kateqoriya yoxlanılır: {cat_url}")
            try:
                page.goto(cat_url, wait_until="domcontentloaded", timeout=15000)
                page.wait_for_timeout(2000)
                links = page.query_selector_all("a")
                for link in links:
                    href = link.get_attribute("href")
                    title = link.inner_text() or link.get_attribute("title") or ""
                    if href and "-izle" in href and href.startswith("http"):
                        if href not in [c[0] for c in CUSTOM_CHANNELS]:
                            CUSTOM_CHANNELS.append((href, title, code))
            except Exception as e:
                print(f"Kateqoriya oxuna bilmədi: {e}")

        # 2. Bütün kanalları tək-tək gəz və m3u8 linkini tut
        print(f"Ümumi {len(CUSTOM_CHANNELS)} kanal səhifəsi yoxlanılacaq...")
        
        for site_url, raw_name, code in CUSTOM_CHANNELS:
            if site_url in visited_urls:
                continue
            visited_urls.add(site_url)

            clean_name = clean_channel_name(raw_name)
            if not clean_name:
                clean_name = "Kanal"
            
            print(f"Yoxlanılır: [{code}] {clean_name} -> {site_url}")
            stream_url = extract_m3u8_from_page(page, site_url)
            
            if stream_url:
                print(f"  [+] Uğurlu! M3U8 tapıldı: {stream_url}")
                final_name = f"[{code}] {clean_name}"
                # Köhnə pleyerlərdə referer problemi olmaması üçün
                valid_channels.append((final_name, stream_url, site_url))
            else:
                print(f"  [-] Tapılmadı: {site_url}")

            # Sayt sahibinin şübhələnməməsi üçün hər kanal arasında 2 saniyə təbii fasilə
            time.sleep(2)

        browser.close()

    # 3. Köhnə siyahını sil və yenisini yaz
    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for name, stream_url, ref_url in valid_channels:
            f.write(f'#EXTINF:-1,{name}\n')
            # Bəzi saytların m3u8 linki yalnız öz saytından gələn sorğuya (Referer) icazə verir:
            f.write(f'#EXTVLCOPT:http-referrer={ref_url}\n')
            f.write(f'{stream_url}\n')

    print(f"Tamamlandı! Ümumi {len(valid_channels)} işlək kanal playlist.m3u faylına yazıldı.")

if __name__ == "__main__":
    main()
