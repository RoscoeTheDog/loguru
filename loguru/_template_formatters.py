"""
Template-aware formatters for loguru integration.

This module extends loguru's formatting system to support template-based styling
while preserving full backward compatibility with existing formatters.
"""

from typing import Dict, Any, Optional, Union, Callable
from ._templates import TemplateEngine, TemplateConfig, template_registry, StyleMode
from ._colorizer import Colorizer
from ._hierarchical_formatter import HierarchicalTemplateFormatter


class TemplateFormatter:
    """
    Template-aware formatter that extends loguru's native formatting.
    
    This formatter acts as a wrapper around loguru's standard formatting process,
    applying template-based styling while preserving all native functionality.
    """
    
    def __init__(
        self, 
        format_string: str,
        template_name: Optional[str] = None,
        template_config: Optional[TemplateConfig] = None,
        enable_templates: bool = True
    ):
        """
        Initialize template formatter.
        
        Args:
            format_string: Standard loguru format string
            template_name: Name of registered template to use
            template_config: Direct template configuration (overrides template_name)
            enable_templates: Whether to enable template processing
        """
        self.format_string = format_string
        self.enable_templates = enable_templates
        self.template_engine = TemplateEngine()
        
        # Determine template configuration
        if template_config:
            self.template = template_config
        elif template_name:
            self.template = template_registry.get(template_name)
            if not self.template:
                raise ValueError(f"Template '{template_name}' not found in registry")
        else:
            # Default to hierarchical template
            self.template = template_registry.get("hierarchical")
        
        # Prepare native colorizer for fallback
        self._colorizer = None
        self._colorized_format = None
        
        # Performance optimization: pre-compile format if static
        self._format_cache_key = None
        self._cached_result = None
    
    def strip(self) -> str:
        """Return stripped format string for non-colorized output."""
        if self._colorizer is None:
            self._colorizer = Colorizer.prepare_format(self.format_string)
        return self._colorizer.strip()
    
    def _make_cache_key(self, message: str, level_name: str, extra: Dict[str, Any]) -> tuple:
        """
        Create a cache key that handles unhashable types safely.
        
        Args:
            message: Log message string
            level_name: Level name (INFO, ERROR, etc.)  
            extra: Extra context dictionary
            
        Returns:
            Tuple cache key safe for hashing
        """
        try:
            if not extra:
                return (message, level_name, frozenset())
            
            # Try to create hashable representation of extra dict
            hashable_items = []
            for key, value in extra.items():
                try:
                    # Try to hash the value directly
                    hash(value)
                    hashable_items.append((key, value))
                except TypeError:
                    # If unhashable, convert to string representation
                    hashable_items.append((key, str(value)))
            
            return (message, level_name, frozenset(hashable_items))
        except Exception:
            # If all else fails, fall back to message and level only
            return (message, level_name, "extra_present")
    
    def format_map(self, record: Dict[str, Any]) -> str:
        """
        Format log record using template-aware processing with performance optimization.
        
        Args:
            record: Log record dictionary from loguru
            
        Returns:
            Formatted log message string
        """
        if not self.enable_templates or self.template.mode == StyleMode.MANUAL:
            # Use standard loguru formatting
            return self._format_native(record)
        
        # Use hierarchical formatter for hierarchical template
        if self.template.name == "hierarchical":
            # Check cache for hierarchical formatting
            message = record.get("message", "")
            level = record.get("level")
            if hasattr(level, 'name'):
                level_name = level.name
            elif isinstance(level, dict) and 'name' in level:
                level_name = level['name']
            else:
                level_name = "INFO"
            extra = record.get("extra", {})
            
            cache_key = self._make_cache_key(message, level_name, extra)
            # Add version info to bust cache after removing prepended newline
            cache_key = cache_key + ("format_function_v1",)
            if cache_key == self._format_cache_key and self._cached_result:
                return self._cached_result
            
            hierarchical_formatter = HierarchicalTemplateFormatter(
                self.format_string, self.template
            )
            result = hierarchical_formatter.format_map(record)
            
            # Cache the result
            self._format_cache_key = cache_key
            self._cached_result = result
            return result
        
        # Create cache key for performance optimization
        message = record.get("message", "")
        level = record.get("level")
        if hasattr(level, 'name'):
            # Real loguru RecordLevel object
            level_name = level.name
        elif isinstance(level, dict) and 'name' in level:
            # Mock dict for testing
            level_name = level['name']
        else:
            level_name = "INFO"
        extra = record.get("extra", {})
        
        # Simple caching for identical messages (common in logging)
        cache_key = self._make_cache_key(message, level_name, extra)
        if cache_key == self._format_cache_key and self._cached_result:
            # Return cached result for identical log calls
            template_record = record.copy()
            template_record["message"] = self._cached_result
            return self._format_native(template_record)
        
        # Apply template styling to message
        styled_message = self.template_engine.apply_template(
            message=message,
            context=extra,
            template=self.template,
            level=level_name
        )
        
        # Cache the styled message
        self._format_cache_key = cache_key
        self._cached_result = styled_message
        
        # Create modified record with styled message
        template_record = record.copy()
        template_record["message"] = styled_message
        
        # Apply native formatting to the template-styled record
        return self._format_native(template_record)
    
    def _format_native(self, record: Dict[str, Any]) -> str:
        """Apply native loguru formatting with colorization."""
        try:
            # Format the string first
            formatted = self.format_string.format_map(record)
            
            # In manual mode, preserve markup literally without colorization
            if hasattr(self, 'template') and self.template.mode == StyleMode.MANUAL:
                return formatted
            
            # If the message contains loguru markup, colorize it
            if '<' in formatted and '>' in formatted:
                from loguru._colorizer import Colorizer
                colorized = Colorizer.ansify(formatted)
                return colorized
            
            return formatted
            
        except (KeyError, ValueError) as e:
            # Fallback to safe formatting
            safe_record = {
                "time": record.get("time", "00:00:00"),
                "level": record.get("level", {}).get("name", "INFO") if isinstance(record.get("level"), dict) else str(record.get("level", "INFO")),
                "message": record.get("message", ""),
                "extra": record.get("extra", {})
            }
            try:
                formatted = self.format_string.format_map(safe_record)
                # Apply colorization if markup is present
                if '<' in formatted and '>' in formatted:
                    from loguru._colorizer import Colorizer
                    return Colorizer.ansify(formatted)
                return formatted
            except:
                return f"{safe_record['time']} | {safe_record['level']} | {safe_record['message']}"


