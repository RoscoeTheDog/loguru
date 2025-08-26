# logging_suite/exceptions/renderer.py
"""
Unified exception renderer for consistent exception formatting across all backends
FIXED: Python 3.9 compatible and standalone
"""

import json
import sys
from typing import Dict, Any, Optional, Tuple, Union
from .context_manager import get_exception_context, get_unified_caller_context
from .traceback_formatter import format_enhanced_traceback


class UnifiedExceptionRenderer:
    """
    Unified renderer for exceptions that works across all backends and output formats
    """

    def __init__(self,
                 output_format: str = 'console',
                 show_enhanced_traceback: bool = True,
                 show_caller_context: bool = True,
                 show_exception_locals: bool = True,
                 colorize: bool = True,
                 compact_mode: bool = False):
        """
        Initialize unified exception renderer

        Args:
            output_format: Output format ('console', 'json', 'file')
            show_enhanced_traceback: Whether to show loguru-style traceback
            show_caller_context: Whether to show caller context
            show_exception_locals: Whether to show local variables
            colorize: Whether to use colors
            compact_mode: Whether to use compact formatting
        """
        self.output_format = output_format.lower()
        self.show_enhanced_traceback = show_enhanced_traceback
        self.show_caller_context = show_caller_context
        self.show_exception_locals = show_exception_locals
        self.colorize = colorize
        self.compact_mode = compact_mode

    def render_exception(self,
                         exc_info: Optional[Tuple] = None,
                         message: str = "",
                         logger_context: Dict[str, Any] = None) -> str:
        """
        Render an exception with full context

        Args:
            exc_info: Exception info tuple or None for current exception
            message: Log message associated with the exception
            logger_context: Additional context from the logger

        Returns:
            Formatted exception string
        """
        if exc_info is None:
            exc_info = sys.exc_info()

        if exc_info == (None, None, None):
            return message

        # Get comprehensive exception context
        exception_context = get_exception_context(exc_info)

        # Get caller context if enabled
        caller_context = {}
        if self.show_caller_context:
            try:
                caller_context = get_unified_caller_context(skip_frames=2)
            except Exception:
                pass

        # Combine all context
        full_context = {
            **exception_context,
            **caller_context,
            **(logger_context or {})
        }

        # Format based on output format
        if self.output_format == 'json':
            return self._render_json(message, full_context, exc_info)
        elif self.output_format == 'console':
            return self._render_console(message, full_context, exc_info)
        elif self.output_format == 'file':
            return self._render_file(message, full_context, exc_info)
        else:
            return self._render_console(message, full_context, exc_info)

    def _render_json(self, message: str, context: Dict[str, Any], exc_info: Tuple) -> str:
        """Render exception for JSON output"""
        exc_type, exc_value, exc_traceback = exc_info

        json_data = {
            'message': message,
            'exception': {
                'type': context.get('exception_type', 'Unknown'),
                'message': context.get('exception_message', 'Unknown error'),
                'location': context.get('exception_location', 'unknown'),
                'function': context.get('exception_function', 'unknown'),
                'module': context.get('exception_module', 'unknown')
            },
            'caller': {
                'function': context.get('caller_function', 'unknown'),
                'location': context.get('caller_location', 'unknown'),
                'module': context.get('caller_module', 'unknown')
            }
        }

        # Add locals if available
        if context.get('exception_locals'):
            json_data['exception']['locals'] = context['exception_locals']

        if context.get('caller_locals'):
            json_data['caller']['locals'] = context['caller_locals']

        # Add stack frames if available
        if context.get('stack_frames'):
            json_data['stack_frames'] = context['stack_frames']

        # Add any additional context
        additional_context = {k: v for k, v in context.items()
                              if not k.startswith(('exception_', 'caller_', 'stack_'))}
        if additional_context:
            json_data['context'] = additional_context

        try:
            if self.compact_mode:
                return json.dumps(json_data, separators=(',', ':'), default=str)
            else:
                return json.dumps(json_data, indent=2, separators=(', ', ': '), default=str)
        except Exception:
            # Fallback if JSON serialization fails
            return json.dumps({
                'message': message,
                'exception_type': str(exc_type.__name__ if exc_type else 'Unknown'),
                'exception_message': str(exc_value),
                'error': 'Failed to serialize full exception context'
            }, default=str)

    def _render_console(self, message: str, context: Dict[str, Any], exc_info: Tuple) -> str:
        """Render exception for console output with loguru-style formatting"""
        lines = []

        # Main error message
        if message:
            lines.append(message)

        # Enhanced traceback if enabled
        if self.show_enhanced_traceback:
            try:
                enhanced_tb = format_enhanced_traceback(
                    exc_info=exc_info,
                    show_locals=self.show_exception_locals,
                    show_values=True,
                    colorize=self.colorize
                )
                if enhanced_tb:
                    lines.append("")
                    lines.append(enhanced_tb)
            except Exception:
                # Fallback to standard traceback
                import traceback
                lines.append("")
                lines.append("".join(traceback.format_exception(*exc_info)))

        # Show additional context if not in compact mode
        if not self.compact_mode:
            context_lines = self._format_context_for_console(context)
            if context_lines:
                lines.append("")
                lines.extend(context_lines)

        return "\n".join(lines)

    def _render_file(self, message: str, context: Dict[str, Any], exc_info: Tuple) -> str:
        """Render exception for file output (structured but readable)"""
        lines = []

        # Message and basic exception info
        exc_type, exc_value, exc_traceback = exc_info
        lines.append(f"ERROR: {message}")
        lines.append(f"Exception: {exc_type.__name__ if exc_type else 'Unknown'}: {exc_value}")

        # Location information
        if context.get('exception_location'):
            lines.append(f"Location: {context['exception_location']}")

        if context.get('caller_location'):
            lines.append(f"Called from: {context['caller_location']}")

        # Stack summary
        if context.get('stack_summary'):
            lines.append(f"Stack: {context['stack_summary']}")

        # Exception locals
        if context.get('exception_locals') and self.show_exception_locals:
            lines.append("Exception locals:")
            for name, value in context['exception_locals'].items():
                lines.append(f"  {name} = {value}")

        # Additional context
        additional_context = {k: v for k, v in context.items()
                              if not k.startswith(('exception_', 'caller_', 'stack_'))}
        if additional_context:
            lines.append("Context:")
            for key, value in additional_context.items():
                lines.append(f"  {key} = {value}")

        return " | ".join(lines) if self.compact_mode else "\n".join(lines)

    def _format_context_for_console(self, context: Dict[str, Any]) -> list:
        """Format context information for console display"""
        lines = []

        # Group context by type
        caller_info = {}
        exception_info = {}
        additional_context = {}

        for key, value in context.items():
            if key.startswith('caller_'):
                caller_info[key] = value
            elif key.startswith('exception_'):
                exception_info[key] = value
            elif key not in ['stack_frames', 'stack_summary']:
                additional_context[key] = value

        # Show caller information
        if caller_info and not self.compact_mode:
            lines.append("Called from:")
            if context.get('caller_location'):
                lines.append(f"  Location: {context['caller_location']}")
            if context.get('caller_function'):
                lines.append(f"  Function: {context['caller_function']}")
            if context.get('caller_module'):
                lines.append(f"  Module: {context['caller_module']}")

        # Show additional context
        if additional_context:
            if self.compact_mode:
                context_pairs = [f"{k}={v}" for k, v in additional_context.items()]
                lines.append(f"Context: {' | '.join(context_pairs)}")
            else:
                lines.append("Additional context:")
                for key, value in additional_context.items():
                    lines.append(f"  {key}: {value}")

        return lines


