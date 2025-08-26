"""
Global exception hook integration for enhanced error handling.

This module provides a global exception hook that automatically captures
and beautifully formats all unhandled exceptions using loguru's template system.
"""

import sys
import threading
from typing import Optional, Callable, Type, Any, Union
from ._templates import template_registry, TemplateConfig


class GlobalExceptionHook:
    """
    Global exception hook that integrates with loguru for beautiful error reporting.
    
    This class provides a centralized way to handle all unhandled exceptions
    with template-based formatting and automatic context capture.
    """
    
    def __init__(self, logger, template_name: str = "beautiful"):
        """
        Initialize the global exception hook.
        
        Args:
            logger: Loguru logger instance
            template_name: Template to use for exception formatting
        """
        self.logger = logger
        self.template_name = template_name
        self.template = template_registry.get(template_name)
        self.original_hook = None
        self.original_threading_hook = None
        self._installed = False
        
    def install(self) -> None:
        """Install the global exception hook."""
        if self._installed:
            return
            
        # Store original hooks
        self.original_hook = sys.excepthook
        if hasattr(threading, 'excepthook'):  # Python 3.8+
            self.original_threading_hook = threading.excepthook
        
        # Install new hooks
        sys.excepthook = self._handle_exception
        if hasattr(threading, 'excepthook'):
            threading.excepthook = self._handle_threading_exception
            
        self._installed = True
        
    def uninstall(self) -> None:
        """Remove the global exception hook and restore original."""
        if not self._installed:
            return
            
        # Restore original hooks
        if self.original_hook:
            sys.excepthook = self.original_hook
        if self.original_threading_hook and hasattr(threading, 'excepthook'):
            threading.excepthook = self.original_threading_hook
            
        self._installed = False
        
    def _handle_exception(self, exc_type: Type[BaseException], exc_value: BaseException, exc_traceback: Any) -> None:
        """
        Handle unhandled exceptions in the main thread.
        
        Args:
            exc_type: Exception type
            exc_value: Exception instance
            exc_traceback: Traceback object
        """
        # Don't handle KeyboardInterrupt and SystemExit normally
        if issubclass(exc_type, (KeyboardInterrupt, SystemExit)):
            if self.original_hook:
                self.original_hook(exc_type, exc_value, exc_traceback)
            return
            
        # Format the exception with context
        context = {
            "exception_type": exc_type.__name__,
            "exception_module": getattr(exc_type, '__module__', 'builtins'),
            "thread_name": threading.current_thread().name,
            "thread_id": threading.get_ident()
        }
        
        # Log the exception with beautiful formatting
        self.logger.bind(**context).opt(exception=(exc_type, exc_value, exc_traceback)).critical(
            "Unhandled exception occurred"
        )
        
        # Call original hook for any additional handling
        if self.original_hook:
            self.original_hook(exc_type, exc_value, exc_traceback)
            
    def _handle_threading_exception(self, args) -> None:
        """
        Handle unhandled exceptions in threads (Python 3.8+).
        
        Args:
            args: threading.ExceptHookArgs with exc_type, exc_value, exc_traceback, thread
        """
        exc_type = args.exc_type
        exc_value = args.exc_value
        exc_traceback = args.exc_traceback
        thread = args.thread
        
        # Format the exception with thread context
        context = {
            "exception_type": exc_type.__name__,
            "exception_module": getattr(exc_type, '__module__', 'builtins'),
            "thread_name": thread.name if thread else "Unknown",
            "thread_id": thread.ident if thread else "Unknown"
        }
        
        # Log the exception with beautiful formatting
        self.logger.bind(**context).opt(exception=(exc_type, exc_value, exc_traceback)).critical(
            "Unhandled exception in thread"
        )
        
        # Call original hook for any additional handling
        if self.original_threading_hook:
            self.original_threading_hook(args)


def install_exception_hook(logger, template_name: str = "beautiful") -> GlobalExceptionHook:
    """
    Convenience function to install global exception hook.
    
    Args:
        logger: Loguru logger instance
        template_name: Template to use for exception formatting
        
    Returns:
        GlobalExceptionHook instance for management
        
    Example:
        >>> from loguru import logger
        >>> hook = install_exception_hook(logger, "beautiful")
        >>> # Now all unhandled exceptions will be beautifully formatted
        >>> # To remove: hook.uninstall()
    """
    hook = GlobalExceptionHook(logger, template_name)
    hook.install()
    return hook


class ExceptionContext:
    """Context manager for temporary exception hook installation."""
    
    def __init__(self, logger, template_name: str = "beautiful"):
        """
        Initialize exception context.
        
        Args:
            logger: Loguru logger instance
            template_name: Template to use for exception formatting
        """
        self.hook = GlobalExceptionHook(logger, template_name)
        
    def __enter__(self):
        """Install exception hook when entering context."""
        self.hook.install()
        return self.hook
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Remove exception hook when exiting context."""
        self.hook.uninstall()
        return False  # Don't suppress exceptions


def with_exception_hook(template_name: str = "beautiful"):
    """
    Decorator to temporarily install exception hook for a function.
    
    Args:
        template_name: Template to use for exception formatting
        
    Example:
        >>> @with_exception_hook("beautiful")
        ... def risky_function():
        ...     # Any unhandled exception will be beautifully formatted
        ...     raise ValueError("Something went wrong")
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Get logger from kwargs, or use default import
            logger = kwargs.pop('logger', None)
            if logger is None:
                from . import logger
            
            with ExceptionContext(logger, template_name):
                return func(*args, **kwargs)
        return wrapper
    return decorator


