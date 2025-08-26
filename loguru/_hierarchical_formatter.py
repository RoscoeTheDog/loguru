"""
Hierarchical box-drawing formatter for beautiful loguru output.

This module provides the beautiful hierarchical formatting with Unicode box-drawing
characters that was the signature feature of the original logging_suite.
"""

import re
from typing import Dict, Any, Optional, List, Union
from ._templates import TemplateConfig, ContextType
from ._colorizer import Colorizer


class HierarchicalFormatter:
    """
    Hierarchical formatter that creates beautiful box-drawing output.
    
    This is the core implementation of the "beautiful" template style that provides
    the distinctive hierarchical logging output with Unicode box-drawing characters.
    """
    
    def __init__(self, template: TemplateConfig):
        """Initialize hierarchical formatter with template configuration."""
        self.template = template
        self.use_colors = True  # Always use colors for beautiful output
        self.use_symbols = True  # Always use symbols for beautiful output
        
        # Level symbols (can be overridden by template)
        self.level_symbols = {
            'DEBUG': '🔍',
            'INFO': '📋',
            'SUCCESS': '✅', 
            'WARNING': '⚠️',
            'ERROR': '❌',
            'CRITICAL': '🚨'
        }
        
        # Fallback symbols for environments that don't support emojis
        self.fallback_symbols = {
            'DEBUG': '?',
            'INFO': 'i',
            'SUCCESS': '✓',
            'WARNING': '!',
            'ERROR': 'X',
            'CRITICAL': '!'
        }
        
    def supports_unicode(self) -> bool:
        """Check if the environment supports Unicode box-drawing characters."""
        try:
            # Test Unicode support
            test_chars = "┌─├─└─│"
            return True  # Assume Unicode support in modern terminals
        except UnicodeError:
            return False
    
    def format_record(
        self,
        level: str,
        message: str, 
        logger_name: str,
        timestamp: str,
        extra: Dict[str, Any] = None
    ) -> str:
        """
        Format a log record using hierarchical box-drawing style.
        
        This creates the signature beautiful formatting with:
        - Header line with timestamp, level symbol, and logger
        - Message line with proper indentation  
        - Context section with hierarchical key-value pairs
        - Footer line for visual separation
        """
        extra = extra or {}
        
        # Determine level symbol and styling
        level_upper = level.upper()
        if self.use_symbols:
            if level_upper in self.level_symbols:
                level_symbol = self.level_symbols[level_upper]
            else:
                level_symbol = self.fallback_symbols.get(level_upper, 'i')
        else:
            level_symbol = level_upper[0]  # First letter
            
        # Apply level coloring using loguru markup
        level_display = level_upper
        if level_upper in self.template.level_styles:
            style = self.template.level_styles[level_upper]
            level_display = f"<{style}>{level_upper}</{style}>"
        
        # Format logger name with coloring
        logger_display = logger_name.split('.')[-1]  # Show only last part
        if self.use_colors:
            logger_display = f"<cyan>{logger_display}</cyan>"
            
        # Apply context styling to the message
        styled_message = self._apply_context_styling(message, extra)
        
        # Build the hierarchical output WITHOUT markup first
        lines = []
        
        # Header line with box-drawing characters
        header = f"┌─ {timestamp} │ {level_symbol} {level_display} │ {logger_display}"
        lines.append(header)
        
        # Message line
        lines.append(f"├─ {styled_message}")
        
        # Context section if available
        if extra:
            context_lines = self._format_context_section(extra)
            lines.extend(context_lines)
        
        # Footer line for visual separation
        footer_width = 50  # Fixed width to avoid color code counting issues
        footer = "└" + "─" * footer_width
        lines.append(footer)
        
        # Join lines and apply colorization at the END
        full_output = '\n'.join(lines)
        
        # Apply loguru colorization to the complete output
        return Colorizer.ansify(full_output)
    
    def _apply_context_styling(self, message: str, context: Dict[str, Any]) -> str:
        """Apply intelligent context-based styling to the message."""
        styled_message = message
        
        # Track processed ranges to avoid overlapping styles
        processed_ranges = []
        
        # Apply style rules from template - but fix the style format
        for rule in sorted(self.template.style_rules, key=lambda r: r.priority, reverse=True):
            matches = list(rule.pattern.finditer(styled_message))
            if matches:
                # Apply replacements in reverse order to maintain positions
                for match in reversed(matches):
                    start, end = match.span()
                    
                    # Check for overlaps with already processed ranges
                    overlap = any(
                        (start < proc_end and end > proc_start)
                        for proc_start, proc_end in processed_ranges
                    )
                    
                    if not overlap:
                        original_text = match.group()
                        
                        # Simplify style handling to avoid nesting issues
                        style = rule.style.strip()
                        if " " in style:
                            # For compound styles, just use the first part (color)
                            style = style.split()[0]
                        
                        styled_text = f"<{style}>{original_text}</{style}>"
                        
                        styled_message = styled_message[:start] + styled_text + styled_message[end:]
                        
                        # Calculate new positions after replacement
                        offset = len(styled_text) - len(original_text)
                        adjusted_start = start
                        adjusted_end = end + offset
                        
                        processed_ranges.append((adjusted_start, adjusted_end))
        
        return styled_message
    
    def _format_context_section(self, context: Dict[str, Any]) -> List[str]:
        """Format context data using hierarchical box-drawing structure."""
        lines = []
        
        if not context:
            return lines
            
        # Filter and prioritize context fields
        important_fields = [
            'user_id', 'user', 'username', 'request_id', 'session_id', 
            'action', 'method', 'path', 'status_code', 'response_time',
            'execution_time_seconds', 'duration', 'error_type', 'function'
        ]
        
        # Separate important and other fields
        important_items = []
        other_items = []
        
        for key, value in context.items():
            # Skip internal fields
            if key.startswith('_'):
                continue
                
            if key in important_fields:
                important_items.append((key, value))
            else:
                other_items.append((key, value))
        
        # Combine (important first, then others, but limit total)
        context_items = important_items + other_items[:3]  # Max 3 additional fields
        
        if not context_items:
            return lines
            
        # Context header
        lines.append("├─ Context:")
        
        # Format each context item
        for i, (key, value) in enumerate(context_items):
            is_last = (i == len(context_items) - 1)
            
            # Choose appropriate box-drawing character
            if is_last:
                prefix = "│  └─"
            else:
                prefix = "│  ├─"
            
            # Format the value
            formatted_value = self._format_context_value(key, value)
            
            # Apply context styling
            if key in self.template.context_styles:
                style = self.template.context_styles[key]
                styled_key = f"<{style}>{key}</{style}>"
            else:
                styled_key = f"<yellow>{key}</yellow>"
                
            # Style value based on type/content
            styled_value = self._style_context_value(formatted_value)
            
            line = f"{prefix} {styled_key}: {styled_value}"
            lines.append(line)
        
        return lines
    
    def _format_context_value(self, key: str, value: Any) -> str:
        """Format a context value appropriately."""
        if key == 'execution_time_seconds' and isinstance(value, (int, float)):
            return f"{value:.3f}s"
        elif key in ['response_time', 'duration'] and isinstance(value, (int, float)):
            if value < 1:
                return f"{value*1000:.1f}ms"
            else:
                return f"{value:.2f}s"
        else:
            return str(value)
    
    def _style_context_value(self, value: Any) -> str:
        """Apply styling to a context value based on its type and content."""
        if isinstance(value, bool):
            color = "green" if value else "red"
            return f"<{color}>{value}</{color}>"
        elif isinstance(value, (int, float)):
            return f"<yellow>{value}</yellow>"
        elif isinstance(value, str):
            # Check for special patterns
            if re.match(r'\d+\.\d+\.\d+\.\d+', value):  # IP address
                return f"<magenta>{value}</magenta>"
            elif '@' in value and '.' in value:  # Email
                return f"<cyan>{value}</cyan>"
            elif value.startswith(('http://', 'https://')):  # URL
                return f"<blue underline>{value}</blue underline>"
            elif value.startswith('/') or '\\' in value:  # File path
                return f"<dim white>{value}</dim white>"
            else:
                return f"<white>{value}</white>"
        else:
            return f"<dim>{value}</dim>"