class StreamTemplateFormatter:
    """
    Stream-specific template formatter for separate console/file styling.
    
    Allows different template configurations for different output streams,
    enabling rich console output while maintaining clean file logs.
    """
    
    def __init__(
        self,
        format_string: str,
        console_template: Optional[Union[str, TemplateConfig]] = None,
        file_template: Optional[Union[str, TemplateConfig]] = None,
        stream_type: str = "console"
    ):
        """
        Initialize stream-specific formatter.
        
        Args:
            format_string: Base loguru format string
            console_template: Template for console output (name or config)
            file_template: Template for file output (name or config)  
            stream_type: Type of stream ("console" or "file")
        """
        self.format_string = format_string
        self.stream_type = stream_type
        
        # Initialize appropriate formatter based on stream type
        if stream_type == "console":
            template = self._resolve_template(console_template or "hierarchical")
        elif stream_type == "file":
            template = self._resolve_template(file_template or "minimal")
        else:
            template = self._resolve_template("classic")
            
        self.formatter = TemplateFormatter(
            format_string=format_string,
            template_config=template,
            enable_templates=True
        )
    
    def _resolve_template(self, template: Union[str, TemplateConfig]) -> TemplateConfig:
        """Resolve template name or config to TemplateConfig instance."""
        if isinstance(template, str):
            resolved = template_registry.get(template)
            if not resolved:
                raise ValueError(f"Template '{template}' not found in registry")
            return resolved
        return template
    
    def strip(self) -> str:
        """Return stripped format string."""
        return self.formatter.strip()
    
    def format_map(self, record: Dict[str, Any]) -> str:
        """Format record using stream-specific template."""
        return self.formatter.format_map(record)


class DynamicTemplateFormatter:
    """
    Dynamic formatter that can switch templates at runtime.
    
    Supports per-message template selection and runtime template switching
    for advanced use cases.
    """
    
    def __init__(
        self,
        format_string: str,
        default_template: str = "hierarchical"
    ):
        """
        Initialize dynamic formatter.
        
        Args:
            format_string: Base loguru format string
            default_template: Default template name to use
        """
        self.format_string = format_string
        self.default_template_name = default_template
        self.template_engine = TemplateEngine()
        self._colorizer = None
        self._formatter_cache: Dict[str, TemplateFormatter] = {}
    
    def set_default_template(self, template_name: str) -> None:
        """Change the default template."""
        if not template_registry.get(template_name):
            raise ValueError(f"Template '{template_name}' not found in registry")
        self.default_template_name = template_name
    
    def strip(self) -> str:
        """Return stripped format string."""
        if self._colorizer is None:
            self._colorizer = Colorizer.prepare_format(self.format_string)
        return self._colorizer.strip()
    
    def format_map(self, record: Dict[str, Any]) -> str:
        """
        Format record with dynamic template selection.
        
        Looks for 'template' key in record extra for per-message template override.
        """
        # Check for per-message template override
        extra = record.get("extra", {})
        template_name = extra.get("template", self.default_template_name)
        
        # Get or create formatter for this template
        if template_name not in self._formatter_cache:
            self._formatter_cache[template_name] = TemplateFormatter(
                format_string=self.format_string,
                template_name=template_name,
                enable_templates=True
            )
        
        formatter = self._formatter_cache[template_name]
        return formatter.format_map(record)


