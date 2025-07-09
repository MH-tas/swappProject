import cv2
import numpy as np
import pyautogui
import subprocess
import time
import threading
import os
from datetime import datetime

class MotionDetector:
    def __init__(self):
        self.cap = None
        self.bg_subtractor = None
        self.motion_threshold = 1000  # Hareket eşiği (daha hassas)
        self.is_running = False
        self.last_motion_time = 0
        self.cooldown_period = 0.3  # 0.3 saniye bekleme süresi (çok hızlı)
        
        # Kamera başlatma
        self.initialize_camera()
        
    def initialize_camera(self):
        """Kamerayı başlat"""
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                print("❌ Kamera açılamadı!")
                return False
            
            # Kamera ayarları
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            # Arka plan çıkarıcı
            self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
                detectShadows=True,
                varThreshold=50,
                history=500
            )
            
            print("✅ Kamera başarıyla başlatıldı!")
            return True
            
        except Exception as e:
            print(f"❌ Kamera başlatma hatası: {e}")
            return False
    
    def detect_motion(self, frame):
        """Hareketi algıla"""
        # Arka plan çıkarma
        fg_mask = self.bg_subtractor.apply(frame)
        
        # Gürültüyü azalt
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        
        # Hareket miktarını hesapla
        motion_area = cv2.countNonZero(fg_mask)
        
        return motion_area > self.motion_threshold, motion_area, fg_mask
    
    def switch_to_cursor(self):
        """Cursor editörüne geç"""
        try:
            # PyAutoGUI gecikme süresini kaldır (maksimum hız)
            pyautogui.PAUSE = 0
            pyautogui.FAILSAFE = False
            
            # Önce mevcut editörleri kontrol et
            code_editors = [
                'Cursor', 'Visual Studio Code', 'Code', 
                'Notepad++', 'Sublime Text', 'PyCharm',
                'IntelliJ', 'WebStorm', 'Atom'
            ]
            
            # Hızlı pencere arama ve aktivasyon
            for editor in code_editors:
                windows = pyautogui.getWindowsWithTitle(editor)
                if windows:
                    windows[0].activate()
                    print(f"⚡ {editor} editörüne ışık hızında geçildi!")
                    return
            
            # Hiçbir editör bulunamadıysa direkt Alt+Tab yap
            pyautogui.hotkey('alt', 'tab')
            print("⚡ Alt+Tab ile ışık hızında geçildi!")
                
        except Exception as e:
            print(f"❌ Geçiş hatası: {e}")
            # Acil durum: Alt+Tab yap
            try:
                pyautogui.hotkey('alt', 'tab')
                print("⚡ Acil ışık hızı Alt+Tab!")
            except:
                print("❌ Hiçbir geçiş yapılamadı!")
    
    def log_motion(self, motion_area):
        """Hareket logla"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"🔥 [{timestamp}] Hareket algılandı! Değer: {motion_area}")
    
    def run(self):
        """Ana döngü"""
        if not self.cap:
            print("❌ Kamera başlatılamadı!")
            return
        
        self.is_running = True
        print("🚀 Hareket algılama sistemi başlatıldı!")
        print("📹 Kamerada hareket algılandığında otomatik olarak Cursor'a geçilecek")
        print("🛑 Çıkmak için Ctrl+C tuşuna basın\n")
        
        frame_count = 0
        
        while self.is_running:
            try:
                ret, frame = self.cap.read()
                if not ret:
                    print("❌ Kamera verisi alınamadı!")
                    break
                
                frame_count += 1
                
                # İlk birkaç frame'i arka plan öğrenimi için atla
                if frame_count < 30:
                    continue
                
                # Hareket algılama
                motion_detected, motion_area, fg_mask = self.detect_motion(frame)
                
                # Görselleştirme
                cv2.putText(frame, f"Hareket: {motion_area}", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                current_time = time.time()
                
                if motion_detected:
                    # Cooldown kontrolü
                    if current_time - self.last_motion_time > self.cooldown_period:
                        self.log_motion(motion_area)
                        
                        # Arka planda sekme değiştirme
                        threading.Thread(target=self.switch_to_cursor, daemon=True).start()
                        
                        self.last_motion_time = current_time
                    
                    # Hareket gösterimi
                    cv2.putText(frame, "HAREKET ALGILANDI!", (10, 70), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
                # Durum gösterimi
                status = "AKTIF" if motion_detected else "BEKLEME"
                color = (0, 0, 255) if motion_detected else (0, 255, 0)
                cv2.putText(frame, f"Durum: {status}", (10, 110), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                
                # Minimal bekleme (maksimum hız için)
                time.sleep(0.001)
                    
            except KeyboardInterrupt:
                print("\n🛑 Program durduruldu!")
                break
            except Exception as e:
                print(f"❌ Hata: {e}")
                continue
        
        self.cleanup()
    
    def cleanup(self):
        """Temizlik işlemleri"""
        self.is_running = False
        if self.cap:
            self.cap.release()
        print("🧹 Sistem temizlendi!")

def main():
    """Ana fonksiyon"""
    print("=" * 50)
    print("🎯 HAREKET ALGILA & ÇALIŞIYORMUŞ GİB GÖRÜN")
    print("=" * 50)
    print("📋 Sistem Özellikleri:")
    print("   • Kamera hareket algılama")
    print("   • Otomatik Cursor editörüne geçiş")
    print("   • Çalışıyormuş gibi görünme modu")
    print("=" * 50)
    
    detector = MotionDetector()
    
    try:
        detector.run()
    except Exception as e:
        print(f"❌ Sistem hatası: {e}")
    finally:
        detector.cleanup()

if __name__ == "__main__":
    main() 