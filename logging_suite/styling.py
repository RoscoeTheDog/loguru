# logging_suite/styling.py - Debug Color Issues
"""
Unified styling and formatting for cross-platform consistency
FIXED: Enhanced color support detection and application
"""

import os
import sys
import re
from typing import Dict, Any, Optional, List, Tuple, Union
from datetime import datetime
from enum import Enum
import json
import logging


class LogLevel(Enum):
    """Log level enumeration for consistent level handling"""
    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'
    CRITICAL = 'CRITICAL'


class OutputStyle:
    """ANSI color and styling utilities"""

    # ANSI color codes
    COLORS = {
        'black': '\033[30m',
        'red': '\033[31m',
        'green': '\033[32m',
        'yellow': '\033[33m',
        'blue': '\033[34m',
        'magenta': '\033[35m',
        'cyan': '\033[36m',
        'white': '\033[37m',
        'bright_red': '\033[91m',
        'bright_green': '\033[92m',
        'bright_yellow': '\033[93m',
        'bright_blue': '\033[94m',
        'bright_magenta': '\033[95m',
        'bright_cyan': '\033[96m',
        'bright_white': '\033[97m',
        'reset': '\033[0m'
    }

    # Text formatting
    FORMATS = {
        'bold': '\033[1m',
        'dim': '\033[2m',
        'italic': '\033[3m',
        'underline': '\033[4m',
        'blink': '\033[5m',
        'reverse': '\033[7m',
        'strikethrough': '\033[9m',
        'reset': '\033[0m'
    }

    # Level-specific colors
    LEVEL_COLORS = {
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'bright_red'
    }

    # Level symbols/emojis
    LEVEL_SYMBOLS = {
        'DEBUG': '🔍',
        'INFO': '✅',
        'WARNING': '⚠️',
        'ERROR': '❌',
        'CRITICAL': '🚨'
    }

    @classmethod
    def _probe_color_support(cls) -> bool:
        """Probe terminal for actual color support by testing ANSI escape sequences"""
        try:
            # If we can display emojis/unicode properly, the terminal likely supports colors too
            if hasattr(sys.stdout, 'write') and hasattr(sys.stdout, 'flush'):
                # Check encoding support
                if hasattr(sys.stdout, 'encoding') and sys.stdout.encoding:
                    encoding = sys.stdout.encoding.lower()
                    
                    # Most modern terminals support ANSI colors
                    # UTF-8, CP1252 (Windows), or similar encoding indicates capable terminal
                    if any(enc in encoding for enc in ['utf', 'cp125', 'latin', 'ascii']):
                        return True
                
                # Test buffer attribute (indicates modern stream handling)
                if hasattr(sys.stdout, 'buffer'):
                    return True
                    
                # If we can handle unicode characters (like emojis), we can likely handle colors
                try:
                    test_str = "✓"  # Unicode check mark
                    # If this doesn't raise an exception, unicode is supported
                    test_str.encode(sys.stdout.encoding or 'utf-8')
                    return True
                except (UnicodeEncodeError, LookupError):
                    pass
            
            return False
            
        except Exception as e:
            return False
    
    @classmethod
    def supports_color(cls) -> bool:
        """Check if terminal supports color output with intelligent probing"""
        try:
            # Check explicit disable first
            if os.environ.get('NO_COLOR', '').lower():
                return False

            # Check explicit enable
            force_color = os.environ.get('FORCE_COLOR', '').lower()
            if force_color in ('1', 'true', 'yes'):
                return True

            # Check standard TTY detection
            is_tty = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
            
            if is_tty:
                term = os.environ.get('TERM', 'unknown')
                if term != 'dumb':
                    return True
                else:
                    return False
            
            # For non-TTY environments, check known color terminal indicators
            colorterm = os.environ.get('COLORTERM', '')
            term = os.environ.get('TERM', '')
            
            # Enhanced terminal detection - many more terminals support colors
            if (colorterm or 
                term in ['xterm-256color', 'screen-256color', 'xterm', 'xterm-color', 'screen', 'tmux'] or
                term.startswith('xterm')):
                return True
            
            # Probe the terminal capabilities
            can_color = cls._probe_color_support()
            if can_color:
                return True
            
            # Fallback: if we're in a development environment and unicode/emojis work,
            # assume colors work too (since they're clearly displaying in the output)
            try:
                # Test if we can output a simple test
                test_unicode = "✓"  # This emoji is showing up in the output
                # If we got this far and emojis work, colors likely work too
                return True
            except:
                pass
            
            return False

        except Exception:
            return False

    @classmethod
    def colorize(cls, text: str, color: str = None, bold: bool = False,
                 dim: bool = False, underline: bool = False) -> str:
        """Apply color and formatting to text"""
        if not cls.supports_color():
            return text

        codes = []

        if color and color in cls.COLORS:
            codes.append(cls.COLORS[color])

        if bold:
            codes.append(cls.FORMATS['bold'])
        if dim:
            codes.append(cls.FORMATS['dim'])
        if underline:
            codes.append(cls.FORMATS['underline'])

        if codes:
            result = ''.join(codes) + text + cls.COLORS['reset']
            return result

        return text

    @classmethod
    def highlight_keywords(cls, text: str, keywords: List[str]) -> str:
        """Highlight specific keywords in text"""
        if not cls.supports_color():
            return text

        highlighted = text
        for keyword in keywords:
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            if keyword.upper() in ['ERROR', 'FAILED', 'EXCEPTION']:
                replacement = cls.colorize(keyword.upper(), 'bright_red', bold=True)
            elif keyword.upper() in ['SUCCESS', 'OK', 'COMPLETED']:
                replacement = cls.colorize(keyword.upper(), 'bright_green', bold=True)
            elif keyword.upper() in ['WARNING', 'WARN']:
                replacement = cls.colorize(keyword.upper(), 'bright_yellow', bold=True)
            else:
                replacement = cls.colorize(keyword, 'bright_cyan', bold=True)

            highlighted = pattern.sub(replacement, highlighted)

        return highlighted


