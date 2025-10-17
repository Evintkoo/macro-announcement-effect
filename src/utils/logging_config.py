"""
Enhanced logging configuration for the macro announcement research project.

This module provides comprehensive logging setup with multiple handlers,
formatters, and log levels for different components of the analysis.
"""

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import sys


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output with Unicode safety."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m'  # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        # Add color to levelname
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.RESET}"
        
        # Format the message
        formatted_message = super().format(record)
        
        # Replace problematic Unicode characters with ASCII alternatives
        # This helps prevent encoding errors on Windows consoles
        unicode_replacements = {
            '[SUCCESS]': '[SUCCESS]',
            '[FAILED]': '[FAILED]', 
            '[WARNING]': '[WARNING]',
            '[INFO]': '[INFO]',
            '[INFO]': '[INFO]',
            '[INFO]': '[INFO]',
            '[INFO]': '[INFO]',
            '[LIST]': '[LIST]',
            '[TARGET]': '[TARGET]',
            '[SEARCH]': '[SEARCH]',
            '[INFO]': '[INFO]',
            '[START]': '[START]',
            '[COMPLETE]': '[COMPLETE]',
            '🔧': '[CONFIG]',
            '⭐': '[STAR]',
            '🔥': '[HOT]',
        }
        
        for emoji, replacement in unicode_replacements.items():
            formatted_message = formatted_message.replace(emoji, replacement)
        
        return formatted_message


