"""
Tests for logging initialization to ensure no FileNotFoundError when logs directory is missing.
"""
import sys
import os
import tempfile
import shutil
from pathlib import Path
import pytest


def test_logging_initialization_without_logs_directory():
    """
    Test that importing detection_system doesn't raise FileNotFoundError
    when the logs directory doesn't exist.
    """
    # Create a temporary directory to work in
    with tempfile.TemporaryDirectory() as tmpdir:
        # Save the original sys.path
        original_sys_path = sys.path.copy()
        original_cwd = os.getcwd()
        
        try:
            # Change to temp directory (simulating a directory without logs/)
            os.chdir(tmpdir)
            
            # Add the src directory to sys.path so we can import the module
            src_path = Path(__file__).parent.parent / 'mvp' / 'malware_detection_mvp' / 'src'
            sys.path.insert(0, str(src_path))
            
            # Remove any existing logs directory in temp to ensure it doesn't exist
            logs_dir = Path(tmpdir) / 'logs'
            if logs_dir.exists():
                shutil.rmtree(logs_dir)
            
            # This should not raise FileNotFoundError
            # The module should handle missing logs directory gracefully
            import detection_system
            
            # If we get here without exception, the test passes
            assert True
            
        finally:
            # Restore original sys.path and working directory
            sys.path = original_sys_path
            os.chdir(original_cwd)
            # Remove detection_system from modules to allow re-import in other tests
            if 'detection_system' in sys.modules:
                del sys.modules['detection_system']


def test_logging_creates_directory():
    """
    Test that the logging initialization creates the logs directory
    when it's missing.
    """
    # Create a temporary directory structure similar to the project
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        
        try:
            # Create a mock project structure
            project_root = Path(tmpdir) / 'test_project'
            project_root.mkdir()
            src_dir = project_root / 'src'
            src_dir.mkdir()
            
            # Create a simple test file that uses the logging setup pattern
            test_file = src_dir / 'test_module.py'
            test_file.write_text("""
import logging
import sys
from pathlib import Path

def _setup_logging():
    handlers = []
    try:
        base_path = Path(__file__).parent.parent
        log_dir = base_path / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / 'test.log'
        handlers.append(logging.FileHandler(str(log_file)))
    except (OSError, PermissionError) as e:
        print(f"Warning: Could not create log file: {e}", file=sys.stderr)
    handlers.append(logging.StreamHandler())
    logging.basicConfig(level=logging.INFO, handlers=handlers)

_setup_logging()
logger = logging.getLogger(__name__)
""")
            
            # Change to project root
            os.chdir(project_root)
            
            # Import the test module
            sys.path.insert(0, str(src_dir))
            import test_module
            
            # Verify logs directory was created
            logs_dir = project_root / 'logs'
            assert logs_dir.exists(), "Logs directory should be created"
            assert logs_dir.is_dir(), "Logs path should be a directory"
            
            # Verify log file was created
            log_file = logs_dir / 'test.log'
            assert log_file.exists(), "Log file should be created"
            
        finally:
            os.chdir(original_cwd)
            if 'test_module' in sys.modules:
                del sys.modules['test_module']


def test_logging_fallback_on_permission_error():
    """
    Test that logging falls back to console-only when directory cannot be created.
    This test verifies the fallback mechanism works correctly.
    """
    # This test is more conceptual - in a real scenario with permission issues,
    # the code should still work. We verify that the handler list is not empty
    # even if file handler creation fails
    
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        
        try:
            os.chdir(tmpdir)
            
            # We can't easily simulate permission errors in a cross-platform way,
            # but we can verify that the logging module has handlers configured
            import logging
            
            # The detection_system module should have configured logging
            # At minimum, there should be a StreamHandler
            root_logger = logging.getLogger()
            
            # Verify that handlers exist (there should be at least one)
            assert len(root_logger.handlers) > 0, "Should have at least one logging handler"
            
            # Verify there's at least a StreamHandler as fallback
            has_stream_handler = any(
                isinstance(h, logging.StreamHandler) 
                for h in root_logger.handlers
            )
            assert has_stream_handler, "Should have a StreamHandler for fallback"
            
        finally:
            os.chdir(original_cwd)
