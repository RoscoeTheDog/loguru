# logging_suite/exceptions/__init__.py
"""
Enhanced exception handling system for logging_suite
FIXED: No circular imports - accepts config as parameters
"""

from .context_manager import (
    ExceptionContextManager,
    get_unified_caller_context,
    get_exception_context
)
from .traceback_formatter import (
    EnhancedTracebackFormatter,
    format_enhanced_traceback,
    capture_frame_locals
)
from .renderer import (
    UnifiedExceptionRenderer,
    format_exception_for_display,
    format_exception_for_json
)
from .backend_adapter import (
    BackendAwareExceptionHandler,
    create_exception_handler_for_backend
)

__all__ = [
    'ExceptionContextManager',
    'get_unified_caller_context',
    'get_exception_context',
    'EnhancedTracebackFormatter',
    'format_enhanced_traceback',
    'capture_frame_locals',
    'UnifiedExceptionRenderer',
    'format_exception_for_display',
    'format_exception_for_json',
    'BackendAwareExceptionHandler',
    'create_exception_handler_for_backend'
]