class EnhancedLogger:
    """Enhanced logger with multiple handlers and configuration options."""
    
    def __init__(self, name: str = "macro_analysis"):
        self.name = name
        self.logger = logging.getLogger(name)
        self._handlers_configured = False
        
    def setup_logging(
        self,
        log_level: str = "INFO",
        log_file: Optional[str] = None,
        console_output: bool = True,
        file_rotation: bool = True,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        log_format: Optional[str] = None,
        component_name: Optional[str] = None
    ) -> logging.Logger:
        """
        Set up comprehensive logging configuration.
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Optional log file path
            console_output: Whether to output to console
            file_rotation: Whether to use rotating file handler
            max_file_size: Maximum size of log file before rotation
            backup_count: Number of backup files to keep
            log_format: Custom log format string
            component_name: Name of the component (for specialized logging)
            
        Returns:
            Configured logger instance
        """
        
        # Clear existing handlers to avoid duplicates
        if self._handlers_configured:
            self.logger.handlers.clear()
        
        # Set log level
        level = getattr(logging, log_level.upper(), logging.INFO)
        self.logger.setLevel(level)
        
        # Create formatters
        if log_format is None:
            if component_name:
                log_format = f'%(asctime)s - {component_name} - %(name)s - %(levelname)s - %(message)s'
            else:
                log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        file_formatter = logging.Formatter(
            log_format,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # Console handler
        if console_output:
            # Use stderr instead of stdout for better compatibility on Windows
            console_handler = logging.StreamHandler(sys.stderr)
            console_handler.setLevel(level)
            console_handler.setFormatter(console_formatter)
            
            # Set stream encoding to handle Unicode properly on Windows
            try:
                if hasattr(console_handler.stream, 'reconfigure'):
                    console_handler.stream.reconfigure(encoding='utf-8', errors='replace')
                elif hasattr(console_handler.stream, 'buffer'):
                    # For Python 3.6+
                    import io
                    console_handler.stream = io.TextIOWrapper(
                        console_handler.stream.buffer, 
                        encoding='utf-8', 
                        errors='replace'
                    )
            except (AttributeError, OSError):
                # Fallback for older versions or restricted environments
                pass
                
            self.logger.addHandler(console_handler)
        
        # File handler
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            if file_rotation:
                file_handler = logging.handlers.RotatingFileHandler(
                    log_file,
                    maxBytes=max_file_size,
                    backupCount=backup_count,
                    encoding='utf-8'
                )
            else:
                try:
                    file_handler = logging.FileHandler(log_file, encoding='utf-8')
                except TypeError:
                    # For very old Python versions
                    file_handler = logging.FileHandler(log_file)
            
            file_handler.setLevel(level)
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
        
        self._handlers_configured = True
        
        # Log initialization message
        self.logger.info(f"Logging initialized for {self.name} - Level: {log_level}")
        
        return self.logger


class ComponentLogger:
    """Specialized logger for different analysis components."""
    
    def __init__(self, base_log_dir: str = "logs"):
        self.base_log_dir = Path(base_log_dir)
        self.base_log_dir.mkdir(parents=True, exist_ok=True)
        self.loggers: Dict[str, logging.Logger] = {}
        
    def get_logger(
        self,
        component: str,
        log_level: str = "INFO",
        separate_file: bool = True
    ) -> logging.Logger:
        """
        Get or create a logger for a specific component.
        
        Args:
            component: Component name (e.g., 'data_collection', 'event_study')
            log_level: Logging level for this component
            separate_file: Whether to create separate log file for component
            
        Returns:
            Logger instance for the component
        """
        
        if component in self.loggers:
            return self.loggers[component]
        
        # Create enhanced logger
        enhanced_logger = EnhancedLogger(f"macro_analysis.{component}")
        
        # Determine log file path
        if separate_file:
            log_file = self.base_log_dir / f"{component}.log"
        else:
            log_file = self.base_log_dir / "analysis.log"
        
        # Setup logging
        logger = enhanced_logger.setup_logging(
            log_level=log_level,
            log_file=str(log_file),
            console_output=True,
            component_name=component
        )
        
        self.loggers[component] = logger
        return logger
    
    def get_main_logger(self, log_level: str = "INFO") -> logging.Logger:
        """Get the main analysis logger."""
        return self.get_logger("main", log_level, separate_file=False)
    
    def get_data_collection_logger(self, log_level: str = "INFO") -> logging.Logger:
        """Get logger for data collection components."""
        return self.get_logger("data_collection", log_level)
    
    def get_preprocessing_logger(self, log_level: str = "INFO") -> logging.Logger:
        """Get logger for data preprocessing components."""
        return self.get_logger("preprocessing", log_level)
    
    def get_analysis_logger(self, log_level: str = "INFO") -> logging.Logger:
        """Get logger for analysis components."""
        return self.get_logger("analysis", log_level)
    
    def get_visualization_logger(self, log_level: str = "INFO") -> logging.Logger:
        """Get logger for visualization components."""
        return self.get_logger("visualization", log_level)


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    component: Optional[str] = None
) -> logging.Logger:
    """
    Convenience function for setting up logging (backward compatible).
    
    Args:
        log_level: Logging level
        log_file: Optional log file path
        component: Optional component name
        
    Returns:
        Configured logger
    """
    
    if component:
        component_logger = ComponentLogger()
        return component_logger.get_logger(component, log_level)
    else:
        enhanced_logger = EnhancedLogger()
        return enhanced_logger.setup_logging(log_level, log_file)


def get_analysis_loggers(config: Dict[str, Any]) -> Dict[str, logging.Logger]:
    """
    Get all loggers needed for the analysis pipeline.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Dictionary of logger instances by component
    """
    
    # Get logging configuration
    logging_config = config.get('logging', {})
    log_level = logging_config.get('level', 'INFO')
    log_dir = logging_config.get('directory', 'logs')
    
    # Create component logger
    component_logger = ComponentLogger(log_dir)
    
    # Get all component loggers
    loggers = {
        'main': component_logger.get_main_logger(log_level),
        'data_collection': component_logger.get_data_collection_logger(log_level),
        'preprocessing': component_logger.get_preprocessing_logger(log_level),
        'analysis': component_logger.get_analysis_logger(log_level),
        'visualization': component_logger.get_visualization_logger(log_level)
    }
    
    return loggers


# Example usage and testing
if __name__ == "__main__":
    # Test basic logging
    logger = setup_logging("DEBUG", "logs/test.log")
    
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    # Test component logging
    component_logger = ComponentLogger()
    data_logger = component_logger.get_data_collection_logger("DEBUG")
    analysis_logger = component_logger.get_analysis_logger("INFO")
    
    data_logger.info("Data collection started")
    analysis_logger.info("Analysis phase started")
    
    logger.info("Logging test completed. Check logs/ directory for output files.")