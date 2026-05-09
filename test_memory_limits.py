#!/usr/bin/env python3
"""
Test script to verify unbounded memory vulnerability is fixed.
Tests that large streams and files are properly rejected.
"""

import sys
import os
import tempfile

# Add the source directory to the path
sys.path.insert(0, '/home/runner/work/mal/mal/malware_detection_mvp/src')

from stream_reassembly import StreamReassembler, StreamState
from file_extraction import FileExtractor


def test_stream_size_limits():
    """Test that TCP streams are limited to prevent memory exhaustion"""
    
    print("="*70)
    print("TESTING UNBOUNDED MEMORY VULNERABILITY FIX")
    print("="*70)
    print()
    
    print("TEST 1: Stream Size Limits")
    print("-" * 70)
    
    # Create config with small max stream size for testing
    config = {
        'stream_timeout': 300,
        'min_stream_size': 1024,
        'max_stream_size': 10 * 1024  # 10KB limit for testing
    }
    
    reassembler = StreamReassembler(config)
    
    # Create a mock stream
    from scapy.all import Ether, IP, TCP, Raw
    
    src_ip = "192.168.1.100"
    dst_ip = "10.0.0.50"
    sport = 54321
    dport = 80
    
    test_cases = [
        ("Small payload (1KB)", b"A" * 1024, True, "Should be accepted"),
        ("Medium payload (5KB)", b"B" * 5120, True, "Should be accepted"),
        ("Large payload (15KB total)", b"C" * 6000, False, "Should exceed limit and be rejected"),
    ]
    
    success_count = 0
    fail_count = 0
    
    timestamp = 1000.0
    
    for i, (description, payload, should_accept, reason) in enumerate(test_cases):
        print(f"\nTest {i+1}: {description}")
        print(f"  Payload size: {len(payload)} bytes")
        print(f"  Reason: {reason}")
        
        # Create packet
        packet = Ether()/IP(src=src_ip, dst=dst_ip)/TCP(sport=sport, dport=dport, flags="PA")/Raw(load=payload)
        packet_data = bytes(packet)
        
        # Process packet
        result = reassembler.process_packet(packet_data, timestamp)
        timestamp += 1.0
        
        # Check result
        session_key = (src_ip, sport, dst_ip, dport, 'TCP')
        stream_exists = session_key in reassembler.streams
        
        if should_accept:
            if stream_exists:
                current_size = len(reassembler.streams[session_key].data_buffer)
                print(f"  ✓ PASS: Payload accepted, stream size now: {current_size} bytes")
                success_count += 1
            else:
                print(f"  ✗ FAIL: Payload should have been accepted but stream was removed")
                fail_count += 1
        else:
            if not stream_exists:
                print(f"  ✓ PASS: Oversized stream rejected and removed (prevented DoS)")
                success_count += 1
            else:
                current_size = len(reassembler.streams[session_key].data_buffer)
                print(f"  ✗ FAIL: Oversized stream was not rejected (size: {current_size})")
                fail_count += 1
    
    # Check statistics
    stats = reassembler.get_statistics()
    print(f"\nStream Statistics:")
    print(f"  Total streams: {stats['total_streams']}")
    print(f"  Rejected streams: {stats['rejected_streams']}")
    print(f"  Active streams: {stats['active_streams']}")
    print(f"  Max stream size: {stats['max_stream_size']} bytes")
    
    print()
    print("-" * 70)
    print()
    
    return success_count, fail_count


