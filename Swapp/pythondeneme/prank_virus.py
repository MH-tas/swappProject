import random
import time
import pyautogui
import tkinter as tk
from tkinter import messagebox
import threading
import winsound
import os
import subprocess

class KomikVirus:
    def __init__(self):
        self.aktif = False
        self.root = None
        pyautogui.FAILSAFE = False  # Güvenlik kapanmasını kapat (dikkatli ol!)
        
    def fake_error_mesajlari(self):
        """Sahte hata mesajları göster"""
        mesajlar = [
            "HATA: Kahve seviyesi kritik derecede düşük! ☕",
            "UYARI: Sistem çok yakışıklı kullanıcı algıladı! 😎",
            "ALARM: Bilgisayarınız çok akıllı olmaya başladı! 🤖",
            "KRITIK: Motivasyon.exe çalışmayı durdurdu! 😴",
            "HATA: Pazartesi sendromu tespit edildi! 😵",
            "UYARI: Aşırı meme algılandı! 😂",
            "SISTEM: Boss.exe yaklaşıyor! Çalışıyormuş gibi yapın! 👔"
        ]
        
        for _ in range(3):
            mesaj = random.choice(mesajlar)
            threading.Thread(target=lambda: messagebox.showwarning("Sistemden Önemli Mesaj", mesaj)).start()
            time.sleep(2)
    
    def fare_deli_et(self):
        """Fareyi rastgele hareket ettir"""
        print("🐭 Fare delirme modu başlatıldı!")
        for _ in range(20):
            if not self.aktif:
                break
            x = random.randint(100, 1000)
            y = random.randint(100, 700)
            pyautogui.moveTo(x, y, duration=0.5)
            time.sleep(0.1)
    
    def ekran_titret(self):
        """Ekranı sallamış gibi göster (fare ile)"""
        print("🔥 Ekran titretme modu!")
        orijinal_pos = pyautogui.position()
        
        for _ in range(30):
            if not self.aktif:
                break
            # Rastgele küçük hareketler
            shake_x = random.randint(-10, 10)
            shake_y = random.randint(-10, 10)
            pyautogui.moveTo(orijinal_pos.x + shake_x, orijinal_pos.y + shake_y, duration=0.1)
            time.sleep(0.05)
        
        pyautogui.moveTo(orijinal_pos.x, orijinal_pos.y)  # Geri dön
    
    def caps_lock_deli(self):
        """Caps Lock'u sürekli aç kapat"""
        print("⌨️ Caps Lock delirme modu!")
        for _ in range(10):
            if not self.aktif:
                break
            pyautogui.press('capslock')
            time.sleep(0.5)
    
    def komik_sesler(self):
        """Komik sistem sesleri çal"""
        print("🔊 Komik ses modu!")
        sesler = ['SystemAsterisk', 'SystemExclamation', 'SystemHand', 'SystemQuestion']
        
        for _ in range(5):
            if not self.aktif:
                break
            ses = random.choice(sesler)
            try:
                winsound.PlaySound(ses, winsound.SND_ALIAS)
            except:
                print("Beep!")
            time.sleep(1)
    
    def yazma_deli(self):
        """Rastgele komik şeyler yaz"""
        print("✍️ Rastgele yazma modu!")
        komik_yazilar = [
            "HELP! I'M TRAPPED IN A COMPUTER! 😱",
            "Your computer has been taken over by cats! 🐱",
            "VIRUS ALERT: Too much fun detected! 🎉",
            "System infected with happiness! 😄",
            "ERROR 404: Motivation not found! 😴"
        ]
        
        time.sleep(3)  # Biraz bekle ki kullanıcı bir yere odaklanabilsin
        
        for _ in range(2):
            if not self.aktif:
                break
            yazi = random.choice(komik_yazilar)
            pyautogui.typewrite(yazi, interval=0.1)
            pyautogui.press('enter')
            time.sleep(2)
    
    def sahte_format_uyarisi(self):
        """Sahte format uyarısı göster"""
        def format_penceresi():
            pencere = tk.Tk()
            pencere.title("Windows Sistem Formatı")
            pencere.geometry("400x200")
            pencere.configure(bg='red')
            
            # Ana yazı
            label = tk.Label(pencere, text="⚠️ SİSTEM FORMATI BAŞLADI ⚠️", 
                           font=("Arial", 16, "bold"), fg="white", bg="red")
            label.pack(pady=20)
            
            # Sahte ilerleme
            progress_label = tk.Label(pencere, text="Tüm dosyalar siliniyor... 0%", 
                                    font=("Arial", 12), fg="white", bg="red")
            progress_label.pack(pady=10)
            
            def update_progress():
                for i in range(0, 101, 5):
                    if not self.aktif:
                        break
                    progress_label.config(text=f"Tüm dosyalar siliniyor... {i}%")
                    pencere.update()
                    time.sleep(0.3)
                
                # Şaka bitişi
                progress_label.config(text="ŞAKA! 😂 Hiçbir şey silinmedi!")
                time.sleep(3)
                pencere.destroy()
            
            threading.Thread(target=update_progress, daemon=True).start()
            pencere.mainloop()
        
        threading.Thread(target=format_penceresi, daemon=True).start()
    
    def matrix_efekti(self):
        """Matrix tarzı terminal efekti"""
        print("💚 Matrix modu başlatılıyor...")
        
        def matrix_penceresi():
            # Yeni bir terminal penceresi aç
            try:
                subprocess.Popen(['cmd', '/c', 'title Matrix Hack && color 0A && echo. && echo HACKING THE MAINFRAME... && echo. && dir /s C:\\ && pause'], shell=True)
            except:
                print("Matrix efekti başlatılamadı!")
        
        threading.Thread(target=matrix_penceresi, daemon=True).start()
    
    def rastgele_prank_yap(self):
        """Rastgele bir prank seç ve yap"""
        pranklar = [
            self.fake_error_mesajlari,
            self.fare_deli_et,
            self.ekran_titret,
            self.caps_lock_deli,
            self.komik_sesler,
            self.yazma_deli,
            self.sahte_format_uyarisi,
            self.matrix_efekti
        ]
        
        secilen_prank = random.choice(pranklar)
        print(f"🎯 Rastgele prank seçildi: {secilen_prank.__name__}")
        secilen_prank()
    
    def mega_kaos_modu(self):
        """Tüm pranklari aynı anda çalıştır (DİKKAT!)"""
        print("💥 MEGA KAOS MODU BAŞLATILIYOR! 💥")
        print("⚠️ UYARI: Tüm pranklar aynı anda çalışacak!")
        
        time.sleep(3)  # Son şans!
        
        if not self.aktif:
            return
            
        # Tüm pranklari thread olarak başlat
        threading.Thread(target=self.fake_error_mesajlari, daemon=True).start()
        time.sleep(1)
        threading.Thread(target=self.fare_deli_et, daemon=True).start()
        time.sleep(1)
        threading.Thread(target=self.caps_lock_deli, daemon=True).start()
        time.sleep(1)
        threading.Thread(target=self.komik_sesler, daemon=True).start()
        time.sleep(1)
        threading.Thread(target=self.sahte_format_uyarisi, daemon=True).start()
        time.sleep(1)
        threading.Thread(target=self.matrix_efekti, daemon=True).start()
    
    def baslat(self, mod=1):
        """Prank sistemini başlat"""
        self.aktif = True
        
        print("🔥" * 50)
        print("       KOMIK PRANK VIRUS v2.0")
        print("     (100% Zararsız, 1000% Komik)")
        print("🔥" * 50)
        print()
        
        try:
            if mod == 1:
                print("🎯 Rastgele Prank Modu")
                self.rastgele_prank_yap()
            elif mod == 2:
                print("🐭 Fare Delirme Modu")
                self.fare_deli_et()
            elif mod == 3:
                print("⚠️ Sahte Hata Mesajları")
                self.fake_error_mesajlari()
            elif mod == 4:
                print("⌨️ Caps Lock Deli Modu")
                self.caps_lock_deli()
            elif mod == 5:
                print("✍️ Rastgele Yazma Modu")
                self.yazma_deli()
            elif mod == 6:
                print("💥 MEGA KAOS MODU")
                self.mega_kaos_modu()
            else:
                print("🔀 Tüm prankları sırayla çalıştır")
                pranklar = [
                    self.fake_error_mesajlari,
                    self.fare_deli_et,
                    self.caps_lock_deli,
                    self.komik_sesler
                ]
                for prank in pranklar:
                    if self.aktif:
                        prank()
                        time.sleep(2)
                        
        except KeyboardInterrupt:
            print("\n🛑 Prank durduruldu! Ctrl+C ile çıkıldı.")
        except Exception as e:
            print(f"❌ Hata: {e}")
        finally:
            self.aktif = False
            print("✅ Prank bitti! Sistem normale döndü.")