class HierarchicalTemplateFormatter:
    """
    Template formatter that uses hierarchical formatting for the beautiful template.
    
    This integrates the hierarchical formatter with loguru's template system.
    """
    
    def __init__(self, format_string: str, template: TemplateConfig):
        """Initialize with format string and template configuration."""
        self.format_string = format_string
        self.template = template
        self.hierarchical_formatter = HierarchicalFormatter(template)
        
        # Cache for performance
        self._format_cache = {}
    
    def format_map(self, record: Dict[str, Any]) -> str:
        """
        Format a loguru record using hierarchical formatting.
        
        This is the main entry point that integrates with loguru's formatting system.
        """
        # Extract record components
        message = record.get("message", "")
        level = record.get("level")
        
        # Handle both real loguru level objects and test dictionaries
        if hasattr(level, 'name'):
            level_name = level.name
        elif isinstance(level, dict) and 'name' in level:
            level_name = level['name']
        else:
            level_name = str(level) if level else "INFO"
            
        # Extract timestamp
        time = record.get("time")
        if hasattr(time, 'strftime'):
            timestamp = time.strftime("%H:%M:%S")
        elif isinstance(time, str):
            timestamp = time
        else:
            timestamp = "00:00:00"
            
        # Extract logger name
        name = record.get("name", "unknown")
        
        # Extract extra context
        extra = record.get("extra", {})
        
        # Use hierarchical formatter for hierarchical template
        if self.template.name == "hierarchical":
            # The hierarchical formatter already applies colorization
            return self.hierarchical_formatter.format_record(
                level=level_name,
                message=message,
                logger_name=name,
                timestamp=timestamp,
                extra=extra
            )
        else:
            # Fall back to standard formatting for other templates
            try:
                formatted = self.format_string.format_map(record)
                if '<' in formatted and '>' in formatted:
                    return Colorizer.ansify(formatted)
                return formatted
            except (KeyError, ValueError):
                # Fallback formatting
                return f"{timestamp} | {level_name} | {message}"
    
    def strip(self) -> str:
        """Return stripped version of format string."""
        # For hierarchical formatting, return a simple stripped version
        return f"{{time:HH:mm:ss}} | {{level}} | {{message}}"


def create_hierarchical_formatter(
    format_string: str = "{time:HH:mm:ss} | {level} | {message}",
    template: Optional[TemplateConfig] = None
) -> HierarchicalTemplateFormatter:
    """
    Factory function to create a hierarchical template formatter.
    
    Args:
        format_string: Base loguru format string (used for fallback)
        template: Template configuration (defaults to beautiful template)
        
    Returns:
        Configured hierarchical template formatter
    """
    if template is None:
        from ._templates import template_registry
        template = template_registry.get("hierarchical")
        
    return HierarchicalTemplateFormatter(format_string, template)