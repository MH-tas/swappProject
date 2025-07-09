# Cisco Switch Manager - Professional Edition

Cisco 9300 Catalyst switch'ler için profesyonel yönetim arayüzü. SSH üzerinden güvenli bağlantı ile switch'inizin tüm portlarını yönetebilir, anlık durum bilgilerini görebilir ve konfigürasyon değişiklikleri yapabilirsiniz.

## Özellikler

- **SSH ile Güvenli Bağlantı**: Cisco switch'e güvenli SSH bağlantısı
- **Anlık Port Durumu**: Tüm portların gerçek zamanlı durumu
- **Port Yönetimi**: Port etkinleştirme/devre dışı bırakma
- **VLAN Yapılandırması**: Port VLAN ayarları
- **Port Açıklamaları**: Port açıklama ekleme/düzenleme
- **MAC Adres Tablosu**: Switch MAC adres tablosunu görüntüleme
- **ARP Tablosu**: ARP tablosunu görüntüleme
- **Otomatik Yenileme**: Verileri otomatik olarak güncelleme
- **Konfigürasyon Kaydetme**: Değişiklikleri switch'e kaydetme
- **Gerçek Zamanlı Uyarılar**: Port durumu değişikliklerini anlık bildirim
- **Cihaz Bağlantı Takibi**: Yeni cihaz bağlantılarını MAC adresi ile izleme

## Gereksinimler

- Python 3.7 veya üzeri
- Tkinter (genellikle Python ile birlikte gelir)
- Netmiko kütüphanesi
- Cisco 9300 Catalyst switch (veya uyumlu IOS cihazı)

## Kurulum

1. **Python bağımlılıklarını yükleyin:**
```bash
pip install -r requirements.txt
```

2. **Uygulamayı çalıştırın:**
```bash
python cisco_gui.py
```

## Kullanım

### Bağlantı Kurma

1. Uygulamayı başlattıktan sonra sol paneldeki bağlantı bilgilerini doldurun:
   - **IP Adresi**: Switch'in IP adresi
   - **Kullanıcı Adı**: SSH kullanıcı adı
   - **Şifre**: SSH şifresi
   - **Enable Şifresi**: Enable modu şifresi (opsiyonel)

2. **"Bağlan"** butonuna tıklayın

### Port Yönetimi

Bağlantı kurulduktan sonra sağ panelde tüm portları görebilirsiniz:

- **Yeşil**: Bağlı ve aktif portlar
- **Kırmızı**: Bağlı olmayan veya devre dışı portlar
- **Sarı**: Bilinmeyen durumdaki portlar

#### Port İşlemleri

1. **Port Seçme**: Üzerinde işlem yapmak istediğiniz portu tıklayın
2. **Port Etkinleştirme**: "Portu Etkinleştir" butonuna tıklayın
3. **Port Devre Dışı Bırakma**: "Portu Devre Dışı Bırak" butonuna tıklayın
4. **Port Ayarları**: "Port Ayarları" butonuna tıklayarak:
   - Port açıklaması ekleyin/düzenleyin
   - VLAN ayarlarını değiştirin

### Sistem Bilgileri

Sol panelde cihaz bilgilerini görüntüleyebilirsiniz:
- Hostname
- Model
- Seri numarası
- IOS sürümü
- Çalışma süresi

### Gerçek Zamanlı Bildirimler

Sol panelin alt kısmında "Port Durumu & Uyarılar" bölümünde:
- 🟢 **Yeni Bağlantılar**: Port aktif olduğunda VLAN ve hız bilgisi ile
- 🔴 **Bağlantı Kopmaları**: Port pasif olduğunda uyarı
- 💻 **Yeni Cihazlar**: Bağlanan cihazın MAC adresi bilgisi
- ✅ **Manuel İşlemler**: Port etkinleştirme/devre dışı bırakma
- ⚙️ **Konfigürasyon**: VLAN ve açıklama değişiklikleri
- 📡 **Sistem**: Bağlantı durumu ve sistem mesajları

Bildirimler otomatik olarak zaman damgası ile kaydedilir ve son 50 kayıt saklanır.

### Ek Özellikler

#### Araçlar Menüsü

- **MAC Adres Tablosu**: Switch'teki MAC adres tablosunu görüntüleyin
- **ARP Tablosu**: ARP tablosunu görüntüleyin
- **Konfigürasyonu Kaydet**: Yaptığınız değişiklikleri switch'e kaydedin

#### Otomatik Yenileme

- Sol panelde "Otomatik Yenileme" seçeneğini işaretleyin
- Veriler 5 saniyede bir otomatik olarak yenilenir

## Güvenlik Notları

- SSH şifrelerinizi güvenli tutun
- Uygulamayı sadece güvenilen ağlarda kullanın
- Önemli değişiklikleri yapmadan önce konfigürasyonu yedekleyin
- Production ortamında test etmeden önce lab ortamında deneyin

## Desteklenen Cihazlar

Bu uygulama özellikle Cisco 9300 Catalyst serisi için geliştirilmiştir, ancak aşağıdaki cihazlarla da uyumludur:

- Cisco Catalyst 9000 serisi
- Cisco Catalyst 3850/3650 serisi
- Cisco Catalyst 2960 serisi
- IOS çalıştıran diğer Cisco switch'ler

## Sorun Giderme

### Bağlantı Sorunları

- IP adresinin doğru olduğundan emin olun
- SSH erişiminin etkin olduğunu kontrol edin
- Firewall kurallarını kontrol edin
- Kullanıcı adı ve şifrenin doğru olduğundan emin olun

### "Pattern not detected" Hatası

Bu hata Cisco cihazının prompt'unu tanıyamamaktan kaynaklanır:
- Uygulama otomatik olarak alternatif komutlar dener
- 3-4 farklı yöntem sırayla denenir
- Bildirim panelinde hangi yöntemin çalıştığını görebilirsiniz
- Bekleme süreleri otomatik olarak artırılmıştır (120 saniye)

### Port Listesi Gözükmüyor

Eğer portlar görünmüyorsa:
1. Bildirim panelindeki hata mesajlarını kontrol edin
2. `cisco_manager.log` dosyasını inceleyin
3. Enable şifresi gerekebilir
4. Cihaz modeli desteklenmiyor olabilir

### Port İşlemleri Çalışmıyor

- Enable şifresinin doğru olduğundan emin olun
- Kullanıcının yeterli yetkisinin olduğunu kontrol edin
- Switch'te configuration terminal erişiminin mevcut olduğunu kontrol edin

### Performans Sorunları

- Otomatik yenileme sıklığını artırın
- Büyük ağlarda veri yüklemesi zaman alabilir
- Ağ gecikmesini kontrol edin

## Log Dosyaları

Uygulama `cisco_manager.log` dosyasına detaylı log kayıtları yazar. Sorun yaşadığınızda bu dosyayı kontrol edebilirsiniz.

## Lisans

Bu proje eğitim ve test amaçlıdır. Production ortamında kullanmadan önce kapsamlı testler yapın.

## Destek

Sorun yaşadığınızda:
1. Log dosyalarını kontrol edin
2. Ağ bağlantısını test edin
3. Switch konfigürasyonunu kontrol edin
4. Gerekirse teknik destek alın 