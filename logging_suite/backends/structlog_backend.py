# logging_suite/backends/structlog_backend.py
# Relative path: LoggingSuite/backends/structlog_backend.py
"""
Structlog backend implementation using unified formatting system
FIXED: Console format logic - format setting now takes precedence over use_json_handlers
"""

import logging
import sys
from typing import Any, Dict
from pathlib import Path

try:
    import structlog

    HAS_STRUCTLOG = True
except ImportError:
    HAS_STRUCTLOG = False
    structlog = None

from .base import LoggingBackend
from ..unified_logger import UnifiedLogger


class UnifiedStructlogRenderer:
    """Structlog renderer that uses the unified formatting system"""

    def __init__(self, format_type: str, config: Dict[str, Any]):
        self.format_type = format_type
        self.config = config
        self._formatter = None

        # Initialize unified formatter
        try:
            from ..renderer_registry import get_global_renderer_registry
            registry = get_global_renderer_registry()
            self._formatter = registry.get_renderer_for_backend('structlog', format_type, config)
        except ImportError:
            self._formatter = None

    def __call__(self, logger, method_name, event_dict):
        """Render event_dict using unified formatter"""
        if not self._formatter:
            # Fallback rendering based on format type
            if self.format_type == 'console':
                # Simple console format
                timestamp = event_dict.get('timestamp', '')
                level = method_name.upper()
                logger_name = event_dict.get('logger', 'structlog')
                message = event_dict.get('event', '')
                return f"{timestamp} | {level:8s} | {logger_name} | {message}"
            else:
                # Fallback to simple JSON rendering
                import json
                return json.dumps(event_dict, default=str, separators=(',', ':'))

        # Convert structlog event_dict to logging-compatible record
        class MockRecord:
            def __init__(self, event_dict, method_name):
                self.name = event_dict.get('logger', 'structlog')
                self.levelname = method_name.upper()
                self.getMessage = lambda: event_dict.get('event', '')
                self.module = event_dict.get('module', 'unknown')
                self.funcName = event_dict.get('function', 'unknown')
                self.lineno = event_dict.get('line', 0)
                self.created = event_dict.get('timestamp', 0)
                self.exc_info = event_dict.get('exception')

                # Add all other fields as attributes
                for key, value in event_dict.items():
                    if not hasattr(self, key):
                        setattr(self, key, value)

        mock_record = MockRecord(event_dict, method_name)

        try:
            return self._formatter.format(mock_record)
        except Exception:
            # Fallback based on format type
            if self.format_type == 'console':
                timestamp = event_dict.get('timestamp', '')
                level = method_name.upper()
                logger_name = event_dict.get('logger', 'structlog')
                message = event_dict.get('event', '')
                return f"{timestamp} | {level:8s} | {logger_name} | {message}"
            else:
                import json
                return json.dumps(event_dict, default=str, separators=(',', ':'))


class StructlogBackend(LoggingBackend):
    """Structlog backend implementation using unified formatters"""

    def __init__(self):
        if not HAS_STRUCTLOG:
            raise ImportError("structlog is not available")

    def create_logger(self, name: str, config: Dict[str, Any]) -> Any:
        """Create a structlog logger using unified formatting"""
        # Configure structlog processors
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
        ]

        # Add custom processors from config
        if 'processors' in config:
            processors.extend(config['processors'])

        # FIXED: Use unified renderer with proper format precedence
        format_type = config.get('format', 'json')

        # Respect format setting - only use JSON if explicitly set
        if format_type == 'json':
            renderer = UnifiedStructlogRenderer('json', config)
        else:
            # Use console renderer for any non-json format (console, etc.)
            renderer = UnifiedStructlogRenderer('console', config)

        processors.append(renderer)

        # Configure structlog
        structlog.configure(
            processors=processors,
            wrapper_class=structlog.stdlib.BoundLogger,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

        # Configure the underlying stdlib logger with unified handlers
        stdlib_logger = logging.getLogger(name)
        self._configure_handlers(stdlib_logger, config)

        return structlog.get_logger(name)

    def _configure_handlers(self, logger: logging.Logger, config: Dict[str, Any]):
        """Configure logging handlers using unified formatters"""
        logger.handlers.clear()

        level = getattr(logging, config.get('level', 'INFO').upper())
        logger.setLevel(level)

        # Get unified formatters
        try:
            from ..renderer_registry import get_global_renderer_registry
            registry = get_global_renderer_registry()
        except ImportError:
            # Fallback to basic handlers
            self._configure_basic_handlers(logger, config)
            return

        # Determine format type
        format_type = config.get('format', 'json')

        # File handler with unified formatting
        if 'file_path' in config:
            file_path = Path(config['file_path'])
            file_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(config['file_path'])
            file_handler.setLevel(level)

            # For files, use JSON if explicitly configured or if format is json
            # FIXED: Respect format setting for files too
            if format_type == 'json' or (format_type != 'console' and config.get('use_json_handlers', True)):
                # Use pass-through formatter since structlog already handles JSON rendering
                file_handler.setFormatter(logging.Formatter('%(message)s'))
            else:
                # Use pass-through formatter - structlog handles console rendering
                file_handler.setFormatter(logging.Formatter('%(message)s'))

            logger.addHandler(file_handler)

        # Console handler with unified formatting
        if config.get('console', True):
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)

            # Use pass-through formatter since structlog handles rendering
            console_handler.setFormatter(logging.Formatter('%(message)s'))
            logger.addHandler(console_handler)

        # Custom handlers
        for handler in config.get('handlers', []):
            logger.addHandler(handler)

    def _configure_basic_handlers(self, logger: logging.Logger, config: Dict[str, Any]):
        """Fallback handler configuration"""
        level = getattr(logging, config.get('level', 'INFO').upper())
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Console handler
        if config.get('console', True):
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        # File handler
        if 'file_path' in config:
            file_path = Path(config['file_path'])
            file_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(config['file_path'])
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    def create_unified_logger(self, name: str, config: Dict[str, Any]) -> UnifiedLogger:
        """Create a unified logger wrapper for structlog"""
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
        """Structlog supports context binding"""
        return True

    def get_backend_name(self) -> str:
        """Get backend name"""
        return 'structlog'