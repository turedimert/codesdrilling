import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
import matplotlib.pyplot as plt
import tempfile
from utils import veritabani_baglantisi, hata_logla

class SondajRaporuOlusturucu:
    """Sondaj projesi için PDF raporu oluşturan sınıf"""
    
    def __init__(self, proje_id, cikti_dizini="raporlar"):
        """
        Rapor oluşturucu başlatır
        
        Args:
            proje_id: Raporlanacak proje ID'si
            cikti_dizini: Raporun kaydedileceği dizin
        """
        self.proje_id = proje_id
        self.cikti_dizini = cikti_dizini
        self.proje_bilgileri = None
        self.tapu_bilgileri = None
        self.sondaj_bilgileri = None
        self.arazi_bilgileri = None
        self.styles = getSampleStyleSheet()
        
        # Özel stiller
        self.styles.add(ParagraphStyle(
            name='TurkishTitle',
            parent=self.styles['Title'],
            fontName='Helvetica-Bold',
            fontSize=16,
            alignment=1,
            spaceAfter=14
        ))
        
        self.styles.add(ParagraphStyle(
            name='TurkishHeading1',
            parent=self.styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=14,
            spaceAfter=10
        ))
        
        self.styles.add(ParagraphStyle(
            name='TurkishBodyText',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            spaceAfter=8
        ))
        
    def veri_yukle(self):
        """Veritabanından gerekli bilgileri yükler"""
        try:
            with veritabani_baglantisi() as conn:
                cursor = conn.cursor()
                
                # Proje bilgilerini al
                cursor.execute("""
                    SELECT * FROM Projeler 
                    WHERE id = ?
                """, (self.proje_id,))
                self.proje_bilgileri = cursor.fetchone()
                
                # Tapu bilgilerini al
                cursor.execute("""
                    SELECT * FROM TapuBilgileri 
                    WHERE proje_id = ?
                """, (self.proje_id,))
                self.tapu_bilgileri = cursor.fetchone()
                
                # Sondaj bilgilerini al
                cursor.execute("""
                    SELECT * FROM SondajBilgileri 
                    WHERE proje_id = ?
                """, (self.proje_id,))
                self.sondaj_bilgileri = cursor.fetchone()
                
                # Arazi bilgilerini al
                cursor.execute("""
                    SELECT * FROM AraziBilgileri 
                    WHERE proje_id = ?
                    ORDER BY "Sondaj derinliği (m)"
                """, (self.proje_id,))
                self.arazi_bilgileri = cursor.fetchall()
                
                if not self.proje_bilgileri:
                    raise ValueError(f"Proje bulunamadı (ID: {self.proje_id})")
                    
                return True
                
        except Exception as e:
            hata_logla(f"Rapor için veri yükleme hatası: {str(e)}", e)
            return False
    
    def spt_grafik_olustur(self):
        """SPT verilerinin grafiğini oluşturur"""
        try:
            if not self.arazi_bilgileri:
                return None
                
            # SPT verilerini filtrele
            derinlikler = []
            n30_degerleri = []
            
            for veri in self.arazi_bilgileri:
                if veri["N30"] is not None:
                    derinlikler.append(veri["Sondaj derinliği (m)"])
                    n30_degerleri.append(veri["N30"])
            
            if not derinlikler:
                return None
                
            # Geçici dosya oluştur
            fd, path = tempfile.mkstemp(suffix='.png')
            os.close(fd)
            
            # Grafiği oluştur
            plt.figure(figsize=(5, 8))
            plt.barh(derinlikler, n30_degerleri, height=0.5, color='blue', alpha=0.7)
            plt.gca().invert_yaxis()  # Derinlik yukarıdan aşağıya artsın
            plt.xlabel('N30 Değeri')
            plt.ylabel('Derinlik (m)')
            plt.title('SPT N30 Değerleri - Derinlik Grafiği')
            plt.grid(True, linestyle='--', alpha=0.7)
            plt.tight_layout()
            plt.savefig(path)
            plt.close()
            
            return path
            
        except Exception as e:
            hata_logla(f"SPT grafiği oluşturma hatası: {str(e)}", e)
            return None
    
    def zemin_profili_grafik_olustur(self):
        """Zemin profili grafiğini oluşturur"""
        try:
            if not self.arazi_bilgileri:
                return None
            
            # Zemin profili verilerini filtrele
            derinlikler = []
            zemin_turleri = []
            
            for veri in self.arazi_bilgileri:
                if veri["Zemin tanımlaması"] is not None:
                    derinlikler.append(veri["Sondaj derinliği (m)"])
                    zemin_turleri.append(veri["Zemin tanımlaması"])
            
            if not derinlikler:
                return None
                
            # Geçici dosya oluştur
            fd, path = tempfile.mkstemp(suffix='.png')
            os.close(fd)
            
            # Benzersiz zemin türlerini bul
            benzersiz_zeminler = list(set(zemin_turleri))
            renkler = plt.cm.tab10(range(len(benzersiz_zeminler)))
            zemin_renk_map = {zemin: renkler[i] for i, zemin in enumerate(benzersiz_zeminler)}
            
            # Grafiği oluştur
            fig, ax = plt.subplots(figsize=(4, 8))
            prev_depth = 0
            
            for i, (derinlik, zemin) in enumerate(zip(derinlikler, zemin_turleri)):
                height = derinlik - prev_depth
                ax.bar(0.5, height, bottom=prev_depth, width=1, 
                       color=zemin_renk_map[zemin], alpha=0.7)
                ax.text(0.5, prev_depth + height/2, f"{zemin}", 
                       ha='center', va='center', fontsize=8,
                       bbox=dict(facecolor='white', alpha=0.5))
                prev_depth = derinlik
                ax.axhline(y=derinlik, color='black', linestyle='-', alpha=0.3)
            
            ax.set_xlim(0, 1)
            ax.set_title('Zemin Profili')
            ax.set_ylabel('Derinlik (m)')
            ax.invert_yaxis()
            ax.set_xticks([])
            
            # Lejant oluştur
            patches = [plt.Rectangle((0,0),1,1, color=zemin_renk_map[label]) for label in benzersiz_zeminler]
            plt.legend(patches, benzersiz_zeminler, loc='best', title="Zemin Türleri")
            
            plt.tight_layout()
            plt.savefig(path)
            plt.close()
            
            return path
            
        except Exception as e:
            hata_logla(f"Zemin profili grafiği oluşturma hatası: {str(e)}", e)
            return None
    
    def rapor_olustur(self):
        """PDF raporu oluşturur ve kaydeder"""
        try:
            if not self.veri_yukle():
                return None, "Veritabanından veri yüklenemedi"
            
            # Çıktı dizinini kontrol et
            if not os.path.exists(self.cikti_dizini):
                os.makedirs(self.cikti_dizini)
            
            # Rapor dosya adı
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            proje_adi = self.proje_bilgileri["proje_adi"].replace(" ", "_")
            rapor_dosyasi = os.path.join(self.cikti_dizini, f"{proje_adi}_rapor_{timestamp}.pdf")
            
            # PDF oluştur
            doc = SimpleDocTemplate(
                rapor_dosyasi,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )
            
            # İçerik listesi
            story = []
            
            # Başlık
            story.append(Paragraph(f"SONDAJ RAPORU: {self.proje_bilgileri['proje_adi']}", self.styles['TurkishTitle']))
            story.append(Spacer(1, 0.5*cm))
            
            # Proje bilgileri
            story.append(Paragraph("1. PROJE BİLGİLERİ", self.styles['TurkishHeading1']))
            
            proje_tablo_verisi = [
                ["Proje Adı", self.proje_bilgileri["proje_adi"]],
                ["Yüklenici Firma", self.proje_bilgileri["yuklenici_firma"] or "-"],
                ["Sorumlu Mühendis", self.proje_bilgileri["sorumlu_muhendis"] or "-"],
                ["Rapor Tarihi", datetime.now().strftime("%d.%m.%Y")]
            ]
            
            t = Table(proje_tablo_verisi, colWidths=[doc.width/3, doc.width*2/3])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(t)
            story.append(Spacer(1, 0.5*cm))
            
            # Tapu bilgileri
            story.append(Paragraph("2. TAPU BİLGİLERİ", self.styles['TurkishHeading1']))
            
            if self.tapu_bilgileri:
                tapu_tablo_verisi = [
                    ["İl", self.tapu_bilgileri["il"] or "-"],
                    ["İlçe", self.tapu_bilgileri["ilce"] or "-"],
                    ["Mahalle", self.tapu_bilgileri["mahalle"] or "-"],
                    ["Ada", self.tapu_bilgileri["ada"] or "-"],
                    ["Pafta", self.tapu_bilgileri["pafta"] or "-"],
                    ["Parsel", self.tapu_bilgileri["parsel"] or "-"],
                    ["Koordinat X", str(self.tapu_bilgileri["koordinat_x"] or "-")],
                    ["Koordinat Y", str(self.tapu_bilgileri["koordinat_y"] or "-")]
                ]
                
                t = Table(tapu_tablo_verisi, colWidths=[doc.width/3, doc.width*2/3])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                    ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(t)
            else:
                story.append(Paragraph("Tapu bilgisi bulunamadı.", self.styles['TurkishBodyText']))
            
            story.append(Spacer(1, 0.5*cm))
            
            # Sondaj bilgileri
            story.append(Paragraph("3. SONDAJ BİLGİLERİ", self.styles['TurkishHeading1']))
            
            if self.sondaj_bilgileri:
                sondaj_tablo_verisi = [
                    ["Sondör Adı", self.sondaj_bilgileri["sondor_adi"] or "-"],
                    ["Sondaj Kotu", str(self.sondaj_bilgileri["sondaj_kotu"] or "-")],
                    ["Sondaj Derinliği", str(self.sondaj_bilgileri["sondaj_derinligi"] or "-")],
                    ["Başlama Tarihi", self.sondaj_bilgileri["baslama_tarihi"] or "-"],
                    ["Bitiş Tarihi", self.sondaj_bilgileri["bitis_tarihi"] or "-"],
                    ["Delgi Çapı", str(self.sondaj_bilgileri["delgi_capi"] or "-")],
                    ["Yeraltı Suyu", str(self.sondaj_bilgileri["yer_alti_suyu"] or "-")],
                    ["UD Örnekleri", self.sondaj_bilgileri["ud_ornekleri"] or "-"],
                    ["Zemin Tipi", self.sondaj_bilgileri["zemin_tipi"] or "-"],
                    ["Makine Tipi", self.sondaj_bilgileri["makine_tipi"] or "-"],
                    ["SPT Şahmerdan Tipi", self.sondaj_bilgileri["spt_sahmerdan_tipi"] or "-"]
                ]
                
                t = Table(sondaj_tablo_verisi, colWidths=[doc.width/3, doc.width*2/3])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                    ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(t)
            else:
                story.append(Paragraph("Sondaj bilgisi bulunamadı.", self.styles['TurkishBodyText']))
            
            story.append(Spacer(1, 0.5*cm))
            
            # Arazi bilgileri
            story.append(Paragraph("4. ARAZİ DENEY BİLGİLERİ", self.styles['TurkishHeading1']))
            
            if self.arazi_bilgileri:
                # Arazi tablo verileri
                arazi_tablo_baslik = [
                    "Derinlik (m)", "SPT N30", "Zemin Tanımlaması",
                    "C (kpa)", "Ø(derece)", "Doğal B.H.A (kN/m³)"
                ]
                
                arazi_tablo_verisi = [arazi_tablo_baslik]
                
                for veri in self.arazi_bilgileri:
                    arazi_tablo_verisi.append([
                        str(veri["Sondaj derinliği (m)"] or "-"),
                        str(veri["N30"] or "-"),
                        veri["Zemin tanımlaması"] or "-",
                        str(veri["C (kpa)"] or "-"),
                        str(veri["Ø(derece)"] or "-"),
                        str(veri["Doğal B.H.A(kN/m3)"] or "-")
                    ])
                
                t = Table(arazi_tablo_verisi, colWidths=[doc.width/6] * 6)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(t)
            else:
                story.append(Paragraph("Arazi bilgisi bulunamadı.", self.styles['TurkishBodyText']))
            
            story.append(Spacer(1, 0.5*cm))
            
            # Grafikler
            story.append(Paragraph("5. DENEY GRAFİKLERİ", self.styles['TurkishHeading1']))
            
            # SPT Grafiği
            spt_grafik_yolu = self.spt_grafik_olustur()
            if spt_grafik_yolu:
                story.append(Paragraph("5.1. SPT Değerleri Grafiği", self.styles['TurkishHeading1']))
                img = Image(spt_grafik_yolu, width=doc.width*0.7, height=doc.width*1.2)
                story.append(img)
                story.append(Spacer(1, 0.5*cm))
            
            # Zemin Profili Grafiği
            zemin_grafik_yolu = self.zemin_profili_grafik_olustur()
            if zemin_grafik_yolu:
                story.append(Paragraph("5.2. Zemin Profili Grafiği", self.styles['TurkishHeading1']))
                img = Image(zemin_grafik_yolu, width=doc.width*0.7, height=doc.width*1.2)
                story.append(img)
                story.append(Spacer(1, 0.5*cm))
            
            # Sonuç ve imza
            story.append(Paragraph("6. SONUÇ VE DEĞERLENDİRME", self.styles['TurkishHeading1']))
            story.append(Paragraph("Bu rapor, sondaj çalışması sonucunda elde edilen verileri içermektedir. Zemin etüt ve değerlendirme çalışmaları için bir kaynak olarak kullanılabilir.", self.styles['TurkishBodyText']))
            
            story.append(Spacer(1, 1*cm))
            story.append(Paragraph(f"Sorumlu Mühendis: {self.proje_bilgileri['sorumlu_muhendis'] or 'Belirtilmemiş'}", self.styles['TurkishBodyText']))
            story.append(Paragraph(f"Rapor Tarihi: {datetime.now().strftime('%d.%m.%Y')}", self.styles['TurkishBodyText']))
            
            # PDF dosyasını oluştur
            doc.build(story)
            
            # Geçici grafik dosyalarını temizle
            if spt_grafik_yolu and os.path.exists(spt_grafik_yolu):
                os.remove(spt_grafik_yolu)
            if zemin_grafik_yolu and os.path.exists(zemin_grafik_yolu):
                os.remove(zemin_grafik_yolu)
            
            return rapor_dosyasi, "Rapor başarıyla oluşturuldu."
            
        except Exception as e:
            hata_mesaji = f"Rapor oluşturma hatası: {str(e)}"
            hata_logla(hata_mesaji, e)
            return None, hata_mesaji
