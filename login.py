import os
import sqlite3
import traceback
from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QFormLayout, 
    QHBoxLayout, QCheckBox, QMessageBox, QFrame
)
from PyQt6.QtCore import QDateTime, Qt, QSize
from PyQt6.QtGui import QIcon, QPixmap, QFont

from constants import LOG_YOLU, VERITABANI_YOLU, UYGULAMA_ADI
from utils import hata_logla, bilgi_goster, hata_goster

class GirisEkrani(QWidget):
    """
    Kullanıcı giriş ekranı
    """
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        """Giriş arayüzünü oluşturur"""
        self.setWindowTitle(f"Giriş - {UYGULAMA_ADI}")
        self.setMinimumSize(450, 550)
        self.setWindowFlags(Qt.WindowType.WindowCloseButtonHint | Qt.WindowType.WindowMinimizeButtonHint)
        
        # Ana düzen
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)
        
        # Logo bölümü
        logo_container = QFrame()
        logo_layout = QVBoxLayout(logo_container)
        logo_label = QLabel()
        logo_label.setPixmap(QPixmap("assets/logo.svg").scaled(
            100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        ))
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(logo_label)
        
        # Başlık
        self.baslik_label = QLabel(UYGULAMA_ADI)
        self.baslik_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.baslik_label.setObjectName("header-label")
        logo_layout.addWidget(self.baslik_label)
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Giriş formu
        form_container = QFrame()
        form_container.setObjectName("login-form-container")
        form_layout = QFormLayout(form_container)
        form_layout.setContentsMargins(20, 30, 20, 30)
        form_layout.setSpacing(15)
        
        # Kullanıcı adı
        self.txt_kullanici = QLineEdit()
        self.txt_kullanici.setPlaceholderText("Kullanıcı Adı")
        self.txt_kullanici.setMinimumHeight(40)
        
        # Şifre
        self.txt_sifre = QLineEdit()
        self.txt_sifre.setPlaceholderText("Şifre")
        self.txt_sifre.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_sifre.setMinimumHeight(40)
        
        # Beni hatırla
        self.chk_hatirla = QCheckBox("Beni Hatırla")
        
        # Giriş butonu
        self.btn_giris = QPushButton("Giriş Yap")
        self.btn_giris.setMinimumHeight(45)
        self.btn_giris.setObjectName("success-btn")
        self.btn_giris.clicked.connect(self.giris_yap)
        
        # Form'a öğeleri ekle
        form_layout.addRow("Kullanıcı Adı:", self.txt_kullanici)
        form_layout.addRow("Şifre:", self.txt_sifre)
        form_layout.addRow("", self.chk_hatirla)
        form_layout.addRow(self.btn_giris)
        
        # Alt bilgi
        alt_bilgi = QLabel("© 2023 Tüm Hakları Saklıdır")
        alt_bilgi.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Ana düzene öğeleri ekle
        main_layout.addWidget(logo_container)
        main_layout.addWidget(form_container)
        main_layout.addStretch()
        main_layout.addWidget(alt_bilgi)
        
        self.setLayout(main_layout)
        
        # Kullanıcı adını hatırla
        self.son_kullaniciyi_yukle()
        
    def son_kullaniciyi_yukle(self):
        """Son giriş yapan kullanıcıyı yükler"""
        try:
            if os.path.exists("kullanici.dat"):
                with open("kullanici.dat", "r") as f:
                    kullanici = f.read().strip()
                    if kullanici:
                        self.txt_kullanici.setText(kullanici)
                        self.chk_hatirla.setChecked(True)
        except Exception as e:
            hata_logla(f"Son kullanıcı yükleme hatası: {str(e)}", e)
        
    def giris_yap(self):
        """Kullanıcı girişi işlemi"""
        kullanici_adi = self.txt_kullanici.text()
        sifre = self.txt_sifre.text()
        
        # Basit doğrulama
        if not kullanici_adi or not sifre:
            hata_goster(self, "Giriş Hatası", "Kullanıcı adı ve şifre giriniz!")
            return
        
        # Gerçek uygulamada burada veritabanı doğrulaması yapılır
        # Bu örnek için basit bir kontrol yapıyoruz
        try:
            # Kullanıcıyı kaydet
            if self.chk_hatirla.isChecked():
                with open("kullanici.dat", "w") as f:
                    f.write(kullanici_adi)
            else:
                if os.path.exists("kullanici.dat"):
                    os.remove("kullanici.dat")
            
            # Ana pencereyi aç
            from main_window import AnaPencere  # Burada import etmeliyiz, yoksa döngüsel import olur
            self.ana_pencere = AnaPencere(kullanici_adi)
            self.ana_pencere.show()
            self.close()
            
        except Exception as e:
            hata_logla(f"Giriş hatası: {str(e)}", e)
            hata_goster(self, "Giriş Hatası", f"Beklenmeyen bir hata oluştu: {str(e)}")
