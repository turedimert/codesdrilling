import sys
import os
import sqlite3
import traceback
from functools import partial
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QTabWidget, QFormLayout, QHBoxLayout,
    QDateEdit, QComboBox, QTableWidget, QTableWidgetItem, QMessageBox, QCheckBox, QInputDialog, QProgressBar,
    QGroupBox, QSplitter, QToolBar, QStatusBar, QMenu, QFileDialog, QFrame, QStackedWidget
)
from PyQt6.QtCore import QDate, Qt, QDateTime, QSize, QTimer
from PyQt6.QtGui import QDoubleValidator, QFont, QIcon, QAction, QPixmap

from constants import VERITABANI_YOLU, LOG_YOLU, UYGULAMA_ADI
from utils import (
    hata_logla, bilgi_goster, hata_goster, uyari_goster, onay_al, 
    veritabani_baglantisi, tema_sinifi_belirle
)
from widgets import (
    ProjectCardWidget, TapuFormWidget, SondajFormWidget, AraziFormWidget,
    ProjectTableWidget, StatusIndicator
)
from dialogs import (
    YeniProjeDialog, ProjeDetayDialog, RaporDialog
)
from visualization import SondajGrafikWidget
from report_generator import SondajRaporuOlusturucu

class AnaPencere(QMainWindow):
    def __init__(self, kullanici_adi):
        super().__init__()
        self.kullanici_adi = kullanici_adi
        self.mevcut_proje_id = None
        self.mevcut_proje_adi = None
        self.is_dark_theme = False
        self.is_data_changed = False
        self.status_timer = None
        self.unsaved_changes = False
        
        hata_logla("Ana pencere başlatılıyor")
        try:
            self.initUI()
            hata_logla("Ana pencere UI oluşturuldu")
        except Exception as e:
            hata_logla(f"Ana pencere başlatma hatası: {str(e)}", e)
            QMessageBox.critical(None, "Kritik Hata", f"Uygulama başlatılamadı: {str(e)}")
            raise
            
    def initUI(self):
        """Ana pencere arayüzünü oluşturur"""
        self.setWindowTitle(f"{UYGULAMA_ADI} - Hoşgeldiniz {self.kullanici_adi}")
        self.setMinimumSize(1200, 800)
        
        # Ana widget oluştur
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Durum çubuğu oluştur
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Durum göstergesi
        self.status_indicator = StatusIndicator()
        self.status_bar.addPermanentWidget(self.status_indicator)
        
        # Araç çubuğu oluştur
        self.create_toolbar()
        
        # Sekme widget'ı oluştur
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.tabs.setDocumentMode(True)
        
        # Sekmeleri oluştur
        self.create_dashboard_tab()
        self.create_project_tab()
        self.create_analysis_tab()
        
        # Ana düzene ekle
        self.main_layout.addWidget(self.tabs)
        
        # Veri yükle
        self.projeleri_yukle()
        
        # Durum çubuğunu güncelleme zamanlayıcısı
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_statusbar)
        self.status_timer.start(5000)  # 5 saniyede bir güncelle
        
        # Başlangıç durumu
        self.update_statusbar("Hazır")
        
    def create_toolbar(self):
        """Araç çubuğunu oluşturur"""
        toolbar = QToolBar("Ana Araç Çubuğu")
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Yeni Proje
        new_action = QAction(QIcon.fromTheme("document-new", QIcon(":/icons/new.svg")), "Yeni Proje", self)
        new_action.triggered.connect(self.yeni_proje_ac)
        toolbar.addAction(new_action)
        
        # Proje Aç
        open_action = QAction(QIcon.fromTheme("document-open", QIcon(":/icons/open.svg")), "Proje Aç", self)
        open_action.triggered.connect(self.proje_yukle)
        toolbar.addAction(open_action)
        
        # Kaydet
        save_action = QAction(QIcon.fromTheme("document-save", QIcon(":/icons/save.svg")), "Kaydet", self)
        save_action.triggered.connect(self.proje_kaydet)
        toolbar.addAction(save_action)
        
        toolbar.addSeparator()
        
        # Rapor Oluştur
        report_action = QAction(QIcon.fromTheme("x-office-document", QIcon(":/icons/report.svg")), "Rapor", self)
        report_action.triggered.connect(self.rapor_olustur)
        toolbar.addAction(report_action)
        
        # Analiz Et
        analyze_action = QAction(QIcon.fromTheme("applications-science", QIcon(":/icons/analyze.svg")), "Analiz", self)
        analyze_action.triggered.connect(lambda: self.tabs.setCurrentIndex(2))
        toolbar.addAction(analyze_action)
        
        toolbar.addSeparator()
        
        # Tema Değiştir
        self.theme_action = QAction(QIcon.fromTheme("preferences-desktop-theme", QIcon(":/icons/theme.svg")), "Tema", self)
        self.theme_action.triggered.connect(self.tema_degistir)
        toolbar.addAction(self.theme_action)
        
        # Yardım
        help_action = QAction(QIcon.fromTheme("help-contents", QIcon(":/icons/help.svg")), "Yardım", self)
        help_action.triggered.connect(self.yardim_goster)
        toolbar.addAction(help_action)
        
        # Çıkış
        exit_action = QAction(QIcon.fromTheme("application-exit", QIcon(":/icons/exit.svg")), "Çıkış", self)
        exit_action.triggered.connect(self.cikis)
        toolbar.addAction(exit_action)
    
    def create_dashboard_tab(self):
        """Gösterge tablosu sekmesini oluşturur"""
        dashboard_tab = QWidget()
        layout = QVBoxLayout(dashboard_tab)
        
        # Karşılama bölümü
        welcome_frame = QFrame()
        welcome_frame.setObjectName("welcome-frame")
        welcome_layout = QVBoxLayout(welcome_frame)
        
        # Logo
        logo_label = QLabel()
        logo_label.setPixmap(QPixmap("assets/logo.svg").scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio))
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Başlık
        title_label = QLabel(UYGULAMA_ADI)
        title_label.setObjectName("header-label")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Hoşgeldin mesajı
        welcome_label = QLabel(f"Hoş geldiniz, {self.kullanici_adi}!")
        welcome_label.setObjectName("subheader-label")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        welcome_layout.addWidget(logo_label)
        welcome_layout.addWidget(title_label)
        welcome_layout.addWidget(welcome_label)
        
        # Proje araç çubuğu
        projects_toolbar = QFrame()
        projects_toolbar.setObjectName("projects-toolbar")
        projects_toolbar_layout = QHBoxLayout(projects_toolbar)
        
        # Arama çubuğu
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Proje ara...")
        self.search_box.setMinimumHeight(35)
        self.search_box.textChanged.connect(self.projeleri_filtrele)
        
        # Yeni proje butonu
        new_project_btn = QPushButton("Yeni Proje")
        new_project_btn.setMinimumHeight(35)
        new_project_btn.setIcon(QIcon.fromTheme("document-new", QIcon(":/icons/new.svg")))
        new_project_btn.clicked.connect(self.yeni_proje_ac)
        
        projects_toolbar_layout.addWidget(self.search_box, 3)
        projects_toolbar_layout.addWidget(new_project_btn, 1)
        
        # Projeler bölümü - Tabloya yüklemek için container
        self.projects_container = QWidget()
        self.projects_layout = QVBoxLayout(self.projects_container)
        
        # Proje tablosu
        self.projects_table = ProjectTableWidget()
        self.projects_table.projectSelected.connect(self.proje_sec)
        self.projects_table.projectDoubleClicked.connect(self.proje_detay_goster)
        self.projects_table.projectDeleteRequested.connect(self.proje_sil)
        self.projects_layout.addWidget(self.projects_table)
        
        # Ana düzene ekle
        layout.addWidget(welcome_frame)
        layout.addWidget(projects_toolbar)
        layout.addWidget(self.projects_container)
        
        self.tabs.addTab(dashboard_tab, QIcon.fromTheme("go-home", QIcon(":/icons/home.svg")), "Ana Sayfa")
    
    def create_project_tab(self):
        """Proje sekmesini oluşturur"""
        project_tab = QWidget()
        project_layout = QVBoxLayout(project_tab)
        
        # Proje başlık bölümü
        self.project_header = QFrame()
        self.project_header.setObjectName("project-header")
        header_layout = QHBoxLayout(self.project_header)
        
        self.project_title = QLabel("Proje Yüklenmedi")
        self.project_title.setObjectName("header-label")
        
        self.project_status = QLabel("Lütfen bir proje seçin veya yeni proje oluşturun")
        self.project_status.setObjectName("status-label")
        
        header_layout.addWidget(self.project_title)
        header_layout.addStretch()
        header_layout.addWidget(self.project_status)
        
        # Proje detay sekmelerini oluştur
        self.project_tabs = QTabWidget()
        
        # Proje Detayları
        self.proje_detay_tab = QWidget()
        proje_detay_layout = QFormLayout(self.proje_detay_tab)
        
        self.txt_proje_adi = QLineEdit()
        self.txt_yuklenici = QLineEdit()
        self.txt_muhendis = QLineEdit()
        
        self.btn_proje_kaydet = QPushButton("Kaydet")
        self.btn_proje_kaydet.setObjectName("success-btn")
        self.btn_proje_kaydet.clicked.connect(self.proje_guncelle)
        
        proje_detay_layout.addRow("Proje Adı:", self.txt_proje_adi)
        proje_detay_layout.addRow("Yüklenici Firma:", self.txt_yuklenici)
        proje_detay_layout.addRow("Sorumlu Mühendis:", self.txt_muhendis)
        proje_detay_layout.addRow("", self.btn_proje_kaydet)
        
        # Tapu Bilgileri
        self.tapu_form_widget = TapuFormWidget()
        self.tapu_form_widget.dataChanged.connect(self.veri_degisti)
        
        # Sondaj Bilgileri
        self.sondaj_form_widget = SondajFormWidget()
        self.sondaj_form_widget.dataChanged.connect(self.veri_degisti)
        
        # Arazi Bilgileri
        self.arazi_form_widget = AraziFormWidget()
        self.arazi_form_widget.dataChanged.connect(self.veri_degisti)
        
        # Sekmeleri ekle
        self.project_tabs.addTab(self.proje_detay_tab, QIcon.fromTheme("document-properties", QIcon(":/icons/properties.svg")), "Proje Detayları")
        self.project_tabs.addTab(self.tapu_form_widget, QIcon.fromTheme("x-office-document", QIcon(":/icons/document.svg")), "Tapu Bilgileri")
        self.project_tabs.addTab(self.sondaj_form_widget, QIcon.fromTheme("applications-engineering", QIcon(":/icons/drill.svg")), "Sondaj Bilgileri")
        self.project_tabs.addTab(self.arazi_form_widget, QIcon.fromTheme("go-jump", QIcon(":/icons/field.svg")), "Arazi Bilgileri")
        
        # Ana düzene ekle
        project_layout.addWidget(self.project_header)
        project_layout.addWidget(self.project_tabs)
        
        self.tabs.addTab(project_tab, QIcon.fromTheme("document-edit", QIcon(":/icons/project.svg")), "Proje Detayları")
    
    def create_analysis_tab(self):
        """Analiz sekmesini oluşturur"""
        analysis_tab = QWidget()
        analysis_layout = QVBoxLayout(analysis_tab)
        
        # Kontrol bölümü
        control_frame = QFrame()
        control_frame.setObjectName("control-frame")
        control_layout = QHBoxLayout(control_frame)
        
        self.analysis_project_selector = QComboBox()
        self.analysis_project_selector.setMinimumHeight(35)
        self.analysis_project_selector.currentIndexChanged.connect(self.analiz_projesi_degisti)
        
        self.btn_update_analysis = QPushButton("Analizi Güncelle")
        self.btn_update_analysis.setIcon(QIcon.fromTheme("view-refresh", QIcon(":/icons/refresh.svg")))
        self.btn_update_analysis.clicked.connect(self.analizi_guncelle)
        
        control_layout.addWidget(QLabel("Proje:"))
        control_layout.addWidget(self.analysis_project_selector, 3)
        control_layout.addWidget(self.btn_update_analysis, 1)
        
        # Grafik gösterici
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # SPT Grafiği
        self.spt_graph_container = QFrame()
        spt_layout = QVBoxLayout(self.spt_graph_container)
        spt_layout.setContentsMargins(0, 0, 0, 0)
        
        spt_title = QLabel("SPT (N30) Değerleri")
        spt_title.setObjectName("subheader-label")
        spt_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.spt_graph = SondajGrafikWidget()
        
        spt_layout.addWidget(spt_title)
        spt_layout.addWidget(self.spt_graph)
        
        # Zemin Profili Grafiği
        self.soil_graph_container = QFrame()
        soil_layout = QVBoxLayout(self.soil_graph_container)
        soil_layout.setContentsMargins(0, 0, 0, 0)
        
        soil_title = QLabel("Zemin Profili")
        soil_title.setObjectName("subheader-label")
        soil_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.soil_graph = SondajGrafikWidget()
        
        soil_layout.addWidget(soil_title)
        soil_layout.addWidget(self.soil_graph)
        
        # Splitter'a ekle
        self.splitter.addWidget(self.spt_graph_container)
        self.splitter.addWidget(self.soil_graph_container)
        self.splitter.setSizes([500, 500])  # Eşit boyut
        
        # Ana düzene ekle
        analysis_layout.addWidget(control_frame)
        analysis_layout.addWidget(self.splitter)
        
        self.tabs.addTab(analysis_tab, QIcon.fromTheme("applications-science", QIcon(":/icons/analyze.svg")), "Analiz")
    
    def projeleri_yukle(self):
        """Veritabanından projeleri yükler"""
        try:
            self.update_statusbar("Projeler yükleniyor...")
            with veritabani_baglantisi() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT p.id, p.proje_adi, p.yuklenici_firma, p.sorumlu_muhendis,
                           t.il, t.ilce, 
                           s.sondaj_derinligi, s.bitis_tarihi
                    FROM Projeler p
                    LEFT JOIN TapuBilgileri t ON p.id = t.proje_id
                    LEFT JOIN SondajBilgileri s ON p.id = s.proje_id
                    ORDER BY p.id DESC
                """)
                
                projeler = cursor.fetchall()
                
                # ComboBox'ları temizle
                self.analysis_project_selector.clear()
                self.analysis_project_selector.addItem("Proje Seçin", None)
                
                # Proje tablosunu güncelle
                self.projects_table.clear_projects()
                
                for proje in projeler:
                    proje_id = proje["id"]
                    proje_adi = proje["proje_adi"]
                    
                    # Tabloya ekle
                    self.projects_table.add_project(
                        proje_id,
                        proje_adi,
                        proje["yuklenici_firma"] or "-",
                        proje["sorumlu_muhendis"] or "-",
                        f"{proje['il'] or '-'}, {proje['ilce'] or '-'}",
                        proje["sondaj_derinligi"] or 0,
                        proje["bitis_tarihi"] or "-"
                    )
                    
                    # Analiz ComboBox'a ekle
                    self.analysis_project_selector.addItem(f"{proje_id} - {proje_adi}", proje_id)
                
                self.update_statusbar("Projeler yüklendi")
        except Exception as e:
            hata_logla(f"Projeleri yükleme hatası: {str(e)}", e)
            hata_goster(self, "Veri Yükleme Hatası", f"Projeler yüklenirken hata oluştu: {str(e)}")
    
    def projeleri_filtrele(self, text):
        """Projeleri filtreler"""
        self.projects_table.filter_projects(text)
    
    def yeni_proje_ac(self):
        """Yeni proje oluşturma diyaloğunu açar"""
        try:
            # Mevcut projede kaydedilmemiş değişiklikler varsa uyar
            if self.unsaved_changes:
                if not onay_al(self, "Kaydedilmemiş Değişiklikler", 
                        "Kaydedilmemiş değişiklikler var. Devam etmek istiyor musunuz?"):
                    return
            
            dialog = YeniProjeDialog(self)
            if dialog.exec():
                proje_adi = dialog.get_project_name()
                if proje_adi.strip():
                    # Yeni proje oluştur
                    with veritabani_baglantisi() as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            "INSERT INTO Projeler (proje_adi) VALUES (?)",
                            (proje_adi,)
                        )
                        conn.commit()
                        proje_id = cursor.lastrowid
                    
                    bilgi_goster(self, "Proje Oluşturuldu", f"{proje_adi} projesi başarıyla oluşturuldu.")
                    
                    # Projeleri yeniden yükle ve yeni projeyi seç
                    self.projeleri_yukle()
                    self.proje_yukle_id(proje_id)
                else:
                    uyari_goster(self, "Geçersiz İsim", "Lütfen geçerli bir proje adı giriniz.")
        except Exception as e:
            hata_logla(f"Yeni proje oluşturma hatası: {str(e)}", e)
            hata_goster(self, "Proje Oluşturma Hatası", f"Yeni proje oluşturulurken bir hata oluştu: {str(e)}")
    
    def proje_sec(self, proje_id):
        """Tablodan seçilen projenin ID'sini alır"""
        if self.unsaved_changes:
            if not onay_al(self, "Kaydedilmemiş Değişiklikler", 
                    "Kaydedilmemiş değişiklikler var. Devam etmek istiyor musunuz?"):
                return
        
        self.proje_yukle_id(proje_id)
    
    def proje_yukle(self):
        """Kullanıcıdan proje seçmesini ister"""
        if self.unsaved_changes:
            if not onay_al(self, "Kaydedilmemiş Değişiklikler", 
                    "Kaydedilmemiş değişiklikler var. Devam etmek istiyor musunuz?"):
                return
        
        try:
            with veritabani_baglantisi() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, proje_adi FROM Projeler ORDER BY proje_adi")
                projeler = cursor.fetchall()
            
            if not projeler:
                uyari_goster(self, "Proje Bulunamadı", "Veritabanında hiç proje bulunamadı. Önce bir proje oluşturun.")
                return
            
            items = [f"{proje['id']} - {proje['proje_adi']}" for proje in projeler]
            selected_item, ok = QInputDialog.getItem(
                self, "Proje Seç", "Proje:", items, 0, False
            )
            
            if ok and selected_item:
                proje_id = int(selected_item.split(" - ")[0])
                self.proje_yukle_id(proje_id)
                
        except Exception as e:
            hata_logla(f"Proje yükleme hatası: {str(e)}", e)
            hata_goster(self, "Proje Yükleme Hatası", f"Proje yüklenirken bir hata oluştu: {str(e)}")
    
    def proje_yukle_id(self, proje_id):
        """Belirli bir ID'ye sahip projeyi yükler"""
        try:
            self.update_statusbar(f"Proje #{proje_id} yükleniyor...")
            
            with veritabani_baglantisi() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM Projeler WHERE id = ?", (proje_id,))
                proje = cursor.fetchone()
                
                if not proje:
                    uyari_goster(self, "Proje Bulunamadı", f"ID: {proje_id} olan proje bulunamadı.")
                    return
                
                # Proje bilgilerini ayarla
                self.mevcut_proje_id = proje_id
                self.mevcut_proje_adi = proje["proje_adi"]
                
                # Başlığı güncelle
                self.project_title.setText(f"Proje: {self.mevcut_proje_adi}")
                self.project_status.setText(f"Proje ID: {proje_id}")
                
                # Form alanlarını doldur
                self.txt_proje_adi.setText(proje["proje_adi"])
                self.txt_yuklenici.setText(proje["yuklenici_firma"] or "")
                self.txt_muhendis.setText(proje["sorumlu_muhendis"] or "")
                
                # Tapu, sondaj ve arazi formlarını yükle
                self.tapu_form_widget.load_data(proje_id)
                self.sondaj_form_widget.load_data(proje_id)
                self.arazi_form_widget.load_data(proje_id)
                
                # Analiz grafiklerini güncelle
                self.analysis_project_selector.setCurrentIndex(
                    self.analysis_project_selector.findData(proje_id)
                )
                self.analizi_guncelle()
                
                # Proje sekmesine geç
                self.tabs.setCurrentIndex(1)
                
                # Değişiklik bayraklarını sıfırla
                self.unsaved_changes = False
                
                self.update_statusbar(f"Proje #{proje_id} - {self.mevcut_proje_adi} yüklendi")
                
        except Exception as e:
            hata_logla(f"Proje yükleme hatası (ID: {proje_id}): {str(e)}", e)
            hata_goster(self, "Proje Yükleme Hatası", f"Proje yüklenirken bir hata oluştu: {str(e)}")
    
    def proje_guncelle(self):
        """Proje bilgilerini günceller"""
        if not self.mevcut_proje_id:
            uyari_goster(self, "Proje Seçilmedi", "Lütfen önce bir proje seçin.")
            return
        
        try:
            proje_adi = self.txt_proje_adi.text().strip()
            yuklenici = self.txt_yuklenici.text().strip()
            muhendis = self.txt_muhendis.text().strip()
            
            if not proje_adi:
                uyari_goster(self, "Geçersiz İsim", "Lütfen geçerli bir proje adı giriniz.")
                return
            
            with veritabani_baglantisi() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE Projeler SET proje_adi = ?, yuklenici_firma = ?, sorumlu_muhendis = ? WHERE id = ?",
                    (proje_adi, yuklenici, muhendis, self.mevcut_proje_id)
                )
                conn.commit()
            
            # Başlığı güncelle
            self.mevcut_proje_adi = proje_adi
            self.project_title.setText(f"Proje: {self.mevcut_proje_adi}")
            
            # Projeleri yeniden yükle
            self.projeleri_yukle()
            
            # Değişiklik bayrağını sıfırla
            self.unsaved_changes = False
            
            bilgi_goster(self, "Güncelleme Başarılı", f"{proje_adi} projesi başarıyla güncellendi.")
            self.update_statusbar(f"Proje #{self.mevcut_proje_id} - {self.mevcut_proje_adi} güncellendi")
            
        except Exception as e:
            hata_logla(f"Proje güncelleme hatası: {str(e)}", e)
            hata_goster(self, "Güncelleme Hatası", f"Proje güncellenirken bir hata oluştu: {str(e)}")
    
    def proje_kaydet(self):
        """Tüm proje değişikliklerini kaydeder"""
        if not self.mevcut_proje_id:
            uyari_goster(self, "Proje Seçilmedi", "Lütfen önce bir proje seçin.")
            return
        
        try:
            # Proje bilgilerini güncelle
            self.proje_guncelle()
            
            # Tapu bilgilerini kaydet
            if not self.tapu_form_widget.save_data(self.mevcut_proje_id):
                raise Exception("Tapu bilgileri kaydedilemedi")
            
            # Sondaj bilgilerini kaydet
            if not self.sondaj_form_widget.save_data(self.mevcut_proje_id):
                raise Exception("Sondaj bilgileri kaydedilemedi")
            
            # Arazi bilgilerini kaydet
            if not self.arazi_form_widget.save_data(self.mevcut_proje_id):
                raise Exception("Arazi bilgileri kaydedilemedi")
            
            # Değişiklik bayrağını sıfırla
            self.unsaved_changes = False
            
            bilgi_goster(self, "Kayıt Başarılı", f"{self.mevcut_proje_adi} projesi tüm bilgileriyle başarıyla kaydedildi.")
            self.update_statusbar(f"Proje #{self.mevcut_proje_id} - {self.mevcut_proje_adi} kaydedildi")
            
        except Exception as e:
            hata_logla(f"Proje kaydetme hatası: {str(e)}", e)
            hata_goster(self, "Kaydetme Hatası", f"Proje kaydedilirken bir hata oluştu: {str(e)}")
    
    def proje_sil(self, proje_id=None):
        """Projeyi siler"""
        if proje_id is None and self.mevcut_proje_id:
            proje_id = self.mevcut_proje_id
        
        if not proje_id:
            uyari_goster(self, "Proje Seçilmedi", "Lütfen silmek için bir proje seçin.")
            return
        
        try:
            # Proje adını al
            with veritabani_baglantisi() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT proje_adi FROM Projeler WHERE id = ?", (proje_id,))
                result = cursor.fetchone()
                
                if not result:
                    uyari_goster(self, "Proje Bulunamadı", f"ID: {proje_id} olan proje bulunamadı.")
                    return
                
                proje_adi = result["proje_adi"]
            
            # Kullanıcıdan onay al
            if not onay_al(self, "Proje Silme Onayı", 
                    f"{proje_adi} projesini silmek istediğinizden emin misiniz?\n\nBu işlem geri alınamaz!"):
                return
            
            # Projeyi sil (ilişkili verileri de CASCADE ile sil)
            with veritabani_baglantisi() as conn:
                cursor = conn.cursor()
                # Önce ilişkili tabloları temizle
                cursor.execute("DELETE FROM AraziBilgileri WHERE proje_id = ?", (proje_id,))
                cursor.execute("DELETE FROM SondajBilgileri WHERE proje_id = ?", (proje_id,))
                cursor.execute("DELETE FROM TapuBilgileri WHERE proje_id = ?", (proje_id,))
                # Şimdi projeyi sil
                cursor.execute("DELETE FROM Projeler WHERE id = ?", (proje_id,))
                conn.commit()
            
            # Eğer mevcut proje silindiyse, form alanlarını temizle
            if proje_id == self.mevcut_proje_id:
                self.mevcut_proje_id = None
                self.mevcut_proje_adi = None
                self.project_title.setText("Proje Yüklenmedi")
                self.project_status.setText("Lütfen bir proje seçin veya yeni proje oluşturun")
                self.txt_proje_adi.clear()
                self.txt_yuklenici.clear()
                self.txt_muhendis.clear()
                self.tapu_form_widget.clear_form()
                self.sondaj_form_widget.clear_form()
                self.arazi_form_widget.clear_form()
                
                # Ana sayfaya dön
                self.tabs.setCurrentIndex(0)
            
            # Projeleri yeniden yükle
            self.projeleri_yukle()
            
            bilgi_goster(self, "Silme Başarılı", f"{proje_adi} projesi başarıyla silindi.")
            self.update_statusbar(f"Proje #{proje_id} - {proje_adi} silindi")
            
        except Exception as e:
            hata_logla(f"Proje silme hatası: {str(e)}", e)
            hata_goster(self, "Silme Hatası", f"Proje silinirken bir hata oluştu: {str(e)}")
    
    def proje_detay_goster(self, proje_id):
        """Proje detaylarını gösteren diyalog açar"""
        try:
            dialog = ProjeDetayDialog(self, proje_id)
            dialog.exec()
        except Exception as e:
            hata_logla(f"Proje detay gösterme hatası: {str(e)}", e)
            hata_goster(self, "Detay Gösterme Hatası", f"Proje detayları gösterilirken bir hata oluştu: {str(e)}")
    
    def analiz_projesi_degisti(self, index):
        """Analiz sekmesinde proje değiştiğinde tetiklenir"""
        proje_id = self.analysis_project_selector.currentData()
        if proje_id:
            self.analizi_guncelle(proje_id)
    
    def analizi_guncelle(self, proje_id=None):
        """Analiz grafiklerini günceller"""
        if proje_id is None:
            proje_id = self.analysis_project_selector.currentData()
            
        if not proje_id:
            # Grafikleri temizle
            self.spt_graph.canvas.axes.clear()
            self.spt_graph.canvas.axes.text(0.5, 0.5, "Lütfen bir proje seçin", 
                                         ha='center', va='center', fontsize=12)
            self.spt_graph.canvas.draw()
            
            self.soil_graph.canvas.axes.clear()
            self.soil_graph.canvas.axes.text(0.5, 0.5, "Lütfen bir proje seçin", 
                                           ha='center', va='center', fontsize=12)
            self.soil_graph.canvas.draw()
            return
        
        try:
            self.update_statusbar("Grafikler oluşturuluyor...")
            
            # SPT Grafiği
            self.spt_graph.spt_verileri_goster(proje_id)
            
            # Zemin Profili Grafiği
            self.soil_graph.zemin_profili_goster(proje_id)
            
            self.update_statusbar("Grafikler oluşturuldu")
            
        except Exception as e:
            hata_logla(f"Analiz güncelleme hatası: {str(e)}", e)
            hata_goster(self, "Analiz Hatası", f"Grafikler oluşturulurken bir hata oluştu: {str(e)}")
    
    def rapor_olustur(self):
        """Rapor oluşturma diyaloğunu açar"""
        if not self.mevcut_proje_id:
            uyari_goster(self, "Proje Seçilmedi", "Lütfen rapor oluşturmak için bir proje seçin.")
            return
        
        try:
            dialog = RaporDialog(self, self.mevcut_proje_id, self.mevcut_proje_adi)
            dialog.exec()
        except Exception as e:
            hata_logla(f"Rapor oluşturma diyaloğu hatası: {str(e)}", e)
            hata_goster(self, "Rapor Diyaloğu Hatası", f"Rapor diyaloğu açılırken bir hata oluştu: {str(e)}")
    
    def tema_degistir(self):
        """Uygulamanın temasını değiştirir"""
        try:
            self.is_dark_theme = not self.is_dark_theme
            
            # Ana uygulama
            app = QApplication.instance()
            
            # Qt şablonunu güncelle
            new_theme = tema_sinifi_belirle(self.is_dark_theme)
            if self.is_dark_theme:
                app.setStyle("Fusion")  # Fusion stili koyu tema için daha uygun
                self.theme_action.setText("☀️ Açık Tema")
            else:
                app.setStyle("Fusion")
                self.theme_action.setText("🌙 Koyu Tema")
            
            # Ana pencereden başlayarak tüm widget'ları güncelle
            self.setProperty("theme", new_theme)
            
            # Stili uygula
            app.style().unpolish(self)
            app.style().polish(self)
            
            # Tüm alt widget'ları güncelle
            for widget in app.allWidgets():
                widget.setProperty("theme", new_theme)
                app.style().unpolish(widget)
                app.style().polish(widget)
            
            self.update_statusbar(f"{'Koyu' if self.is_dark_theme else 'Açık'} tema uygulandı")
            
        except Exception as e:
            hata_logla(f"Tema değiştirme hatası: {str(e)}", e)
            hata_goster(self, "Tema Değiştirme Hatası", f"Tema değiştirilirken bir hata oluştu: {str(e)}")
    
    def veri_degisti(self):
        """Formlardan herhangi birindeki veri değiştiğinde çağrılır"""
        self.unsaved_changes = True
        self.update_statusbar("Kaydedilmemiş değişiklikler var", True)
    
    def update_statusbar(self, message=None, is_warning=False):
        """Durum çubuğunu günceller"""
        if message:
            self.status_bar.showMessage(message)
            
            if is_warning:
                self.status_indicator.set_status("warning")
            else:
                self.status_indicator.set_status("success")
        else:
            if self.unsaved_changes:
                self.status_bar.showMessage("Kaydedilmemiş değişiklikler var")
                self.status_indicator.set_status("warning")
            else:
                self.status_bar.showMessage("Hazır")
                self.status_indicator.set_status("success")
    
    def yardim_goster(self):
        """Yardım penceresini gösterir"""
        yardim_metni = """
        <h3>Sondaj Proje Yönetimi Yardım</h3>
        <p>Bu uygulama, sondaj projelerinin yönetimi için geliştirilmiştir.</p>
        
        <h4>Ana Özellikler:</h4>
        <ul>
            <li>Yeni proje oluşturma</li>
            <li>Mevcut projeleri yükleme</li>
            <li>Tapu, sondaj ve arazi bilgilerini kaydetme</li>
            <li>SPT ve zemin profili analizleri</li>
            <li>PDF raporu oluşturma</li>
        </ul>
        
        <h4>Kısayollar:</h4>
        <ul>
            <li>Ctrl+N: Yeni Proje</li>
            <li>Ctrl+O: Proje Aç</li>
            <li>Ctrl+S: Kaydet</li>
            <li>F1: Yardım</li>
            <li>Ctrl+Q: Çıkış</li>
        </ul>
        
        <p>Sorunlar ve öneriler için: <a href="mailto:destek@sondaj.com">destek@sondaj.com</a></p>
        """
        
        msg = QMessageBox(self)
        msg.setWindowTitle("Yardım")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(yardim_metni)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()
    
    def cikis(self):
        """Uygulamadan çıkış yapar"""
        if self.unsaved_changes:
            if not onay_al(self, "Kaydedilmemiş Değişiklikler", 
                    "Kaydedilmemiş değişiklikler var. Çıkmak istediğinizden emin misiniz?"):
                return
        
        QApplication.quit()
    
    def closeEvent(self, event):
        """Pencere kapatılmadan önce tetiklenir"""
        if self.unsaved_changes:
            if not onay_al(self, "Kaydedilmemiş Değişiklikler", 
                    "Kaydedilmemiş değişiklikler var. Çıkmak istediğinizden emin misiniz?"):
                event.ignore()
                return
        
        event.accept()
