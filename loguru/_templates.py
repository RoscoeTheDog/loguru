"""
Template engine core for enhanced loguru styling system.

This module provides a flexible template-based styling system that extends loguru's
native formatting capabilities while preserving backward compatibility.
"""

import re
from enum import Enum
from typing import Dict, List, Optional, Union, Any, Pattern
from dataclasses import dataclass, field
from string import Formatter


class StyleMode(Enum):
    """Style processing modes for template application."""
    AUTO = "auto"      # Full template automation, no manual markup
    MANUAL = "manual"  # Pure loguru markup, no template processing  
    HYBRID = "hybrid"  # Template automation + preserve existing markup


class ContextType(Enum):
    """Recognized context types for auto-styling."""
    USER = "user"
    ERROR = "error"
    IP = "ip"
    URL = "url"
    EMAIL = "email"
    FILEPATH = "filepath"
    SQL = "sql"
    DATETIME = "datetime"
    NUMERIC = "numeric"
    BOOLEAN = "boolean"
    JSON = "json"
    DEFAULT = "default"


@dataclass
class StyleRule:
    """Individual styling rule for context patterns."""
    pattern: Union[str, Pattern]
    style: str
    priority: int = 0
    context_type: ContextType = ContextType.DEFAULT
    
    def __post_init__(self):
        if isinstance(self.pattern, str):
            self.pattern = re.compile(self.pattern, re.IGNORECASE)


@dataclass
class TemplateConfig:
    """Configuration for a complete template."""
    name: str
    description: str
    
    # Core styling elements
    level_styles: Dict[str, str] = field(default_factory=dict)
    context_styles: Dict[str, str] = field(default_factory=dict)
    
    # Hierarchical formatting
    indent_char: str = "  "
    tree_chars: Dict[str, str] = field(default_factory=lambda: {
        "branch": "├── ",
        "last": "└── ",
        "vertical": "│   ",
        "empty": "    "
    })
    
    # Auto-styling rules
    style_rules: List[StyleRule] = field(default_factory=list)
    
    # Template behavior
    mode: StyleMode = StyleMode.HYBRID
    preserve_markup: bool = True
    context_detection: bool = True


class MarkupAnalyzer:
    """Analyzes existing loguru markup in format strings."""
    
    # Regex patterns for loguru markup detection
    LOGURU_PATTERNS = [
        r'<[^>]*>',                    # Basic markup tags like <red>, <bold>
        r'\{[^}]*\|[^}]*\}',          # Conditional formatting {value|default}
        r'\{[^}]*![^}]*\}',           # Format specifiers {value!r}
        r'\{[^}]*:[^}]*\}',           # Format strings {value:format}
    ]
    
    def __init__(self):
        self._compiled_patterns = [re.compile(pattern) for pattern in self.LOGURU_PATTERNS]
    
    def detect_markup(self, format_string: str) -> List[Dict[str, Any]]:
        """
        Detect existing loguru markup in a format string.
        
        Returns list of markup segments with position and type information.
        """
        markup_segments = []
        
        for pattern in self._compiled_patterns:
            for match in pattern.finditer(format_string):
                markup_segments.append({
                    'start': match.start(),
                    'end': match.end(),
                    'text': match.group(),
                    'type': self._classify_markup(match.group())
                })
        
        # Sort by position for processing
        markup_segments.sort(key=lambda x: x['start'])
        return markup_segments
    
    def _classify_markup(self, markup_text: str) -> str:
        """Classify the type of markup found."""
        if markup_text.startswith('<') and markup_text.endswith('>'):
            return 'color_tag'
        elif '|' in markup_text:
            return 'conditional'
        elif '!' in markup_text:
            return 'repr_format'
        elif ':' in markup_text:
            return 'format_spec'
        else:
            return 'unknown'
    
    def has_manual_markup(self, format_string: str) -> bool:
        """Quick check if format string contains any manual markup."""
        return any(pattern.search(format_string) for pattern in self._compiled_patterns)