def format_exception_for_display(exc_info: Optional[Tuple] = None,
                                 message: str = "",
                                 context: Dict[str, Any] = None,
                                 output_format: str = 'console',
                                 enhanced: bool = True) -> str:
    """
    Convenience function to format exception for display

    Args:
        exc_info: Exception info tuple or None for current
        message: Associated message
        context: Additional context
        output_format: Output format ('console', 'json', 'file')
        enhanced: Whether to use enhanced formatting

    Returns:
        Formatted exception string
    """
    renderer = UnifiedExceptionRenderer(
        output_format=output_format,
        show_enhanced_traceback=enhanced,
        show_caller_context=enhanced,
        show_exception_locals=enhanced
    )

    return renderer.render_exception(exc_info, message, context)


def format_exception_for_json(exc_info: Optional[Tuple] = None,
                              message: str = "",
                              context: Dict[str, Any] = None,
                              compact: bool = False) -> str:
    """
    Convenience function to format exception as JSON

    Args:
        exc_info: Exception info tuple or None for current
        message: Associated message
        context: Additional context
        compact: Whether to use compact JSON formatting

    Returns:
        JSON-formatted exception string
    """
    renderer = UnifiedExceptionRenderer(
        output_format='json',
        compact_mode=compact
    )

    return renderer.render_exception(exc_info, message, context)