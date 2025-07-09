# 🔧 Cisco Catalyst 9300 Professional Switch Manager

Profesyonel Cisco switch yönetim uygulaması. SNMP ve COM port bağlantısı ile gelişmiş switch izleme ve yönetim özelliklerine sahiptir.

## 📋 Özellikler

- 🔌 **SNMP Bağlantısı**: Gerçek zamanlı switch bilgilerini çekme
- 📱 **COM Port Terminal**: Putty benzeri seri bağlantı
- 🏠 **Sistem Bilgileri**: Switch adı, model, uptime, konum
- 🔌 **Port Durumları**: 24 port için detaylı durum bilgisi
- 🏷️ **VLAN Yönetimi**: VLAN bilgilerini görüntüleme
- 📊 **Gerçek Zamanlı İzleme**: 30 saniyede bir otomatik güncelleme
- 💻 **Terminal Komutları**: Hızlı komut butonları

## 🚀 Kurulum

### 1. Gerekli Kütüphaneleri Yükleyin
```bash
pip install pysnmp pyserial paramiko pyperclip
```

### 1.1. Windows'ta SNMP Araçları (Opsiyonel)
SNMP komutlarını Windows'tan test etmek için:
```bash
# Net-SNMP kurulumu için:
# https://www.net-snmp.org/download.html
# 64-bit Windows versiyonunu indirip kurun
# Kurulumda "Add to PATH" seçeneğini işaretleyin
```

### 2. Uygulamayı Başlatın
```bash
python Main.py
```

## 🔧 SNMP Bağlantı Sorunları ve Çözümleri

### Yaygın SNMP Hataları:

#### ❌ "No response from device"
**Olası Nedenler:**
- Yanlış IP adresi
- Switch'e network erişimi yok
- Firewall SNMP portunu (161) engelliyor

**Çözüm:**
```bash
# Switch'e ping atın
ping 192.168.1.1

# Telnet ile port kontrolü
telnet 192.168.1.1 161
```

#### ❌ "SNMP timeout or invalid community string"
**Olası Nedenler:**
- Yanlış community string
- Switch'te SNMP etkin değil
- SNMP erişim izni yok

**Çözüm:**
Switch'te şu komutları çalıştırın:
```cisco
configure terminal
snmp-server community public RO
snmp-server enable
exit
write memory
```

### 🔍 SNMP Test Araçları

Uygulamada **"🔍 Test SNMP"** butonunu kullanarak detaylı bağlantı testı yapabilirsiniz:

1. Network bağlantısını test eder
2. SNMP community'yi doğrular  
3. Farklı OID'leri test eder
4. Detaylı hata raporları verir
5. Çözüm önerileri sunar

**Yeni: 🔍 SNMP Walk Test** Hardware Status sekmesinde:
- Windows CMD komutlarını otomatik oluşturur
- Python SNMP testlerini çalıştırır
- Komutları kopyalama özelliği
- Detaylı sorun giderme rehberi

## 📡 Switch Konfigürasyonu

### Cisco Catalyst 9300 için SNMP Ayarları:

```cisco
# Basic SNMP configuration
configure terminal
snmp-server community public RO
snmp-server location "Network Room"
snmp-server contact "admin@company.com"
snmp-server enable traps

# Optional: Secure community
snmp-server community mysecret RO
snmp-server community mysecret view iso

# Save configuration
write memory
exit
```

### VLAN Bilgileri için VTP Ayarları:
```cisco
configure terminal
vtp mode server
vtp domain COMPANY
exit
```

## 🔌 COM Port Bağlantısı

### Cisco Console Kablosu:
- **Baud Rate**: 9600
- **Data Bits**: 8
- **Parity**: None  
- **Stop Bits**: 1
- **Flow Control**: None

### Windows'ta COM Port Bulma:
1. **Device Manager** açın
2. **Ports (COM & LPT)** genişletin
3. Cisco USB Serial Port'u bulun
4. Port numarasını (örn: COM8) not edin

## 🎯 Kullanım Rehberi

### 1. İlk Bağlantı:
1. **Switch IP**: Switch'in management IP'sini girin
2. **Community**: SNMP community string'i girin (varsayılan: public)
3. **COM Port**: Windows'ta belirlenen COM portunu girin
4. **"🔌 Connect SNMP"** ile SNMP bağlantısı yapın
5. **"📱 Connect COM"** ile terminal bağlantısı yapın

### 2. Port Durumlarını İzleme:
- **"Port Status"** sekmesine gidin
- **"🔄 Refresh Ports"** ile manuel yenileme
- Yeşil 🟢 = UP portlar
- Kırmızı 🔴 = DOWN portlar

### 3. Terminal Kullanımı:
- **"Terminal"** sekmesinde komut yazın
- **Enter** tuşu veya **"Send"** butonu ile gönderin
- Hızlı komut butonlarını kullanın:
  - Show Version
  - Show Interfaces  
  - Show VLANs
  - Show Running Config

### 4. Gerçek Zamanlı İzleme:
- **"🔄 Start Monitor"** ile başlatın
- Her 30 saniyede otomatik güncelleme
- **"⏹️ Stop Monitor"** ile durdurun

## 🛠️ Sorun Giderme

### SNMP Bağlanamıyor:
1. **"🔍 Test SNMP"** aracını kullanın
2. Switch IP adresini ping ile test edin
3. Community string'i kontrol edin
4. Switch'te SNMP ayarlarını kontrol edin

### COM Port Bağlanamıyor:
1. Device Manager'da COM port'u kontrol edin
2. Başka uygulama (PuTTY) portu kullanıyor olabilir
3. USB sürücülerini güncelleyin
4. Kabloyu kontrol edin

### Port Bilgileri Gelmiyor:
1. SNMP bağlantısını kontrol edin
2. Switch'te interface'lerin aktif olduğunu kontrol edin
3. SNMP OID'lerinin desteklendiğini kontrol edin

## 📊 Desteklenen SNMP OID'ler

- **System Name**: 1.3.6.1.2.1.1.5.0
- **System Description**: 1.3.6.1.2.1.1.1.0  
- **System Uptime**: 1.3.6.1.2.1.1.3.0
- **Interface Count**: 1.3.6.1.2.1.2.1.0
- **Interface Descriptions**: 1.3.6.1.2.1.2.2.1.2
- **Interface Status**: 1.3.6.1.2.1.2.2.1.8
- **Interface Speed**: 1.3.6.1.2.1.2.2.1.5
- **VLAN Information**: 1.3.6.1.4.1.9.9.46.1.3.1.1.x

## 🎨 Arayüz Özellikleri

- **Modern Dark Theme**: Profesyonel görünüm
- **Sekmeli Arayüz**: Organize edilmiş fonksiyonlar
- **Gerçek Zamanlı Güncelleme**: Anlık durum bilgileri
- **Renkli Göstergeler**: Yeşil/Kırmızı durum işaretleri
- **Hızlı Komutlar**: Tek tıkla switch komutları

## 📝 Lisans

Bu proje eğitim amaçlı geliştirilmiştir. Ticari kullanım için geliştirici ile iletişime geçin.

## 🤝 Destek

Sorunlar için:
1. **"🔍 Test SNMP"** aracını kullanın
2. Switch konfigürasyonunu kontrol edin  
3. Network bağlantısını test edin
4. Log dosyalarını inceleyin

---
🔧 **Cisco Catalyst 9300 Professional Switch Manager** - v1.0 