class TemplateEngine:
    """Core template processing engine."""
    
    def __init__(self):
        self.analyzer = MarkupAnalyzer()
        self._formatter = Formatter()
        self._template_cache: Dict[str, Any] = {}
        self._compiled_patterns_cache: Dict[int, List[Pattern]] = {}
    
    def _make_context_cache_key(self, template_id: int, context: Dict[str, Any]) -> str:
        """Create a safe cache key from template ID and context dict."""
        try:
            if not context:
                return f"{template_id}_empty"
            
            # Try to create hashable representation of context
            hashable_items = []
            for key, value in context.items():
                try:
                    hash(value)
                    hashable_items.append((key, value))
                except TypeError:
                    # If unhashable, use string representation
                    hashable_items.append((key, str(value)))
            
            context_hash = hash(frozenset(hashable_items))
            return f"{template_id}_{context_hash}"
        except Exception:
            # Fall back to template ID only
            return f"{template_id}_context_present"
    
    def apply_template(
        self, 
        message: str, 
        context: Dict[str, Any], 
        template: TemplateConfig,
        level: str = "INFO"
    ) -> str:
        """
        Apply template styling to a message based on configuration and mode.
        """
        if template.mode == StyleMode.MANUAL:
            # Pass through without template processing
            return message
        
        # Detect existing markup
        markup_segments = self.analyzer.detect_markup(message)
        has_markup = len(markup_segments) > 0
        
        if template.mode == StyleMode.AUTO:
            # Full automation - strip existing markup and apply template
            clean_message = self._strip_markup(message, markup_segments)
            return self._apply_auto_styling(clean_message, context, template, level)
        
        elif template.mode == StyleMode.HYBRID:
            # Preserve existing markup, apply template to unmarked regions
            if has_markup and template.preserve_markup:
                return self._apply_hybrid_styling(message, context, template, level, markup_segments)
            else:
                return self._apply_auto_styling(message, context, template, level)
    
    def _strip_markup(self, message: str, markup_segments: List[Dict]) -> str:
        """Remove existing markup from message."""
        if not markup_segments:
            return message
        
        # Remove segments in reverse order to preserve positions
        result = message
        for segment in reversed(markup_segments):
            # Extract just the content inside markup
            markup_text = segment['text']
            if segment['type'] == 'color_tag':
                # For <tag>content</tag> patterns, keep content
                content = re.sub(r'<[^>]*>', '', markup_text)
                result = result[:segment['start']] + content + result[segment['end']:]
            else:
                # For other patterns, remove entirely
                result = result[:segment['start']] + result[segment['end']:]
        
        return result
    
    def _apply_auto_styling(
        self, 
        message: str, 
        context: Dict[str, Any], 
        template: TemplateConfig,
        level: str
    ) -> str:
        """Apply full template automation styling."""
        styled_message = message
        
        # Apply level-based styling
        if level.upper() in template.level_styles:
            level_style = template.level_styles[level.upper()]
            styled_message = f"<{level_style}>{styled_message}</{level_style}>"
        
        # Apply context-based styling if enabled
        if template.context_detection and context:
            styled_message = self._apply_context_styling(styled_message, context, template)
        
        return styled_message
    
    def _apply_hybrid_styling(
        self, 
        message: str, 
        context: Dict[str, Any], 
        template: TemplateConfig,
        level: str,
        markup_segments: List[Dict]
    ) -> str:
        """Apply template styling while preserving existing markup."""
        # For hybrid mode, we apply template styles only to unmarked regions
        # This is a simplified implementation - full version would need more sophisticated parsing
        
        if not markup_segments:
            return self._apply_auto_styling(message, context, template, level)
        
        # Apply context styling to non-markup regions
        if template.context_detection and context:
            return self._apply_context_styling(message, context, template)
        
        return message
    
    def _apply_context_styling(
        self, 
        message: str, 
        context: Dict[str, Any], 
        template: TemplateConfig
    ) -> str:
        """Apply context-based styling rules with performance optimization."""
        styled_message = message
        
        # Cache compiled patterns for this template
        template_id = id(template)
        if template_id not in self._compiled_patterns_cache:
            self._compiled_patterns_cache[template_id] = [
                rule.pattern for rule in template.style_rules
            ]
        
        # Apply context-specific styles with caching
        context_cache_key = self._make_context_cache_key(template_id, context)
        if context_cache_key in self._template_cache:
            context_replacements = self._template_cache[context_cache_key]
        else:
            context_replacements = []
            for key, value in context.items():
                if key in template.context_styles:
                    style = template.context_styles[key]
                    value_str = str(value)
                    styled_value = f"<{style}>{value_str}</{style}>"
                    context_replacements.append((value_str, styled_value))
            
            # Cache the replacements (keep cache small)
            if len(self._template_cache) > 100:
                self._template_cache.clear()
            self._template_cache[context_cache_key] = context_replacements
        
        # Apply context replacements
        for old_value, new_value in context_replacements:
            styled_message = styled_message.replace(old_value, new_value)
        
        # Apply style rules based on patterns (with priority sorting)
        for rule in sorted(template.style_rules, key=lambda r: r.priority, reverse=True):
            matches = list(rule.pattern.finditer(styled_message))
            if matches:
                # Apply replacements in reverse order to maintain positions
                for match in reversed(matches):
                    start, end = match.span()
                    original_text = match.group()
                    styled_text = f"<{rule.style}>{original_text}</{rule.style}>"
                    styled_message = styled_message[:start] + styled_text + styled_message[end:]
        
        return styled_message


