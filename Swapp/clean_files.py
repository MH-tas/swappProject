#!/usr/bin/env python3
"""Clean null bytes from Python files"""

import os

def clean_file(filename):
    """Clean null bytes from a file"""
    try:
        # Read the file in binary mode
        with open(filename, 'rb') as f:
            content = f.read()
        
        # Count null bytes
        null_count = content.count(b'\x00')
        print(f"{filename}: {len(content)} bytes, {null_count} null bytes")
        
        if null_count > 0:
            # Remove null bytes
            clean_content = content.replace(b'\x00', b'')
            
            # Write back the clean content
            with open(filename, 'wb') as f:
                f.write(clean_content)
            
            print(f"✅ Cleaned {null_count} null bytes from {filename}")
        else:
            print(f"✅ {filename} is already clean")
            
    except Exception as e:
        print(f"❌ Error cleaning {filename}: {e}")

if __name__ == "__main__":
    # Clean Python files
    files_to_clean = ['cisco_manager.py', 'main.py', 'gui_components.py']
    
    for filename in files_to_clean:
        if os.path.exists(filename):
            clean_file(filename)
        else:
            print(f"⚠️ File not found: {filename}")
    
    print("\n🔧 File cleaning completed!") 