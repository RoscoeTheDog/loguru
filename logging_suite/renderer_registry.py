# logging_suite/renderer_registry.py
# Relative path: LoggingSuite/renderer_registry.py
"""
Renderer registry for managing unified formatters across all backends
This eliminates duplicate formatters and ensures consistent styling
"""

from typing import Dict, Type, Any, Optional
import logging


class RendererRegistry:
    """Registry for managing unified formatters across all backends"""

    def __init__(self):
        self._renderers: Dict[str, Any] = {}
        self._default_config: Dict[str, Any] = {}

    def register_renderer(self, name: str, renderer_class: Type, config: Dict[str, Any] = None):
        """Register a renderer class"""
        self._renderers[name] = {
            'class': renderer_class,
            'config': config or {}
        }

    def create_renderer(self, name: str, config: Dict[str, Any] = None) -> Any:
        """Create a renderer instance with configuration"""
        if name not in self._renderers:
            raise ValueError(f"Unknown renderer: {name}. Available: {list(self._renderers.keys())}")

        renderer_info = self._renderers[name]
        renderer_class = renderer_info['class']

        # Merge default config with provided config
        final_config = {**renderer_info['config'], **(config or {})}

        try:
            return renderer_class(**final_config)
        except TypeError:
            # Some classes might not accept **kwargs
            return renderer_class()

    def get_available_renderers(self) -> list:
        """Get list of available renderer names"""
        return list(self._renderers.keys())

    def set_default_config(self, config: Dict[str, Any]):
        """Set default configuration for all renderers"""
        self._default_config = config

    def get_renderer_for_backend(self, backend_name: str, format_type: str, config: Dict[str, Any] = None) -> Any:
        """Get appropriate renderer for a specific backend and format type"""
        # Determine renderer name based on format type
        if format_type.lower() == 'json':
            if config and config.get('pretty_json', False):
                renderer_name = 'pretty_json'
            else:
                renderer_name = 'compact_json'
        elif format_type.lower() == 'console':
            renderer_name = 'console'
        elif format_type.lower() == 'file':
            renderer_name = 'file'
        else:
            renderer_name = format_type.lower()

        # Create renderer with merged config
        final_config = {**self._default_config, **(config or {})}
        return self.create_renderer(renderer_name, final_config)


# Global renderer registry instance
_global_registry = None


def get_global_renderer_registry() -> RendererRegistry:
    """Get the global renderer registry"""
    global _global_registry
    if _global_registry is None:
        _global_registry = RendererRegistry()
        _initialize_default_renderers(_global_registry)
    return _global_registry


def _initialize_default_renderers(registry: RendererRegistry):
    """Initialize the registry with default renderers from styling module"""
    try:
        from .styling import (
            PrettyJSONFormatter,
            CompactJSONFormatter,
            UnifiedLoggingFormatter,
            FileLoggingFormatter
        )

        # Register JSON formatters
        registry.register_renderer('pretty_json', PrettyJSONFormatter, {
            'pretty': True,
            'indent': 2,
            'separators': (', ', ': ')
        })

        registry.register_renderer('compact_json', CompactJSONFormatter)

        # Register console formatter (now with style support)
        registry.register_renderer('console', UnifiedLoggingFormatter, {
            'use_colors': True,
            'use_symbols': True,
            'compact': False,
            'console_log_style': 'hierarchical'  # Will be mapped to style in UnifiedLoggingFormatter
        })

        # Register file formatter
        registry.register_renderer('file', FileLoggingFormatter, {
            'include_context': True,
            'max_context_fields': 10
        })

    except ImportError:
        # Styling module not available, register basic logging formatter
        registry.register_renderer('basic', logging.Formatter, {
            'fmt': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        })


def register_custom_renderer(name: str, renderer_class: Type, config: Dict[str, Any] = None):
    """Register a custom renderer in the global registry"""
    registry = get_global_renderer_registry()
    registry.register_renderer(name, renderer_class, config)


def create_unified_formatter(format_type: str, config: Dict[str, Any] = None) -> Any:
    """Create a unified formatter that works across all backends"""
    registry = get_global_renderer_registry()
    return registry.get_renderer_for_backend('unified', format_type, config)


__all__ = [
    'RendererRegistry',
    'get_global_renderer_registry',
    'register_custom_renderer',
    'create_unified_formatter'
]