class UnifiedConsoleFormatter:
    """Unified console formatter that provides consistent styling across all backends"""

    def __init__(self,
                 use_colors: bool = True,
                 use_symbols: bool = True,
                 compact: bool = False,
                 highlight_keywords: List[str] = None,
                 show_module: bool = True,
                 show_function: bool = False,
                 datetime_format: str = '%H:%M:%S',
                 style: str = 'standard'):
        """
        Initialize unified console formatter

        Args:
            use_colors: Enable ANSI colors
            use_symbols: Use emoji symbols for log levels
            compact: Use compact single-line format
            highlight_keywords: Keywords to highlight in messages
            show_module: Show module name in output
            show_function: Show function name in output
            datetime_format: Datetime format string
            style: Output style ('standard', 'hierarchical')
        """
        self.use_colors = use_colors and OutputStyle.supports_color()
        self.use_symbols = use_symbols
        self.compact = compact
        self.highlight_keywords = highlight_keywords or ['ERROR', 'SUCCESS', 'FAILED', 'WARNING']
        self.show_module = show_module
        self.show_function = show_function
        self.datetime_format = datetime_format
        self.style = style


    def format_log_entry(self,
                         level: str,
                         message: str,
                         logger_name: str,
                         timestamp: str = None,
                         context: Dict[str, Any] = None) -> str:
        """Format a log entry with unified styling"""

        # Parse timestamp
        if timestamp:
            try:
                if isinstance(timestamp, str):
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                else:
                    dt = timestamp
                time_str = dt.strftime(self.datetime_format)
            except:
                time_str = timestamp if isinstance(timestamp, str) else str(timestamp)
        else:
            time_str = datetime.now().strftime(self.datetime_format)

        # Format level
        level_str = level.upper()
        if self.use_symbols and level_str in OutputStyle.LEVEL_SYMBOLS:
            level_display = f"{OutputStyle.LEVEL_SYMBOLS[level_str]} {level_str:8s}"
        else:
            level_display = f"{level_str:8s}"

        # Apply level coloring
        if self.use_colors and level_str in OutputStyle.LEVEL_COLORS:
            color = OutputStyle.LEVEL_COLORS[level_str]
            bold = level_str in ['ERROR', 'CRITICAL']
            level_display = OutputStyle.colorize(
                level_display,
                color,
                bold=bold
            )

        # Format logger name
        if self.show_module:
            logger_display = logger_name
        else:
            # Show only the last part of the logger name
            logger_display = logger_name.split('.')[-1]

        # Highlight keywords in message
        formatted_message = message
        if self.use_colors and self.highlight_keywords:
            formatted_message = OutputStyle.highlight_keywords(message, self.highlight_keywords)
            
        # Check for explicit highlight flag from highlight() method
        if self.use_colors and context and context.get('_highlight', False):
            # Highlight the entire message with bright cyan and bold
            formatted_message = OutputStyle.colorize(formatted_message, 'bright_cyan', bold=True)

        # Format context
        context_str = ""
        if context:
            # Show important context fields
            important_fields = ['user_id', 'request_id', 'session_id', 'action', 'status_code',
                                'execution_time_seconds', 'error_type', 'function']

            context_parts = []
            for key in important_fields:
                if key in context:
                    value = context[key]
                    if key == 'execution_time_seconds':
                        context_parts.append(f"{key}={value:.3f}s")
                    else:
                        context_parts.append(f"{key}={value}")

            # Add any other context fields (limited)
            other_fields = {k: v for k, v in context.items() if k not in important_fields}
            if other_fields and len(context_parts) < 5:  # Limit context display
                for key, value in list(other_fields.items())[:3]:  # Max 3 additional fields
                    context_parts.append(f"{key}={value}")

            if context_parts:
                if self.compact:
                    context_str = f" ({' '.join(context_parts)})"
                else:
                    context_str = f"\n    Context: {' | '.join(context_parts)}"

        # Use hierarchical formatting if specified
        if self.style == 'hierarchical':
            return self._format_hierarchical(level, message, logger_name, time_str, context)
        
        # Combine all parts (standard formatting)
        if self.compact:
            # Single line format: TIME LEVEL LOGGER: MESSAGE (context)
            result = f"{time_str} {level_display} {logger_display}: {formatted_message}{context_str}"
        else:
            # Multi-line format with more detail
            parts = [f"{time_str} | {level_display} | {logger_display}"]

            if self.show_function and context and 'function' in context:
                parts.append(f" | {context['function']}")

            result = ''.join(parts) + f"\n  {formatted_message}"

            if context_str:
                result += context_str

        return result

    def _format_hierarchical(self, 
                            level: str, 
                            message: str, 
                            logger_name: str, 
                            time_str: str, 
                            context: Dict[str, Any] = None) -> str:
        """Format log entry using hierarchical style with box-drawing characters"""
        
        # Level symbols and colors
        level_upper = level.upper()
        if self.use_symbols and level_upper in OutputStyle.LEVEL_SYMBOLS:
            level_symbol = OutputStyle.LEVEL_SYMBOLS[level_upper]
        else:
            level_symbol = "📋" if level_upper == 'INFO' else "⚠️"
            
        # Apply level coloring
        if self.use_colors and level_upper in OutputStyle.LEVEL_COLORS:
            color = OutputStyle.LEVEL_COLORS[level_upper]
            bold = level_upper in ['ERROR', 'CRITICAL']
            level_display = OutputStyle.colorize(level_upper, color, bold=bold)
        else:
            level_display = level_upper
            
        # Format logger name
        logger_display = logger_name if self.show_module else logger_name.split('.')[-1]
        
        # Highlight message keywords
        formatted_message = message
        if self.use_colors and self.highlight_keywords:
            formatted_message = OutputStyle.highlight_keywords(message, self.highlight_keywords)
            
        # Check for explicit highlight flag
        if self.use_colors and context and context.get('_highlight', False):
            formatted_message = OutputStyle.colorize(formatted_message, 'bright_cyan', bold=True)

        # Start building hierarchical output
        lines = []
        
        # Header line with time, level, and logger
        header = f"┌─ {time_str} │ {level_symbol} {level_display} │ "
        if self.use_colors:
            header += OutputStyle.colorize(logger_display, 'cyan')
        else:
            header += logger_display
        lines.append(header)
        
        # Message line
        lines.append(f"├─ {formatted_message}")
        
        # Context section
        if context:
            # Show important context fields
            important_fields = ['user_id', 'request_id', 'session_id', 'action', 'status_code',
                                'execution_time_seconds', 'error_type', 'function', 'method', 'path']
            
            context_items = []
            for key in important_fields:
                if key in context:
                    value = context[key]
                    if key == 'execution_time_seconds':
                        context_items.append((key, f"{value:.3f}s"))
                    else:
                        context_items.append((key, str(value)))
            
            # Add other context fields (limited)
            other_fields = {k: v for k, v in context.items() if k not in important_fields and not k.startswith('_')}
            if other_fields and len(context_items) < 6:  # Limit context display
                for key, value in list(other_fields.items())[:3]:  # Max 3 additional fields
                    context_items.append((key, str(value)))
            
            if context_items:
                lines.append("├─ Context:")
                for i, (key, value) in enumerate(context_items):
                    is_last = (i == len(context_items) - 1)
                    prefix = "│  └─" if is_last else "│  ├─"
                    
                    if self.use_colors:
                        key_colored = OutputStyle.colorize(key, 'yellow')
                        value_colored = OutputStyle.colorize(value, 'white')
                        lines.append(f"{prefix} {key_colored}: {value_colored}")
                    else:
                        lines.append(f"{prefix} {key}: {value}")
        
        # Footer line
        lines.append("└─" + "─" * (max(50, len(lines[0]) - 2)))
        
        return '\n'.join(lines)

    def format_exception(self, exc_info: Dict[str, Any]) -> str:
        """Format exception information with styling"""
        if not exc_info:
            return ""

        exc_type = exc_info.get('type', 'Exception')
        exc_message = exc_info.get('message', 'Unknown error')
        exc_traceback = exc_info.get('traceback', '')

        # Style the exception
        if self.use_colors:
            exc_header = OutputStyle.colorize(f"{exc_type}: {exc_message}", 'bright_red', bold=True)
        else:
            exc_header = f"{exc_type}: {exc_message}"

        result = f"\n  Exception: {exc_header}"

        if exc_traceback and not self.compact:
            # Show traceback with indentation
            traceback_lines = exc_traceback.strip().split('\n')
            for line in traceback_lines[-3:]:  # Show last 3 lines
                result += f"\n    {line}"

        return result


