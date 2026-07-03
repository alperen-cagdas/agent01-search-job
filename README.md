# İş Radarı — Günlük Otomatik İş Arama

Alperen Çağdaş'ın CV profiline göre kariyer.net ve Indeed'den günlük olarak ilan toplayan,
puanlayan ve tek sayfalık bir sitede (GitHub Pages) yayınlayan otomasyon.

## Nasıl çalışır

1. Her gün 08:00 (TR saati) GitHub Actions `scraper/pipeline.py`'yi çalıştırır.
2. `config/profile.yaml`'daki rol/beceri/lokasyon anahtar kelimelerine göre kariyer.net
   (nazik/rate-limited tarama) ve Indeed (RSS) sorgulanır.
3. Sonuçlar `scraper/scoring.py`'deki ağırlıklı anahtar kelime modeline göre puanlanır,
   eşik altındakiler elenir.
4. `data/latest.json` güncellenir (bir kaynak tamamen başarısız olursa dosya üzerine
   yazılmaz — site son geçerli veriyi göstermeye devam eder), `data/history/` altına
   günlük arşiv eklenir.
5. `index.html` bu JSON'ları `fetch()` ile okuyup render eder. Ayrıca `data/companies.json`
   (doğrudan başvurulabilecek firmalar) ve `data/linkedin_links.json` (LinkedIn hazır arama
   linkleri — LinkedIn otomatik taranmaz, ToS gereği) statik olarak gösterilir.

## LinkedIn neden otomatik taranmıyor

LinkedIn kullanım şartları her türlü otomatik veri toplamayı (crawler/bot/scraping)
açıkça yasaklıyor ve 2025-2026'da yaptırımlar sertleşti (kalıcı hesap banları, scraping
sağlayıcılarına açılan davalar). Bu risk kabul edilebilir olmadığından, bunun yerine
`data/linkedin_links.json` içinde hazır arama linkleri üretiliyor — elle tıklanır.

## Yerel geliştirme / test

```bash
pip install -r requirements.txt
python -m scraper.pipeline      # data/latest.json'u günceller
python -m http.server           # siteyi http://localhost:8000 üzerinde açar
```

## kariyer.net scraper'ı hakkında önemli not

`scraper/source_kariyer.py` içindeki arama URL'si ve CSS selector'ları, bu proje
geliştirilirken canlı olarak doğrulanamadı (geliştirme ortamının ağ politikası
kariyer.net'e erişimi engelliyordu). İlk çalıştırmadan sonra loglarda
`"kariyer.net: 0 listings parsed"` uyarısı görürsen, gerçek bir arama sonucunu
tarayıcıda inceleyip dosyanın başındaki `CARD_SELECTOR` / `TITLE_SELECTOR` /
`COMPANY_SELECTOR` / `LOCATION_SELECTOR` sabitlerini güncellemen gerekir. Bu durumda
bile Indeed sonuçları etkilenmeden yayınlanmaya devam eder.

## Tek seferlik kurulum adımları

1. Repo ayarlarından **public** yap (Settings → General → Danger Zone → Change visibility).
2. Settings → Pages → Source = **GitHub Actions**.
3. Actions sekmesinden `Daily Job Search` workflow'unu `workflow_dispatch` ile bir kez
   manuel çalıştırıp loglara ve yayınlanan siteye bak.

## Listeleri güncelleme

- `data/companies.json`: doğrudan başvurulabilecek firmalar — elle düzenle.
- `data/linkedin_links.json`: LinkedIn arama linkleri — elle düzenle.
- `config/profile.yaml`: arama anahtar kelimeleri ve puanlama ağırlıkları.
- 
