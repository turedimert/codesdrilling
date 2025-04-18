import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
from PyQt6.QtWidgets import QVBoxLayout, QWidget
from PyQt6.QtCore import Qt
from utils import hata_logla, veritabani_baglantisi

class MatplotlibCanvas(FigureCanvas):
    """Matplotlib için Qt özellikleriyle genişletilmiş tuval sınıfı"""
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        """
        Canvas oluşturur
        
        Args:
            parent: Ebeveyn widget
            width: Genişlik (inç)
            height: Yükseklik (inç)
            dpi: Çözünürlük (dots per inch)
        """
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super(MatplotlibCanvas, self).__init__(self.fig)

class SondajGrafikWidget(QWidget):
    """Sondaj verilerini görselleştirmek için widget"""
    def __init__(self, parent=None):
        super(SondajGrafikWidget, self).__init__(parent)
        self.layout = QVBoxLayout(self)
        self.canvas = MatplotlibCanvas(self, width=5, height=8, dpi=100)
        self.layout.addWidget(self.canvas)
        self.setLayout(self.layout)
        
    def spt_verileri_goster(self, proje_id):
        """
        SPT verilerini gösteren grafik oluşturur
        
        Args:
            proje_id: Projenin ID'si
        """
        try:
            with veritabani_baglantisi() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT "Sondaj derinliği (m)", "N30"
                    FROM AraziBilgileri
                    WHERE proje_id = ? AND "N30" IS NOT NULL
                    ORDER BY "Sondaj derinliği (m)"
                """, (proje_id,))
                
                veriler = cursor.fetchall()
                
                if not veriler:
                    self.canvas.axes.clear()
                    self.canvas.axes.text(0.5, 0.5, "Bu proje için SPT verisi bulunamadı", 
                                         ha='center', va='center', fontsize=12)
                    self.canvas.fig.tight_layout()
                    self.canvas.draw()
                    return
                    
                derinlikler = [row["Sondaj derinliği (m)"] for row in veriler]
                n30_degerleri = [row["N30"] for row in veriler]
                
                self.canvas.axes.clear()
                self.canvas.axes.barh(derinlikler, n30_degerleri, height=0.5, color='blue', alpha=0.7)
                
                # Y eksenini ters çevir (derinlik yukarıdan aşağıya artsın)
                self.canvas.axes.invert_yaxis()
                
                # Diğer grafik detayları
                self.canvas.axes.set_xlabel('N30 Değeri')
                self.canvas.axes.set_ylabel('Derinlik (m)')
                self.canvas.axes.set_title('SPT N30 Değerleri - Derinlik Grafiği')
                self.canvas.axes.grid(True, linestyle='--', alpha=0.7)
                
                # Referans çizgileri
                self.canvas.axes.axvline(x=10, color='r', linestyle='--', alpha=0.5)
                self.canvas.axes.axvline(x=30, color='r', linestyle='--', alpha=0.5)
                self.canvas.axes.axvline(x=50, color='r', linestyle='--', alpha=0.5)
                
                # Değerleri grafik üzerine ekle
                for i, v in enumerate(n30_degerleri):
                    self.canvas.axes.text(v + 1, derinlikler[i], str(v), 
                                         va='center', fontsize=8)
                
                self.canvas.fig.tight_layout()
                self.canvas.draw()
                
        except Exception as e:
            hata_logla(f"SPT grafiği oluşturma hatası: {str(e)}", e)
            self.canvas.axes.clear()
            self.canvas.axes.text(0.5, 0.5, f"Grafik oluşturma hatası: {str(e)}", 
                               ha='center', va='center', fontsize=10, color='red')
            self.canvas.fig.tight_layout()
            self.canvas.draw()

    def zemin_profili_goster(self, proje_id):
        """
        Zemin profili grafiği oluşturur
        
        Args:
            proje_id: Projenin ID'si
        """
        try:
            with veritabani_baglantisi() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT "Sondaj derinliği (m)", "Zemin tanımlaması"
                    FROM AraziBilgileri
                    WHERE proje_id = ? AND "Zemin tanımlaması" IS NOT NULL
                    ORDER BY "Sondaj derinliği (m)"
                """, (proje_id,))
                
                veriler = cursor.fetchall()
                
                if not veriler:
                    self.canvas.axes.clear()
                    self.canvas.axes.text(0.5, 0.5, "Bu proje için zemin profili verisi bulunamadı", 
                                         ha='center', va='center', fontsize=12)
                    self.canvas.fig.tight_layout()
                    self.canvas.draw()
                    return
                
                # Zemin türleri ve derinlikler
                derinlikler = [row["Sondaj derinliği (m)"] for row in veriler]
                zemin_turleri = [row["Zemin tanımlaması"] for row in veriler]
                
                # Benzersiz zemin türleri
                benzersiz_zeminler = list(set(zemin_turleri))
                
                # Her zemin türü için renk belirle
                renkler = plt.cm.tab10(np.linspace(0, 1, len(benzersiz_zeminler)))
                zemin_renk_map = {zemin: renkler[i] for i, zemin in enumerate(benzersiz_zeminler)}
                
                self.canvas.axes.clear()
                
                # Zemin profili çizim
                prev_depth = 0
                patches = []
                labels = []
                
                for i, (derinlik, zemin) in enumerate(zip(derinlikler, zemin_turleri)):
                    height = derinlik - prev_depth
                    rect = self.canvas.axes.bar(0.5, height, bottom=prev_depth, width=1, 
                                              color=zemin_renk_map[zemin], alpha=0.7)[0]
                    prev_depth = derinlik
                    
                    # Zemin tanımlaması ekle
                    self.canvas.axes.text(0.5, prev_depth - height/2, f"{zemin}", 
                                         ha='center', va='center', fontsize=8,
                                         bbox=dict(facecolor='white', alpha=0.5))
                    
                    # Derinlik çizgisi
                    self.canvas.axes.axhline(y=derinlik, color='black', linestyle='-', alpha=0.3)
                    
                    # Derinlik değerini ekle
                    self.canvas.axes.text(0.05, derinlik, f"{derinlik} m", 
                                         ha='left', va='bottom', fontsize=8)
                    
                    # Lejant için kaydet
                    if zemin not in labels:
                        patches.append(rect)
                        labels.append(zemin)
                
                # Lejant ekle
                self.canvas.axes.legend(patches, labels, loc='best', title="Zemin Türleri")
                
                self.canvas.axes.set_xlim(0, 1)
                self.canvas.axes.set_title('Zemin Profili')
                self.canvas.axes.set_ylabel('Derinlik (m)')
                self.canvas.axes.invert_yaxis()  # Derinlik yukarıdan aşağıya
                self.canvas.axes.set_xticks([])  # X eksenindeki işaretleri gizle
                
                self.canvas.fig.tight_layout()
                self.canvas.draw()
                
        except Exception as e:
            hata_logla(f"Zemin profili grafiği oluşturma hatası: {str(e)}", e)
            self.canvas.axes.clear()
            self.canvas.axes.text(0.5, 0.5, f"Grafik oluşturma hatası: {str(e)}", 
                               ha='center', va='center', fontsize=10, color='red')
            self.canvas.fig.tight_layout()
            self.canvas.draw()