# Enhanced logging.Formatter for standard logging integration
class UnifiedLoggingFormatter(logging.Formatter):
    """
    Logging.Formatter wrapper around UnifiedConsoleFormatter for standard logging integration
    """

    def __init__(self, **formatter_options):
        """Initialize with UnifiedConsoleFormatter options"""
        super().__init__()

        # Map console_log_style to style parameter (prioritize console_log_style over style)
        if 'console_log_style' in formatter_options:
            formatter_options['style'] = formatter_options.pop('console_log_style')
        elif 'style' not in formatter_options:
            # Default to hierarchical if no style specified
            formatter_options['style'] = 'hierarchical'
        
        self.console_formatter = UnifiedConsoleFormatter(**formatter_options)

    def format(self, record: logging.LogRecord) -> str:
        """Format LogRecord using UnifiedConsoleFormatter"""

        # Extract context from record
        context = {}
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                           'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                           'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                           'thread', 'threadName', 'processName', 'process', 'getMessage']:
                context[key] = value

        # Add function context if available
        if hasattr(record, 'funcName') and record.funcName:
            context['function'] = record.funcName

        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created)

        # Use UnifiedConsoleFormatter
        formatted = self.console_formatter.format_log_entry(
            level=record.levelname,
            message=record.getMessage(),
            logger_name=record.name,
            timestamp=timestamp.isoformat(),
            context=context
        )

        # Add exception if present
        if record.exc_info:
            exc_dict = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else 'Exception',
                'message': str(record.exc_info[1]) if record.exc_info[1] else 'Unknown error',
                'traceback': self.formatException(record.exc_info) if record.exc_info else ''
            }
            formatted += self.console_formatter.format_exception(exc_dict)

        return formatted