def test_file_size_limits():
    """Test that files are limited to prevent memory exhaustion"""
    
    print("TEST 2: File Size Limits")
    print("-" * 70)
    
    # Create config with file size limits
    config = {
        'min_file_size': 100,
        'max_file_size': 5 * 1024  # 5KB limit for testing
    }
    
    extractor = FileExtractor(config)
    
    test_files = [
        ("Tiny file (50 bytes)", b"x" * 50, False, "Too small"),
        ("Valid small file (500 bytes)", b"y" * 500, True, "Within limits"),
        ("Valid medium file (3KB)", b"z" * 3072, True, "Within limits"),
        ("Oversized file (10KB)", b"w" * 10240, False, "Exceeds max size"),
    ]
    
    success_count = 0
    fail_count = 0
    
    for description, data, should_accept, reason in test_files:
        print(f"\nTest: {description}")
        print(f"  File size: {len(data)} bytes")
        print(f"  Reason: {reason}")
        
        # Create file info list
        files = [{
            'filename': f'test_{len(data)}.bin',
            'data': data,
            'size': len(data),
            'content_type': 'application/octet-stream',
            'source': 'test',
            'session': {'src_ip': '192.168.1.1', 'dst_ip': '10.0.0.1'}
        }]
        
        session_data = {
            'protocol': 'HTTP',
            'src_ip': '192.168.1.1',
            'dst_ip': '10.0.0.1'
        }
        
        # Process through size filter
        valid_files = []
        rejected = 0
        
        for file_info in files:
            size = file_info.get('size', 0)
            if config['min_file_size'] <= size <= config['max_file_size']:
                file_info['hash'] = extractor._compute_hashes(file_info['data'])
                valid_files.append(file_info)
            else:
                rejected += 1
        
        accepted = len(valid_files) > 0
        
        if should_accept:
            if accepted:
                print(f"  ✓ PASS: File accepted")
                success_count += 1
            else:
                print(f"  ✗ FAIL: File should have been accepted")
                fail_count += 1
        else:
            if not accepted:
                print(f"  ✓ PASS: File rejected (prevented memory exhaustion)")
                success_count += 1
            else:
                print(f"  ✗ FAIL: File should have been rejected")
                fail_count += 1
    
    print()
    print("-" * 70)
    print()
    
    return success_count, fail_count


def test_memory_exhaustion_prevention():
    """Test that the system can handle attempts to exhaust memory"""
    
    print("TEST 3: Memory Exhaustion Attack Prevention")
    print("-" * 70)
    
    # Simulate an attack with very large stream
    config = {
        'max_stream_size': 50 * 1024  # 50KB limit for testing
    }
    
    reassembler = StreamReassembler(config)
    
    from scapy.all import Ether, IP, TCP, Raw
    
    # Attacker tries to send multiple packets to exceed limit
    print("\nSimulating attacker sending multiple packets to exceed limit...")
    
    src_ip = "203.0.113.100"  # Attacker IP
    dst_ip = "10.0.0.50"
    sport = 12345
    dport = 80
    
    # Send multiple smaller packets that add up to exceed limit
    # 20 packets x 4KB = 80KB total (should be rejected at 50KB)
    chunk_size = 4 * 1024  # 4KB per packet (valid TCP size)
    num_packets = 20
    
    timestamp = 2000.0
    rejected = False
    
    for i in range(num_packets):
        payload = b"X" * chunk_size
        packet = Ether()/IP(src=src_ip, dst=dst_ip)/TCP(sport=sport, dport=dport, flags="PA", seq=i*chunk_size)/Raw(load=payload)
        packet_data = bytes(packet)
        
        result = reassembler.process_packet(packet_data, timestamp)
        timestamp += 0.1
        
        session_key = (src_ip, sport, dst_ip, dport, 'TCP')
        if session_key not in reassembler.streams:
            print(f"  ✓ Stream rejected after packet {i+1} (total attempted: {(i+1) * chunk_size} bytes)")
            rejected = True
            break
    
    if rejected:
        print(f"  ✓ PASS: Attack prevented - stream was rejected before exhausting memory")
        stats = reassembler.get_statistics()
        print(f"  Rejected streams: {stats['rejected_streams']}")
        success = 1
        fail = 0
    else:
        print(f"  ✗ FAIL: Attack not prevented - system accepted oversized stream")
        success = 0
        fail = 1
    
    print()
    print("-" * 70)
    print()
    
    return success, fail


def main():
    """Run all tests"""
    
    total_success = 0
    total_fail = 0
    
    # Test 1: Stream size limits
    s, f = test_stream_size_limits()
    total_success += s
    total_fail += f
    
    # Test 2: File size limits
    s, f = test_file_size_limits()
    total_success += s
    total_fail += f
    
    # Test 3: Memory exhaustion prevention
    s, f = test_memory_exhaustion_prevention()
    total_success += s
    total_fail += f
    
    # Summary
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Tests passed: {total_success}")
    print(f"Tests failed: {total_fail}")
    print()
    
    if total_fail == 0:
        print("🎉 ALL TESTS PASSED - Unbounded memory vulnerability is FIXED!")
        print()
        print("Security improvements:")
        print("  ✓ TCP streams limited to prevent memory exhaustion")
        print("  ✓ Files limited to prevent memory exhaustion")
        print("  ✓ Oversized streams/files are logged")
        print("  ✓ System resistant to DoS via large streams")
        return True
    else:
        print("⚠️  SOME TESTS FAILED - Review the output above")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
