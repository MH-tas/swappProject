"""
CISCO SWITCH PORT YÖNETİMİ - COMPREHENSIVE TEST
==============================================
Gerçek switch ile port açma/kapama özelliklerini test eder.
"""

import time
import sys
from cisco_manager import CiscoManager

def print_header():
    """Print test header"""
    print("=" * 60)
    print("🔧 CISCO SWITCH PORT YÖNETİMİ - COMPREHENSIVE TEST")
    print("=" * 60)
    print("Bu script port açma/kapama özelliklerini gerçek switch ile test eder.")
    print("⚠️  UYARI: Gerçek portları kapatıp açacak!")
    print()

def get_switch_credentials():
    """Get switch connection details"""
    print("🔐 Switch Bağlantı Bilgileri:")
    print("-" * 30)
    
    host = input("Switch IP adresi [192.168.20.1]: ").strip()
    if not host:
        host = "192.168.20.1"
    
    username = input("Kullanıcı adı [swapp]: ").strip()
    if not username:
        username = "swapp"
    
    password = input("Şifre: ").strip()
    if not password:
        print("❌ Şifre gerekli!")
        return None
    
    return {"host": host, "username": username, "password": password}

def test_connection(manager, credentials):
    """Test basic connection"""
    print("\n🔌 BAĞLANTI TESTİ")
    print("-" * 20)
    
    try:
        print(f"Bağlanılıyor: {credentials['host']}...")
        success = manager.connect(
            host=credentials['host'],
            username=credentials['username'],
            password=credentials['password']
        )
        
        if success:
            print("✅ Bağlantı başarılı!")
            return True
        else:
            print("❌ Bağlantı başarısız!")
            return False
            
    except Exception as e:
        print(f"❌ Bağlantı hatası: {e}")
        return False

def test_interface_listing(manager):
    """Test interface listing"""
    print("\n📋 INTERFACE LİSTELEME TESTİ")
    print("-" * 30)
    
    try:
        print("Interface listesi alınıyor...")
        interfaces = manager.get_interfaces_status()
        
        if interfaces:
            active_count = 0
            total_count = len(interfaces)
            
            print(f"✅ {total_count} interface bulundu")
            print("\nİlk 10 Interface:")
            print("-" * 50)
            
            for i, (name, info) in enumerate(interfaces.items()):
                if i >= 10:
                    break
                    
                status = info.get('status', 'unknown')
                vlan = info.get('vlan', 'N/A')
                
                if status.lower() in ['connected', 'up']:
                    active_count += 1
                    status_icon = "🟢"
                elif status.lower() in ['notconnect', 'down']:
                    status_icon = "🔴" 
                elif status.lower() in ['disabled', 'shutdown']:
                    status_icon = "⚫"
                else:
                    status_icon = "🟡"
                
                print(f"{status_icon} {name:<15} | {status:<12} | VLAN: {vlan}")
            
            if total_count > 10:
                print(f"... (+{total_count-10} daha)")
            
            print(f"\n📊 Özet: {active_count} aktif, {total_count-active_count} pasif")
            return interfaces
        else:
            print("❌ Interface listesi alınamadı!")
            return None
            
    except Exception as e:
        print(f"❌ Interface listeleme hatası: {e}")
        return None

def select_test_interface(interfaces):
    """Select an interface for testing"""
    print("\n🎯 TEST İNTERFACE SEÇİMİ")
    print("-" * 25)
    
    # Filter for reasonable test interfaces
    test_candidates = []
    for name, info in interfaces.items():
        if name.startswith('Gi') and info.get('status', '').lower() in ['notconnect', 'down']:
            test_candidates.append(name)
    
    if not test_candidates:
        print("⚠️  Güvenli test interface'i bulunamadı (sadece bağlantısız portları test ederiz)")
        return None
    
    print("Test için güvenli interface'ler (bağlantısız):")
    for i, interface in enumerate(test_candidates[:5], 1):
        status = interfaces[interface].get('status', 'unknown')
        print(f"{i}. {interface} ({status})")
    
    if len(test_candidates) > 5:
        print(f"... (+{len(test_candidates)-5} daha)")
    
    choice = input(f"\nSeçim (1-{min(5, len(test_candidates))}) veya interface adı: ").strip()
    
    try:
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < min(5, len(test_candidates)):
                return test_candidates[idx]
        else:
            if choice in interfaces:
                return choice
    except:
        pass
    
    print("❌ Geçersiz seçim!")
    return None

