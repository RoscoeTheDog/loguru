"""
Stream separation manager for independent console/file formatting.

This module provides utilities for managing separate output streams with
different formatting configurations, enabling rich console output while
maintaining clean file logs.
"""

import sys
from typing import Dict, Any, Optional, Union, TextIO
from pathlib import Path
from ._template_formatters import StreamTemplateFormatter, TemplateConfig


class StreamConfig:
    """Configuration for a specific output stream."""
    
    def __init__(
        self,
        sink: Union[str, Path, TextIO],
        format_string: str = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                            "<level>{level: <8}</level> | "
                            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                            "<level>{message}</level>",
        template: Optional[Union[str, TemplateConfig]] = None,
        level: str = "DEBUG",
        colorize: Optional[bool] = None,
        serialize: bool = False,
        **kwargs
    ):
        """
        Initialize stream configuration.
        
        Args:
            sink: Output destination (file path, file object, or sys.stderr/stdout)
            format_string: Format string for this stream
            template: Template configuration for styling
            level: Minimum log level for this stream
            colorize: Whether to colorize output (auto-detected if None)
            serialize: Whether to serialize as JSON
            **kwargs: Additional loguru handler options
        """
        self.sink = sink
        self.format_string = format_string
        self.template = template
        self.level = level
        self.serialize = serialize
        self.handler_options = kwargs
        
        # Auto-detect stream type and colorization
        self.stream_type = self._detect_stream_type(sink)
        if colorize is None:
            self.colorize = self._should_colorize(sink, self.stream_type)
        else:
            self.colorize = colorize
    
    def _detect_stream_type(self, sink: Any) -> str:
        """Detect if sink is console or file-based."""
        if sink in (sys.stdout, sys.stderr):
            return "console"
        elif hasattr(sink, 'isatty') and callable(sink.isatty):
            return "console" if sink.isatty() else "file"
        elif isinstance(sink, (str, Path)):
            return "file"
        else:
            return "file"  # Default to file for unknown sinks
    
    def _should_colorize(self, sink: Any, stream_type: str) -> bool:
        """Determine if output should be colorized."""
        if self.serialize:
            return False  # Never colorize JSON output
        
        if stream_type == "console":
            if sink in (sys.stdout, sys.stderr):
                return hasattr(sink, 'isatty') and sink.isatty()
            elif hasattr(sink, 'isatty') and callable(sink.isatty):
                return sink.isatty()
        
        return False  # Default to no colorization for files
    
    def get_formatter(self) -> StreamTemplateFormatter:
        """Create appropriate formatter for this stream."""
        return StreamTemplateFormatter(
            format_string=self.format_string,
            stream_type=self.stream_type,
            console_template=self.template if self.stream_type == "console" else None,
            file_template=self.template if self.stream_type == "file" else None
        )