class SmartExceptionHook:
    """
    Advanced exception hook with smart filtering and context detection.
    
    This version provides more intelligent exception handling with filtering
    capabilities and enhanced context detection.
    """
    
    def __init__(
        self, 
        logger, 
        template_name: str = "beautiful",
        filter_func: Optional[Callable[[Type[BaseException], BaseException, Any], bool]] = None,
        context_extractors: Optional[list] = None
    ):
        """
        Initialize smart exception hook.
        
        Args:
            logger: Loguru logger instance
            template_name: Template to use for exception formatting
            filter_func: Function to filter which exceptions to handle
            context_extractors: List of functions to extract additional context
        """
        self.base_hook = GlobalExceptionHook(logger, template_name)
        self.filter_func = filter_func
        self.context_extractors = context_extractors or []
        
    def install(self) -> None:
        """Install the smart exception hook."""
        # Override the base hook's exception handler
        original_handle = self.base_hook._handle_exception
        
        def smart_handle_exception(exc_type, exc_value, exc_traceback):
            # Apply filtering
            if self.filter_func and not self.filter_func(exc_type, exc_value, exc_traceback):
                # Use original hook instead
                if self.base_hook.original_hook:
                    self.base_hook.original_hook(exc_type, exc_value, exc_traceback)
                return
                
            # Extract additional context
            extra_context = {}
            for extractor in self.context_extractors:
                try:
                    context = extractor(exc_type, exc_value, exc_traceback)
                    if isinstance(context, dict):
                        extra_context.update(context)
                except Exception:
                    # Don't let context extraction break exception handling
                    pass
            
            # Add extra context to logger
            if extra_context:
                bound_logger = self.base_hook.logger.bind(**extra_context)
                original_logger = self.base_hook.logger
                self.base_hook.logger = bound_logger
                try:
                    original_handle(exc_type, exc_value, exc_traceback)
                finally:
                    self.base_hook.logger = original_logger
            else:
                original_handle(exc_type, exc_value, exc_traceback)
        
        self.base_hook._handle_exception = smart_handle_exception
        self.base_hook.install()
        
    def uninstall(self) -> None:
        """Remove the smart exception hook."""
        self.base_hook.uninstall()
        

def create_development_hook(logger) -> SmartExceptionHook:
    """
    Create an exception hook optimized for development.
    
    This includes enhanced context extraction and filtering for development scenarios.
    
    Args:
        logger: Loguru logger instance
        
    Returns:
        SmartExceptionHook configured for development
    """
    def extract_local_vars(exc_type, exc_value, exc_traceback):
        """Extract local variables from the traceback."""
        context = {}
        if exc_traceback and exc_traceback.tb_frame:
            frame = exc_traceback.tb_frame
            # Get local variables (be careful with sensitive data)
            locals_dict = frame.f_locals
            # Only extract simple types to avoid issues
            for key, value in locals_dict.items():
                if isinstance(value, (str, int, float, bool, list, dict, tuple)):
                    try:
                        # Limit size to prevent huge logs
                        str_value = str(value)
                        if len(str_value) <= 200:
                            context[f"local_{key}"] = value
                    except:
                        pass
        return context
    
    def development_filter(exc_type, exc_value, exc_traceback):
        """Filter for development - handle most exceptions."""
        # Don't handle system exits and keyboard interrupts
        return not issubclass(exc_type, (KeyboardInterrupt, SystemExit))
    
    return SmartExceptionHook(
        logger=logger,
        template_name="beautiful", 
        filter_func=development_filter,
        context_extractors=[extract_local_vars]
    )


def create_production_hook(logger) -> SmartExceptionHook:
    """
    Create an exception hook optimized for production.
    
    This includes minimal context extraction and conservative filtering.
    
    Args:
        logger: Loguru logger instance
        
    Returns:
        SmartExceptionHook configured for production
    """
    def extract_basic_context(exc_type, exc_value, exc_traceback):
        """Extract only basic, safe context information."""
        context = {
            "error_message": str(exc_value),
            "error_class": exc_type.__name__
        }
        return context
    
    def production_filter(exc_type, exc_value, exc_traceback):
        """Filter for production - be more selective."""
        # Handle serious errors but not user interrupts
        if issubclass(exc_type, (KeyboardInterrupt, SystemExit)):
            return False
        # Could add more filtering logic here
        return True
    
    return SmartExceptionHook(
        logger=logger,
        template_name="minimal",  # Use minimal template for production
        filter_func=production_filter,
        context_extractors=[extract_basic_context]
    )