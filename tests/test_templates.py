"""
Tests for the template engine and styling system.
"""

import pytest
import re
from loguru._templates import (
    TemplateEngine, TemplateConfig, TemplateRegistry, MarkupAnalyzer,
    StyleMode, ContextType, StyleRule, template_registry
)


class TestMarkupAnalyzer:
    """Test markup detection and analysis."""
    
    def test_detect_basic_markup(self):
        analyzer = MarkupAnalyzer()
        
        # Test basic color tags
        markup = analyzer.detect_markup("Hello <red>world</red>!")
        assert len(markup) == 2
        assert markup[0]['text'] == '<red>'
        assert markup[1]['text'] == '</red>'
        
        # Test no markup
        markup = analyzer.detect_markup("Plain text message")
        assert len(markup) == 0
    
    def test_detect_format_specifiers(self):
        analyzer = MarkupAnalyzer()
        
        # Test format specifications
        markup = analyzer.detect_markup("Value: {value:>10}")
        assert len(markup) == 1
        assert markup[0]['type'] == 'format_spec'
        
        # Test repr format
        markup = analyzer.detect_markup("Object: {obj!r}")
        assert len(markup) == 1
        assert markup[0]['type'] == 'repr_format'
    
    def test_has_manual_markup(self):
        analyzer = MarkupAnalyzer()
        
        assert analyzer.has_manual_markup("<red>text</red>")
        assert analyzer.has_manual_markup("Value: {value:>10}")
        assert not analyzer.has_manual_markup("Plain text")


class TestTemplateEngine:
    """Test core template engine functionality."""
    
    @pytest.fixture
    def engine(self):
        return TemplateEngine()
    
    @pytest.fixture
    def simple_template(self):
        return TemplateConfig(
            name="test",
            description="Test template",
            level_styles={"INFO": "blue", "ERROR": "red"},
            context_styles={"user": "cyan"},
            mode=StyleMode.AUTO
        )
    
    def test_manual_mode_passthrough(self, engine, simple_template):
        """Test that manual mode passes messages through unchanged."""
        simple_template.mode = StyleMode.MANUAL
        
        message = "<red>Already styled</red> message"
        result = engine.apply_template(message, {}, simple_template, "INFO")
        assert result == message
    
    def test_auto_mode_level_styling(self, engine, simple_template):
        """Test automatic level-based styling."""
        simple_template.mode = StyleMode.AUTO
        
        message = "Test message"
        result = engine.apply_template(message, {}, simple_template, "INFO")
        assert "<blue>" in result
        assert "Test message" in result
    
    def test_context_styling(self, engine, simple_template):
        """Test context-based styling."""
        simple_template.mode = StyleMode.AUTO
        simple_template.context_detection = True
        
        context = {"user": "john_doe"}
        message = "User john_doe logged in"
        result = engine.apply_template(message, context, simple_template, "INFO")
        
        # Should contain both level styling and context styling
        assert "<blue>" in result  # Level styling
        assert "<cyan>" in result  # Context styling for user
    
    def test_hybrid_mode_preserve_markup(self, engine, simple_template):
        """Test hybrid mode preserves existing markup."""
        simple_template.mode = StyleMode.HYBRID
        
        message = "Error: <red>Something failed</red>"
        result = engine.apply_template(message, {}, simple_template, "ERROR")
        
        # Should preserve the existing <red> markup
        assert "<red>Something failed</red>" in result


class TestStyleRules:
    """Test style rule pattern matching."""
    
    def test_ip_address_detection(self):
        rule = StyleRule(r'\b\d+\.\d+\.\d+\.\d+\b', 'magenta', 10, ContextType.IP)
        
        text = "Connection from 192.168.1.1"
        match = rule.pattern.search(text)
        assert match is not None
        assert match.group() == "192.168.1.1"
    
    def test_url_detection(self):
        rule = StyleRule(r'https?://[^\s]+', 'blue underline', 10, ContextType.URL)
        
        text = "Visit https://example.com for more info"
        match = rule.pattern.search(text)
        assert match is not None
        assert match.group() == "https://example.com"
    
    def test_email_detection(self):
        rule = StyleRule(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 
            'cyan', 10, ContextType.EMAIL
        )
        
        text = "Contact user@example.com"
        match = rule.pattern.search(text)
        assert match is not None
        assert match.group() == "user@example.com"


