#!/usr/bin/env python3
"""
Test script to validate security improvements
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, 'mvp/malware_detection_mvp/src')

def test_path_validation():
    """Test path traversal protection"""
    print("\n=== Testing Path Validation ===")
    from detection_system import MalwareDetectionSystem
    
    # Test valid paths
    valid_paths = ['config/config.json', 'samples/test.pcap']
    for path in valid_paths:
        result = MalwareDetectionSystem._is_safe_path(path)
        print(f"✓ Valid path '{path}': {result}")
        assert result, f"Valid path rejected: {path}"
    
    # Test invalid paths (directory traversal)
    invalid_paths = ['../etc/passwd', '../../secret.txt', 'config/../../../etc/shadow']
    for path in invalid_paths:
        result = MalwareDetectionSystem._is_safe_path(path)
        print(f"✓ Invalid path '{path}' blocked: {not result}")
        assert not result, f"Invalid path not blocked: {path}"
    
    # Test null byte injection
    null_path = 'config.json\x00malicious'
    result = MalwareDetectionSystem._is_safe_path(null_path)
    print(f"✓ Null byte attack blocked: {not result}")
    assert not result, "Null byte injection not blocked"
    
    print("✓ All path validation tests passed!")

def test_filename_sanitization():
    """Test filename sanitization"""
    print("\n=== Testing Filename Sanitization ===")
    from file_extraction import FileExtractor
    
    test_cases = [
        ('../../etc/passwd', ''),  # Will be sanitized to safe name
        ('invoice.pdf', 'invoice.pdf'),
        ('../../../malware.exe', ''),  # Path components removed
        ('test\x00file.txt', ''),  # Null byte removed
        ('normal_file-123.txt', 'normal_file-123.txt'),
        ('a' * 300 + '.txt', ''),  # Will be truncated
    ]
    
    for original, expected_safe in test_cases:
        result = FileExtractor._sanitize_filename(original)
        # Just check it doesn't contain dangerous characters
        assert '..' not in result, f"Sanitization failed for {original}"
        assert '\x00' not in result, f"Null byte not removed from {original}"
        assert '/' not in result and '\\' not in result, f"Path separators not removed from {original}"
        print(f"✓ Sanitized '{original[:50]}' -> '{result[:50]}'")
    
    print("✓ All filename sanitization tests passed!")

def test_interface_validation():
    """Test network interface validation"""
    print("\n=== Testing Interface Validation ===")
    from packet_capture import PacketCapture
    
    # Valid interfaces
    valid_interfaces = ['eth0', 'wlan0', 'enp0s3', 'lo']
    for iface in valid_interfaces:
        result = PacketCapture._is_valid_interface(iface)
        print(f"✓ Valid interface '{iface}': {result}")
        assert result, f"Valid interface rejected: {iface}"
    
    # Invalid interfaces (command injection attempts)
    invalid_interfaces = ['eth0; rm -rf /', 'eth0 && cat /etc/passwd', 'eth0|nc', '`whoami`']
    for iface in invalid_interfaces:
        result = PacketCapture._is_valid_interface(iface)
        print(f"✓ Invalid interface '{iface}' blocked: {not result}")
        assert not result, f"Dangerous interface not blocked: {iface}"
    
    print("✓ All interface validation tests passed!")

def test_bpf_filter_validation():
    """Test BPF filter validation"""
    print("\n=== Testing BPF Filter Validation ===")
    from packet_capture import PacketCapture
    
    # Valid BPF filters
    valid_filters = ['tcp', 'tcp port 80', 'tcp and port 443', 'host 192.168.1.1']
    for filt in valid_filters:
        result = PacketCapture._is_safe_bpf_filter(filt)
        print(f"✓ Valid BPF filter '{filt}': {result}")
        assert result, f"Valid BPF filter rejected: {filt}"
    
    # Invalid BPF filters
    invalid_filters = ['tcp; rm -rf /', 'tcp && whoami', 'tcp | nc', 'a' * 600]
    for filt in invalid_filters:
        result = PacketCapture._is_safe_bpf_filter(filt)
        print(f"✓ Invalid BPF filter blocked: {not result}")
        assert not result, f"Dangerous BPF filter not blocked: {filt}"
    
    print("✓ All BPF filter validation tests passed!")

def test_quarantine_path_safety():
    """Test quarantine path safety"""
    print("\n=== Testing Quarantine Path Safety ===")
    from response_handler import ResponseHandler
    
    # Test sanitization
    test_cases = [
        '../../etc/passwd',
        'normal_file.exe',
        '../../../secret.txt',
        'file\x00.exe',
        'a' * 150 + '.txt',
    ]
    
    for filename in test_cases:
        result = ResponseHandler._sanitize_for_filename(filename)
        # Check no directory traversal
        assert '..' not in result, f"Directory traversal in result: {result}"
        assert '/' not in result and '\\' not in result, f"Path separator in result: {result}"
        assert '\x00' not in result, f"Null byte in result: {result}"
        assert len(result) <= 100, f"Result too long: {len(result)}"
        print(f"✓ Sanitized '{filename[:50]}' -> '{result[:50]}'")
    
    print("✓ All quarantine path safety tests passed!")

def test_ip_validation():
    """Test IP address validation"""
    print("\n=== Testing IP Validation ===")
    from response_handler import ResponseHandler
    
    # Valid IPs
    valid_ips = ['192.168.1.1', '10.0.0.1', '172.16.0.1', '8.8.8.8']
    for ip in valid_ips:
        result = ResponseHandler._is_valid_ip(ip)
        print(f"✓ Valid IP '{ip}': {result}")
        assert result, f"Valid IP rejected: {ip}"
    
    # Invalid IPs
    invalid_ips = ['999.999.999.999', 'abc.def.ghi.jkl', 'unknown', '', '192.168.1']
    for ip in invalid_ips:
        result = ResponseHandler._is_valid_ip(ip)
        print(f"✓ Invalid IP '{ip}' rejected: {not result}")
        assert not result, f"Invalid IP not rejected: {ip}"
    
    print("✓ All IP validation tests passed!")

def main():
    """Run all security tests"""
    print("=" * 60)
    print("Security Improvements Validation Tests")
    print("=" * 60)
    
    try:
        test_path_validation()
        test_filename_sanitization()
        test_interface_validation()
        test_bpf_filter_validation()
        test_quarantine_path_safety()
        test_ip_validation()
        
        print("\n" + "=" * 60)
        print("✓ ALL SECURITY TESTS PASSED!")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
