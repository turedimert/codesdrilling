# LOOGY - Sondaj Proje Yönetim Uygulaması

## Proje Hakkında
LOOGY, jeolojik ve mühendislik profesyonelleri için tasarlanmış modern bir sondaj projesi yönetim web uygulamasıdır. Gelişmiş veri yakalama, görselleştirme ve interaktif analiz özellikleri sunar.

## Teknik Altyapı
- Flask/Python arka uç
- Duyarlı web arayüzü
- PostgreSQL veritabanı
- Modern web teknolojileri (HTML5, CSS3, JavaScript)
- Bootstrap ve MDI ikonları
- Animasyonlu UI bileşenleri

## Kurulum Adımları

### 1. Gerekli Paketlerin Kurulumu
```bash
# Sanal ortam oluşturma (opsiyonel ama önerilir)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# veya
venv\Scripts\activate  # Windows

# Gereksinimlerin kurulumu
pip install -r requirements.txt
```

### 2. Veritabanı Ayarları
PostgreSQL veritabanı kurulumu yapılmalı ve bağlantı bilgileri çevre değişkenlerinde tanımlanmalıdır:

```bash
# .env dosyası veya çevre değişkenleri olarak aşağıdakileri tanımlayın
export DATABASE_URL="postgresql://kullanici:sifre@localhost:5432/sondaj_db"
export FLASK_SECRET_KEY="gizli_anahtar"
```

### 3. Veritabanı Şemasını Oluşturma
```bash
# Flask-Migrate ile veritabanı oluşturma
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### 4. Uygulamayı Çalıştırma
```bash
# Geliştirme sunucusu
python main.py
```

Uygulama varsayılan olarak http://localhost:5000 adresinde çalışacaktır.

## Özellikler
- Sondaj projelerinin oluşturulması ve yönetimi
- Tapu ve arazi bilgilerinin kaydedilmesi
- Sondaj metrajlarının otomatik oluşturulması (1.5m artışlarla)
- SPT ve UD örneklerinin kaydı
- Analiz grafikleri ve raporlar
- Kullanıcı yönetimi ve yetkilendirme

## Not
Bu uygulama orijinal olarak PyQt6 ile masaüstü uygulaması olarak geliştirilmiş, daha sonra web tabanlı versiyona dönüştürülmüştür. Uygulamanın web sürümünde tüm orijinal işlevsellik korunmuştur.