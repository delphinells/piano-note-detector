# Piano Note Detector

Piyano notalarını gerçek zamanlı olarak tespit eden bir uygulama. Bu proje, kullanıcının çaldığı piyano notalarını dinleyip hangi notaların çalındığını tespit eder ve görsel olarak gösterir.

## Özellikler

- 🎵 Gerçek zamanlı nota tespiti
- 🎹 Piyano sesi analizi
- 📱 Modern Flutter arayüzü
- 🔊 Mikrofon ile ses kaydı
- 🎼 Nota görselleştirme

## Teknolojiler

### Backend
- Python 3.x
- librosa (ses analizi)
- Flask (API)
- sounddevice (ses kaydı)
- numpy (matematiksel işlemler)

### Frontend
- Flutter
- HTTP package (API iletişimi)
- Material Design

## Kurulum

### Backend Kurulumu

1. Python bağımlılıklarını yükleyin:
```bash
# Virtual environment oluşturun
python3 -m venv venv
source venv/bin/activate

# Bağımlılıkları yükleyin
pip install -r requirements.txt
```

2. Backend sunucusunu başlatın:
```bash
python backend/app.py
```

### Frontend Kurulumu

1. Flutter bağımlılıklarını yükleyin:
```bash
cd piano_note_detector
flutter pub get
```

2. Uygulamayı çalıştırın:
```bash
flutter run
```

## Kullanım

1. Uygulamayı başlatın
2. "Kayda Başla" butonuna tıklayın
3. Piyano notalarını çalın
4. Uygulama çalınan notaları otomatik olarak tespit edip gösterecektir

## Geliştirme Planı

- [ ] Real-time nota tespiti
- [ ] Nota görselleştirmesi için müzik notası sembolleri
- [ ] Kaydedilen melodileri saklama ve tekrar dinleme
- [ ] Farklı enstrümanlar için özelleştirme
- [ ] Akor tespiti

## Katkıda Bulunma

1. Bu repository'yi fork edin
2. Feature branch'i oluşturun (`git checkout -b feature/amazing-feature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add some amazing feature'`)
4. Branch'inizi push edin (`git push origin feature/amazing-feature`)
5. Pull Request oluşturun

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Daha fazla bilgi için `LICENSE` dosyasına bakın.

## İletişim

Delfin Olmez - [@delphinells](https://github.com/delphinells)

Proje Linki: [https://github.com/delphinells/piano-note-detector](https://github.com/delphinells/piano-note-detector) 