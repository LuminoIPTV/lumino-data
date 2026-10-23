import urllib.request
import re

# Botun internet istekleri için kullandığı tarayıcı kimliği
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# 1. Aramak istediğimiz Master Liste (Senin istediğin sıra ve büyük harf standartlarında)
MASTER_CHANNELS = [
    # AZERBAYCAN
    "[AZ] CBC TV AZERBAYCAN", "[AZ] CBC SPORT", "[AZ] İCTİMAİ TV", "[AZ] AZTV", 
    "[AZ] XƏZƏR TV", "[AZ] ATV AZERBAYCAN", "[AZ] SPACE TV", "[AZ] ARB TV", 
    "[AZ] ARB SPOR", "[AZ] ARB GÜNƏŞ", "[AZ] REAL TV", "[AZ] BAKU TV", 
    "[AZ] İDMAN TV", "[AZ] MİDİYA TV", "[AZ] BOZBASH PICTURES TV", "[AZ] CTV AZ", 
    "[AZ] CTV SİNEMA", "[AZ] CTV YERLİ", "[AZ] CTV MUSİC", "[AZ] ALVİN CHANNEL TV MİNGƏÇEVİR", 
    "[AZ] QAFQAZ TV", "[AZ] APA TV", "[AZ] KÖNÜL TV", "[AZ] 106.3 FM", "[AZ] TTV", 
    "[AZ] SHOWPLUS TV", "[AZ] KANAL S2 AZ", "[AZ] AZ STAR TV", "[AZ] LİVE TV AZ", 
    "[AZ] AL ZAHRA TV", "[AZ] QARABAQ TV", "[AZ] AZAD SÖZ TV", "[AZ] PAPARAZİ MÜZİK", 
    "[AZ] TMB AZ", "[AZ] SON ÜMİD TV", "[AZ] KANAL ON4", "[AZ] AGRO TV AZERBAYCAN", 
    "[AZ] LİVE TV", "[AZ] KÖNÜL TV 2", "[AZ] QAFQAZ TV 2", "[AZ] VOSTOK TV", 
    "[AZ] KƏPƏZ TV GƏNCƏ", "[AZ] KANAL 35 NAXÇIVAN", "[AZ] NAXÇIVAN TV", "[AZ] AN.T", "[AZ] AZNEWS TV",

    # TÜRKIYE
    "[TR] TRT 1", "[TR] TRT 2", "[TR] TRT 3 TBMM", "[TR] TRT HABER", "[TR] TRT SPOR", 
    "[TR] TRT SPOR YILDIZ", "[TR] TRT ÇOCUK", "[TR] TRT BELGESEL", "[TR] TRT MÜZİK", 
    "[TR] TRT AVAZ", "[TR] TRT TÜRK", "[TR] TRT KURDİ", "[TR] TRT ARABİ", "[TR] SHOW TV", 
    "[TR] SHOW MAX", "[TR] SHOW TÜRK", "[TR] ATV", "[TR] ATV TÜRKİYE", "[TR] A HABER", 
    "[TR] A SPOR", "[TR] A PARA", "[TR] A TARİH", "[TR] STAR TV", "[TR] STAR TV 2", 
    "[TR] KANAL D", "[TR] EURO D", "[TR] CNN TÜRK", "[TR] TV8", "[TR] TV8 BUÇUK", 
    "[TR] TV 8 İNT", "[TR] FOX TV / NOW TV", "[TR] FOX TÜRK", "[TR] KANAL 7", 
    "[TR] KANAL 7 AVRUPA", "[TR] ÜLKE TV", "[TR] 24 TV", "[TR] HABERTÜRK", "[TR] BLOOMBERG HT", 
    "[TR] HABER GLOBAL", "[TR] TGRT HABER", "[TR] TGRT BELGESEL", "[TR] TGRT EU", "[TR] BEYAZ TV", 
    "[TR] A9 TV", "[TR] TVNET", "[TR] EGE TV", "[TR] KONTV", "[TR] KADIRGA TV", 
    "[TR] OLAY TV BURSA", "[TR] TEVE 2", "[TR] DMAX TR", "[TR] TLC TÜRK", "[TR] TMB", 
    "[TR] KRAL TV", "[TR] KRAL POP", "[TR] TATLISES TV", "[TR] NUMBER ONE TV", "[TR] POWER TÜRK", 
    "[TR] DREAM TÜRK", "[TR] FB TV", "[TR] GS TV", "[TR] BJK TV", "[TR] S SPORT 1", "[TR] S SPORT 2",
    "[TR] HALK TV", "[TR] TELE 1", "[TR] KRT TV", "[TR] SÖZCÜ TV",

    # RUSYA EN ÇOK İZLENENLER
    "[RU] PERVIY KANAL", "[RU] ROSSIYA 1", "[RU] NTV", "[RU] MATCH TV", "[RU] STS", 
    "[RU] TNT", "[RU] REN TV", "[RU] DOMASHNIY", "[RU] PYATNITSA", "[RU] TV 3", 
    "[RU] ZVEZDA", "[RU] ROSSIYA 24", "[RU] 5 KANAL", "[RU] TV TSENTR", "[RU] MIR", 
    "[RU] MUZ TV", "[RU] RU TV", "[RU] KINOPOKAZ", "[RU] TV1000 RUSSKOE KINO", "[RU] TV1000 ACTION"
]

# 2. Canlı linklerin taranacağı güvenli açık kaynak havuzları
SOURCE_LISTS = [
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/az.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/tr.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/ru.m3u"
]

def clean_name(name):
    name = re.sub(r'\[.*?\]|\{.*?\}|\(.*?\)', '', name)
    patterns = [r'\b1080p\b', r'\b720p\b', r'\b4K\b', r'\bHD\b', r'\bSD\b', r'\bFHD\b', r'\|']
    for p in patterns:
        name = re.sub(p, '', name, flags=re.IGNORECASE)
    return ' '.join(name.split()).upper()

def main():
    found_channels = {}

    # Açık kaynaklardan mevcut aktif linkleri çek ve sözlüğe kaydet
    for url in SOURCE_LISTS:
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=10) as response:
                content = response.read().decode('utf-8', errors='ignore')
                lines = content.splitlines()
                current_name = ""
                for line in lines:
                    if line.startswith("#EXTINF:"):
                        match = re.search(r',(.+)$', line)
                        if match:
                            current_name = clean_name(match.group(1))
                    elif line.startswith("http") and current_name:
                        found_channels[current_name] = line.strip()
                        current_name = ""
        except Exception as e:
            print(f"Kaynak okunamadı ({url}): {e}")

    # 3. Master listeyi tara, bulunanları eşleştir, bulunamayanlara [LINK_BURAYA] yaz
    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for master_item in MASTER_CHANNELS:
            # Örn: "[AZ] CBC SPORT" -> ismini ayıkla: "CBC SPORT"
            clean_lookup_name = clean_name(master_item.split(']', 1)[1])
            
            # Eğer havuzda bu kanalın çalışan linki varsa onu yaz, yoksa [LINK_BURAYA] bırak
            stream_link = found_channels.get(clean_lookup_name, "[LINK_BURAYA]")
            
            f.write(f"#EXTINF:-1,{master_item}\n")
            f.write(f"{stream_link}\n")

    print("İşlem tamamlandı! playlist.m3u dosyası güncellendi.")

if __name__ == "__main__":
    main()
