# logging_suite/backends/loguru_backend.py
# Relative path: LoggingSuite/backends/loguru_backend.py
"""
Loguru backend implementation using unified formatting system
FIXED: Console format logic - format setting now takes precedence over use_json_handlers
"""

import sys
from typing import Any, Dict
from pathlib import Path

try:
    import loguru

    HAS_LOGURU = True
except ImportError:
    HAS_LOGURU = False
    loguru = None

from .base import LoggingBackend
from ..unified_logger import UnifiedLogger


def create_unified_loguru_formatter(format_type: str, config: Dict[str, Any]):
    """Create a Loguru-compatible formatter using unified styling system"""
    try:
        from ..renderer_registry import get_global_renderer_registry
        registry = get_global_renderer_registry()

        # Get unified formatter
        formatter = registry.get_renderer_for_backend('loguru', format_type, config)

        def loguru_format_function(record):
            """Loguru format function that uses unified formatters"""

            # Convert loguru record to logging-compatible format
            class MockRecord:
                def __init__(self, loguru_record):
                    self.name = loguru_record['name']
                    self.levelname = loguru_record['level'].name
                    self.getMessage = lambda: loguru_record['message']
                    self.module = loguru_record['module']
                    self.funcName = loguru_record['function']
                    self.lineno = loguru_record['line']
                    self.created = loguru_record['time'].timestamp()
                    self.exc_info = loguru_record.get('exception')

                    # Add extra context from loguru
                    extra_data = loguru_record.get('extra', {})
                    for key, value in extra_data.items():
                        setattr(self, key, value)

            mock_record = MockRecord(record)

            # Use unified formatter
            try:
                return formatter.format(mock_record)
            except Exception:
                # Fallback based on format type
                if format_type == 'console':
                    return f"{record['time']} | {record['level'].name:8s} | {record['name']} | {record['message']}\n"
                else:
                    # Fallback to basic JSON
                    import json
                    log_data = {
                        'timestamp': str(record['time']),
                        'level': record['level'].name,
                        'logger': record['name'],
                        'message': record['message']
                    }
                    return json.dumps(log_data, separators=(',', ':')) + '\n'

        return loguru_format_function

    except ImportError:
        # Fallback if unified system not available
        def basic_format(record):
            if format_type == 'console':
                return f"{record['time']} | {record['level'].name:8s} | {record['name']} | {record['message']}\n"
            else:
                import json
                log_data = {
                    'timestamp': str(record['time']),
                    'level': record['level'].name,
                    'logger': record['name'],
                    'message': record['message']
                }
                return json.dumps(log_data, separators=(',', ':')) + '\n'

        return basic_format


class LoguruBackend(LoggingBackend):
    """Loguru backend implementation using unified formatters"""

    def __init__(self):
        if not HAS_LOGURU:
            raise ImportError("loguru is not available")

    def create_logger(self, name: str, config: Dict[str, Any]) -> Any:
        """Create a loguru logger using unified formatting"""
        # Create a new logger instance
        logger = loguru.logger.bind(logger_name=name)

        # Remove default handler if we're configuring our own
        if config.get('file_path') or not config.get('console', True):
            logger.remove()

        level = config.get('level', 'INFO').upper()

        # FIXED: Determine format type with proper precedence
        format_type = config.get('format', 'console')

        # Add console handler with unified formatting
        if config.get('console', True):
            # FIXED: Respect format setting - only use JSON if explicitly set
            if format_type == 'json':
                console_formatter = create_unified_loguru_formatter('json', config)
            else:
                # Use console formatter for any non-json format (console, etc.)
                console_formatter = create_unified_loguru_formatter('console', config)

            logger.add(
                sys.stdout,
                level=level,
                format=console_formatter,
                serialize=False
            )

        # Add file handler with unified formatting
        if 'file_path' in config:
            file_path = Path(config['file_path'])
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # For files, use JSON if format is json or if use_json_handlers is True and format isn't console
            # FIXED: Better logic for file format selection
            if format_type == 'json' or (format_type != 'console' and config.get('use_json_handlers', True)):
                file_formatter = create_unified_loguru_formatter('json', config)
            else:
                file_formatter = create_unified_loguru_formatter('file', config)

            logger.add(
                config['file_path'],
                level=level,
                format=file_formatter,
                rotation=config.get('rotation', "10 MB"),
                retention=config.get('retention', "1 week"),
                serialize=False
            )

        return logger

    def create_unified_logger(self, name: str, config: Dict[str, Any]) -> UnifiedLogger:
        """Create a unified logger wrapper for loguru"""
        raw_logger = self.create_logger(name, config)
        unified_logger = UnifiedLogger(raw_logger, self, config)  # FIXED: Pass config parameter

        # Apply processor if configured
        processor_type = config.get('processor_type', 'development' if config.get('level') == 'DEBUG' else 'production')
        try:
            from ..processors import DefaultProcessors
            if processor_type == 'development':
                processor = DefaultProcessors.create_development_processor()
            else:
                processor = DefaultProcessors.create_production_processor()
            unified_logger.set_processor(processor)
        except ImportError:
            pass  # Processors not available

        return unified_logger

    def supports_context_binding(self) -> bool:
        """Loguru supports context binding"""
        return True

    def get_backend_name(self) -> str:
        """Get backend name"""
        return 'loguru'