class TestTemplateConfig:
    """Test template configuration."""
    
    def test_template_creation(self):
        template = TemplateConfig(
            name="custom",
            description="Custom template",
            level_styles={"INFO": "blue"},
            mode=StyleMode.HYBRID
        )
        
        assert template.name == "custom"
        assert template.mode == StyleMode.HYBRID
        assert template.level_styles["INFO"] == "blue"
        assert template.preserve_markup is True  # Default value
    
    def test_tree_chars_default(self):
        template = TemplateConfig(name="test", description="Test")
        
        assert "branch" in template.tree_chars
        assert "last" in template.tree_chars
        assert template.tree_chars["branch"] == "├── "


class TestTemplateRegistry:
    """Test template registry functionality."""
    
    def test_built_in_templates_loaded(self):
        registry = TemplateRegistry()
        
        templates = registry.list_templates()
        assert "hierarchical" in templates
        assert "minimal" in templates
        assert "classic" in templates
    
    def test_register_custom_template(self):
        registry = TemplateRegistry()
        
        custom_template = TemplateConfig(
            name="custom_test",
            description="Custom test template"
        )
        
        registry.register(custom_template)
        assert "custom_test" in registry.list_templates()
        
        retrieved = registry.get("custom_test")
        assert retrieved is not None
        assert retrieved.name == "custom_test"
    
    def test_unregister_template(self):
        registry = TemplateRegistry()
        
        # Register then unregister
        custom_template = TemplateConfig(name="temp", description="Temporary")
        registry.register(custom_template)
        
        assert registry.unregister("temp") is True
        assert registry.get("temp") is None
        assert registry.unregister("nonexistent") is False
    
    def test_get_nonexistent_template(self):
        registry = TemplateRegistry()
        assert registry.get("nonexistent") is None


class TestBuiltInTemplates:
    """Test built-in template configurations."""
    
    def test_hierarchical_template(self):
        template = template_registry.get("hierarchical")
        assert template is not None
        assert template.name == "hierarchical"
        assert template.mode == StyleMode.HYBRID
        assert template.context_detection is True
        assert len(template.style_rules) > 0
    
    def test_minimal_template(self):
        template = template_registry.get("minimal")
        assert template is not None
        assert template.name == "minimal"
        assert template.context_detection is False
        assert template.tree_chars["branch"] == "- "
    
    def test_classic_template(self):
        template = template_registry.get("classic")
        assert template is not None
        assert template.name == "classic" 
        assert template.mode == StyleMode.MANUAL
        assert template.context_detection is False


class TestIntegration:
    """Integration tests for the complete template system."""
    
    def test_full_template_pipeline(self):
        """Test complete template processing pipeline."""
        engine = TemplateEngine()
        template = template_registry.get("hierarchical")
        
        context = {
            "user": "alice",
            "ip": "192.168.1.100",
            "action": "login"
        }
        
        message = "User alice logged in from 192.168.1.100"
        result = engine.apply_template(message, context, template, "INFO")
        
        # Should contain level styling, context styling, and pattern matching
        assert isinstance(result, str)
        assert len(result) >= len(message)  # Should be enhanced with markup
    
    def test_template_switching(self):
        """Test switching between different templates."""
        engine = TemplateEngine()
        
        message = "Test message"
        context = {"user": "test"}
        
        # Test with hierarchical template
        hierarchical = template_registry.get("hierarchical")
        result1 = engine.apply_template(message, context, hierarchical, "INFO")
        
        # Test with minimal template  
        minimal = template_registry.get("minimal")
        result2 = engine.apply_template(message, context, minimal, "INFO")
        
        # Results should be different due to different templates
        # (This is a basic test - in practice, styling differences would be more apparent)
        assert isinstance(result1, str)
        assert isinstance(result2, str)
    
    def test_error_handling(self):
        """Test error handling in template processing."""
        engine = TemplateEngine()
        template = TemplateConfig(name="test", description="Test")
        
        # Test with None context
        result = engine.apply_template("Test", None, template, "INFO")
        assert isinstance(result, str)
        
        # Test with empty context
        result = engine.apply_template("Test", {}, template, "INFO")
        assert isinstance(result, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])