class StreamManager:
    """
    Manager for multiple output streams with independent configurations.
    
    Enables easy setup of dual-stream logging with different templates
    for console and file output.
    """
    
    def __init__(self):
        """Initialize stream manager."""
        self.streams: Dict[str, StreamConfig] = {}
        self.handler_ids: Dict[str, int] = {}
    
    def add_console_stream(
        self,
        name: str = "console",
        sink: TextIO = sys.stderr,
        template: Union[str, TemplateConfig] = "beautiful",
        level: str = "DEBUG",
        format_string: Optional[str] = None,
        **kwargs
    ) -> 'StreamManager':
        """
        Add a console output stream with rich formatting.
        
        Args:
            name: Unique name for this stream
            sink: Console sink (default: sys.stderr)
            template: Template for console styling
            level: Minimum log level
            format_string: Custom format string (uses default if None)
            **kwargs: Additional handler options
            
        Returns:
            Self for method chaining
        """
        if format_string is None:
            format_string = (
                "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                "<level>{message}</level>"
            )
        
        self.streams[name] = StreamConfig(
            sink=sink,
            format_string=format_string,
            template=template,
            level=level,
            colorize=True,
            serialize=False,
            **kwargs
        )
        return self
    
    def add_file_stream(
        self,
        name: str,
        filepath: Union[str, Path],
        template: Union[str, TemplateConfig] = "minimal",
        level: str = "DEBUG",
        format_string: Optional[str] = None,
        rotation: Optional[Union[str, int]] = None,
        retention: Optional[Union[str, int]] = None,
        compression: Optional[str] = None,
        serialize: bool = False,
        **kwargs
    ) -> 'StreamManager':
        """
        Add a file output stream with clean formatting.
        
        Args:
            name: Unique name for this stream
            filepath: Path to log file
            template: Template for file styling  
            level: Minimum log level
            format_string: Custom format string (uses default if None)
            rotation: File rotation policy
            retention: Log retention policy
            compression: Compression format
            serialize: Whether to output JSON
            **kwargs: Additional handler options
            
        Returns:
            Self for method chaining
        """
        if format_string is None:
            if serialize:
                format_string = "{message}"  # Minimal for JSON serialization
            else:
                format_string = (
                    "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
                    "{level: <8} | "
                    "{name}:{function}:{line} - {message}"
                )
        
        handler_options = kwargs.copy()
        if rotation:
            handler_options['rotation'] = rotation
        if retention:
            handler_options['retention'] = retention
        if compression:
            handler_options['compression'] = compression
        
        self.streams[name] = StreamConfig(
            sink=str(filepath),
            format_string=format_string,
            template=template,
            level=level,
            colorize=False,
            serialize=serialize,
            **handler_options
        )
        return self
    
    def add_json_stream(
        self,
        name: str,
        filepath: Union[str, Path],
        level: str = "DEBUG",
        **kwargs
    ) -> 'StreamManager':
        """
        Add a JSON-serialized file stream.
        
        Args:
            name: Unique name for this stream
            filepath: Path to JSON log file
            level: Minimum log level
            **kwargs: Additional handler options
            
        Returns:
            Self for method chaining
        """
        return self.add_file_stream(
            name=name,
            filepath=filepath,
            template="classic",  # Minimal template for JSON
            level=level,
            format_string="{message}",
            serialize=True,
            **kwargs
        )
    
    def configure_logger(self, logger) -> Dict[str, int]:
        """
        Configure logger with all defined streams.
        
        Args:
            logger: Loguru logger instance
            
        Returns:
            Dictionary mapping stream names to handler IDs
        """
        handler_ids = {}
        
        for stream_name, config in self.streams.items():
            formatter = config.get_formatter()
            
            handler_id = logger.add(
                sink=config.sink,
                format=formatter.format_map if hasattr(formatter, 'format_map') else formatter,
                level=config.level,
                colorize=config.colorize,
                serialize=config.serialize,
                **config.handler_options
            )
            
            handler_ids[stream_name] = handler_id
            
        self.handler_ids = handler_ids
        return handler_ids
    
    def remove_stream(self, logger, name: str) -> bool:
        """
        Remove a stream from the logger.
        
        Args:
            logger: Loguru logger instance
            name: Name of stream to remove
            
        Returns:
            True if stream was removed, False if not found
        """
        if name not in self.streams:
            return False
        
        if name in self.handler_ids:
            logger.remove(self.handler_ids[name])
            del self.handler_ids[name]
        
        del self.streams[name]
        return True
    
    def list_streams(self) -> Dict[str, str]:
        """
        List all configured streams.
        
        Returns:
            Dictionary mapping stream names to their descriptions
        """
        descriptions = {}
        for name, config in self.streams.items():
            sink_desc = str(config.sink) if isinstance(config.sink, (str, Path)) else repr(config.sink)
            template_desc = config.template if isinstance(config.template, str) else "custom"
            descriptions[name] = f"{config.stream_type}: {sink_desc} (template: {template_desc})"
        
        return descriptions


def create_dual_stream_logger(
    logger,
    console_template: str = "beautiful",
    file_path: Optional[Union[str, Path]] = None,
    file_template: str = "minimal",
    console_level: str = "INFO",
    file_level: str = "DEBUG"
) -> Dict[str, int]:
    """
    Convenience function to set up dual-stream logging (console + file).
    
    Args:
        logger: Loguru logger instance
        console_template: Template for console output
        file_path: Optional file path for file logging
        file_template: Template for file output
        console_level: Minimum level for console
        file_level: Minimum level for file
        
    Returns:
        Dictionary mapping stream names to handler IDs
    """
    manager = StreamManager()
    
    # Add console stream
    manager.add_console_stream(
        name="console",
        template=console_template,
        level=console_level
    )
    
    # Add file stream if path provided
    if file_path:
        manager.add_file_stream(
            name="file",
            filepath=file_path,
            template=file_template,
            level=file_level,
            rotation="10 MB",
            retention="1 week"
        )
    
    return manager.configure_logger(logger)