class CompatibilityFormatter:
    """
    Compatibility formatter that provides seamless template integration.
    
    This formatter automatically detects whether templates should be applied
    based on format string content and usage patterns.
    """
    
    def __init__(self, format_string: str):
        """
        Initialize compatibility formatter.
        
        Args:
            format_string: Loguru format string
        """
        self.format_string = format_string
        self.template_engine = TemplateEngine()
        
        # Analyze format string to determine if templates should be used
        self.should_use_templates = self._analyze_format_string(format_string)
        
        if self.should_use_templates:
            # Use minimal template to avoid conflicts with existing markup
            self.template_formatter = TemplateFormatter(
                format_string=format_string,
                template_name="minimal",
                enable_templates=True
            )
        else:
            # Use native formatting only
            self._colorizer = Colorizer.prepare_format(format_string)
    
    def _analyze_format_string(self, format_string: str) -> bool:
        """
        Analyze format string to determine if templates should be applied.
        
        Returns False if format string contains complex loguru markup that
        might conflict with template processing.
        """
        # Check for complex markup patterns that suggest manual formatting
        complex_patterns = [
            '</',  # Closing tags
            '{time:',  # Complex time formatting
            '{level.name:',  # Complex level formatting
            '{extra[',  # Direct extra access
        ]
        
        return not any(pattern in format_string for pattern in complex_patterns)
    
    def strip(self) -> str:
        """Return stripped format string."""
        if self.should_use_templates:
            return self.template_formatter.strip()
        return self._colorizer.strip()
    
    def format_map(self, record: Dict[str, Any]) -> str:
        """Format record with compatibility logic."""
        if self.should_use_templates:
            return self.template_formatter.format_map(record)
        return self._colorizer.format_map(record)


def create_template_formatter(
    format_string: str,
    template: Optional[Union[str, TemplateConfig]] = None,
    stream_type: Optional[str] = None,
    compatibility_mode: bool = False
) -> Union[TemplateFormatter, StreamTemplateFormatter, CompatibilityFormatter]:
    """
    Factory function to create appropriate template formatter.
    
    Args:
        format_string: Loguru format string
        template: Template name or configuration
        stream_type: Stream type for stream-specific formatting
        compatibility_mode: Use compatibility formatter for automatic detection
        
    Returns:
        Appropriate formatter instance
    """
    if compatibility_mode:
        return CompatibilityFormatter(format_string)
    
    if stream_type:
        return StreamTemplateFormatter(
            format_string=format_string,
            stream_type=stream_type
        )
    
    if isinstance(template, str):
        return TemplateFormatter(
            format_string=format_string,
            template_name=template
        )
    elif isinstance(template, TemplateConfig):
        return TemplateFormatter(
            format_string=format_string,
            template_config=template
        )
    else:
        return TemplateFormatter(
            format_string=format_string,
            template_name="hierarchical"
        )


def create_hierarchical_format_function(
    format_string: str = "{time:HH:mm:ss} | {level} | {name} | {message}",
    template: Optional[Union[str, TemplateConfig]] = None
):
    """
    Create a format function for hierarchical logging with proper line ending control.
    
    This follows loguru's documented pattern for custom formatters by returning a function
    that handles explicit line endings, ensuring proper spacing between hierarchical log blocks.
    
    Args:
        format_string: Base loguru format string (used for fallback)
        template: Template name or configuration
        
    Returns:
        Format function suitable for loguru's format parameter
        
    Example:
        logger.add(sys.stderr, format=create_hierarchical_format_function(), colorize=True)
    """
    from ._hierarchical_formatter import HierarchicalFormatter
    from ._templates import template_registry
    
    # Get the hierarchical template
    if isinstance(template, str):
        template_config = template_registry.get(template)
    elif isinstance(template, TemplateConfig):
        template_config = template
    else:
        template_config = template_registry.get("hierarchical")
    
    # Create the hierarchical formatter
    hierarchical_formatter = HierarchicalFormatter(template_config)
    
    def hierarchical_format_function(record):
        """
        Format function that provides hierarchical formatting with explicit line ending control.
        
        This function takes complete responsibility for formatting and line endings,
        following the maintainer's guidance for custom formatters.
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
        
        # Extract exception information if present
        exception_info = record.get("exception")
        
        # Use hierarchical formatter to generate the formatted output
        formatted_output = hierarchical_formatter.format_record(
            level=level_name,
            message=message,
            logger_name=name,
            timestamp=timestamp,
            extra=extra,
            exception_info=exception_info
        )
        
        # CRITICAL: Add explicit line ending as required by loguru's custom formatter pattern
        # This ensures proper separation between log entries
        if not formatted_output.endswith('\n'):
            formatted_output += '\n'
            
        return formatted_output
    
    return hierarchical_format_function