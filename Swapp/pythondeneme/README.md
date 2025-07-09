# 🎯 Hareket Algıla & Çalışıyormuş Gibi Görün

Bu proje, laptop kameranızda hareket algıladığında otomatik olarak Cursor editörüne (veya başka bir kod editörüne) geçiş yapan bir sistem sağlar. İş yerinde YouTube izlerken birisi yaklaştığında anında çalışıyormuş gibi görünmenizi sağlar!

## 🚀 Özellikler

- ✅ **Gerçek zamanlı hareket algılama** - Kameranızı sürekli izler
- ✅ **Otomatik sekme değiştirme** - Hareket algılandığında Cursor editörüne geçer
- ✅ **Akıllı pencere yönetimi** - Cursor bulunamazsa diğer editörleri dener
- ✅ **Işık hızı geçiş** - Ultra hızlı sekme değiştirme (0.3 saniye cooldown)
- ✅ **Sessiz çalışma** - Arka planda çalışır, kamera penceresi açmaz

## 📋 Gereksinimler

- Python 3.7+
- Webcam/laptop kamerası
- Windows işletim sistemi
- Cursor editörü (opsiyonel - diğer editörler de desteklenir)

## 🛠️ Kurulum

1. **Gerekli kütüphaneleri yükleyin:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Kamera izinlerini kontrol edin:**
   - Windows Ayarlar > Gizlilik > Kamera
   - Python uygulamalarının kameraya erişimine izin verin

## ▶️ Kullanım

1. **Programı çalıştırın:**
   ```bash
   python motion_detector.py
   ```

2. **Sistem başladığında:**
   - Program arka planda çalışacak (kamera penceresi açılmaz)
   - Hareket algılandığında konsola log yazılacak
   - Otomatik sekme değiştirme çalışmaya başlayacak

3. **Çıkış yapmak için:**
   - `Ctrl+C` tuşlarına basın

## 🎮 Nasıl Çalışır?

1. **Arka Plan Öğrenimi**: İlk 30 frame'de sistem arka planı öğrenir
2. **Hareket Algılama**: Her frame'de arka plandan farklılıkları tespit eder
3. **Eşik Kontrolü**: Hareket miktarı 1000+ piksel olduğunda tetiklenir
4. **Işık Hızı Geçiş**: Ultra hızlı Cursor editörüne geçiş yapar
5. **Minimal Cooldown**: Sadece 0.3 saniye boyunca tekrar tetiklenmez

## ⚙️ Ayarlar

`motion_detector.py` dosyasındaki şu değerleri değiştirebilirsiniz:

```python
self.motion_threshold = 1000      # Hareket hassasiyet eşiği (daha hassas)
self.cooldown_period = 0.3        # Bekleme süresi (çok hızlı)
```

## 🔧 Sorun Giderme

**Kamera açılmıyorsa:**
- Başka uygulama kamerayı kullanıyor olabilir
- Kamera sürücülerini kontrol edin
- Windows kamera ayarlarını kontrol edin

**Cursor bulunamıyorsa:**
- Visual Studio Code, Notepad++ gibi editörleri dener
- Son çare olarak Notepad açar

**Çok hassas algılama:**
- `motion_threshold` değerini artırın (örn: 2000)

**Az hassas algılama:**
- `motion_threshold` değerini azaltın (örn: 500)

## 🎯 Kullanım Senaryosu

Bu proje özellikle şu durumda faydalıdır:
- Ofiste YouTube, sosyal medya vs. gezinirken
- Birisi yaklaştığında anında çalışıyormuş gibi görünmek
- Otomatik "iş modu" aktivasyonu

## ⚠️ Uyarı

Bu proje eğlence/demo amaçlıdır. İş yerinde kullanımdan doğabilecek sorumluluk kullanıcıya aittir!

## 📝 Notlar

- Program tamamen arka planda çalışır, kamera penceresi açılmaz
- İlk çalıştırmada birkaç saniye kalibrasyona izin verin
- Çok aydınlık/karanlık ortamlarda performans değişebilir
- Kamera kalitesi hareket algılama hassasiyetini etkiler
- Ultra hızlı algılama ve anında geçiş sistemi 