#!/usr/bin/env python3
"""Fix encoding issues in Python files"""

import os
import codecs

def fix_encoding(filename):
    """Fix encoding issues in a file"""
    try:
        # Try to read with different encodings
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
        content = None
        
        for encoding in encodings:
            try:
                with open(filename, 'r', encoding=encoding) as f:
                    content = f.read()
                print(f"✅ Successfully read {filename} with {encoding} encoding")
                break
            except:
                continue
        
        if content is None:
            # Try binary read and clean
            with open(filename, 'rb') as f:
                raw_content = f.read()
            
            # Remove BOM and problematic bytes
            if raw_content.startswith(b'\xff\xfe'):
                raw_content = raw_content[2:]
            elif raw_content.startswith(b'\xfe\xff'):
                raw_content = raw_content[2:]
            elif raw_content.startswith(b'\xef\xbb\xbf'):
                raw_content = raw_content[3:]
            
            # Try to decode as UTF-8, replacing problematic characters
            try:
                content = raw_content.decode('utf-8', errors='replace')
            except:
                content = raw_content.decode('latin-1', errors='replace')
        
        # Clean up any remaining problematic characters
        content = content.replace('\ufffd', '')  # Remove replacement characters
        content = content.replace('\x00', '')   # Remove null bytes
        
        # Write back as clean UTF-8
        with open(filename, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)
        
        print(f"✅ Fixed encoding for {filename}")
        
    except Exception as e:
        print(f"❌ Error fixing {filename}: {e}")

if __name__ == "__main__":
    # Fix encoding for Python files
    files_to_fix = ['cisco_manager.py', 'main.py', 'gui_components.py']
    
    for filename in files_to_fix:
        if os.path.exists(filename):
            fix_encoding(filename)
        else:
            print(f"⚠️ File not found: {filename}")
    
    print("\n🔧 Encoding fix completed!") 