class LogFileFormatter:
    """Formatter for log files (non-console output)"""

    def __init__(self, include_context: bool = True, max_context_fields: int = 10):
        self.include_context = include_context
        self.max_context_fields = max_context_fields

    def format_log_entry(self,
                         level: str,
                         message: str,
                         logger_name: str,
                         timestamp: str = None,
                         context: Dict[str, Any] = None) -> str:
        """Format log entry for file output (plain text, no colors)"""

        # Use ISO timestamp for files
        if timestamp:
            try:
                if isinstance(timestamp, str):
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                else:
                    dt = timestamp
                time_str = dt.isoformat()
            except:
                time_str = timestamp if isinstance(timestamp, str) else str(timestamp)
        else:
            time_str = datetime.now().isoformat()

        # Build the log line
        parts = [
            time_str,
            level.upper().ljust(8),
            logger_name,
            message
        ]

        base_line = ' | '.join(parts)

        # Add context if present
        if context and self.include_context:
            context_parts = []
            field_count = 0

            for key, value in context.items():
                if field_count >= self.max_context_fields:
                    break

                # Skip internal fields
                if key.startswith('_'):
                    continue

                context_parts.append(f"{key}={value}")
                field_count += 1

            if context_parts:
                base_line += f" | Context: {' | '.join(context_parts)}"

        return base_line


