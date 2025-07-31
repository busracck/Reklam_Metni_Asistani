import csv
import random
from datetime import datetime, timedelta
from faker import Faker # type: ignore # Faker kütüphanesini kullanmak için pip install Faker yapmanız gerekebilir

fake = Faker()

# Kategorik sütunlar için olası değerleri tanımlayın
platforms = ["Instagram", "Facebook"] # Sadece Instagram ve Facebook olarak güncellendi
genders = ["Kadın", "Erkek"] # Zaten doğruydu, teyit edildi
impression_devices = ["ipad", "iphone", "android", "desktop", "other"] # Belirtilen cihazlar olarak güncellendi
campaign_names = [
    "TR-17.06-Web Sitesi",
    "-17.06-Web Sitesi",
    "-13.06-Bilinirlik",
    "TR-13.06-Arama",
    "TR-13.06-Dönüşüm",
    "Global-Marka-Farkındalığı", 
    "AB-Yeni-Ürün-Lansmanı",
    "TR-Yaz-Kampanyası",
    "US-Mobil-Uygulama"
]
regions = [
    "Şamotokrzyski Voyvodalığı",
    "Ile-de-France",
    "Łódź Voyvodalığı",
    "Bilinmiyor", 
    "İzmir İli",
    "İstanbul", 
    "Ankara",
    "Berlin",
    "Londra",
    "New York"
]

# Looker Studio alanlarına göre TÜRKÇE başlıkları tanımlayın
header = [
    "Platform",
    "Tarih",
    "Kampanya Adı",
    "Cinsiyet",
    "Gösterim Cihazı",
    "Bölge",
    "Gösterimler",
    "Tüm Tıklamalar",
    "Harcanan Tutar",
    "Erişim",
    "Frekans"
]

# Oluşturulacak satır sayısı (veri setinin büyüklüğü)
num_rows = 2000 # 2000 satır, dashboard'daki özetleri oluşturmak için yeterli olmalı

# Veri oluşturma
data = []
for _ in range(num_rows):
    platform = random.choice(platforms)
    
    # Son 90 gün içinde rastgele tarihler
    start_date = datetime.now() - timedelta(days=90)
    end_date = datetime.now()
    date = fake.date_between(start_date=start_date, end_date=end_date).strftime("%Y-%m-%d")

    # Kampanya isimleri için ağırlıklı seçim
    campaign = random.choices(campaign_names, weights=[0.1, 0.1, 0.15, 0.15, 0.15, 0.1, 0.1, 0.075, 0.075], k=1)[0]
    
    # Cinsiyet dağılımı (pasta grafiğe göre erkek ~%70, kadın ~%30)
    gender = random.choices(genders, weights=[0.286, 0.714], k=1)[0] 
    
    # Cihaz dağılımı (iPhone gösterimleri Android tabletten daha yüksek, yeni listeye göre ağırlıklar ayarlandı)
    # ipad, iphone, android, desktop, other
    device = random.choices(impression_devices, weights=[0.15, 0.35, 0.25, 0.15, 0.10], k=1)[0] 
    
    # Bölge dağılımı
    region = random.choices(regions, weights=[0.08, 0.08, 0.15, 0.1, 0.15, 0.15, 0.1, 0.07, 0.07, 0.05], k=1)[0]

    # Gösterim (Impressions), Tıklama (Clicks), Harcama (Amount Spent), Erişim (Reach), Frekans (Frequency) simülasyonu
    base_impressions = random.randint(500, 15000) # Temel gösterim aralığı
    
    # Cinsiyete göre gösterim ayarlaması
    if gender == "Erkek": # Türkçe cinsiyet kullanıldı
        impressions = base_impressions * random.uniform(1.8, 2.5) # Erkekler daha fazla gösterim alsın
    else: # Kadın
        impressions = base_impressions * random.uniform(0.8, 1.2) # Kadınlar daha az veya temel seviyede
    
    impressions = int(impressions) # Tam sayıya yuvarla

    # Tıklamalar: Gösterimlerin yaklaşık %0.5 ila %3'ü
    clicks_all = int(impressions * random.uniform(0.005, 0.03))
    if clicks_all < 0: clicks_all = 0 # Negatif tıklama olmasın

    # Harcama: Tıklamalara ve gösterimlere bağlı olarak değişsin
    amount_spent = round(clicks_all * random.uniform(0.1, 1.5) + random.uniform(0, 50), 2)
    if amount_spent < 0: amount_spent = 0 # Negatif harcama olmasın

    # Erişim: Genellikle gösterimlerden biraz daha azdır
    reach = int(impressions * random.uniform(0.7, 0.98))
    if reach > impressions: reach = impressions # Erişim gösterimden fazla olamaz

    # Frekans: Gösterim / Erişim (Erişim 0 ise rastgele bir değer)
    frequency = round(impressions / reach if reach > 0 else random.uniform(1.0, 2.5), 2)
    if frequency < 1.0: frequency = round(random.uniform(1.0, 1.5), 2) # Frekans 1'den küçük olamaz

    data.append([
        platform,
        date,
        campaign,
        gender,
        device,
        region,
        impressions,
        clicks_all,
        amount_spent,
        reach,
        frequency
    ])

# CSV dosyasına kaydet
csv_path = "adresgezgini_meta_veri_raporu_turkce.csv" # Dosya adı güncellendi
with open(csv_path, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(header)
    writer.writerows(data)

print(f"'{csv_path}' dosyası başarıyla oluşturuldu.")
print("Bu dosya, Looker Studio raporunuzdaki verilere benzer sentetik veriler içermektedir ve başlıkları Türkçedir.")
