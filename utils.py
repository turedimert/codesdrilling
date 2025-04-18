import sqlite3
import traceback
from PyQt6.QtCore import QDateTime
from PyQt6.QtWidgets import QMessageBox

VERITABANI_YOLU = "sondaj_veritabani.db"
LOG_YOLU = "error_log.txt"

def hata_logla(mesaj, exception=None):
    """
    Hata mesajlarını log dosyasına kaydeder.
    
    Args:
        mesaj (str): Log dosyasına kaydedilecek mesaj
        exception (Exception, optional): Yakalanmış hata
    """
    log_mesaj = f"{QDateTime.currentDateTime().toString()} - {mesaj}"
    print(log_mesaj)
    try:
        with open(LOG_YOLU, "a", encoding="utf-8") as f:
            f.write(f"{log_mesaj}\n")
            if exception:
                f.write(f"{traceback.format_exc()}\n\n")
    except Exception as e:
        print(f"Log dosyasına yazma hatası: {str(e)}")

def veritabani_baglantisi():
    """
    SQLite veritabanına bağlantı oluşturur.
    
    Returns:
        sqlite3.Connection: Veritabanı bağlantısı
    """
    try:
        conn = sqlite3.connect(VERITABANI_YOLU)
        conn.row_factory = sqlite3.Row  # Sonuçları sözlük olarak al
        return conn
    except Exception as e:
        hata_logla(f"Veritabanı bağlantı hatası: {str(e)}", e)
        raise

def veritabani_olustur():
    """
    Gerekli veritabanı tablolarını oluşturur (yoksa).
    """
    print("Veritabanı kontrol ediliyor...")
    with sqlite3.connect(VERITABANI_YOLU) as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS Projeler (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            proje_adi TEXT NOT NULL,
                            yuklenici_firma TEXT,
                            sorumlu_muhendis TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS TapuBilgileri (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            proje_id INTEGER,
                            il TEXT,
                            ilce TEXT,
                            mahalle TEXT,
                            ada TEXT,
                            pafta TEXT,
                            parsel TEXT,
                            koordinat_x REAL,
                            koordinat_y REAL,
                            FOREIGN KEY (proje_id) REFERENCES Projeler(id))''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS SondajBilgileri (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            proje_id INTEGER,
                            sondor_adi TEXT,
                            sondaj_kotu REAL,
                            sondaj_derinligi REAL,
                            baslama_tarihi TEXT,
                            bitis_tarihi TEXT,
                            delgi_capi REAL,
                            yer_alti_suyu REAL,
                            ud_ornekleri TEXT,
                            zemin_tipi TEXT,
                            makine_tipi TEXT,
                            spt_sahmerdan_tipi TEXT,
                            FOREIGN KEY (proje_id) REFERENCES Projeler(id))''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS AraziBilgileri (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            proje_id INTEGER,
                            "Sondaj derinliği (m)" REAL,
                            "Muhafaza borusu derinliği" REAL,
                            "Kuyu içi deneyler" TEXT,
                            "Örnek derinliği (m)" TEXT,
                            "Örnek türü ve no." TEXT,
                            "SPT0-15" INTEGER,
                            "SPT15-30" INTEGER,
                            "SPT30-45" INTEGER,
                            "N30" INTEGER,
                            "Tmax" REAL,
                            "TYoğrulmuş" REAL,
                            "C (kpa)" REAL,
                            "Ø(derece)" REAL,
                            "Doğal B.H.A(kN/m3)" REAL,
                            "Kuru B.H.A (kN/m3)" REAL,
                            "Zemin profili" TEXT,
                            "Zemin tanımlaması" TEXT,
                            FOREIGN KEY (proje_id) REFERENCES Projeler(id))''')
        conn.commit()
    print("Veritabanı hazır.")

def tema_sinifi_belirle(is_dark_theme):
    """
    Temaya göre CSS sınıfını döndürür.
    
    Args:
        is_dark_theme (bool): Koyu tema kullanılıyorsa True

    Returns:
        str: CSS sınıf adı
    """
    return "dark-theme" if is_dark_theme else "light-theme"

def hata_goster(parent, baslik, mesaj):
    """
    Hata mesajı gösterir.
    
    Args:
        parent: Ebeveyn pencere
        baslik (str): Mesaj kutusu başlığı
        mesaj (str): Gösterilecek hata mesajı
    """
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Icon.Critical)
    msg_box.setWindowTitle(baslik)
    msg_box.setText(mesaj)
    msg_box.exec()

def bilgi_goster(parent, baslik, mesaj):
    """
    Bilgi mesajı gösterir.
    
    Args:
        parent: Ebeveyn pencere
        baslik (str): Mesaj kutusu başlığı
        mesaj (str): Gösterilecek bilgi mesajı
    """
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Icon.Information)
    msg_box.setWindowTitle(baslik)
    msg_box.setText(mesaj)
    msg_box.exec()

def uyari_goster(parent, baslik, mesaj):
    """
    Uyarı mesajı gösterir.
    
    Args:
        parent: Ebeveyn pencere
        baslik (str): Mesaj kutusu başlığı
        mesaj (str): Gösterilecek uyarı mesajı
    """
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Icon.Warning)
    msg_box.setWindowTitle(baslik)
    msg_box.setText(mesaj)
    msg_box.exec()

def onay_al(parent, baslik, mesaj):
    """
    Kullanıcıdan onay ister.
    
    Args:
        parent: Ebeveyn pencere
        baslik (str): Mesaj kutusu başlığı
        mesaj (str): Gösterilecek mesaj
    
    Returns:
        bool: Kullanıcı onay verdiyse True, aksi halde False
    """
    dialog = QMessageBox(parent)
    dialog.setIcon(QMessageBox.Icon.Question)
    dialog.setWindowTitle(baslik)
    dialog.setText(mesaj)
    dialog.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    dialog.setDefaultButton(QMessageBox.StandardButton.No)
    
    return dialog.exec() == QMessageBox.StandardButton.Yes