# Built-in template definitions
BUILT_IN_TEMPLATES = {
    "beautiful": TemplateConfig(
        name="beautiful",
        description="Elegant hierarchical styling with rich colors and Unicode symbols",
        level_styles={
            "DEBUG": "dim cyan",
            "INFO": "bold blue", 
            "SUCCESS": "bold green",
            "WARNING": "bold yellow",
            "ERROR": "bold red",
            "CRITICAL": "bold white on red"
        },
        context_styles={
            "user": "bold cyan",
            "error": "bold red",
            "ip": "magenta",
            "url": "blue underline",
            "email": "cyan",
            "filepath": "dim white"
        },
        tree_chars={
            "branch": "├── ",
            "last": "└── ", 
            "vertical": "│   ",
            "empty": "    "
        },
        style_rules=[
            StyleRule(r'\b\d+\.\d+\.\d+\.\d+\b', 'magenta', 10, ContextType.IP),
            StyleRule(r'https?://[^\s]+', 'blue underline', 10, ContextType.URL),
            StyleRule(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 'cyan', 10, ContextType.EMAIL),
            StyleRule(r'/[^\s]*', 'dim white', 5, ContextType.FILEPATH),
        ],
        mode=StyleMode.HYBRID,
        preserve_markup=True,
        context_detection=True
    ),
    
    "minimal": TemplateConfig(
        name="minimal",
        description="Clean, minimal styling for production environments",
        level_styles={
            "ERROR": "red",
            "WARNING": "yellow", 
            "CRITICAL": "bold red"
        },
        context_styles={
            "error": "red",
            "user": "cyan"
        },
        indent_char="  ",
        tree_chars={
            "branch": "- ",
            "last": "- ",
            "vertical": "  ",
            "empty": "  "
        },
        mode=StyleMode.HYBRID,
        preserve_markup=True,
        context_detection=False
    ),
    
    "classic": TemplateConfig(
        name="classic",
        description="Traditional logging appearance with basic styling",
        level_styles={
            "DEBUG": "dim",
            "INFO": "white",
            "WARNING": "yellow",
            "ERROR": "red", 
            "CRITICAL": "bold red"
        },
        context_styles={},
        indent_char="    ",
        tree_chars={
            "branch": "",
            "last": "",
            "vertical": "",
            "empty": ""
        },
        mode=StyleMode.MANUAL,
        preserve_markup=True,
        context_detection=False
    )
}


class TemplateRegistry:
    """Registry for managing template configurations."""
    
    def __init__(self):
        self._templates: Dict[str, TemplateConfig] = {}
        self._load_built_in_templates()
    
    def _load_built_in_templates(self):
        """Load built-in templates into registry."""
        for name, template in BUILT_IN_TEMPLATES.items():
            self._templates[name] = template
    
    def register(self, template: TemplateConfig) -> None:
        """Register a new template configuration."""
        self._templates[template.name] = template
    
    def get(self, name: str) -> Optional[TemplateConfig]:
        """Get template configuration by name."""
        return self._templates.get(name)
    
    def list_templates(self) -> List[str]:
        """List all registered template names."""
        return list(self._templates.keys())
    
    def unregister(self, name: str) -> bool:
        """Remove a template from registry."""
        if name in self._templates:
            del self._templates[name]
            return True
        return False


# Global registry instance
template_registry = TemplateRegistry()