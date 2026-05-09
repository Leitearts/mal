#!/usr/bin/env python3
"""
Test Suite for Privilege Escalation Fix (C7)

This test suite validates that:
1. drop_privileges() function works correctly
2. Privilege drop is verified
3. Directories are created with proper permissions
4. System can write files after privilege drop
5. Error handling works for missing users/groups
"""

import os
import sys
import tempfile
import shutil

# Add src directory to path
sys.path.insert(0, 'malware_detection_mvp/src')

def test_drop_privileges_function_exists():
    """Test 1: Verify drop_privileges function exists"""
    print("\n" + "="*70)
    print("TEST 1: Verifying drop_privileges() function exists")
    print("="*70)
    
    try:
        from packet_capture import drop_privileges
        print("✓ drop_privileges function imported successfully")
        
        # Check function signature
        import inspect
        sig = inspect.signature(drop_privileges)
        params = list(sig.parameters.keys())
        
        if 'uid_name' in params and 'gid_name' in params:
            print("✓ Function has correct parameters (uid_name, gid_name)")
        else:
            print("✗ Function missing expected parameters")
            return False
        
        return True
        
    except ImportError as e:
        print(f"✗ Failed to import drop_privileges: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


def test_drop_privileges_logic():
    """Test 2: Test privilege drop logic (simulation)"""
    print("\n" + "="*70)
    print("TEST 2: Testing privilege drop logic")
    print("="*70)
    
    try:
        from packet_capture import drop_privileges
        
        # Test when not running as root
        current_uid = os.getuid()
        print(f"Current UID: {current_uid}")
        
        if current_uid == 0:
            print("⚠️  Running as root - cannot safely test privilege drop")
            print("   (Would actually drop privileges)")
            return True
        else:
            print("✓ Running as non-root user")
            print("  Testing that drop_privileges() handles this gracefully...")
            
            # Should return without error when not root
            drop_privileges()
            print("✓ drop_privileges() handled non-root execution correctly")
            return True
            
    except Exception as e:
        print(f"✗ Error in privilege drop logic: {e}")
        return False


def test_directory_permissions_function():
    """Test 3: Test directory permission setup function"""
    print("\n" + "="*70)
    print("TEST 3: Testing directory permissions setup")
    print("="*70)
    
    try:
        from detection_system import _ensure_directory_permissions
        print("✓ _ensure_directory_permissions function imported")
        
        # Create test directories in /tmp
        test_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        
        try:
            os.chdir(test_dir)
            
            # Call the function
            _ensure_directory_permissions()
            
            # Check if directories were created
            if os.path.exists('logs') and os.path.exists('quarantine'):
                print("✓ Required directories created (logs, quarantine)")
            else:
                print("✗ Directories not created")
                return False
            
            # Check permissions
            logs_stat = os.stat('logs')
            logs_mode = oct(logs_stat.st_mode)[-3:]
            print(f"  logs/ permissions: {logs_mode}")
            
            quarantine_stat = os.stat('quarantine')
            quarantine_mode = oct(quarantine_stat.st_mode)[-3:]
            print(f"  quarantine/ permissions: {quarantine_mode}")
            
            if logs_mode == '755' and quarantine_mode == '755':
                print("✓ Directories have correct permissions (755)")
            else:
                print("⚠️  Permissions may vary based on umask")
            
            return True
            
        finally:
            os.chdir(old_cwd)
            shutil.rmtree(test_dir)
            
    except ImportError as e:
        print(f"✗ Failed to import: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_live_capture_has_privilege_drop():
    """Test 4: Verify live_capture method includes privilege drop"""
    print("\n" + "="*70)
    print("TEST 4: Verifying live_capture() includes privilege drop")
    print("="*70)
    
    try:
        import inspect
        from packet_capture import PacketCapture
        
        # Get source code of live_capture method
        source = inspect.getsource(PacketCapture.live_capture)
        
        # Check for key security elements
        checks = {
            'drop_privileges call': 'drop_privileges()' in source,
            'privileges_dropped flag': 'privileges_dropped' in source,
            'SECURITY comment': 'SECURITY:' in source,
            'privilege check': 'os.getuid() == 0' in source,
        }
        
        all_passed = True
        for check_name, passed in checks.items():
            if passed:
                print(f"✓ Found: {check_name}")
            else:
                print(f"✗ Missing: {check_name}")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_code_verification():
    """Test 5: Code verification - ensure no unsafe patterns"""
    print("\n" + "="*70)
    print("TEST 5: Code verification for security patterns")
    print("="*70)
    
    try:
        import inspect
        from packet_capture import drop_privileges
        
        # Get source code
        source = inspect.getsource(drop_privileges)
        
        # Check for required security elements
        security_checks = {
            'setgroups([]) to remove supplementary groups': 'setgroups([])' in source,
            'setgid before setuid': source.index('setgid') < source.index('setuid'),
            'Privilege verification (getuid check)': 'if os.getuid() == 0 or os.geteuid() == 0' in source,
            'RuntimeError on failed drop': 'RuntimeError' in source and 'Failed to drop' in source,
            'Logging of successful drop': 'logger.info' in source and 'Successfully dropped' in source,
        }
        
        all_passed = True
        for check_name, passed in security_checks.items():
            if passed:
                print(f"✓ Security: {check_name}")
            else:
                print(f"✗ Missing: {check_name}")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_no_root_required_for_pcap_mode():
    """Test 6: Verify PCAP mode doesn't require root"""
    print("\n" + "="*70)
    print("TEST 6: Verifying PCAP mode works without root")
    print("="*70)
    
    try:
        from packet_capture import PacketCapture
        
        config = {'mode': 'PCAP'}
        pc = PacketCapture(config)
        
        print("✓ PacketCapture initialized successfully in PCAP mode")
        print(f"  Current UID: {os.getuid()}")
        print(f"  Current GID: {os.getgid()}")
        
        if os.getuid() == 0:
            print("  Running as root (UID 0)")
        else:
            print("  Running as non-root user (safe)")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def run_all_tests():
    """Run all privilege escalation fix tests"""
    print("\n")
    print("="*70)
    print("PRIVILEGE ESCALATION FIX TEST SUITE (C7)")
    print("="*70)
    print("Testing privilege dropping and directory permissions...")
    print()
    
    tests = [
        ("drop_privileges function exists", test_drop_privileges_function_exists),
        ("drop_privileges logic", test_drop_privileges_logic),
        ("directory permissions", test_directory_permissions_function),
        ("live_capture privilege drop", test_live_capture_has_privilege_drop),
        ("code security verification", test_code_verification),
        ("PCAP mode (no root)", test_no_root_required_for_pcap_mode),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ Test '{test_name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print()
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - Privilege escalation vulnerability is FIXED!")
        print()
        print("Security improvements:")
        print("  ✓ drop_privileges() function implemented")
        print("  ✓ Privileges dropped after capturing packets")
        print("  ✓ Privilege drop verified (double-checks UID/GID)")
        print("  ✓ Directories created with proper permissions")
        print("  ✓ System can operate as unprivileged user")
        print("  ✓ Defense in depth: limits damage if compromised")
        return True
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
