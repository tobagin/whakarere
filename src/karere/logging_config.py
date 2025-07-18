"""
Logging configuration for Karere application.
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path


class KarereLogger:
    """Centralized logging configuration for Karere."""
    
    def __init__(self):
        self.logger = None
        self.log_level = logging.INFO
        self.log_file = None
        self.console_handler = None
        self.file_handler = None
        
    def setup_logging(self, log_level=None, enable_file_logging=True, log_file=None):
        """
        Set up logging configuration for the application.
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            enable_file_logging: Whether to enable file logging
            log_file: Custom log file path (optional)
        """
        # Determine log level
        if log_level is None:
            # Check environment variable
            env_level = os.environ.get('KARERE_LOG_LEVEL', 'INFO').upper()
            if env_level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
                self.log_level = getattr(logging, env_level)
            else:
                self.log_level = logging.INFO
        else:
            self.log_level = log_level
            
        # Create logger
        self.logger = logging.getLogger('karere')
        self.logger.setLevel(self.log_level)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        self.console_handler = logging.StreamHandler(sys.stdout)
        self.console_handler.setLevel(self.log_level)
        self.console_handler.setFormatter(formatter)
        self.logger.addHandler(self.console_handler)
        
        # File handler (optional)
        if enable_file_logging:
            if log_file is None:
                # Use XDG directories for log file
                log_dir = os.environ.get('XDG_DATA_HOME', os.path.expanduser('~/.local/share'))
                log_dir = os.path.join(log_dir, 'karere')
                os.makedirs(log_dir, exist_ok=True)
                self.log_file = os.path.join(log_dir, 'karere.log')
            else:
                self.log_file = log_file
                
            # Create rotating file handler (5MB max, 3 backups)
            self.file_handler = logging.handlers.RotatingFileHandler(
                self.log_file,
                maxBytes=5 * 1024 * 1024,  # 5MB
                backupCount=3
            )
            self.file_handler.setLevel(self.log_level)
            self.file_handler.setFormatter(formatter)
            self.logger.addHandler(self.file_handler)
            
        # Log initial setup message
        self.logger.info(f"Karere logging initialized - Level: {logging.getLevelName(self.log_level)}")
        if enable_file_logging:
            self.logger.info(f"Log file: {self.log_file}")
            
    def get_logger(self, name=None):
        """Get a logger instance."""
        if name:
            return logging.getLogger(f'karere.{name}')
        return self.logger
        
    def set_level(self, level):
        """Change the logging level dynamically."""
        if isinstance(level, str):
            level = getattr(logging, level.upper())
            
        self.log_level = level
        if self.logger:
            self.logger.setLevel(level)
        if self.console_handler:
            self.console_handler.setLevel(level)
        if self.file_handler:
            self.file_handler.setLevel(level)
            
        self.logger.info(f"Log level changed to: {logging.getLevelName(level)}")
        
    def disable_console_logging(self):
        """Disable console logging (keep only file logging)."""
        if self.console_handler and self.logger:
            self.logger.removeHandler(self.console_handler)
            self.console_handler = None
            
    def enable_console_logging(self):
        """Re-enable console logging."""
        if not self.console_handler and self.logger:
            self.console_handler = logging.StreamHandler(sys.stdout)
            self.console_handler.setLevel(self.log_level)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            self.console_handler.setFormatter(formatter)
            self.logger.addHandler(self.console_handler)


# Global logger instance
_karere_logger = KarereLogger()


def setup_logging(**kwargs):
    """Global function to set up logging."""
    _karere_logger.setup_logging(**kwargs)


def get_logger(name=None):
    """Global function to get a logger instance."""
    return _karere_logger.get_logger(name)


def set_log_level(level):
    """Global function to set log level."""
    _karere_logger.set_level(level)


def disable_console_logging():
    """Global function to disable console logging."""
    _karere_logger.disable_console_logging()


def enable_console_logging():
    """Global function to enable console logging."""
    _karere_logger.enable_console_logging()