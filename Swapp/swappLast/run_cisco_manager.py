#!/usr/bin/env python3
"""
Cisco Switch Manager Launcher
Simple launcher script with dependency check
"""

import sys
import subprocess
import importlib

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = ['netmiko', 'paramiko']
    missing_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✓ {package} yüklü")
        except ImportError:
            missing_packages.append(package)
            print(f"✗ {package} bulunamadı")
    
    if missing_packages:
        print("\nEksik paketler tespit edildi!")
        print("Lütfen aşağıdaki komutu çalıştırın:")
        print("pip install -r requirements.txt")
        return False
    
    return True

def main():
    """Main launcher function"""
    print("Cisco Switch Manager - Professional Edition")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("Hata: Python 3.7 veya üzeri gerekli!")
        print(f"Mevcut sürüm: {sys.version}")
        return
    
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    
    # Check dependencies
    print("\nBağımlılıklar kontrol ediliyor...")
    if not check_dependencies():
        return
    
    print("\nUygulama başlatılıyor...")
    try:
        from cisco_gui import CiscoGUI
        app = CiscoGUI()
        app.run()
    except ImportError as e:
        print(f"Hata: {e}")
        print("cisco_gui.py dosyasının mevcut olduğundan emin olun.")
    except Exception as e:
        print(f"Beklenmeyen hata: {e}")

if __name__ == "__main__":
    main() 