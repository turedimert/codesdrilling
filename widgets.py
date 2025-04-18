import sqlite3
from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, 
    QFormLayout, QDateEdit, QComboBox, QTableWidget, QTableWidgetItem, 
    QHeaderView, QAbstractItemView, QCheckBox, QFrame, QGroupBox, QSpinBox,
    QDoubleSpinBox, QScrollArea, QTabWidget, QSizePolicy, QSpacerItem,
    QMenu, QStyledItemDelegate
)
from PyQt6.QtCore import (
    Qt, QDate, QDateTime, pyqtSignal, QEvent, QObject, QSize, QPoint, QTimer
)
from PyQt6.QtGui import (
    QFont, QIcon, QColor, QPalette, QDoubleValidator, QAction, QCursor
)

from utils import (
    hata_logla, bilgi_goster, hata_goster, uyari_goster, onay_al,
    veritabani_baglantisi
)
from constants import ZEMIN_TIPLERI, MAKINE_TIPLERI, SPT_TIP_SECENEKLERI

class StatusIndicator(QWidget):
    """Durum çubuğu için durum göstergesi"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(12, 12)
        self.setMaximumSize(12, 12)
        self._status = "normal"
        
    def set_status(self, status):
        """Durumu ayarlar: 'normal', 'success', 'warning', 'error'"""
        self._status = status
        self.update()
        
    def paintEvent(self, event):
        """Widget'ı çizer"""
        from PyQt6.QtGui import QPainter, QBrush
        
        colors = {
            "normal": QColor("#bdc3c7"),
            "success": QColor("#2ecc71"),
            "warning": QColor("#f39c12"),
            "error": QColor("#e74c3c")
        }
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        brush = QBrush(colors.get(self._status, colors["normal"]))
        painter.setBrush(brush)
        painter.setPen(Qt.PenStyle.NoPen)
        
        painter.drawEllipse(2, 2, 8, 8)
        
class ProjectTableWidget(QTableWidget):
    """Projeleri gösteren tablo widget'ı"""
    
    # Özel sinyaller
    projectSelected = pyqtSignal(int)  # Proje ID'si
    projectDoubleClicked = pyqtSignal(int)  # Proje ID'si
    projectDeleteRequested = pyqtSignal(int)  # Proje ID'si
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUI()
        self.project_ids = []  # ID'leri saklamak için
        
    def setupUI(self):
        """Tablo arayüzünü ayarlar"""
        # Tablo özellikleri
        self.setColumnCount(6)
        self.setHorizontalHeaderLabels([
            "Proje Adı", "Yüklenici", "Sorumlu Mühendis", 
            "Konum", "Derinlik (m)", "Tamamlanma"
        ])
        
        # Sütun genişlikleri
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        
        # Tablo davranışı
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setAlternatingRowColors(True)
        self.verticalHeader().setVisible(False)
        self.setSortingEnabled(True)
        
        # Bağlantılar
        self.cellClicked.connect(self.on_cell_clicked)
        self.cellDoubleClicked.connect(self.on_cell_double_clicked)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
    def add_project(self, proje_id, proje_adi, yuklenici, muhendis, konum, derinlik, tarih):
        """Tabloya yeni bir proje ekler"""
        row_position = self.rowCount()
        self.insertRow(row_position)
        
        # Proje ID'sini sakla
        self.project_ids.append(proje_id)
        
        # Hücreleri doldur
        self.setItem(row_position, 0, QTableWidgetItem(proje_adi))
        self.setItem(row_position, 1, QTableWidgetItem(yuklenici))
        self.setItem(row_position, 2, QTableWidgetItem(muhendis))
        self.setItem(row_position, 3, QTableWidgetItem(konum))
        
        # Derinlik (sayısal değer)
        depth_item = QTableWidgetItem()
        if derinlik:
            depth_item.setData(Qt.ItemDataRole.DisplayRole, float(derinlik))
        else:
            depth_item.setData(Qt.ItemDataRole.DisplayRole, 0.0)
        self.setItem(row_position, 4, depth_item)
        
        # Tamamlanma tarihi
        self.setItem(row_position, 5, QTableWidgetItem(tarih))
        
    def clear_projects(self):
        """Tabloyu temizler"""
        self.setRowCount(0)
        self.project_ids = []
        
    def filter_projects(self, text):
        """Projeleri arama metnine göre filtreler"""
        text = text.lower()
        for row in range(self.rowCount()):
            match_found = False
            for col in range(self.columnCount()):
                item = self.item(row, col)
                if item and text in item.text().lower():
                    match_found = True
                    break
            
            self.setRowHidden(row, not match_found)
    
    def on_cell_clicked(self, row, column):
        """Hücre tıklandığında proje seçilir"""
        if 0 <= row < len(self.project_ids):
            self.projectSelected.emit(self.project_ids[row])
    
    def on_cell_double_clicked(self, row, column):
        """Hücre çift tıklandığında proje detayları açılır"""
        if 0 <= row < len(self.project_ids):
            self.projectDoubleClicked.emit(self.project_ids[row])
    
    def show_context_menu(self, position):
        """Sağ tık menüsünü gösterir"""
        row = self.rowAt(position.y())
        
        if row >= 0 and row < len(self.project_ids):
            context_menu = QMenu(self)
            
            open_action = QAction("Projeyi Aç", self)
            open_action.triggered.connect(lambda: self.projectSelected.emit(self.project_ids[row]))
            
            details_action = QAction("Proje Detayları", self)
            details_action.triggered.connect(lambda: self.projectDoubleClicked.emit(self.project_ids[row]))
            
            delete_action = QAction("Projeyi Sil", self)
            delete_action.triggered.connect(lambda: self.projectDeleteRequested.emit(self.project_ids[row]))
            
            context_menu.addAction(open_action)
            context_menu.addAction(details_action)
            context_menu.addSeparator()
            context_menu.addAction(delete_action)
            
            context_menu.exec(QCursor.pos())

