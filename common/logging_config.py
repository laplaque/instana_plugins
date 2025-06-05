import logging
import os
from logging.handlers import RotatingFileHandler

def _resolve_log_file_path(log_file=None):
    """
    Resolve the log file path, creating any necessary directories.
    
    This function:
    1. Determines the appropriate log file path (default or custom)
    2. Creates any missing directories in the path
    3. Returns the absolute path to the log file
    
    Args:
        log_file: Path to the log file (default: None, which will use project_root/logs/app.log)
        
    Returns:
        Absolute path to the log file
        
    Examples:
        >>> _resolve_log_file_path()
        '/path/to/project/logs/app.log'
        
        >>> _resolve_log_file_path('/custom/path/app.log')
        '/custom/path/app.log'
        
    Raises:
        PermissionError: If directory creation fails due to permissions
        OSError: If directory creation fails for other reasons
    """
    # Determine the default log file path if not provided
    if log_file is None:
        # Get the project root directory (one level up from common/ directory)
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        log_dir = os.path.join(project_root, 'logs')
        log_file = os.path.join(log_dir, 'app.log')
    
    # Create directory for log file if it doesn't exist
    log_dir = os.path.dirname(os.path.abspath(log_file))
    os.makedirs(log_dir, exist_ok=True)
        
    return os.path.abspath(log_file)

def setup_logging(log_level=logging.INFO, log_file=None):
    """
    Setup logging configuration with file and console handlers.
    
    Args:
        log_level: The logging level (default: logging.INFO)
        log_file: Path to the log file (default: None, which will use project_root/logs/app.log)
    """
    # Resolve the log file path, creating directories if needed
    log_file = _resolve_log_file_path(log_file)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Add file handler with rotation
    try:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=3,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        root_logger.info(f"Logging to file: {log_file}")
    except Exception as e:
        console_handler.setLevel(logging.WARNING)
        root_logger.warning(f"Could not create log file at {log_file}: {e}")
        root_logger.warning("Logging to console only")