def test_single_port_operations(manager, interface):
    """Test individual port operations"""
    print(f"\n🔧 TEK PORT İŞLEMLERİ TESTİ - {interface}")
    print("-" * 40)
    
    success_count = 0
    total_tests = 0
    
    # Test 1: Disable port
    print(f"1️⃣ Port kapatma testi...")
    total_tests += 1
    try:
        result = manager.disable_interface(interface)
        if result:
            print(f"✅ {interface} başarıyla kapatıldı")
            success_count += 1
        else:
            print(f"❌ {interface} kapatılamadı")
        time.sleep(2)
    except Exception as e:
        print(f"❌ Port kapatma hatası: {e}")
    
    # Test 2: Enable port  
    print(f"2️⃣ Port açma testi...")
    total_tests += 1
    try:
        result = manager.enable_interface(interface)
        if result:
            print(f"✅ {interface} başarıyla açıldı")
            success_count += 1
        else:
            print(f"❌ {interface} açılamadı")
        time.sleep(2)
    except Exception as e:
        print(f"❌ Port açma hatası: {e}")
    
    # Test 3: Verify final state
    print(f"3️⃣ Durum doğrulama...")
    total_tests += 1
    try:
        interfaces = manager.get_interfaces_status()
        if interface in interfaces:
            current_status = interfaces[interface].get('status', 'unknown')
            print(f"📊 {interface} mevcut durum: {current_status}")
            success_count += 1
        else:
            print(f"❌ {interface} durumu doğrulanamadı")
    except Exception as e:
        print(f"❌ Durum doğrulama hatası: {e}")
    
    print(f"\n📈 TEK PORT TEST SONUCU: {success_count}/{total_tests} başarılı")
    return success_count == total_tests

def test_bulk_operations(manager, interfaces):
    """Test bulk operations with safe interfaces"""
    print(f"\n🏭 TOPLU İŞLEMLER TESTİ")
    print("-" * 25)
    
    # Find safe interfaces for bulk test
    safe_interfaces = []
    for name, info in interfaces.items():
        if (name.startswith('Gi') and 
            info.get('status', '').lower() in ['notconnect', 'down'] and
            len(safe_interfaces) < 3):  # Limit to 3 for safety
            safe_interfaces.append(name)
    
    if len(safe_interfaces) < 2:
        print("⚠️  Toplu test için yeterli güvenli interface yok (minimum 2 gerekli)")
        return False
    
    print(f"Test interface'leri: {', '.join(safe_interfaces)}")
    
    success_count = 0
    total_tests = 0
    
    # Test 1: Bulk disable
    print(f"1️⃣ Toplu kapatma testi ({len(safe_interfaces)} port)...")
    total_tests += 1
    try:
        results = manager.bulk_disable_interfaces_optimized(safe_interfaces)
        successful = sum(1 for success in results.values() if success)
        if successful == len(safe_interfaces):
            print(f"✅ Tüm {len(safe_interfaces)} port başarıyla kapatıldı")
            success_count += 1
        else:
            print(f"⚠️  {successful}/{len(safe_interfaces)} port kapatıldı")
        time.sleep(3)
    except Exception as e:
        print(f"❌ Toplu kapatma hatası: {e}")
    
    # Test 2: Bulk enable
    print(f"2️⃣ Toplu açma testi ({len(safe_interfaces)} port)...")
    total_tests += 1
    try:
        results = manager.bulk_enable_interfaces_optimized(safe_interfaces)
        successful = sum(1 for success in results.values() if success)
        if successful == len(safe_interfaces):
            print(f"✅ Tüm {len(safe_interfaces)} port başarıyla açıldı")
            success_count += 1
        else:
            print(f"⚠️  {successful}/{len(safe_interfaces)} port açıldı")
        time.sleep(3)
    except Exception as e:
        print(f"❌ Toplu açma hatası: {e}")
    
    print(f"\n📈 TOPLU İŞLEM TEST SONUCU: {success_count}/{total_tests} başarılı")
    return success_count == total_tests

def run_comprehensive_test():
    """Run comprehensive port management test"""
    print_header()
    
    # Get credentials
    credentials = get_switch_credentials()
    if not credentials:
        return
    
    # Initialize manager
    manager = CiscoManager()
    
    try:
        # Test connection
        if not test_connection(manager, credentials):
            return
        
        # Test interface listing
        interfaces = test_interface_listing(manager)
        if not interfaces:
            return
        
        # Select test interface
        test_interface = select_test_interface(interfaces)
        if test_interface:
            # Test single port operations
            single_port_success = test_single_port_operations(manager, test_interface)
        else:
            print("⚠️  Tek port testi atlanıyor")
            single_port_success = False
        
        # Test bulk operations
        bulk_success = test_bulk_operations(manager, interfaces)
        
        # Final summary
        print("\n" + "=" * 60)
        print("🏁 FINAL TEST SONUCU")
        print("=" * 60)
        
        if single_port_success:
            print("✅ Tek port işlemleri: BAŞARILI")
        else:
            print("❌ Tek port işlemleri: BAŞARISIZ")
        
        if bulk_success:
            print("✅ Toplu işlemler: BAŞARILI")
        else:
            print("❌ Toplu işlemler: BAŞARISIZ")
        
        if single_port_success and bulk_success:
            print("\n🎉 TÜM TESTLER BAŞARILI! Port yönetimi çalışıyor.")
        else:
            print("\n⚠️  BAZI TESTLER BAŞARISIZ! Log dosyalarını kontrol edin.")
        
    except Exception as e:
        print(f"\n❌ Test sırasında kritik hata: {e}")
    
    finally:
        # Cleanup
        try:
            manager.disconnect()
            print("\n🔌 Bağlantı kapatıldı")
        except:
            pass

if __name__ == "__main__":
    try:
        run_comprehensive_test()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test kullanıcı tarafından iptal edildi")
    except Exception as e:
        print(f"\n❌ Beklenmeyen hata: {e}")
    
    input("\nÇıkmak için Enter'a basın...") 