# Enhanced logging.Formatter for file output
class FileLoggingFormatter(logging.Formatter):
    """
    Logging.Formatter wrapper around LogFileFormatter for file logging
    """

    def __init__(self, **formatter_options):
        """Initialize with LogFileFormatter options"""
        super().__init__()
        self.file_formatter = LogFileFormatter(**formatter_options)

    def format(self, record: logging.LogRecord) -> str:
        """Format LogRecord using LogFileFormatter"""

        # Extract context from record
        context = {}
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                           'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                           'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                           'thread', 'threadName', 'processName', 'process', 'getMessage']:
                context[key] = value

        # Add function context if available
        if hasattr(record, 'funcName') and record.funcName:
            context['function'] = record.funcName

        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created)

        # Use LogFileFormatter
        formatted = self.file_formatter.format_log_entry(
            level=record.levelname,
            message=record.getMessage(),
            logger_name=record.name,
            timestamp=timestamp.isoformat(),
            context=context
        )

        # Add exception if present
        if record.exc_info:
            formatted += f" | Exception: {self.formatException(record.exc_info)}"

        return formatted


class PrettyJSONFormatter(logging.Formatter):
    """
    JSON formatter with configurable pretty printing for development use
    Enhanced with better configuration options
    """

    def __init__(self,
                 indent: Optional[int] = None,
                 separators: Optional[Tuple[str, str]] = None,
                 pretty: bool = False,
                 **kwargs):
        """
        Initialize JSON formatter

        Args:
            indent: JSON indentation (None for compact, 2 for pretty)
            separators: JSON separators (item_sep, key_sep)
            pretty: Enable pretty printing (overrides indent/separators)
            **kwargs: Additional formatter arguments
        """
        super().__init__(**kwargs)

        if pretty:
            # Pretty printing defaults with proper spacing
            self.indent = indent or 2
            self.separators = separators or (', ', ': ')
        else:
            # Compact defaults
            self.indent = indent
            self.separators = separators or (',', ':')

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""

        # Build base log entry
        log_entry = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                           'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                           'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                           'thread', 'threadName', 'processName', 'process', 'getMessage']:
                log_entry[key] = value

        # Handle exceptions
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)

        # Format as JSON with specified indentation and separators
        try:
            if self.indent is not None:
                # Pretty printing
                formatted = json.dumps(
                    log_entry,
                    indent=self.indent,
                    separators=self.separators,
                    default=str,
                    ensure_ascii=False
                )
            else:
                # Compact printing
                formatted = json.dumps(
                    log_entry,
                    separators=self.separators,
                    default=str,
                    ensure_ascii=False
                )
            return formatted
        except (TypeError, ValueError) as e:
            # Fallback to string representation if JSON serialization fails
            return f"JSON formatting error: {e} - {log_entry}"


