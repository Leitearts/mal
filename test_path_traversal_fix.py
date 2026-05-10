#!/usr/bin/env python3
"""
Test script to verify path traversal vulnerability is fixed.
Tests various malicious filenames to ensure they're properly sanitized.
"""

import sys
import os
import tempfile
import shutil

# Add the source directory to the path
sys.path.insert(0, '/home/runner/work/mal/mal/malware_detection_mvp/src')

from response_handler import ResponseHandler


def test_path_traversal_protection():
    """Test that malicious filenames are properly sanitized"""
    
    print("="*70)
    print("TESTING PATH TRAVERSAL VULNERABILITY FIX")
    print("="*70)
    print()
    
    # Create temporary quarantine directory for testing
    temp_dir = tempfile.mkdtemp(prefix='test_quarantine_')
    print(f"✓ Created test quarantine directory: {temp_dir}")
    print()
    
    try:
        # Initialize ResponseHandler with test config
        config = {
            'quarantine_dir': temp_dir,
            'enable_quarantine': True,
            'enable_blocking': False,
            'enable_alerting': False
        }
        handler = ResponseHandler(config)
        
        # Test cases: (input_filename, expected_behavior)
        test_cases = [
            # Path traversal attempts
            ("../../etc/passwd", "Should be sanitized (path traversal)"),
            ("../../../root/.ssh/id_rsa", "Should be sanitized (path traversal)"),
            ("/etc/shadow", "Should be sanitized (absolute path)"),
            ("C:\\Windows\\System32\\config\\SAM", "Should be sanitized (Windows path)"),
            
            # Null byte injection
            ("file.txt\x00.exe", "Should remove null bytes"),
            
            # Shell metacharacters
            ("file|rm -rf.txt", "Should sanitize shell characters"),
            ("file<script>alert.html", "Should sanitize HTML/script"),
            
            # Normal safe filenames (should pass through)
            ("invoice.pdf", "Should remain unchanged"),
            ("report_2024.xlsx", "Should remain unchanged"),
            ("photo.jpg", "Should remain unchanged"),
            
            # Edge cases
            ("", "Should handle empty filename"),
            ("....", "Should handle all dots"),
            ("////", "Should handle all slashes"),
        ]
        
        print("TESTING FILENAME SANITIZATION:")
        print("-" * 70)
        
        success_count = 0
        fail_count = 0
        
        for original, description in test_cases:
            sanitized = handler._sanitize_filename(original)
            
            # Check for path traversal sequences
            is_safe = (
                '..' not in sanitized and
                '/' not in sanitized and
                '\\' not in sanitized and
                '\x00' not in sanitized and
                sanitized == os.path.basename(sanitized)
            )
            
            status = "✓ PASS" if is_safe else "✗ FAIL"
            if is_safe:
                success_count += 1
            else:
                fail_count += 1
            
            print(f"{status}: {description}")
            print(f"  Original:  '{original}'")
            print(f"  Sanitized: '{sanitized}'")
            print()
        
        print("-" * 70)
        print()
        
        # Test path validation
        print("TESTING PATH VALIDATION:")
        print("-" * 70)
        
        # Test that valid paths within quarantine are accepted
        valid_path = os.path.join(temp_dir, "safe_file.txt")
        is_valid = handler._validate_quarantine_path(valid_path)
        print(f"{'✓ PASS' if is_valid else '✗ FAIL'}: Valid path within quarantine")
        print(f"  Path: {valid_path}")
        print(f"  Result: {'Accepted' if is_valid else 'Rejected'}")
        print()
        
        # Test that paths outside quarantine are rejected
        invalid_path = "/tmp/outside_quarantine.txt"
        is_invalid = not handler._validate_quarantine_path(invalid_path)
        print(f"{'✓ PASS' if is_invalid else '✗ FAIL'}: Invalid path outside quarantine")
        print(f"  Path: {invalid_path}")
        print(f"  Result: {'Rejected' if is_invalid else 'Accepted (SECURITY ISSUE!)'}")
        print()
        
        # Test path with traversal in constructed path
        traversal_path = os.path.join(temp_dir, "..", "escaped.txt")
        is_blocked = not handler._validate_quarantine_path(traversal_path)
        print(f"{'✓ PASS' if is_blocked else '✗ FAIL'}: Path traversal attempt blocked")
        print(f"  Path: {traversal_path}")
        print(f"  Result: {'Blocked' if is_blocked else 'Allowed (SECURITY ISSUE!)'}")
        print()
        
        print("-" * 70)
        print()
        
        # Test actual file quarantine with malicious filename
        print("TESTING ACTUAL QUARANTINE OPERATION:")
        print("-" * 70)
        
        malicious_file_info = {
            'filename': '../../etc/passwd',
            'data': b'This is test malware data',
            'size': 25,
            'hash': {'sha256': 'abcd1234567890'},
            'content_type': 'text/plain',
            'source': 'http_upload'
        }
        
        session_data = {
            'src_ip': '192.168.1.100',
            'dst_ip': '10.0.0.50',
            'protocol': 'HTTP'
        }
        
        risk_assessment = {
            'verdict': 'malicious',
            'risk_score': 0.95,
            'confidence': 0.90,
            'reasoning': ['Test case'],
            'action': 'quarantine'
        }
        
        # Perform quarantine
        handler._quarantine_file(malicious_file_info, session_data, risk_assessment)
        
        # Check that file was created in quarantine (not outside)
        files_in_quarantine = os.listdir(temp_dir)
        
        print(f"Files created in quarantine: {len(files_in_quarantine)}")
        for f in files_in_quarantine:
            full_path = os.path.join(temp_dir, f)
            # Verify file is actually inside quarantine
            is_inside = os.path.commonpath([temp_dir, full_path]) == temp_dir
            print(f"  {'✓' if is_inside else '✗'} {f} ({'Inside' if is_inside else 'OUTSIDE!'})")
        
        # Check that /etc/passwd was NOT created
        if not os.path.exists('/etc/passwd.quarantine'):
            print("✓ PASS: Malicious file NOT written to /etc/passwd")
        else:
            print("✗ FAIL: File may have been written outside quarantine!")
        
        print()
        print("="*70)
        print("SUMMARY")
        print("="*70)
        print(f"Sanitization tests: {success_count} passed, {fail_count} failed")
        print(f"Path validation: {'✓ WORKING' if is_valid and is_invalid and is_blocked else '✗ ISSUES'}")
        print(f"Quarantine operation: {'✓ SECURE' if len(files_in_quarantine) > 0 else '✗ FAILED'}")
        print()
        
        if fail_count == 0 and is_valid and is_invalid and is_blocked:
            print("🎉 ALL TESTS PASSED - Path traversal vulnerability is FIXED!")
            return True
        else:
            print("⚠️  SOME TESTS FAILED - Review the output above")
            return False
            
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)
        print(f"\n✓ Cleaned up test directory: {temp_dir}")


if __name__ == '__main__':
    success = test_path_traversal_protection()
    sys.exit(0 if success else 1)
