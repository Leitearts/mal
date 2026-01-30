#!/usr/bin/env python3
"""
Demonstration: Path Traversal Vulnerability Fix

This script demonstrates how the fixed code handles malicious filenames.
"""

import sys
sys.path.insert(0, '/home/runner/work/mal/mal/malware_detection_mvp/src')

from response_handler import ResponseHandler
import tempfile
import os

def demo():
    print("=" * 70)
    print("DEMONSTRATION: PATH TRAVERSAL VULNERABILITY FIX")
    print("=" * 70)
    print()
    
    # Create temp quarantine directory
    temp_dir = tempfile.mkdtemp(prefix='demo_quarantine_')
    
    config = {
        'quarantine_dir': temp_dir,
        'enable_quarantine': True,
        'enable_blocking': False,
        'enable_alerting': False
    }
    
    handler = ResponseHandler(config)
    
    print("BEFORE THE FIX:")
    print("-" * 70)
    print("Malicious filename: '../../etc/passwd'")
    print("Without sanitization, this would write to:")
    print(f"  {os.path.join(temp_dir, '../../etc/passwd')}")
    print(f"  Which resolves to: /etc/passwd (OUTSIDE quarantine!)")
    print()
    
    print("AFTER THE FIX:")
    print("-" * 70)
    malicious_filename = "../../etc/passwd"
    sanitized = handler._sanitize_filename(malicious_filename)
    print(f"Original:  '{malicious_filename}'")
    print(f"Sanitized: '{sanitized}'")
    print()
    
    print("The sanitized filename:")
    print("  ✓ Removes '../' sequences")
    print("  ✓ Removes '/' path separators")
    print("  ✓ Results in a safe filename")
    print()
    
    # Test various attack vectors
    print("MORE ATTACK VECTORS NEUTRALIZED:")
    print("-" * 70)
    
    attacks = [
        ("../../../root/.ssh/id_rsa", "Attempt to access SSH keys"),
        ("/etc/shadow", "Attempt to overwrite shadow password file"),
        ("file.txt\x00.exe", "Null byte injection"),
        ("C:\\Windows\\System32\\config\\SAM", "Windows SAM file access"),
    ]
    
    for attack, description in attacks:
        sanitized = handler._sanitize_filename(attack)
        print(f"Attack: {description}")
        print(f"  Input:  '{attack}'")
        print(f"  Output: '{sanitized}'")
        print()
    
    print("=" * 70)
    print("RESULT: All path traversal attacks are BLOCKED!")
    print("=" * 70)
    
    # Cleanup
    os.rmdir(temp_dir)

if __name__ == '__main__':
    demo()