class ProjectCardWidget(QFrame):
    """Kart şeklinde proje bilgilerini gösteren widget"""
    
    projectClicked = pyqtSignal(int)
    
    def __init__(self, proje_id, proje_adi, yuklenici, konum, parent=None):
        super().__init__(parent)
        self.proje_id = proje_id
        self.setupUI(proje_adi, yuklenici, konum)
        
    def setupUI(self, proje_adi, yuklenici, konum):
        """Kart UI'ını oluşturur"""
        self.setObjectName("project-card")
        self.setFixedHeight(100)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Proje adı
        title = QLabel(proje_adi)
        title.setObjectName("card-title")
        
        # Alt bilgiler
        info_layout = QHBoxLayout()
        
        # Yüklenici
        yuklenici_label = QLabel(f"<b>Yüklenici:</b> {yuklenici}")
        
        # Konum
        konum_label = QLabel(f"<b>Konum:</b> {konum}")
        
        info_layout.addWidget(yuklenici_label)
        info_layout.addWidget(konum_label)
        
        layout.addWidget(title)
        layout.addLayout(info_layout)
        
    def mousePressEvent(self, event):
        """Kart tıklandığında projeyi seçer"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.projectClicked.emit(self.proje_id)
        super().mousePressEvent(event)

class TapuFormWidget(QWidget):
    """Tapu bilgileri formu"""
    
    dataChanged = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUI()
        
    def setupUI(self):
        """Form arayüzünü oluşturur"""
        layout = QFormLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Form alanları
        self.txt_il = QLineEdit()
        self.txt_ilce = QLineEdit()
        self.txt_mahalle = QLineEdit()
        self.txt_ada = QLineEdit()
        self.txt_pafta = QLineEdit()
        self.txt_parsel = QLineEdit()
        self.txt_koordinat_x = QLineEdit()
        self.txt_koordinat_x.setValidator(QDoubleValidator())
        self.txt_koordinat_y = QLineEdit()
        self.txt_koordinat_y.setValidator(QDoubleValidator())
        
        # Kaydet butonu
        self.btn_kaydet = QPushButton("Tapu Bilgilerini Kaydet")
        self.btn_kaydet.clicked.connect(self.save_triggered)
        
        # Form düzeni
        layout.addRow("İl:", self.txt_il)
        layout.addRow("İlçe:", self.txt_ilce)
        layout.addRow("Mahalle:", self.txt_mahalle)
        layout.addRow("Ada:", self.txt_ada)
        layout.addRow("Pafta:", self.txt_pafta)
        layout.addRow("Parsel:", self.txt_parsel)
        layout.addRow("Koordinat X:", self.txt_koordinat_x)
        layout.addRow("Koordinat Y:", self.txt_koordinat_y)
        layout.addRow("", self.btn_kaydet)
        
        # Veri değişikliği sinyallerini bağla
        self.txt_il.textChanged.connect(self.dataChanged)
        self.txt_ilce.textChanged.connect(self.dataChanged)
        self.txt_mahalle.textChanged.connect(self.dataChanged)
        self.txt_ada.textChanged.connect(self.dataChanged)
        self.txt_pafta.textChanged.connect(self.dataChanged)
        self.txt_parsel.textChanged.connect(self.dataChanged)
        self.txt_koordinat_x.textChanged.connect(self.dataChanged)
        self.txt_koordinat_y.textChanged.connect(self.dataChanged)
    
    def load_data(self, proje_id):
        """Veritabanından verileri yükler"""
        try:
            with veritabani_baglantisi() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM TapuBilgileri
                    WHERE proje_id = ?
                """, (proje_id,))
                
                tapu = cursor.fetchone()
                
                if tapu:
                    # Mevcut kayıtları yükle
                    self.txt_il.setText(tapu["il"] or "")
                    self.txt_ilce.setText(tapu["ilce"] or "")
                    self.txt_mahalle.setText(tapu["mahalle"] or "")
                    self.txt_ada.setText(tapu["ada"] or "")
                    self.txt_pafta.setText(tapu["pafta"] or "")
                    self.txt_parsel.setText(tapu["parsel"] or "")
                    self.txt_koordinat_x.setText(str(tapu["koordinat_x"] or ""))
                    self.txt_koordinat_y.setText(str(tapu["koordinat_y"] or ""))
                else:
                    # Formları temizle
                    self.clear_form()
            
            return True
        except Exception as e:
            hata_logla(f"Tapu bilgileri yükleme hatası: {str(e)}", e)
            return False
    
    def save_data(self, proje_id):
        """Verileri veritabanına kaydeder"""
        try:
            # Koordinat değerlerini hazırla
            koordinat_x = None
            if self.txt_koordinat_x.text().strip():
                koordinat_x = float(self.txt_koordinat_x.text().replace(",", "."))
                
            koordinat_y = None
            if self.txt_koordinat_y.text().strip():
                koordinat_y = float(self.txt_koordinat_y.text().replace(",", "."))
            
            with veritabani_baglantisi() as conn:
                cursor = conn.cursor()
                
                # Önce mevcut kaydı kontrol et
                cursor.execute("""
                    SELECT id FROM TapuBilgileri
                    WHERE proje_id = ?
                """, (proje_id,))
                
                existing = cursor.fetchone()
                
                if existing:
                    # Mevcut kaydı güncelle
                    cursor.execute("""
                        UPDATE TapuBilgileri
                        SET il = ?, ilce = ?, mahalle = ?, ada = ?, 
                            pafta = ?, parsel = ?, koordinat_x = ?, koordinat_y = ?
                        WHERE proje_id = ?
                    """, (
                        self.txt_il.text(), self.txt_ilce.text(), self.txt_mahalle.text(),
                        self.txt_ada.text(), self.txt_pafta.text(), self.txt_parsel.text(),
                        koordinat_x, koordinat_y, proje_id
                    ))
                else:
                    # Yeni kayıt oluştur
                    cursor.execute("""
                        INSERT INTO TapuBilgileri
                        (proje_id, il, ilce, mahalle, ada, pafta, parsel, koordinat_x, koordinat_y)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        proje_id, self.txt_il.text(), self.txt_ilce.text(), self.txt_mahalle.text(),
                        self.txt_ada.text(), self.txt_pafta.text(), self.txt_parsel.text(),
                        koordinat_x, koordinat_y
                    ))
                
                conn.commit()
            
            return True
        except Exception as e:
            hata_logla(f"Tapu bilgileri kaydetme hatası: {str(e)}", e)
            return False
    
    def clear_form(self):
        """Form alanlarını temizler"""
        self.txt_il.clear()
        self.txt_ilce.clear()
        self.txt_mahalle.clear()
        self.txt_ada.clear()
        self.txt_pafta.clear()
        self.txt_parsel.clear()
        self.txt_koordinat_x.clear()
        self.txt_koordinat_y.clear()
    
    def save_triggered(self):
        """Kaydet butonu tıklandığında çağrılır"""
        # Bu metod, butondan çağrılacak, proje_id içermediği için
        # değişiklik sinyali göndermesi yeterli, asıl kayıt ana pencereden yapılacak
        self.dataChanged.emit()

class SondajFormWidget(QWidget):
    """Sondaj bilgileri formu"""
    
    dataChanged = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUI()
        
    def setupUI(self):
        """Form arayüzünü oluşturur"""
        layout = QFormLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Form alanları
        self.txt_sondor = QLineEdit()
        
        self.txt_kotu = QDoubleSpinBox()
        self.txt_kotu.setDecimals(2)
        self.txt_kotu.setRange(-999.99, 9999.99)
        
        self.txt_derinlik = QDoubleSpinBox()
        self.txt_derinlik.setDecimals(2)
        self.txt_derinlik.setRange(0, 9999.99)
        
        self.date_baslama = QDateEdit()
        self.date_baslama.setCalendarPopup(True)
        self.date_baslama.setDisplayFormat("dd.MM.yyyy")
        self.date_baslama.setDate(QDate.currentDate())
        
        self.date_bitis = QDateEdit()
        self.date_bitis.setCalendarPopup(True)
        self.date_bitis.setDisplayFormat("dd.MM.yyyy")
        self.date_bitis.setDate(QDate.currentDate())
        
        self.txt_delgi_capi = QDoubleSpinBox()
        self.txt_delgi_capi.setDecimals(2)
        self.txt_delgi_capi.setRange(0, 999.99)
        
        self.txt_yer_alti_suyu = QDoubleSpinBox()
        self.txt_yer_alti_suyu.setDecimals(2)
        self.txt_yer_alti_suyu.setRange(-999.99, 9999.99)
        
        self.txt_ud_ornekleri = QLineEdit()
        
        self.cmb_zemin_tipi = QComboBox()
        self.cmb_zemin_tipi.addItems([""] + ZEMIN_TIPLERI)
        
        self.cmb_makine_tipi = QComboBox()
        self.cmb_makine_tipi.addItems([""] + MAKINE_TIPLERI)
        
        self.cmb_spt_tip = QComboBox()
        self.cmb_spt_tip.addItems([""] + SPT_TIP_SECENEKLERI)
        
        # Kaydet butonu
        self.btn_kaydet = QPushButton("Sondaj Bilgilerini Kaydet")
        self.btn_kaydet.clicked.connect(self.save_triggered)
        
        # Form düzeni
        layout.addRow("Sondör Adı:", self.txt_sondor)
        layout.addRow("Sondaj Kotu (m):", self.txt_kotu)
        layout.addRow("Sondaj Derinliği (m):", self.txt_derinlik)
        layout.addRow("Başlama Tarihi:", self.date_baslama)
        layout.addRow("Bitiş Tarihi:", self.date_bitis)
        layout.addRow("Delgi Çapı (mm):", self.txt_delgi_capi)
        layout.addRow("Yeraltı Suyu (m):", self.txt_yer_alti_suyu)
        layout.addRow("UD Örnekleri:", self.txt_ud_ornekleri)
        layout.addRow("Zemin Tipi:", self.cmb_zemin_tipi)
        layout.addRow("Makine Tipi:", self.cmb_makine_tipi)
        layout.addRow("SPT Şahmerdan Tipi:", self.cmb_spt_tip)
        layout.addRow("", self.btn_kaydet)
        
        # Veri değişikliği sinyallerini bağla
        self.txt_sondor.textChanged.connect(self.dataChanged)
        self.txt_kotu.valueChanged.connect(self.dataChanged)
        self.txt_derinlik.valueChanged.connect(self.dataChanged)
        self.date_baslama.dateChanged.connect(self.dataChanged)
        self.date_bitis.dateChanged.connect(self.dataChanged)
        self.txt_delgi_capi.valueChanged.connect(self.dataChanged)
        self.txt_yer_alti_suyu.valueChanged.connect(self.dataChanged)
        self.txt_ud_ornekleri.textChanged.connect(self.dataChanged)
        self.cmb_zemin_tipi.currentIndexChanged.connect(self.dataChanged)
        self.cmb_makine_tipi.currentIndexChanged.connect(self.dataChanged)
        self.cmb_spt_tip.currentIndexChanged.connect(self.dataChanged)
    
    def load_data(self, proje_id):
        """Veritabanından verileri yükler"""
        try:
            with veritabani_baglantisi() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM SondajBilgileri
                    WHERE proje_id = ?
                """, (proje_id,))
                
                sondaj = cursor.fetchone()
                
                if sondaj:
                    # Mevcut kayıtları yükle
                    self.txt_sondor.setText(sondaj["sondor_adi"] or "")
                    
                    if sondaj["sondaj_kotu"] is not None:
                        self.txt_kotu.setValue(sondaj["sondaj_kotu"])
                    else:
                        self.txt_kotu.setValue(0)
                        
                    if sondaj["sondaj_derinligi"] is not None:
                        self.txt_derinlik.setValue(sondaj["sondaj_derinligi"])
                    else:
                        self.txt_derinlik.setValue(0)
                    
                    if sondaj["baslama_tarihi"]:
                        self.date_baslama.setDate(QDate.fromString(sondaj["baslama_tarihi"], "dd.MM.yyyy"))
                    else:
                        self.date_baslama.setDate(QDate.currentDate())
                    
                    if sondaj["bitis_tarihi"]:
                        self.date_bitis.setDate(QDate.fromString(sondaj["bitis_tarihi"], "dd.MM.yyyy"))
                    else:
                        self.date_bitis.setDate(QDate.currentDate())
                    
                    if sondaj["delgi_capi"] is not None:
                        self.txt_delgi_capi.setValue(sondaj["delgi_capi"])
                    else:
                        self.txt_delgi_capi.setValue(0)
                    
                    if sondaj["yer_alti_suyu"] is not None:
                        self.txt_yer_alti_suyu.setValue(sondaj["yer_alti_suyu"])
                    else:
                        self.txt_yer_alti_suyu.setValue(0)
                    
                    self.txt_ud_ornekleri.setText(sondaj["ud_ornekleri"] or "")
                    
                    # Combobox'lar için
                    zemin_index = self.cmb_zemin_tipi.findText(sondaj["zemin_tipi"] or "")
                    self.cmb_zemin_tipi.setCurrentIndex(max(0, zemin_index))
                    
                    makine_index = self.cmb_makine_tipi.findText(sondaj["makine_tipi"] or "")
                    self.cmb_makine_tipi.setCurrentIndex(max(0, makine_index))
                    
                    spt_index = self.cmb_spt_tip.findText(sondaj["spt_sahmerdan_tipi"] or "")
                    self.cmb_spt_tip.setCurrentIndex(max(0, spt_index))
                else:
                    # Formları temizle
                    self.clear_form()
            
            return True
        except Exception as e:
            hata_logla(f"Sondaj bilgileri yükleme hatası: {str(e)}", e)
            return False
    
    def save_data(self, proje_id):
        """Verileri veritabanına kaydeder"""
        try:
            with veritabani_baglantisi() as conn:
                cursor = conn.cursor()
                
                # Önce mevcut kaydı kontrol et
                cursor.execute("""
                    SELECT id FROM SondajBilgileri
                    WHERE proje_id = ?
                """, (proje_id,))
                
                existing = cursor.fetchone()
                
                # Tarihleri biçimlendir
                baslama_tarihi = self.date_baslama.date().toString("dd.MM.yyyy")
                bitis_tarihi = self.date_bitis.date().toString("dd.MM.yyyy")
                
                # Zemin tipi, makine tipi ve SPT tipi
                zemin_tipi = self.cmb_zemin_tipi.currentText() if self.cmb_zemin_tipi.currentIndex() > 0 else None
                makine_tipi = self.cmb_makine_tipi.currentText() if self.cmb_makine_tipi.currentIndex() > 0 else None
                spt_tipi = self.cmb_spt_tip.currentText() if self.cmb_spt_tip.currentIndex() > 0 else None
                
                if existing:
                    # Mevcut kaydı güncelle
                    cursor.execute("""
                        UPDATE SondajBilgileri
                        SET sondor_adi = ?, sondaj_kotu = ?, sondaj_derinligi = ?, 
                            baslama_tarihi = ?, bitis_tarihi = ?, delgi_capi = ?, 
                            yer_alti_suyu = ?, ud_ornekleri = ?, zemin_tipi = ?, 
                            makine_tipi = ?, spt_sahmerdan_tipi = ?
                        WHERE proje_id = ?
                    """, (
                        self.txt_sondor.text(), self.txt_kotu.value(), self.txt_derinlik.value(),
                        baslama_tarihi, bitis_tarihi, self.txt_delgi_capi.value(),
                        self.txt_yer_alti_suyu.value(), self.txt_ud_ornekleri.text(),
                        zemin_tipi, makine_tipi, spt_tipi, proje_id
                    ))
                else:
                    # Yeni kayıt oluştur
                    cursor.execute("""
                        INSERT INTO SondajBilgileri
                        (proje_id, sondor_adi, sondaj_kotu, sondaj_derinligi, 
                         baslama_tarihi, bitis_tarihi, delgi_capi, 
                         yer_alti_suyu, ud_ornekleri, zemin_tipi, 
                         makine_tipi, spt_sahmerdan_tipi)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        proje_id, self.txt_sondor.text(), self.txt_kotu.value(), self.txt_derinlik.value(),
                        baslama_tarihi, bitis_tarihi, self.txt_delgi_capi.value(),
                        self.txt_yer_alti_suyu.value(), self.txt_ud_ornekleri.text(),
                        zemin_tipi, makine_tipi, spt_tipi
                    ))
                
                conn.commit()
            
            return True
        except Exception as e:
            hata_logla(f"Sondaj bilgileri kaydetme hatası: {str(e)}", e)
            return False
    
    def clear_form(self):
        """Form alanlarını temizler"""
        self.txt_sondor.clear()
        self.txt_kotu.setValue(0)
        self.txt_derinlik.setValue(0)
        self.date_baslama.setDate(QDate.currentDate())
        self.date_bitis.setDate(QDate.currentDate())
        self.txt_delgi_capi.setValue(0)
        self.txt_yer_alti_suyu.setValue(0)
        self.txt_ud_ornekleri.clear()
        self.cmb_zemin_tipi.setCurrentIndex(0)
        self.cmb_makine_tipi.setCurrentIndex(0)
        self.cmb_spt_tip.setCurrentIndex(0)
    
    def save_triggered(self):
        """Kaydet butonu tıklandığında çağrılır"""
        self.dataChanged.emit()

class AraziFormWidget(QWidget):
    """Arazi bilgileri formu"""
    
    dataChanged = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.arazi_id = None
        self.setupUI()
        
    def setupUI(self):
        """Form arayüzünü oluşturur"""
        # Ana düzen
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Form kısmı
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        # Form alanları
        self.txt_sondaj_derinligi = QDoubleSpinBox()
        self.txt_sondaj_derinligi.setDecimals(2)
        self.txt_sondaj_derinligi.setRange(0, 999.99)
        
        self.txt_muhafaza_derinligi = QDoubleSpinBox()
        self.txt_muhafaza_derinligi.setDecimals(2)
        self.txt_muhafaza_derinligi.setRange(0, 999.99)
        
        self.txt_kuyu_ici_deneyler = QLineEdit()
        self.txt_ornek_derinligi = QLineEdit()
        self.txt_ornek_turu = QLineEdit()
        
        self.txt_spt_0_15 = QSpinBox()
        self.txt_spt_0_15.setRange(0, 99)
        
        self.txt_spt_15_30 = QSpinBox()
        self.txt_spt_15_30.setRange(0, 99)
        
        self.txt_spt_30_45 = QSpinBox()
        self.txt_spt_30_45.setRange(0, 99)
        
        self.txt_n30 = QSpinBox()
        self.txt_n30.setRange(0, 99)
        
        self.txt_tmax = QDoubleSpinBox()
        self.txt_tmax.setDecimals(2)
        self.txt_tmax.setRange(0, 999.99)
        
        self.txt_tyogrulmus = QDoubleSpinBox()
        self.txt_tyogrulmus.setDecimals(2)
        self.txt_tyogrulmus.setRange(0, 999.99)
        
        self.txt_c_kpa = QDoubleSpinBox()
        self.txt_c_kpa.setDecimals(2)
        self.txt_c_kpa.setRange(0, 999.99)
        
        self.txt_aci = QDoubleSpinBox()
        self.txt_aci.setDecimals(2)
        self.txt_aci.setRange(0, 99.99)
        
        self.txt_dogal_birim_hacim = QDoubleSpinBox()
        self.txt_dogal_birim_hacim.setDecimals(2)
        self.txt_dogal_birim_hacim.setRange(0, 99.99)
        
        self.txt_kuru_birim_hacim = QDoubleSpinBox()
        self.txt_kuru_birim_hacim.setDecimals(2)
        self.txt_kuru_birim_hacim.setRange(0, 99.99)
        
        self.txt_zemin_profili = QLineEdit()
        self.txt_zemin_tanimlamasi = QLineEdit()
        
        # Form düzeni
        form_layout.addRow("Sondaj Derinliği (m):", self.txt_sondaj_derinligi)
        form_layout.addRow("Muhafaza Borusu Derinliği (m):", self.txt_muhafaza_derinligi)
        form_layout.addRow("Kuyu İçi Deneyler:", self.txt_kuyu_ici_deneyler)
        form_layout.addRow("Örnek Derinliği (m):", self.txt_ornek_derinligi)
        form_layout.addRow("Örnek Türü ve No.:", self.txt_ornek_turu)
        form_layout.addRow("SPT 0-15:", self.txt_spt_0_15)
        form_layout.addRow("SPT 15-30:", self.txt_spt_15_30)
        form_layout.addRow("SPT 30-45:", self.txt_spt_30_45)
        form_layout.addRow("N30:", self.txt_n30)
        form_layout.addRow("Tmax:", self.txt_tmax)
        form_layout.addRow("TYoğrulmuş:", self.txt_tyogrulmus)
        form_layout.addRow("C (kpa):", self.txt_c_kpa)
        form_layout.addRow("Ø (derece):", self.txt_aci)
        form_layout.addRow("Doğal B.H.A (kN/m³):", self.txt_dogal_birim_hacim)
        form_layout.addRow("Kuru B.H.A (kN/m³):", self.txt_kuru_birim_hacim)
        form_layout.addRow("Zemin Profili:", self.txt_zemin_profili)
        form_layout.addRow("Zemin Tanımlaması:", self.txt_zemin_tanimlamasi)
        
        # Butonlar
        button_layout = QHBoxLayout()
        
        self.btn_onceki = QPushButton("Önceki Kayıt")
        self.btn_onceki.clicked.connect(self.onceki_kayit)
        
        self.btn_kaydet = QPushButton("Arazi Bilgilerini Kaydet")
        self.btn_kaydet.setObjectName("success-btn")
        self.btn_kaydet.clicked.connect(self.save_triggered)
        
        self.btn_sonraki = QPushButton("Sonraki Kayıt")
        self.btn_sonraki.clicked.connect(self.sonraki_kayit)
        
        self.btn_yeni = QPushButton("Yeni Kayıt")
        self.btn_yeni.clicked.connect(self.yeni_kayit)
        
        button_layout.addWidget(self.btn_onceki)
        button_layout.addWidget(self.btn_kaydet)
        button_layout.addWidget(self.btn_sonraki)
        button_layout.addWidget(self.btn_yeni)
        
        # Ana düzene ekle
        layout.addLayout(form_layout)
        layout.addLayout(button_layout)
        
        # Veri değişikliği sinyallerini bağla
        self.txt_sondaj_derinligi.valueChanged.connect(self.dataChanged)
        self.txt_muhafaza_derinligi.valueChanged.connect(self.dataChanged)
        self.txt_kuyu_ici_deneyler.textChanged.connect(self.dataChanged)
        self.txt_ornek_derinligi.textChanged.connect(self.dataChanged)
        self.txt_ornek_turu.textChanged.connect(self.dataChanged)
        self.txt_spt_0_15.valueChanged.connect(self.dataChanged)
        self.txt_spt_15_30.valueChanged.connect(self.dataChanged)
        self.txt_spt_30_45.valueChanged.connect(self.dataChanged)
        self.txt_n30.valueChanged.connect(self.dataChanged)
        self.txt_tmax.valueChanged.connect(self.dataChanged)
        self.txt_tyogrulmus.valueChanged.connect(self.dataChanged)
        self.txt_c_kpa.valueChanged.connect(self.dataChanged)
        self.txt_aci.valueChanged.connect(self.dataChanged)
        self.txt_dogal_birim_hacim.valueChanged.connect(self.dataChanged)
        self.txt_kuru_birim_hacim.valueChanged.connect(self.dataChanged)
        self.txt_zemin_profili.textChanged.connect(self.dataChanged)
        self.txt_zemin_tanimlamasi.textChanged.connect(self.dataChanged)
    
    def load_data(self, proje_id):
        """Veritabanından verileri yükler"""
        try:
            self.proje_id = proje_id
            with veritabani_baglantisi() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM AraziBilgileri
                    WHERE proje_id = ?
                    ORDER BY "Sondaj derinliği (m)"
                """, (proje_id,))
                
                self.arazi_kayitlari = cursor.fetchall()
                
                if self.arazi_kayitlari:
                    # İlk kaydı yükle
                    self.mevcut_kayit_indeksi = 0
                    self.kayit_goster(self.mevcut_kayit_indeksi)
                else:
                    # Yeni kayıt
                    self.clear_form()
                    self.arazi_id = None
                    self.btn_onceki.setEnabled(False)
                    self.btn_sonraki.setEnabled(False)
            
            return True
        except Exception as e:
            hata_logla(f"Arazi bilgileri yükleme hatası: {str(e)}", e)
            return False
    
    def kayit_goster(self, indeks):
        """Belirli bir indeksteki kaydı gösterir"""
        if not hasattr(self, 'arazi_kayitlari') or not self.arazi_kayitlari:
            self.clear_form()
            self.arazi_id = None
            self.btn_onceki.setEnabled(False)
            self.btn_sonraki.setEnabled(False)
            return
        
        if 0 <= indeks < len(self.arazi_kayitlari):
            self.mevcut_kayit_indeksi = indeks
            kayit = self.arazi_kayitlari[indeks]
            self.arazi_id = kayit["id"]
            
            # Form alanlarını doldur
            if kayit["Sondaj derinliği (m)"] is not None:
                self.txt_sondaj_derinligi.setValue(kayit["Sondaj derinliği (m)"])
            else:
                self.txt_sondaj_derinligi.setValue(0)
                
            if kayit["Muhafaza borusu derinliği"] is not None:
                self.txt_muhafaza_derinligi.setValue(kayit["Muhafaza borusu derinliği"])
            else:
                self.txt_muhafaza_derinligi.setValue(0)
            
            self.txt_kuyu_ici_deneyler.setText(kayit["Kuyu içi deneyler"] or "")
            self.txt_ornek_derinligi.setText(kayit["Örnek derinliği (m)"] or "")
            self.txt_ornek_turu.setText(kayit["Örnek türü ve no."] or "")
            
            self.txt_spt_0_15.setValue(kayit["SPT0-15"] or 0)
            self.txt_spt_15_30.setValue(kayit["SPT15-30"] or 0)
            self.txt_spt_30_45.setValue(kayit["SPT30-45"] or 0)
            self.txt_n30.setValue(kayit["N30"] or 0)
            
            if kayit["Tmax"] is not None:
                self.txt_tmax.setValue(kayit["Tmax"])
            else:
                self.txt_tmax.setValue(0)
                
            if kayit["TYoğrulmuş"] is not None:
                self.txt_tyogrulmus.setValue(kayit["TYoğrulmuş"])
            else:
                self.txt_tyogrulmus.setValue(0)
                
            if kayit["C (kpa)"] is not None:
                self.txt_c_kpa.setValue(kayit["C (kpa)"])
            else:
                self.txt_c_kpa.setValue(0)
                
            if kayit["Ø(derece)"] is not None:
                self.txt_aci.setValue(kayit["Ø(derece)"])
            else:
                self.txt_aci.setValue(0)
                
            if kayit["Doğal B.H.A(kN/m3)"] is not None:
                self.txt_dogal_birim_hacim.setValue(kayit["Doğal B.H.A(kN/m3)"])
            else:
                self.txt_dogal_birim_hacim.setValue(0)
                
            if kayit["Kuru B.H.A (kN/m3)"] is not None:
                self.txt_kuru_birim_hacim.setValue(kayit["Kuru B.H.A (kN/m3)"])
            else:
                self.txt_kuru_birim_hacim.setValue(0)
            
            self.txt_zemin_profili.setText(kayit["Zemin profili"] or "")
            self.txt_zemin_tanimlamasi.setText(kayit["Zemin tanımlaması"] or "")
            
            # Navigasyon butonlarını güncelle
            self.btn_onceki.setEnabled(indeks > 0)
            self.btn_sonraki.setEnabled(indeks < len(self.arazi_kayitlari) - 1)
    
    def save_data(self, proje_id=None):
        """Verileri veritabanına kaydeder"""
        if proje_id is None:
            proje_id = self.proje_id
            
        if not proje_id:
            uyari_goster(self, "Proje Seçilmedi", "Lütfen önce bir proje seçin.")
            return False
        
        try:
            with veritabani_baglantisi() as conn:
                cursor = conn.cursor()
                
                # Eğer bir arazi_id varsa, mevcut kaydı güncelle
                if self.arazi_id:
                    cursor.execute("""
                        UPDATE AraziBilgileri
                        SET "Sondaj derinliği (m)" = ?, 
                            "Muhafaza borusu derinliği" = ?, 
                            "Kuyu içi deneyler" = ?, 
                            "Örnek derinliği (m)" = ?, 
                            "Örnek türü ve no." = ?, 
                            "SPT0-15" = ?, 
                            "SPT15-30" = ?, 
                            "SPT30-45" = ?, 
                            "N30" = ?, 
                            "Tmax" = ?, 
                            "TYoğrulmuş" = ?, 
                            "C (kpa)" = ?, 
                            "Ø(derece)" = ?, 
                            "Doğal B.H.A(kN/m3)" = ?, 
                            "Kuru B.H.A (kN/m3)" = ?, 
                            "Zemin profili" = ?, 
                            "Zemin tanımlaması" = ?
                        WHERE id = ?
                    """, (
                        self.txt_sondaj_derinligi.value(),
                        self.txt_muhafaza_derinligi.value(),
                        self.txt_kuyu_ici_deneyler.text(),
                        self.txt_ornek_derinligi.text(),
                        self.txt_ornek_turu.text(),
                        self.txt_spt_0_15.value(),
                        self.txt_spt_15_30.value(),
                        self.txt_spt_30_45.value(),
                        self.txt_n30.value(),
                        self.txt_tmax.value(),
                        self.txt_tyogrulmus.value(),
                        self.txt_c_kpa.value(),
                        self.txt_aci.value(),
                        self.txt_dogal_birim_hacim.value(),
                        self.txt_kuru_birim_hacim.value(),
                        self.txt_zemin_profili.text(),
                        self.txt_zemin_tanimlamasi.text(),
                        self.arazi_id
                    ))
                else:
                    # Yeni kayıt oluştur
                    cursor.execute("""
                        INSERT INTO AraziBilgileri
                        (proje_id, "Sondaj derinliği (m)", "Muhafaza borusu derinliği", 
                         "Kuyu içi deneyler", "Örnek derinliği (m)", "Örnek türü ve no.", 
                         "SPT0-15", "SPT15-30", "SPT30-45", "N30", "Tmax", "TYoğrulmuş", 
                         "C (kpa)", "Ø(derece)", "Doğal B.H.A(kN/m3)", "Kuru B.H.A (kN/m3)", 
                         "Zemin profili", "Zemin tanımlaması")
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        proje_id,
                        self.txt_sondaj_derinligi.value(),
                        self.txt_muhafaza_derinligi.value(),
                        self.txt_kuyu_ici_deneyler.text(),
                        self.txt_ornek_derinligi.text(),
                        self.txt_ornek_turu.text(),
                        self.txt_spt_0_15.value(),
                        self.txt_spt_15_30.value(),
                        self.txt_spt_30_45.value(),
                        self.txt_n30.value(),
                        self.txt_tmax.value(),
                        self.txt_tyogrulmus.value(),
                        self.txt_c_kpa.value(),
                        self.txt_aci.value(),
                        self.txt_dogal_birim_hacim.value(),
                        self.txt_kuru_birim_hacim.value(),
                        self.txt_zemin_profili.text(),
                        self.txt_zemin_tanimlamasi.text()
                    ))
                    self.arazi_id = cursor.lastrowid
                
                conn.commit()
                
                # Kayıtları yeniden yükle
                self.load_data(proje_id)
            
            return True
        except Exception as e:
            hata_logla(f"Arazi bilgileri kaydetme hatası: {str(e)}", e)
            return False
    
    def clear_form(self):
        """Form alanlarını temizler"""
        self.txt_sondaj_derinligi.setValue(0)
        self.txt_muhafaza_derinligi.setValue(0)
        self.txt_kuyu_ici_deneyler.clear()
        self.txt_ornek_derinligi.clear()
        self.txt_ornek_turu.clear()
        self.txt_spt_0_15.setValue(0)
        self.txt_spt_15_30.setValue(0)
        self.txt_spt_30_45.setValue(0)
        self.txt_n30.setValue(0)
        self.txt_tmax.setValue(0)
        self.txt_tyogrulmus.setValue(0)
        self.txt_c_kpa.setValue(0)
        self.txt_aci.setValue(0)
        self.txt_dogal_birim_hacim.setValue(0)
        self.txt_kuru_birim_hacim.setValue(0)
        self.txt_zemin_profili.clear()
        self.txt_zemin_tanimlamasi.clear()
    
    def onceki_kayit(self):
        """Önceki kaydı gösterir"""
        if hasattr(self, 'mevcut_kayit_indeksi') and self.mevcut_kayit_indeksi > 0:
            self.kayit_goster(self.mevcut_kayit_indeksi - 1)
    
    def sonraki_kayit(self):
        """Sonraki kaydı gösterir"""
        if (hasattr(self, 'mevcut_kayit_indeksi') and 
            hasattr(self, 'arazi_kayitlari') and 
            self.mevcut_kayit_indeksi < len(self.arazi_kayitlari) - 1):
            self.kayit_goster(self.mevcut_kayit_indeksi + 1)
    
    def yeni_kayit(self):
        """Yeni kayıt formu açar"""
        # Mevcut kayıttaki değişiklikleri kaydet sorusu
        if hasattr(self, 'arazi_id') and self.arazi_id:
            if onay_al(self, "Kaydet", "Mevcut kayıttaki değişiklikleri kaydetmek istiyor musunuz?"):
                self.save_data()
        
        # Yeni kayıt için form temizle
        self.clear_form()
        self.arazi_id = None
        
        # Navigasyon butonlarını güncelle
        self.btn_onceki.setEnabled(True)
        self.btn_sonraki.setEnabled(False)
    
    def save_triggered(self):
        """Kaydet butonu tıklandığında çağrılır"""
        if self.save_data():
            bilgi_goster(self, "Kayıt Başarılı", "Arazi bilgileri başarıyla kaydedildi.")
        else:
            hata_goster(self, "Kayıt Hatası", "Arazi bilgileri kaydedilirken bir hata oluştu.")