class CompactJSONFormatter(logging.Formatter):
    """
    Compact JSON formatter optimized for production logging
    """

    def __init__(self, **kwargs):
        """Initialize compact JSON formatter"""
        super().__init__(**kwargs)
        self.separators = (',', ':')  # Most compact separators

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as compact JSON"""

        # Build minimal log entry with shorter field names for space efficiency
        log_entry = {
            'ts': self.formatTime(record),
            'lvl': record.levelname,
            'name': record.name,
            'msg': record.getMessage(),
            'mod': record.module,
            'func': record.funcName,
            'line': record.lineno
        }

        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                           'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                           'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                           'thread', 'threadName', 'processName', 'process', 'getMessage']:
                log_entry[key] = value

        # Handle exceptions with compact format
        if record.exc_info:
            log_entry['exc'] = self.formatException(record.exc_info)

        # Format as compact JSON
        try:
            return json.dumps(log_entry, separators=self.separators, default=str, ensure_ascii=False)
        except (TypeError, ValueError) as e:
            # Fallback to string representation if JSON serialization fails
            return f"JSON formatting error: {e} - {log_entry}"


class StyleManager:
    """Manage styling across different output destinations"""

    def __init__(self):
        self.console_formatter = UnifiedConsoleFormatter()
        self.file_formatter = LogFileFormatter()

    def format_for_console(self, log_data: Dict[str, Any]) -> str:
        """Format log entry for console output"""
        return self.console_formatter.format_log_entry(
            level=log_data.get('level', 'INFO'),
            message=log_data.get('message', ''),
            logger_name=log_data.get('logger', 'unknown'),
            timestamp=log_data.get('timestamp'),
            context=log_data.get('context', {})
        )

    def format_for_file(self, log_data: Dict[str, Any]) -> str:
        """Format log entry for file output"""
        return self.file_formatter.format_log_entry(
            level=log_data.get('level', 'INFO'),
            message=log_data.get('message', ''),
            logger_name=log_data.get('logger', 'unknown'),
            timestamp=log_data.get('timestamp'),
            context=log_data.get('context', {})
        )

    def configure_console_style(self, **options):
        """Configure console styling options"""
        self.console_formatter = UnifiedConsoleFormatter(**options)

    def configure_file_style(self, **options):
        """Configure file formatting options"""
        self.file_formatter = LogFileFormatter(**options)


# Factory functions for creating formatters
def create_formatter(format_type: str, config: Dict[str, Any]) -> logging.Formatter:
    """
    Create a formatter based on configuration

    Args:
        format_type: Type of formatter ('json', 'pretty_json', 'compact_json', 'console', 'file')
        config: Configuration dictionary

    Returns:
        Configured formatter instance
    """
    format_type = format_type.lower()

    if format_type == 'pretty_json':
        return PrettyJSONFormatter(
            indent=config.get('json_indent', 2),
            separators=config.get('json_separators', (', ', ': ')),
            pretty=config.get('pretty_json', True)
        )
    elif format_type == 'compact_json':
        return CompactJSONFormatter()
    elif format_type == 'json':
        # Default JSON formatter - pretty in development, compact in production
        is_development = config.get('format') == 'console' or config.get('level') == 'DEBUG'
        if is_development and config.get('pretty_json', True):
            return PrettyJSONFormatter(
                indent=config.get('json_indent', 2),
                separators=config.get('json_separators', (', ', ': ')),
                pretty=True
            )
        else:
            return CompactJSONFormatter()
    elif format_type == 'console':
        return UnifiedLoggingFormatter(
            use_colors=config.get('use_colors', True),
            use_symbols=config.get('use_symbols', True),
            compact=config.get('compact_format', False),
            show_module=config.get('show_module', True),
            show_function=config.get('show_function', False)
        )
    elif format_type == 'file':
        return FileLoggingFormatter(
            include_context=config.get('include_context', True),
            max_context_fields=config.get('max_context_fields', 10)
        )
    else:
        # Default to console formatter
        return UnifiedLoggingFormatter()


def get_formatter_for_handler(handler_type: str, config: Dict[str, Any]) -> logging.Formatter:
    """
    Get appropriate formatter for a specific handler type

    Args:
        handler_type: Type of handler ('console', 'file', 'rotating_file', etc.)
        config: Configuration dictionary

    Returns:
        Appropriate formatter instance
    """

    if handler_type == 'console':
        if config.get('format') == 'json' or config.get('use_json_handlers', False):
            if config.get('pretty_json', False):
                return create_formatter('pretty_json', config)
            else:
                return create_formatter('json', config)
        else:
            return create_formatter('console', config)

    elif handler_type in ['file', 'rotating_file', 'timed_rotating_file']:
        if config.get('use_json_handlers', True):
            # Use compact JSON for files to save space unless pretty is explicitly requested
            if config.get('pretty_json', False) and config.get('level') == 'DEBUG':
                return create_formatter('pretty_json', config)
            else:
                return create_formatter('compact_json', config)
        else:
            return create_formatter('file', config)

    else:
        # Default to console formatter
        return create_formatter('console', config)


# Legacy function for backwards compatibility
def create_pretty_json_formatter(config: Dict[str, Any]) -> PrettyJSONFormatter:
    """Create a JSON formatter based on configuration (legacy function)"""
    return PrettyJSONFormatter(
        indent=config.get('json_indent'),
        separators=config.get('json_separators'),
        pretty=config.get('pretty_json', False)
    )


# Export all formatters and utilities
__all__ = [
    'LogLevel',
    'OutputStyle',
    'UnifiedConsoleFormatter',
    'UnifiedLoggingFormatter',
    'LogFileFormatter',
    'FileLoggingFormatter',
    'PrettyJSONFormatter',
    'CompactJSONFormatter',
    'StyleManager',
    'create_formatter',
    'create_pretty_json_formatter',
    'get_formatter_for_handler'
]