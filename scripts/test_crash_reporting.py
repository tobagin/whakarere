#!/usr/bin/env python3
"""
Test script for crash reporting functionality.

This script tests the crash reporting system to ensure it works correctly.
"""

import os
import sys
import tempfile
import json
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from karere.crash_reporter import CrashReporter, initialize_crash_reporter


def test_crash_reporter_initialization():
    """Test crash reporter initialization."""
    print("Testing crash reporter initialization...")
    
    try:
        crash_reporter = CrashReporter("TestApp", enable_reporting=True)
        assert crash_reporter.app_name == "TestApp"
        assert crash_reporter.enable_reporting is True
        assert crash_reporter.crash_dir.exists()
        print("  ✅ Crash reporter initialized successfully")
        return True
    except Exception as e:
        print(f"  ❌ Crash reporter initialization failed: {e}")
        return False


def test_system_info_collection():
    """Test system information collection."""
    print("Testing system information collection...")
    
    try:
        crash_reporter = CrashReporter("TestApp", enable_reporting=True)
        system_info = crash_reporter._get_system_info()
        
        # Check that system info contains expected fields
        expected_fields = ['platform', 'system', 'python_version', 'uptime']
        for field in expected_fields:
            assert field in system_info, f"Missing field: {field}"
        
        print("  ✅ System information collection working")
        return True
    except Exception as e:
        print(f"  ❌ System information collection failed: {e}")
        return False


def test_crash_report_generation():
    """Test crash report generation."""
    print("Testing crash report generation...")
    
    try:
        crash_reporter = CrashReporter("TestApp", enable_reporting=True)
        
        # Generate a test exception
        try:
            raise ValueError("Test exception for crash reporting")
        except ValueError as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            crash_id = crash_reporter.generate_crash_report(exc_type, exc_value, exc_traceback)
        
        # Check that crash report was generated
        assert crash_id != "unknown"
        assert len(crash_id) > 0
        
        # Check that crash report file exists
        report_file = crash_reporter.reports_dir / f"crash_{crash_id}.json"
        assert report_file.exists(), f"Crash report file not found: {report_file}"
        
        # Check crash report content
        with open(report_file, 'r') as f:
            crash_data = json.load(f)
        
        assert crash_data['crash_id'] == crash_id
        assert crash_data['app_name'] == "TestApp"
        assert crash_data['exception']['type'] == "ValueError"
        assert crash_data['exception']['message'] == "Test exception for crash reporting"
        assert 'traceback' in crash_data['exception']
        assert 'system_info' in crash_data
        assert 'runtime_info' in crash_data
        
        print("  ✅ Crash report generation working")
        return True
    except Exception as e:
        print(f"  ❌ Crash report generation failed: {e}")
        return False


def test_crash_report_management():
    """Test crash report management."""
    print("Testing crash report management...")
    
    try:
        crash_reporter = CrashReporter("TestApp", enable_reporting=True)
        
        # Clear any existing reports first
        crash_reporter.clear_crash_reports()
        
        # Generate multiple crash reports
        crash_ids = []
        for i in range(3):
            try:
                raise RuntimeError(f"Test crash {i}")
            except RuntimeError as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                crash_id = crash_reporter.generate_crash_report(exc_type, exc_value, exc_traceback)
                crash_ids.append(crash_id)
        
        # Get crash reports
        reports = crash_reporter.get_crash_reports()
        assert len(reports) == 3, f"Expected 3 reports, got {len(reports)}"
        
        # Check that all crash IDs are present
        report_ids = [r['crash_id'] for r in reports]
        for crash_id in crash_ids:
            assert crash_id in report_ids, f"Crash ID {crash_id} not found in reports"
        
        # Test clearing crash reports
        crash_reporter.clear_crash_reports()
        reports_after_clear = crash_reporter.get_crash_reports()
        assert len(reports_after_clear) == 0, "Crash reports not cleared"
        
        print("  ✅ Crash report management working")
        return True
    except Exception as e:
        print(f"  ❌ Crash report management failed: {e}")
        return False


def test_privacy_features():
    """Test privacy-aware features."""
    print("Testing privacy features...")
    
    try:
        # Test with system info collection disabled
        crash_reporter = CrashReporter("TestApp", enable_reporting=True)
        crash_reporter.collect_system_info = False
        
        try:
            raise ValueError("Privacy test exception")
        except ValueError as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            crash_id = crash_reporter.generate_crash_report(exc_type, exc_value, exc_traceback)
        
        # Check crash report
        report_file = crash_reporter.reports_dir / f"crash_{crash_id}.json"
        with open(report_file, 'r') as f:
            crash_data = json.load(f)
        
        # System info should be empty when collection is disabled
        assert crash_data['system_info'] == {}, "System info should be empty when collection is disabled"
        
        # Test with reporting disabled
        crash_reporter.enable_reporting = False
        # This should still work for generating reports, but in a real scenario
        # the exception handler would check this flag
        
        print("  ✅ Privacy features working")
        return True
    except Exception as e:
        print(f"  ❌ Privacy features test failed: {e}")
        return False


def test_error_handling():
    """Test error handling in crash reporter."""
    print("Testing error handling...")
    
    try:
        crash_reporter = CrashReporter("TestApp", enable_reporting=True)
        
        # Test with invalid crash report directory
        original_reports_dir = crash_reporter.reports_dir
        crash_reporter.reports_dir = Path("/invalid/path/that/does/not/exist")
        
        try:
            raise ValueError("Test exception with invalid path")
        except ValueError as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            crash_id = crash_reporter.generate_crash_report(exc_type, exc_value, exc_traceback)
        
        # Should return "unknown" when save fails
        assert crash_id == "unknown", f"Expected 'unknown', got '{crash_id}'"
        
        # Restore original path
        crash_reporter.reports_dir = original_reports_dir
        
        print("  ✅ Error handling working")
        return True
    except Exception as e:
        print(f"  ❌ Error handling test failed: {e}")
        return False


def test_global_crash_handler():
    """Test global crash handler installation."""
    print("Testing global crash handler installation...")
    
    try:
        # Test initialization
        crash_reporter = initialize_crash_reporter("TestApp")
        crash_reporter.install_exception_handler()
        
        # Check that exception handler is installed
        assert sys.excepthook != sys.__excepthook__, "Exception handler not installed"
        
        print("  ✅ Global crash handler installation working")
        return True
    except Exception as e:
        print(f"  ❌ Global crash handler installation failed: {e}")
        return False


def main():
    """Run all crash reporting tests."""
    print("Crash Reporting Test Suite")
    print("=" * 50)
    
    tests = [
        ("Crash Reporter Initialization", test_crash_reporter_initialization),
        ("System Info Collection", test_system_info_collection),
        ("Crash Report Generation", test_crash_report_generation),
        ("Crash Report Management", test_crash_report_management),
        ("Privacy Features", test_privacy_features),
        ("Error Handling", test_error_handling),
        ("Global Crash Handler", test_global_crash_handler),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ UNEXPECTED ERROR in {test_name}: {e}")
            failed += 1
    
    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All crash reporting tests passed!")
        return 0
    else:
        print(f"❌ {failed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())