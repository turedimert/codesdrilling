import os
import logging
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, DateField, SelectField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Length, Email
import json
from datetime import datetime

# Uygulama oluşturma
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'xxx'), 'gizli_anahtar')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
# SSL bağlantı sorununu çözmek için bağlantı ayarları
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
    "connect_args": {
        "sslmode": "prefer"
    }
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Veritabanı ve Migrasyon Ayarları
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Login Manager Ayarları
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Lütfen giriş yapın.'
login_manager.login_message_category = 'warning'

# Veritabanı Modelleri
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Proje(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    proje_adi = db.Column(db.String(128), nullable=False)
    yuklenici_firma = db.Column(db.String(128))
    sorumlu_muhendis = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # İlişkiler
    tapu_bilgileri = db.relationship('TapuBilgileri', backref='proje', uselist=False, cascade='all, delete-orphan')
    sondaj_bilgileri = db.relationship('SondajBilgileri', backref='proje', uselist=False, cascade='all, delete-orphan')
    arazi_bilgileri = db.relationship('AraziBilgileri', backref='proje', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Proje {self.proje_adi}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'proje_adi': self.proje_adi,
            'yuklenici_firma': self.yuklenici_firma,
            'sorumlu_muhendis': self.sorumlu_muhendis,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class TapuBilgileri(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    proje_id = db.Column(db.Integer, db.ForeignKey('proje.id'), nullable=False)
    il = db.Column(db.String(64))
    ilce = db.Column(db.String(64))
    mahalle = db.Column(db.String(64))
    ada = db.Column(db.String(64))
    pafta = db.Column(db.String(64))
    parsel = db.Column(db.String(64))
    koordinat_x = db.Column(db.Float)
    koordinat_y = db.Column(db.Float)
    
    def __repr__(self):
        return f'<TapuBilgileri {self.id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'proje_id': self.proje_id,
            'il': self.il,
            'ilce': self.ilce,
            'mahalle': self.mahalle,
            'ada': self.ada,
            'pafta': self.pafta,
            'parsel': self.parsel,
            'koordinat_x': self.koordinat_x,
            'koordinat_y': self.koordinat_y
        }

class SondajBilgileri(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    proje_id = db.Column(db.Integer, db.ForeignKey('proje.id'), nullable=False)
    sondor_adi = db.Column(db.String(128))
    sondaj_kotu = db.Column(db.Float)
    sondaj_derinligi = db.Column(db.Float)
    baslama_tarihi = db.Column(db.Date)
    bitis_tarihi = db.Column(db.Date)
    delgi_capi = db.Column(db.Float)
    yer_alti_suyu = db.Column(db.Float)
    ud_ornekleri = db.Column(db.String(256))
    zemin_tipi = db.Column(db.String(128))
    makine_tipi = db.Column(db.String(128))
    spt_sahmerdan_tipi = db.Column(db.String(128))
    
    def __repr__(self):
        return f'<SondajBilgileri {self.id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'proje_id': self.proje_id,
            'sondor_adi': self.sondor_adi,
            'sondaj_kotu': self.sondaj_kotu,
            'sondaj_derinligi': self.sondaj_derinligi,
            'baslama_tarihi': self.baslama_tarihi.isoformat() if self.baslama_tarihi else None,
            'bitis_tarihi': self.bitis_tarihi.isoformat() if self.bitis_tarihi else None,
            'delgi_capi': self.delgi_capi,
            'yer_alti_suyu': self.yer_alti_suyu,
            'ud_ornekleri': self.ud_ornekleri,
            'zemin_tipi': self.zemin_tipi,
            'makine_tipi': self.makine_tipi,
            'spt_sahmerdan_tipi': self.spt_sahmerdan_tipi
        }

class AraziBilgileri(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    proje_id = db.Column(db.Integer, db.ForeignKey('proje.id'), nullable=False)
    sondaj_derinligi = db.Column(db.Float)
    muhafaza_borusu_derinligi = db.Column(db.Float)
    kuyu_ici_deneyler = db.Column(db.String(256))
    ornek_derinligi = db.Column(db.String(64))
    ornek_turu_no = db.Column(db.String(64))
    spt_0_15 = db.Column(db.Integer)
    spt_15_30 = db.Column(db.Integer)
    spt_30_45 = db.Column(db.Integer)
    n30 = db.Column(db.Integer)
    tmax = db.Column(db.Float)
    tyogrulmus = db.Column(db.Float)
    c_kpa = db.Column(db.Float)
    aci_derece = db.Column(db.Float)
    dogal_bha = db.Column(db.Float)
    kuru_bha = db.Column(db.Float)
    zemin_profili = db.Column(db.String(128))
    zemin_tanimlamasi = db.Column(db.String(256))
    
    def __repr__(self):
        return f'<AraziBilgileri {self.id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'proje_id': self.proje_id,
            'sondaj_derinligi': self.sondaj_derinligi,
            'muhafaza_borusu_derinligi': self.muhafaza_borusu_derinligi,
            'kuyu_ici_deneyler': self.kuyu_ici_deneyler,
            'ornek_derinligi': self.ornek_derinligi,
            'ornek_turu_no': self.ornek_turu_no,
            'spt_0_15': self.spt_0_15,
            'spt_15_30': self.spt_15_30,
            'spt_30_45': self.spt_30_45,
            'n30': self.n30,
            'tmax': self.tmax,
            'tyogrulmus': self.tyogrulmus,
            'c_kpa': self.c_kpa,
            'aci_derece': self.aci_derece,
            'dogal_bha': self.dogal_bha,
            'kuru_bha': self.kuru_bha,
            'zemin_profili': self.zemin_profili,
            'zemin_tanimlamasi': self.zemin_tanimlamasi
        }

# Formlar
class LoginForm(FlaskForm):
    username = StringField('Kullanıcı Adı', validators=[DataRequired()])
    password = PasswordField('Şifre', validators=[DataRequired()])
    remember = BooleanField('Beni Hatırla')
    submit = SubmitField('Giriş Yap')

class ProjeForm(FlaskForm):
    proje_adi = StringField('Proje Adı', validators=[DataRequired()])
    yuklenici_firma = StringField('Yüklenici Firma')
    sorumlu_muhendis = StringField('Sorumlu Mühendis')
    submit = SubmitField('Kaydet')

class TapuBilgileriForm(FlaskForm):
    il = StringField('İl')
    ilce = StringField('İlçe')
    mahalle = StringField('Mahalle')
    ada = StringField('Ada')
    pafta = StringField('Pafta')
    parsel = StringField('Parsel')
    koordinat_x = FloatField('Koordinat X')
    koordinat_y = FloatField('Koordinat Y')
    submit = SubmitField('Kaydet')

class SondajBilgileriForm(FlaskForm):
    sondor_adi = StringField('Sondör Adı')
    sondaj_kotu = FloatField('Sondaj Kotu')
    sondaj_derinligi = FloatField('Sondaj Derinliği')
    baslama_tarihi = DateField('Başlama Tarihi', format='%Y-%m-%d')
    bitis_tarihi = DateField('Bitiş Tarihi', format='%Y-%m-%d')
    delgi_capi = FloatField('Delgi Çapı')
    yer_alti_suyu = FloatField('Yeraltı Suyu')
    ud_ornekleri = StringField('UD Örnekleri')
    zemin_tipi = StringField('Zemin Tipi')
    makine_tipi = StringField('Makine Tipi')
    spt_sahmerdan_tipi = StringField('SPT Şahmerdan Tipi')
    submit = SubmitField('Kaydet')

class AraziBilgileriForm(FlaskForm):
    sondaj_derinligi = FloatField('Sondaj Derinliği (m)')
    muhafaza_borusu_derinligi = FloatField('Muhafaza Borusu Derinliği')
    kuyu_ici_deneyler = StringField('Kuyu İçi Deneyler')
    ornek_derinligi = StringField('Örnek Derinliği (m)')
    ornek_turu_no = StringField('Örnek Türü ve No.')
    spt_0_15 = StringField('SPT 0-15')
    spt_15_30 = StringField('SPT 15-30')
    spt_30_45 = StringField('SPT 30-45')
    n30 = StringField('N30')
    tmax = FloatField('Tmax')
    tyogrulmus = FloatField('TYoğrulmuş')
    c_kpa = FloatField('C (kpa)')
    aci_derece = FloatField('Ø(derece)')
    dogal_bha = FloatField('Doğal B.H.A(kN/m3)')
    kuru_bha = FloatField('Kuru B.H.A (kN/m3)')
    zemin_profili = StringField('Zemin Profili')
    zemin_tanimlamasi = StringField('Zemin Tanımlaması')
    submit = SubmitField('Kaydet')

# Kullanıcı yükleme
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Demo kullanıcısı oluşturma fonksiyonu
def create_demo_user():
    # Ek olarak admin kullanıcı da ekleyelim
    if not User.query.filter_by(username='admin').first():
        admin_user = User(
            username='admin',
            email='admin@sondaj.com',
            password='admin123',  # Gerçek uygulamada şifre hash'lenir!
            is_admin=True
        )
        db.session.add(admin_user)
        
    # Demo kullanıcı
    if not User.query.filter_by(username='demo').first():
        demo_user = User(
            username='demo',
            email='demo@sondaj.com',
            password='demo123',  # Gerçek uygulamada şifre hash'lenir!
            is_admin=True
        )
        db.session.add(demo_user)
        
    db.session.commit()

# Flask 2.0+ için alternatif ilk çalıştırma işlemi
with app.app_context():
    db.create_all()
    create_demo_user()

# Rotalar
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.password == form.password.data:  # Gerçek uygulamada şifre doğrulama kullanılır
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Giriş başarısız. Lütfen kullanıcı adı ve şifrenizi kontrol edin.', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    projeler = Proje.query.all()
    return render_template('dashboard.html', projeler=projeler)

# Proje İşlemleri
@app.route('/projeler')
@login_required
def proje_listesi():
    projeler = Proje.query.all()
    return render_template('projeler/liste.html', projeler=projeler)

@app.route('/projeler/yeni', methods=['GET', 'POST'])
@login_required
def proje_ekle():
    form = ProjeForm()
    if form.validate_on_submit():
        proje = Proje(
            proje_adi=form.proje_adi.data,
            yuklenici_firma=form.yuklenici_firma.data,
            sorumlu_muhendis=form.sorumlu_muhendis.data
        )
        db.session.add(proje)
        db.session.commit()
        flash('Proje başarıyla oluşturuldu!', 'success')
        return redirect(url_for('proje_detay', proje_id=proje.id))
    return render_template('projeler/ekle.html', form=form)

@app.route('/projeler/<int:proje_id>')
@login_required
def proje_detay(proje_id):
    proje = Proje.query.get_or_404(proje_id)
    return render_template('projeler/detay.html', proje=proje)

@app.route('/projeler/<int:proje_id>/duzenle', methods=['GET', 'POST'])
@login_required
def proje_duzenle(proje_id):
    proje = Proje.query.get_or_404(proje_id)
    form = ProjeForm(obj=proje)
    if form.validate_on_submit():
        form.populate_obj(proje)
        db.session.commit()
        flash('Proje bilgileri güncellendi!', 'success')
        return redirect(url_for('proje_detay', proje_id=proje.id))
    return render_template('projeler/duzenle.html', form=form, proje=proje)

@app.route('/projeler/<int:proje_id>/sil', methods=['POST'])
@login_required
def proje_sil(proje_id):
    proje = Proje.query.get_or_404(proje_id)
    db.session.delete(proje)
    db.session.commit()
    flash('Proje silindi!', 'success')
    return redirect(url_for('proje_listesi'))

# Tapu Bilgileri
@app.route('/projeler/<int:proje_id>/tapu', methods=['GET', 'POST'])
@login_required
def tapu_bilgileri(proje_id):
    proje = Proje.query.get_or_404(proje_id)
    tapu = proje.tapu_bilgileri or TapuBilgileri(proje_id=proje.id)
    form = TapuBilgileriForm(obj=tapu)
    
    if form.validate_on_submit():
        if not proje.tapu_bilgileri:
            tapu = TapuBilgileri(proje_id=proje.id)
            db.session.add(tapu)
        form.populate_obj(tapu)
        db.session.commit()
        flash('Tapu bilgileri kaydedildi!', 'success')
        return redirect(url_for('proje_detay', proje_id=proje.id))
    
    return render_template('projeler/tapu.html', form=form, proje=proje)

# Sondaj Bilgileri
@app.route('/projeler/<int:proje_id>/sondaj', methods=['GET', 'POST'])
@login_required
def sondaj_bilgileri(proje_id):
    proje = Proje.query.get_or_404(proje_id)
    sondaj = proje.sondaj_bilgileri or SondajBilgileri(proje_id=proje.id)
    form = SondajBilgileriForm(obj=sondaj)
    
    if form.validate_on_submit():
        if not proje.sondaj_bilgileri:
            sondaj = SondajBilgileri(proje_id=proje.id)
            db.session.add(sondaj)
        form.populate_obj(sondaj)
        db.session.commit()
        flash('Sondaj bilgileri kaydedildi!', 'success')
        return redirect(url_for('proje_detay', proje_id=proje.id))
    
    return render_template('projeler/sondaj.html', form=form, proje=proje)

# Arazi Bilgileri
@app.route('/projeler/<int:proje_id>/arazi', methods=['GET'])
@login_required
def arazi_bilgileri_liste(proje_id):
    proje = Proje.query.get_or_404(proje_id)
    arazi_bilgileri = AraziBilgileri.query.filter_by(proje_id=proje.id).all()
    return render_template('projeler/arazi_liste_tablo.html', proje=proje, arazi_bilgileri=arazi_bilgileri)

@app.route('/projeler/<int:proje_id>/arazi/ekle', methods=['GET', 'POST'])
@login_required
def arazi_bilgileri_ekle(proje_id):
    proje = Proje.query.get_or_404(proje_id)
    
    # Önceki kayıtları sil ve derinlik bilgisi al (POST metrajı oluştur)
    if request.method == 'POST' and 'metraj_olustur' in request.form:
        try:
            # Her zaman sondaj bilgilerinden derinliği al
            if proje.sondaj_bilgileri and proje.sondaj_bilgileri.sondaj_derinligi and proje.sondaj_bilgileri.sondaj_derinligi > 0:
                derinlik = proje.sondaj_bilgileri.sondaj_derinligi
                # Sondaj bilgilerinden derinliği formda göster
                form_derinlik = request.form.get('sondaj_derinligi', derinlik)
                # Eğer form derinliği girilmişse ve 0'dan büyükse ama sondaj derinliğinden farklıysa, uyarı göster
                if form_derinlik and float(form_derinlik) > 0 and abs(float(form_derinlik) - derinlik) > 0.01:
                    flash(f'Girdiğiniz derinlik ({form_derinlik}m) sondaj bilgilerindeki derinlikten ({derinlik}m) farklı. Sondaj bilgilerindeki derinlik kullanılacak.', 'warning')
            else:
                form_derinlik = request.form.get('sondaj_derinligi', '0')
                if not form_derinlik or float(form_derinlik) <= 0:
                    flash('Sondaj bilgilerinde tanımlı sondaj derinliği bulunamadı. Lütfen önce sondaj bilgilerini güncelleyin.', 'danger')
                    return render_template('projeler/arazi_ekle_tablo.html', proje=proje, arazi_kayitlari=[], 
                                          has_data=False, derinlik=None, spt_count=1, karot_count=1, ud_count=1)
                derinlik = float(form_derinlik)
            
            if derinlik <= 0:
                flash('Lütfen geçerli bir sondaj derinliği girin (0\'dan büyük).', 'danger')
                return render_template('projeler/arazi_ekle_tablo.html', proje=proje, arazi_kayitlari=[], 
                                      has_data=False, derinlik=None, spt_count=1, karot_count=1, ud_count=1)

            # Eğer kaydetme işlemi değilse, boş satır listesi hazırla
            arazi_kayitlari = []
            
            # Tam olarak orijinal koda göre metraj oluştur
            # Mevcut kayıtları sil
            AraziBilgileri.query.filter_by(proje_id=proje.id).delete()
            db.session.commit()
            
            # Debug bilgileri
            app.logger.info(f"Metraj oluşturma başlıyor. Proje ID: {proje.id}, Derinlik: {derinlik}m")
            
            # Tam orijinal PyQt6 kodu gibi metraj oluştur
            # Sondaj derinliğine göre 1.5 metre artışlı satırlar 
            current_depth = 0.0
            row = 0
            
            try:
                # Debug bilgisi
                app.logger.info(f"Metraj oluşturma döngüsü başlıyor")
                
                # Tam olarak orijinal kodun davranışını taklit ediyoruz
                # while current_depth < derinlik döngüsü kullanılıyor (çok önemli!)
                while current_depth < derinlik:
                    # Debug bilgisi
                    app.logger.info(f"Satır {row} oluşturuluyor, derinlik: {current_depth}m")
                    
                    # Veritabanına kaydet
                    yeni_arazi = AraziBilgileri(
                        proje_id=proje.id,
                        sondaj_derinligi=current_depth,
                        muhafaza_borusu_derinligi=current_depth,
                        kuyu_ici_deneyler='',
                        ornek_derinligi=f"{current_depth:.2f}-{(current_depth + 0.45):.2f}",
                        ornek_turu_no='',
                        spt_0_15=0,
                        spt_15_30=0,
                        spt_30_45=0,
                        n30=0,
                        tmax=0,
                        tyogrulmus=0,
                        c_kpa=0,
                        aci_derece=0,
                        dogal_bha=0,
                        kuru_bha=0,
                        zemin_profili='',
                        zemin_tanimlamasi=''
                    )
                    db.session.add(yeni_arazi)
                    
                    # Tabloda gösterme için listeye ekle
                    arazi_kayitlari.append({
                        'sondaj_derinligi': current_depth,
                        'muhafaza_borusu_derinligi': current_depth,
                        'kuyu_ici_deneyler': '',
                        'ornek_derinligi': f"{current_depth:.2f}-{(current_depth + 0.45):.2f}",
                        'ornek_turu_no': '',
                        'spt_0_15': 0,
                        'spt_15_30': 0,
                        'spt_30_45': 0,
                        'n30': 0,
                        'tmax': 0,
                        'tyogrulmus': 0,
                        'c_kpa': 0,
                        'aci_derece': 0,
                        'dogal_bha': 0,
                        'kuru_bha': 0,
                        'zemin_profili': '',
                        'zemin_tanimlamasi': ''
                    })
                    
                    # Tam olarak orijinal kodda olduğu gibi 1.5 metre artış
                    current_depth += 1.5
                    
                    # Ondalık sayı yuvarlama hataları için düzeltme
                    current_depth = round(current_depth * 100) / 100
                    row += 1
                
                # PYQT6 KODUNDAKİ GİBİ: SON DERİNLİK EKLENMEMELİ!
                app.logger.info(f"Döngü tamamlandı. Son derinlik: {current_depth}m, Hedef derinlik: {derinlik}m")
                
                # Değişiklikleri kaydet
                db.session.commit()
            
            # Log bilgisi
            except Exception as e:
                app.logger.error(f"Metraj oluşturma hatası: {str(e)}", exc_info=True)
                flash(f"Metraj oluşturulurken bir hata oluştu: {str(e)}", "danger")
                return render_template('projeler/arazi_ekle_tablo.html', proje=proje, arazi_kayitlari=[],
                                      has_data=False, derinlik=None, spt_count=1, karot_count=1, ud_count=1)
            app.logger.info(f"Metraj oluşturuldu: {len(arazi_kayitlari)} satır, derinlik: {derinlik}m")
                
            # UD örneği varsa
            if 'ud_ornekleri_var' in request.form:
                ud_derinlikler = request.form.get('ud_derinlikler', '')
                ud_adet = int(request.form.get('ud_adet', 1))
                
                if ud_derinlikler:
                    try:
                        # Virgülle ayrılmış UD derinliklerini işle
                        ud_depths = [float(d.strip()) for d in ud_derinlikler.replace(',', '.').split(',') if d.strip()]
                        
                        # UD adet ve derinlik sayısının eşit olup olmadığını kontrol et
                        if len(ud_depths) != ud_adet:
                            flash(f'UD derinlik sayısı ({len(ud_depths)}) ile UD adet sayısı ({ud_adet}) eşleşmiyor! Metraj oluşturuldu ancak UD örnekleri eklenemedi.', 'warning')
                        else:
                            # Tam olarak orijinal koddaki ud_ornekleri_ekle_arazi fonksiyonuna benzer uygula
                            for ud_depth in ud_depths:
                                # Önce uygun satır var mı kontrol et
                                found_exact = False
                                found_row = None
                                
                                # Tam eşleşme var mı?
                                for i, arazi in enumerate(arazi_kayitlari):
                                    if abs(arazi['sondaj_derinligi'] - ud_depth) < 0.01:  # Tam eşleşme kontrolü
                                        found_exact = True
                                        found_row = i
                                        break
                                
                                # Eğer tam eşleşme yoksa, en yakın satırı bul
                                if not found_exact:
                                    closest_row = None
                                    min_distance = float('inf')
                                    for i, arazi in enumerate(arazi_kayitlari):
                                        distance = abs(arazi['sondaj_derinligi'] - ud_depth)
                                        if distance < min_distance:
                                            min_distance = distance
                                            closest_row = i
                                    
                                    if closest_row is not None:
                                        found_row = closest_row
                                
                                # Eğer uygun satır bulunduysa, UD örneğini işaretle
                                if found_row is not None:
                                    arazi_kayitlari[found_row]['kuyu_ici_deneyler'] = 'UD'
                                    arazi_kayitlari[found_row]['ornek_turu_no'] = f'UD-{ud_depths.index(ud_depth)+1}'
                                    
                                    # Veritabanında da güncelle
                                    arazi_db = AraziBilgileri.query.filter_by(
                                        proje_id=proje.id, 
                                        sondaj_derinligi=arazi_kayitlari[found_row]['sondaj_derinligi']
                                    ).first()
                                    
                                    if arazi_db:
                                        arazi_db.kuyu_ici_deneyler = 'UD'
                                        arazi_db.ornek_turu_no = f'UD-{ud_depths.index(ud_depth)+1}'
                                        db.session.commit()
                                else:
                                    # Bulunamadıysa yeni satır ekle
                                    next_depth = 0
                                    insert_index = 0
                                    for i, arazi in enumerate(arazi_kayitlari):
                                        if arazi['sondaj_derinligi'] > ud_depth:
                                            insert_index = i
                                            break
                                        else:
                                            insert_index = i + 1
                                    
                                    # Yeni satır hazırla
                                    new_row = {
                                        'sondaj_derinligi': ud_depth,
                                        'muhafaza_borusu_derinligi': ud_depth,
                                        'kuyu_ici_deneyler': 'UD',
                                        'ornek_derinligi': f"{ud_depth:.2f}-{(ud_depth + 0.45):.2f}",
                                        'ornek_turu_no': f'UD-{ud_depths.index(ud_depth)+1}',
                                        'spt_0_15': 0,
                                        'spt_15_30': 0,
                                        'spt_30_45': 0,
                                        'n30': 0,
                                        'tmax': 0,
                                        'tyogrulmus': 0,
                                        'c_kpa': 0,
                                        'aci_derece': 0,
                                        'dogal_bha': 0,
                                        'kuru_bha': 0,
                                        'zemin_profili': '',
                                        'zemin_tanimlamasi': ''
                                    }
                                    
                                    # Hem geçici listeye hem de veritabanına ekle
                                    arazi_kayitlari.insert(insert_index, new_row)
                                    
                                    # Veritabanına da ekle
                                    yeni_arazi = AraziBilgileri(
                                        proje_id=proje.id,
                                        sondaj_derinligi=ud_depth,
                                        muhafaza_borusu_derinligi=ud_depth,
                                        kuyu_ici_deneyler='UD',
                                        ornek_derinligi=f"{ud_depth:.2f}-{(ud_depth + 0.45):.2f}",
                                        ornek_turu_no=f'UD-{ud_depths.index(ud_depth)+1}',
                                        spt_0_15=0,
                                        spt_15_30=0,
                                        spt_30_45=0,
                                        n30=0,
                                        tmax=0,
                                        tyogrulmus=0,
                                        c_kpa=0,
                                        aci_derece=0,
                                        dogal_bha=0,
                                        kuru_bha=0,
                                        zemin_profili='',
                                        zemin_tanimlamasi=''
                                    )
                                    db.session.add(yeni_arazi)
                                    db.session.commit()
                    except Exception as e:
                        flash(f'UD örnekleri eklenirken hata oluştu: {str(e)}', 'danger')
                        app.logger.error(f'UD örnekleri eklenirken hata: {str(e)}', exc_info=True)
            
            # Oturum verisine kaydet
            session['arazi_kayitlari'] = arazi_kayitlari
            session['spt_sayac'] = 1
            session['karot_sayac'] = 1
            session['ud_sayac'] = 1
            
            return render_template('projeler/arazi_ekle_tablo.html', proje=proje, 
                                  arazi_kayitlari=arazi_kayitlari, has_data=True, 
                                  derinlik=derinlik, spt_count=1, karot_count=1, ud_count=1)
        
        except ValueError:
            flash('Lütfen geçerli bir sayı girin.', 'danger')
            return render_template('projeler/arazi_ekle_tablo.html', proje=proje, arazi_kayitlari=[], 
                                  has_data=False, derinlik=None, spt_count=1, karot_count=1, ud_count=1)
    
    # Verileri kaydetme işlemi
    elif request.method == 'POST' and 'kaydet' in request.form:
        # Mevcut arazi bilgilerini temizle
        AraziBilgileri.query.filter_by(proje_id=proje.id).delete()
        db.session.commit()
        
        # Tablodan gelen verileri işle
        for i in range(int(request.form.get('satir_sayisi', 0))):
            if request.form.get(f'sondaj_derinligi_{i}'):
                try:
                    arazi = AraziBilgileri(
                        proje_id=proje.id,
                        sondaj_derinligi=float(request.form.get(f'sondaj_derinligi_{i}', 0)),
                        muhafaza_borusu_derinligi=float(request.form.get(f'muhafaza_borusu_derinligi_{i}', 0)) if request.form.get(f'muhafaza_borusu_derinligi_{i}') else None,
                        kuyu_ici_deneyler=request.form.get(f'kuyu_ici_deneyler_{i}', ''),
                        ornek_derinligi=request.form.get(f'ornek_derinligi_{i}', ''),
                        ornek_turu_no=request.form.get(f'ornek_turu_no_{i}', ''),
                        spt_0_15=int(request.form.get(f'spt_0_15_{i}', 0)) if request.form.get(f'spt_0_15_{i}') else None,
                        spt_15_30=int(request.form.get(f'spt_15_30_{i}', 0)) if request.form.get(f'spt_15_30_{i}') else None,
                        spt_30_45=int(request.form.get(f'spt_30_45_{i}', 0)) if request.form.get(f'spt_30_45_{i}') else None,
                        n30=int(request.form.get(f'n30_{i}', 0)) if request.form.get(f'n30_{i}') else None,
                        tmax=float(request.form.get(f'tmax_{i}', 0)) if request.form.get(f'tmax_{i}') else None,
                        tyogrulmus=float(request.form.get(f'tyogrulmus_{i}', 0)) if request.form.get(f'tyogrulmus_{i}') else None,
                        c_kpa=float(request.form.get(f'c_kpa_{i}', 0)) if request.form.get(f'c_kpa_{i}') else None,
                        aci_derece=float(request.form.get(f'aci_derece_{i}', 0)) if request.form.get(f'aci_derece_{i}') else None,
                        dogal_bha=float(request.form.get(f'dogal_bha_{i}', 0)) if request.form.get(f'dogal_bha_{i}') else None,
                        kuru_bha=float(request.form.get(f'kuru_bha_{i}', 0)) if request.form.get(f'kuru_bha_{i}') else None,
                        zemin_profili=request.form.get(f'zemin_profili_{i}', ''),
                        zemin_tanimlamasi=request.form.get(f'zemin_tanimlamasi_{i}', '')
                    )
                    db.session.add(arazi)
                except Exception as e:
                    flash(f'Satır {i+1} kaydedilirken hata oluştu: {str(e)}', 'danger')
                    continue
        
        db.session.commit()
        flash('Arazi bilgileri kaydedildi!', 'success')
        return redirect(url_for('arazi_bilgileri_liste', proje_id=proje.id))
    
    # Normal GET işlemi veya POST olmayan durum
    if 'arazi_kayitlari' in session and session['arazi_kayitlari']:
        arazi_kayitlari = session['arazi_kayitlari']
        spt_count = session.get('spt_sayac', 1)
        karot_count = session.get('karot_sayac', 1)
        ud_count = session.get('ud_sayac', 1)
        derinlik = arazi_kayitlari[-1]['sondaj_derinligi'] if arazi_kayitlari else None
        has_data = True
    else:
        arazi_kayitlari = []
        spt_count = 1
        karot_count = 1
        ud_count = 1
        derinlik = None
        has_data = False
    
    return render_template('projeler/arazi_ekle_tablo.html', proje=proje, 
                          arazi_kayitlari=arazi_kayitlari, has_data=has_data,
                          derinlik=derinlik, spt_count=spt_count, karot_count=karot_count, ud_count=ud_count)

@app.route('/projeler/<int:proje_id>/arazi/<int:arazi_id>/duzenle', methods=['GET', 'POST'])
@login_required
def arazi_bilgileri_duzenle(proje_id, arazi_id):
    proje = Proje.query.get_or_404(proje_id)
    arazi = AraziBilgileri.query.get_or_404(arazi_id)
    form = AraziBilgileriForm(obj=arazi)
    
    if form.validate_on_submit():
        form.populate_obj(arazi)
        db.session.commit()
        flash('Arazi bilgileri güncellendi!', 'success')
        return redirect(url_for('arazi_bilgileri_liste', proje_id=proje.id))
    
    return render_template('projeler/arazi_duzenle.html', form=form, proje=proje, arazi=arazi)

@app.route('/projeler/<int:proje_id>/arazi/<int:arazi_id>/sil', methods=['POST'])
@login_required
def arazi_bilgileri_sil(proje_id, arazi_id):
    arazi = AraziBilgileri.query.get_or_404(arazi_id)
    db.session.delete(arazi)
    db.session.commit()
    flash('Arazi bilgisi silindi!', 'success')
    return redirect(url_for('arazi_bilgileri_liste', proje_id=proje_id))

# Analiz ve Grafikler
@app.route('/projeler/<int:proje_id>/analiz')
@login_required
def proje_analiz(proje_id):
    proje = Proje.query.get_or_404(proje_id)
    arazi_bilgileri = AraziBilgileri.query.filter_by(proje_id=proje.id).all()
    
    # SPT Verileri
    spt_derinlikler = []
    spt_degerler = []
    
    # Zemin Profili
    zemin_derinlikler = []
    zemin_turleri = []
    
    for arazi in arazi_bilgileri:
        if arazi.n30:
            spt_derinlikler.append(arazi.sondaj_derinligi)
            spt_degerler.append(arazi.n30)
        
        if arazi.zemin_tanimlamasi:
            zemin_derinlikler.append(arazi.sondaj_derinligi)
            zemin_turleri.append(arazi.zemin_tanimlamasi)
    
    return render_template('projeler/analiz.html', 
                           proje=proje, 
                           spt_derinlikler=json.dumps(spt_derinlikler),
                           spt_degerler=json.dumps(spt_degerler),
                           zemin_derinlikler=json.dumps(zemin_derinlikler),
                           zemin_turleri=json.dumps(zemin_turleri))

# API Rotaları
@app.route('/api/projeler')
@login_required
def api_projeler():
    projeler = Proje.query.all()
    return jsonify([proje.to_dict() for proje in projeler])

@app.route('/api/projeler/<int:proje_id>')
@login_required
def api_proje_detay(proje_id):
    proje = Proje.query.get_or_404(proje_id)
    return jsonify(proje.to_dict())

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)