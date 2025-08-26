# logging_suite/exceptions/traceback_formatter.py
"""
Enhanced traceback formatter providing loguru-style exception details
FIXED: Python 3.9 compatible type hints
"""

import sys
import traceback
import linecache
from typing import Dict, Any, List, Optional, Tuple, Union
from pathlib import Path

# Python 3.9 compatible type hint for frame
try:
    from types import FrameType
except ImportError:
    FrameType = type(sys._getframe())


class EnhancedTracebackFormatter:
    """
    Formatter that provides loguru-style enhanced tracebacks with variable values
    """

    def __init__(self,
                 show_locals: bool = True,
                 max_locals: int = 10,
                 max_string_length: int = 100,
                 colorize: bool = True,
                 show_values: bool = True):
        """
        Initialize enhanced traceback formatter

        Args:
            show_locals: Whether to show local variable values
            max_locals: Maximum number of local variables to show per frame
            max_string_length: Maximum length for string representations
            colorize: Whether to use colors in output (if supported)
            show_values: Whether to show variable values with arrows
        """
        self.show_locals = show_locals
        self.max_locals = max_locals
        self.max_string_length = max_string_length
        self.colorize = colorize
        self.show_values = show_values

    def format_exception(self, exc_info: Tuple) -> str:
        """
        Format exception with enhanced traceback

        Args:
            exc_info: Exception info tuple (type, value, traceback)

        Returns:
            Formatted exception string with enhanced details
        """
        if exc_info == (None, None, None):
            return ""

        exc_type, exc_value, exc_traceback = exc_info

        if exc_traceback is None:
            return f"{exc_type.__name__}: {exc_value}"

        lines = []
        lines.append("Traceback (most recent call last):")
        lines.append("")

        # Process each frame in the traceback
        tb = exc_traceback
        frames = []

        # Collect all frames first
        while tb is not None:
            frames.append((tb.tb_frame, tb.tb_lineno))
            tb = tb.tb_next

        # Format each frame
        for i, (frame, lineno) in enumerate(frames):
            is_last_frame = (i == len(frames) - 1)
            frame_output = self._format_frame(frame, lineno, is_last_frame)
            lines.extend(frame_output)

            if not is_last_frame:
                lines.append("")

        # Add final exception line
        lines.append("")
        lines.append(f"{exc_type.__name__}: {exc_value}")

        return "\n".join(lines)

    def _format_frame(self, frame, lineno: int, is_exception_frame: bool = False) -> List[str]:
        """
        Format a single frame with enhanced details

        Args:
            frame: Frame object
            lineno: Line number where exception occurred
            is_exception_frame: Whether this is the frame where exception occurred

        Returns:
            List of formatted lines for this frame
        """
        code = frame.f_code
        filename = code.co_filename
        function_name = code.co_name

        lines = []

        # Frame header with file and function info
        display_filename = Path(filename).name if filename else 'unknown'
        prefix = ">" if is_exception_frame else " "

        lines.append(f"{prefix} File \"{display_filename}\", line {lineno}, in {function_name}")

        # Get the source line
        source_line = linecache.getline(filename, lineno).strip()
        if source_line:
            # Show the source code line with indentation
            lines.append(f"    {source_line}")

            # Show variable values if enabled and this is the exception frame
            if self.show_values and is_exception_frame:
                variable_lines = self._extract_variable_values(source_line, frame)
                lines.extend(variable_lines)

        # Show local variables if enabled
        if self.show_locals and is_exception_frame:
            locals_lines = self._format_frame_locals(frame)
            if locals_lines:
                lines.extend(locals_lines)

        return lines

    def _extract_variable_values(self, source_line: str, frame) -> List[str]:
        """
        Extract and format variable values from the source line
        Creates loguru-style arrows pointing to variable values

        Args:
            source_line: Source code line
            frame: Frame object

        Returns:
            List of formatted lines showing variable values
        """
        lines = []
        frame_locals = frame.f_locals
        frame_globals = frame.f_globals

        # Simple variable extraction - look for identifiers in the source line
        import re
        import keyword

        # Find potential variable names (simple heuristic)
        variable_pattern = re.compile(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b')
        variables_found = []

        for match in variable_pattern.finditer(source_line):
            var_name = match.group(1)

            # Skip keywords and built-ins
            if keyword.iskeyword(var_name) or var_name in ['True', 'False', 'None']:
                continue

            # Check if variable exists in locals or globals
            value = None
            if var_name in frame_locals:
                value = frame_locals[var_name]
            elif var_name in frame_globals:
                value = frame_globals[var_name]
            else:
                continue

            # Get position of variable in source line
            start_pos = match.start()
            variables_found.append((start_pos, var_name, value))

        if not variables_found:
            return lines

        # Sort by position (rightmost first for proper arrow placement)
        variables_found.sort(key=lambda x: x[0], reverse=True)

        # Create arrow lines
        for pos, var_name, value in variables_found:
            # Format the value
            formatted_value = self._format_value(value)

            # Create arrow line pointing to the variable
            arrow_line = " " * (pos + 4) + "│" + " " * (len(var_name) - 1) + f"└ {formatted_value}"
            lines.append(arrow_line)

        return lines

    def _format_value(self, value: Any) -> str:
        """
        Format a variable value for display

        Args:
            value: Variable value to format

        Returns:
            Formatted string representation
        """
        try:
            if value is None:
                return "None"
            elif isinstance(value, str):
                if len(value) > self.max_string_length:
                    return f'"{value[:self.max_string_length]}..."'
                else:
                    return f'"{value}"'
            elif isinstance(value, (int, float, bool)):
                return str(value)
            elif isinstance(value, (list, tuple)):
                if len(value) == 0:
                    return "[]" if isinstance(value, list) else "()"
                elif len(value) <= 3:
                    items = [self._format_value(item) for item in value]
                    return f"[{', '.join(items)}]" if isinstance(value, list) else f"({', '.join(items)})"
                else:
                    return f"[{len(value)} items]" if isinstance(value, list) else f"({len(value)} items)"
            elif isinstance(value, dict):
                if len(value) == 0:
                    return "{}"
                elif len(value) <= 2:
                    items = [f"{k}: {self._format_value(v)}" for k, v in list(value.items())[:2]]
                    return f"{{{', '.join(items)}}}"
                else:
                    return f"{{{len(value)} items}}"
            elif callable(value):
                return f"<function {getattr(value, '__name__', 'unknown')} at {hex(id(value))}>"
            else:
                class_name = type(value).__name__
                if hasattr(value, '__str__'):
                    try:
                        str_repr = str(value)
                        if len(str_repr) > 50:
                            return f"<{class_name}>"
                        else:
                            return f"<{class_name}: {str_repr}>"
                    except Exception:
                        return f"<{class_name}>"
                else:
                    return f"<{class_name}>"
        except Exception:
            return f"<{type(value).__name__}>"

    def _format_frame_locals(self, frame) -> List[str]:
        """
        Format local variables for a frame

        Args:
            frame: Frame object

        Returns:
            List of formatted lines showing local variables
        """
        lines = []
        frame_locals = frame.f_locals

        if not frame_locals:
            return lines

        # Filter and limit locals
        relevant_locals = {}
        for name, value in frame_locals.items():
            # Skip private variables and built-ins
            if name.startswith('__') and name.endswith('__'):
                continue
            if name in ['self', 'cls'] and len(relevant_locals) > 0:
                continue

            relevant_locals[name] = value

            if len(relevant_locals) >= self.max_locals:
                break

        if relevant_locals:
            lines.append("    Local variables:")
            for name, value in relevant_locals.items():
                formatted_value = self._format_value(value)
                lines.append(f"      {name} = {formatted_value}")

        return lines


def format_enhanced_traceback(exc_info: Optional[Tuple] = None,
                              show_locals: bool = True,
                              show_values: bool = True,
                              colorize: bool = True) -> str:
    """
    Convenience function to format enhanced traceback

    Args:
        exc_info: Exception info tuple or None for current exception
        show_locals: Whether to show local variables
        show_values: Whether to show variable values with arrows
        colorize: Whether to use colors (if terminal supports it)

    Returns:
        Formatted enhanced traceback string
    """
    if exc_info is None:
        exc_info = sys.exc_info()

    if exc_info == (None, None, None):
        return ""

    formatter = EnhancedTracebackFormatter(
        show_locals=show_locals,
        show_values=show_values,
        colorize=colorize
    )

    return formatter.format_exception(exc_info)


def capture_frame_locals(frame,
                         max_locals: int = 10,
                         max_string_length: int = 100,
                         sensitive_keys: List[str] = None) -> Dict[str, Any]:
    """
    Capture local variables from a frame with sanitization

    Args:
        frame: Frame to capture locals from
        max_locals: Maximum number of locals to capture
        max_string_length: Maximum length for string values
        sensitive_keys: Keys to mask (for security)

    Returns:
        Dictionary of captured and sanitized local variables
    """
    if sensitive_keys is None:
        sensitive_keys = ['password', 'token', 'secret', 'key', 'auth']

    if not frame:
        return {}

    try:
        locals_dict = {}
        frame_locals = frame.f_locals
        count = 0

        for name, value in frame_locals.items():
            if count >= max_locals:
                break

            # Skip private/internal variables
            if name.startswith('__') and name.endswith('__'):
                continue

            # Check for sensitive data
            if any(sensitive in name.lower() for sensitive in sensitive_keys):
                locals_dict[name] = "***REDACTED***"
                count += 1
                continue

            # Format value safely
            try:
                if callable(value):
                    locals_dict[name] = f"<function {getattr(value, '__name__', 'unknown')}>"
                elif hasattr(value, '__dict__') and not isinstance(value, (str, int, float, bool, list, dict, tuple)):
                    locals_dict[name] = f"<{type(value).__name__}>"
                else:
                    str_value = str(value)
                    if len(str_value) > max_string_length:
                        locals_dict[name] = f"{str_value[:max_string_length]}...(truncated)"
                    else:
                        locals_dict[name] = value
            except Exception:
                locals_dict[name] = f"<{type(value).__name__}>"

            count += 1

        return locals_dict

    except Exception:
        return {}