def menu():
    print("\n🎮 PRANK MENÜSÜ:")
    print("1. 🎯 Rastgele Prank")
    print("2. 🐭 Fare Delirme")
    print("3. ⚠️ Sahte Hatalar")
    print("4. ⌨️ Caps Lock Delilik")
    print("5. ✍️ Rastgele Yazma")
    print("6. 💥 MEGA KAOS (DİKKAT!)")
    print("7. 🔀 Hepsini Sırayla")
    print("0. 🚪 Çıkış")

def main():
    virus = KomikVirus()
    
    print("😈 KOMIK PRANK VIRUS'E HOŞGELDİN!")
    print("⚠️ UYARI: Bu program tamamen zararsızdır!")
    print("🎯 Sadece komik efektler yapar, hiçbir dosyayı bozmaz.")
    print("🛑 Durdurmak için: Ctrl+C")
    print("\n" + "="*50)
    
    while True:
        menu()
        try:
            secim = int(input("\n🤔 Hangi prank'ı denemek istiyorsun? "))
            
            if secim == 0:
                print("👋 Görüşürüz! Prank yapmaya devam et! 😄")
                break
            elif 1 <= secim <= 7:
                print(f"\n⏰ 3 saniye sonra başlıyor... Hazır ol!")
                for i in range(3, 0, -1):
                    print(f"⏱️ {i}...")
                    time.sleep(1)
                print("🚀 BAŞLADI!")
                
                virus.baslat(secim)
                
                input("\n⏸️ Devam etmek için Enter'a bas...")
            else:
                print("❌ Geçersiz seçim! 1-7 arasında bir sayı gir.")
                
        except ValueError:
            print("❌ Lütfen sadece sayı gir!")
        except KeyboardInterrupt:
            print("\n👋 Program kapatıldı!")
            break

if __name__ == "__main__":
    main() 