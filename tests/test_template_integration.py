"""
Comprehensive integration tests for loguru template system features.

This module provides extensive testing for Phase 3 advanced features including:
- Template formatters and stream management
- Global exception hook integration
- Enhanced tracing system with function pattern matching  
- Smart context auto-styling engine
- Performance optimization validation
"""

import pytest
import sys
import tempfile
import time
import threading
from pathlib import Path
from unittest.mock import Mock, patch

from loguru import logger
from loguru._template_formatters import (
    TemplateFormatter, StreamTemplateFormatter, DynamicTemplateFormatter,
    CompatibilityFormatter, create_template_formatter
)
from loguru._stream_manager import StreamManager, StreamConfig, create_dual_stream_logger
from loguru._templates import template_registry, TemplateConfig, StyleMode
from loguru._exception_hook import GlobalExceptionHook, SmartExceptionHook, ExceptionContext
from loguru._tracing import FunctionTracer, PerformanceTracer, TracingRule, create_development_tracer
from loguru._context_styling import SmartContextEngine, AdaptiveContextEngine


class TestTemplateFormatter:
    """Test template formatter functionality."""
    
    def test_basic_template_formatting(self):
        """Test basic template application."""
        formatter = TemplateFormatter(
            format_string="{level} | {message}",
            template_name="hierarchical"
        )
        
        record = {
            "level": {"name": "INFO"},
            "message": "Test message",
            "extra": {"user": "alice"}
        }
        
        result = formatter.format_map(record)
        assert isinstance(result, str)
        assert "Test message" in result
    
    def test_template_disabled(self):
        """Test formatter with templates disabled."""
        formatter = TemplateFormatter(
            format_string="{level} | {message}",
            template_name="hierarchical",
            enable_templates=False
        )
        
        record = {
            "level": {"name": "INFO"},
            "message": "Test message",
            "extra": {}
        }
        
        result = formatter.format_map(record)
        assert isinstance(result, str)
        # Should contain raw format without template styling
    
    def test_manual_mode_passthrough(self):
        """Test that manual mode preserves existing markup."""
        manual_template = TemplateConfig(
            name="manual_test",
            description="Manual mode test",
            mode=StyleMode.MANUAL
        )
        
        formatter = TemplateFormatter(
            format_string="{level} | {message}",
            template_config=manual_template
        )
        
        record = {
            "level": {"name": "INFO"},
            "message": "<red>Already styled</red>",
            "extra": {}
        }
        
        result = formatter.format_map(record)
        assert "<red>Already styled</red>" in result
    
    def test_strip_method(self):
        """Test format string stripping."""
        formatter = TemplateFormatter(
            format_string="<green>{time}</green> | {message}",
            template_name="hierarchical"
        )
        
        stripped = formatter.strip()
        assert isinstance(stripped, str)
        assert "<green>" not in stripped


class TestStreamTemplateFormatter:
    """Test stream-specific template formatting."""
    
    def test_console_stream_formatter(self):
        """Test console stream with hierarchical template."""
        formatter = StreamTemplateFormatter(
            format_string="{level} | {message}",
            console_template="hierarchical",
            stream_type="console"
        )
        
        record = {
            "level": {"name": "INFO"},
            "message": "Console test",
            "extra": {}
        }
        
        result = formatter.format_map(record)
        assert isinstance(result, str)
        assert "Console test" in result
    
    def test_file_stream_formatter(self):
        """Test file stream with minimal template."""
        formatter = StreamTemplateFormatter(
            format_string="{level} | {message}",
            file_template="minimal",
            stream_type="file"
        )
        
        record = {
            "level": {"name": "ERROR"},
            "message": "File test",
            "extra": {}
        }
        
        result = formatter.format_map(record)
        assert isinstance(result, str)
        assert "File test" in result


class TestDynamicTemplateFormatter:
    """Test dynamic template switching."""
    
    def test_default_template(self):
        """Test using default template."""
        formatter = DynamicTemplateFormatter(
            format_string="{level} | {message}",
            default_template="hierarchical"
        )
        
        record = {
            "level": {"name": "INFO"},
            "message": "Default template test",
            "extra": {}
        }
        
        result = formatter.format_map(record)
        assert isinstance(result, str)
        assert "Default template test" in result
    
    def test_per_message_template(self):
        """Test per-message template override."""
        formatter = DynamicTemplateFormatter(
            format_string="{level} | {message}",
            default_template="hierarchical"
        )
        
        record = {
            "level": {"name": "INFO"},
            "message": "Override test",
            "extra": {"template": "minimal"}
        }
        
        result = formatter.format_map(record)
        assert isinstance(result, str)
        assert "Override test" in result
    
    def test_template_switching(self):
        """Test runtime template switching."""
        formatter = DynamicTemplateFormatter(
            format_string="{message}",
            default_template="hierarchical"
        )
        
        formatter.set_default_template("minimal")
        assert formatter.default_template_name == "minimal"
    
    def test_invalid_template_name(self):
        """Test error handling for invalid template names."""
        formatter = DynamicTemplateFormatter(
            format_string="{message}",
            default_template="hierarchical"
        )
        
        with pytest.raises(ValueError, match="not found in registry"):
            formatter.set_default_template("nonexistent")


class TestCompatibilityFormatter:
    """Test compatibility formatter auto-detection."""
    
    def test_simple_format_uses_templates(self):
        """Test that simple format strings use templates."""
        formatter = CompatibilityFormatter("{level} | {message}")
        assert formatter.should_use_templates is True
    
    def test_complex_format_avoids_templates(self):
        """Test that complex format strings avoid templates."""
        formatter = CompatibilityFormatter("{time:%Y-%m-%d} | {level.name:>8} | {message}")
        assert formatter.should_use_templates is False
    
    def test_closing_tags_detected(self):
        """Test detection of closing tags."""
        formatter = CompatibilityFormatter("<red>{message}</red>")
        assert formatter.should_use_templates is False


class TestStreamManager:
    """Test stream management functionality."""
    
    def test_add_console_stream(self):
        """Test adding console stream."""
        manager = StreamManager()
        manager.add_console_stream(
            name="test_console",
            template="hierarchical",
            level="INFO"
        )
        
        assert "test_console" in manager.streams
        stream_config = manager.streams["test_console"]
        assert stream_config.stream_type == "console"
        assert stream_config.template == "hierarchical"
        assert stream_config.level == "INFO"
    
    def test_add_file_stream(self):
        """Test adding file stream."""
        manager = StreamManager()
        test_file = Path("test.log")
        
        manager.add_file_stream(
            name="test_file",
            filepath=test_file,
            template="minimal",
            level="DEBUG"
        )
        
        assert "test_file" in manager.streams
        stream_config = manager.streams["test_file"]
        assert stream_config.stream_type == "file"
        assert stream_config.template == "minimal"
        assert stream_config.level == "DEBUG"
    
    def test_add_json_stream(self):
        """Test adding JSON stream."""
        manager = StreamManager()
        json_file = Path("test.json")
        
        manager.add_json_stream(
            name="test_json",
            filepath=json_file,
            level="WARNING"
        )
        
        assert "test_json" in manager.streams
        stream_config = manager.streams["test_json"]
        assert stream_config.serialize is True
        assert stream_config.level == "WARNING"
    
    def test_method_chaining(self):
        """Test fluent interface method chaining."""
        manager = StreamManager()
        
        result = (manager
                 .add_console_stream("console")
                 .add_file_stream("file", Path("test.log"))
                 .add_json_stream("json", Path("test.json")))
        
        assert result is manager
        assert len(manager.streams) == 3
    
    def test_list_streams(self):
        """Test stream listing functionality."""
        manager = StreamManager()
        manager.add_console_stream("console", template="hierarchical")
        manager.add_file_stream("file", Path("test.log"), template="minimal")
        
        streams = manager.list_streams()
        assert len(streams) == 2
        assert "console" in streams
        assert "file" in streams
        assert "hierarchical" in streams["console"]
        assert "minimal" in streams["file"]


class TestStreamConfig:
    """Test stream configuration."""
    
    def test_console_stream_detection(self):
        """Test automatic console stream detection."""
        config = StreamConfig(sys.stderr, "{message}")
        assert config.stream_type == "console"
        # Colorize depends on whether stderr is a tty - just check it's a boolean
        assert isinstance(config.colorize, bool)
    
    def test_file_stream_detection(self):
        """Test automatic file stream detection."""
        config = StreamConfig("test.log", "{message}")
        assert config.stream_type == "file"
        assert config.colorize is False
    
    def test_json_no_colorize(self):
        """Test that JSON serialization disables colorization."""
        config = StreamConfig(sys.stderr, "{message}", serialize=True)
        assert config.colorize is False
    
    def test_get_formatter(self):
        """Test formatter creation."""
        config = StreamConfig(sys.stderr, "{message}", template="hierarchical")
        formatter = config.get_formatter()
        assert isinstance(formatter, StreamTemplateFormatter)


class TestFactoryFunction:
    """Test formatter factory function."""
    
    def test_create_basic_template_formatter(self):
        """Test creating basic template formatter."""
        formatter = create_template_formatter(
            format_string="{message}",
            template="hierarchical"
        )
        assert isinstance(formatter, TemplateFormatter)
    
    def test_create_stream_formatter(self):
        """Test creating stream-specific formatter."""
        formatter = create_template_formatter(
            format_string="{message}",
            stream_type="console"
        )
        assert isinstance(formatter, StreamTemplateFormatter)
    
    def test_create_compatibility_formatter(self):
        """Test creating compatibility formatter."""
        formatter = create_template_formatter(
            format_string="{message}",
            compatibility_mode=True
        )
        assert isinstance(formatter, CompatibilityFormatter)
    
    def test_create_with_template_config(self):
        """Test creating formatter with template config object."""
        template_config = template_registry.get("hierarchical")
        formatter = create_template_formatter(
            format_string="{message}",
            template=template_config
        )
        assert isinstance(formatter, TemplateFormatter)


class TestLoggerIntegration:
    """Test integration with loguru Logger class."""
    
    @pytest.fixture(autouse=True)
    def setup_logger(self):
        """Setup clean logger for each test."""
        # Remove all handlers
        logger.remove()
        yield
        # Cleanup
        logger.remove()
    
    def test_configure_style_console_only(self):
        """Test configure_style with console only."""
        handler_ids = logger.configure_style("hierarchical", console_level="INFO")
        
        assert "console" in handler_ids
        assert isinstance(handler_ids["console"], int)
    
    def test_configure_style_with_file(self):
        """Test configure_style with file output."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler_ids = logger.configure_style(
                "hierarchical",
                file_path=tmp_path,
                console_level="INFO",
                file_level="DEBUG"
            )
            
            assert "console" in handler_ids
            assert "file" in handler_ids
            assert len(handler_ids) == 2
        finally:
            # Remove handlers to release file before deleting
            for handler_id in handler_ids.values():
                try:
                    logger.remove(handler_id)
                except:
                    pass
            Path(tmp_path).unlink(missing_ok=True)
    
    def test_configure_streams_multiple(self):
        """Test configure_streams with multiple outputs."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler_ids = logger.configure_streams(
                console=dict(sink=sys.stderr, template="hierarchical", level="INFO"),
                file=dict(sink=tmp_path, template="minimal", level="DEBUG"),
                json=dict(sink=tmp_path + ".json", template="classic", serialize=True)
            )
            
            assert len(handler_ids) == 3
            assert "console" in handler_ids
            assert "file" in handler_ids
            assert "json" in handler_ids
        finally:
            # Remove handlers to release files before deleting
            for handler_id in handler_ids.values():
                try:
                    logger.remove(handler_id)
                except:
                    pass
            Path(tmp_path).unlink(missing_ok=True)
            Path(tmp_path + ".json").unlink(missing_ok=True)
    
    def test_set_template_method(self):
        """Test set_template method."""
        handler_id = logger.add(sys.stderr, format="{message}")
        
        # This is a simplified test - full implementation would actually change the template
        result = logger.set_template(handler_id, "hierarchical")
        assert result is True
        
        # Test with invalid handler ID
        result = logger.set_template(99999, "hierarchical")
        assert result is False
        
        # Test with invalid template name
        with pytest.raises(ValueError, match="not found in registry"):
            logger.set_template(handler_id, "nonexistent")


class TestEndToEndIntegration:
    """End-to-end integration tests."""
    
    @pytest.fixture(autouse=True)
    def setup_logger(self):
        """Setup clean logger for each test."""
        logger.remove()
        yield
        logger.remove()
    
    def test_dual_stream_logging(self):
        """Test complete dual-stream logging setup."""
        with tempfile.NamedTemporaryFile(delete=False, mode='w') as tmp:
            tmp_path = tmp.name
        
        try:
            # Configure dual streams
            handler_ids = create_dual_stream_logger(
                logger=logger,
                console_template="hierarchical",
                file_path=tmp_path,
                file_template="minimal"
            )
            
            # Log some messages
            logger.info("Test info message")
            logger.error("Test error message", user="alice", action="login")
            logger.warning("Test warning with IP", ip="192.168.1.1")
            
            # Verify handlers were created
            assert len(handler_ids) >= 1  # At least console
            if tmp_path:
                assert len(handler_ids) == 2  # Console + file
            
        finally:
            # Remove handlers to release file before deleting
            for handler_id in handler_ids.values():
                try:
                    logger.remove(handler_id)
                except:
                    pass
            Path(tmp_path).unlink(missing_ok=True)
    
    def test_template_switching_runtime(self):
        """Test runtime template switching."""
        # This would be a more complex test in full implementation
        # For now, test basic functionality
        logger.add(sys.stderr, format="{message}")
        
        # Log with different contexts to test template application
        logger.bind(template="hierarchical").info("Beautiful template message")
        logger.bind(template="minimal").info("Minimal template message")
    
    def test_backward_compatibility(self):
        """Test that existing loguru usage still works."""
        # Standard loguru usage should work unchanged
        logger.add(sys.stderr, format="<green>{time}</green> | {level} | {message}")
        
        logger.info("Standard loguru message")
        logger.error("Error with <red>manual styling</red>")
        
        # Should not raise any exceptions
        assert True


class TestExceptionHookIntegration:
    """Test suite for global exception hook system."""

    def test_global_exception_hook_basic(self):
        """Test basic exception hook functionality."""
        hook = GlobalExceptionHook(logger, "hierarchical")
        hook.install()
        
        try:
            # Test that hook is installed
            assert hook._installed
            assert sys.excepthook == hook._handle_exception
        finally:
            hook.uninstall()

    def test_exception_hook_formatting(self):
        """Test exception formatting with template."""
        hook = GlobalExceptionHook(logger, "hierarchical")
        
        # Mock exception handling
        exc_type = ValueError
        exc_value = ValueError("Test error message")
        exc_tb = None
        
        # Capture the log call
        with patch.object(logger, 'bind') as mock_bind:
            mock_bound = Mock()
            mock_bind.return_value = mock_bound
            mock_opt = Mock()
            mock_bound.opt.return_value = mock_opt
            
            hook._handle_exception(exc_type, exc_value, exc_tb)
            
            # Verify bind was called with proper context
            mock_bind.assert_called_once()
            context = mock_bind.call_args[1]
            assert 'exception_type' in context
            assert 'thread_name' in context
            assert context['exception_type'] == 'ValueError'

    def test_exception_context_manager(self):
        """Test exception context manager."""
        with ExceptionContext(logger, "hierarchical") as ctx:
            assert ctx._installed
        assert not ctx._installed

    def test_smart_exception_hook_filtering(self):
        """Test smart exception hook with filtering."""
        def test_filter(exc_type, exc_value, exc_tb):
            return exc_type != ValueError  # Don't handle ValueError
            
        hook = SmartExceptionHook(logger, "hierarchical", filter_func=test_filter)
        hook.install()
        
        try:
            # Test filter behavior
            original_hook = Mock()
            hook.base_hook.original_hook = original_hook
            
            # This should be filtered out
            hook.base_hook._handle_exception(ValueError, ValueError("test"), None)
            original_hook.assert_called_once()
            
            original_hook.reset_mock()
            
            # This should be handled
            with patch.object(logger, 'bind') as mock_bind:
                mock_bound = Mock()
                mock_bind.return_value = mock_bound
                mock_opt = Mock()
                mock_bound.opt.return_value = mock_opt
                
                hook.base_hook._handle_exception(RuntimeError, RuntimeError("test"), None)
                mock_bind.assert_called_once()
                
        finally:
            hook.uninstall()


class TestTracingSystem:
    """Test suite for enhanced function tracing."""

    def test_function_tracer_basic(self):
        """Test basic function tracing."""
        # Capture logs in a list
        logs = []
        logger.add(logs.append, format="{message}")
        
        try:
            tracer = FunctionTracer(logger, "hierarchical")
            
            @tracer.trace
            def test_function(x, y):
                return x + y
                
            result = test_function(1, 2)
            assert result == 3
            
            # Verify logs were created
            assert len(logs) >= 2  # Entry and exit logs
        finally:
            logger.remove()

    def test_tracing_rules(self):
        """Test pattern-based tracing rules."""
        tracer = FunctionTracer(logger, "hierarchical")
        
        # Add rule for test functions
        tracer.add_rule(
            pattern=r"^test_.*",
            log_args=True,
            log_result=True,
            level="DEBUG"
        )
        
        @tracer.trace
        def test_sample_function(value):
            return value * 2
            
        result = test_sample_function(5)
        assert result == 10
        
        # Verify rule was applied
        rule = tracer.get_rule_for_function("test_sample_function")
        assert rule is not None
        assert rule.log_args
        assert rule.log_result

    def test_performance_tracer(self):
        """Test performance monitoring tracer."""
        tracer = PerformanceTracer(logger, "hierarchical")
        
        @tracer.trace_performance(threshold_ms=100)
        def slow_function():
            time.sleep(0.01)  # 10ms
            return "done"
            
        result = slow_function()
        assert result == "done"
        
        # Check performance stats
        stats = tracer.get_performance_stats("slow_function")
        assert stats is not None
        assert stats["count"] == 1
        assert stats["avg_ms"] >= 10

    def test_tracing_with_exceptions(self):
        """Test tracing behavior with exceptions."""
        logs = []
        logger.add(logs.append, format="{level} | {message}")
        
        try:
            tracer = FunctionTracer(logger, "hierarchical")
            
            @tracer.trace
            def failing_function():
                raise ValueError("Test error")
                
            with pytest.raises(ValueError):
                failing_function()
                
            # Verify exception was logged - tracer should log exceptions by default
            error_logs = [log for log in logs if "ERROR" in str(log)]
            assert len(error_logs) >= 1
        finally:
            logger.remove()

    def test_development_tracer_configuration(self):
        """Test pre-configured development tracer."""
        tracer = create_development_tracer(logger)
        
        # Test that rules are configured
        assert len(tracer.rules) > 0
        
        # Test private function rule (should be disabled)
        private_rule = tracer.get_rule_for_function("_private_function")
        assert private_rule is not None
        assert not private_rule.enabled


class TestContextStyling:
    """Test suite for smart context auto-styling."""

    def test_smart_context_engine_basic(self):
        """Test basic context recognition."""
        engine = SmartContextEngine()
        
        message = "User john@example.com logged in from 192.168.1.1"
        matches = engine.analyze_message(message)
        
        # Should detect email and IP
        assert len(matches) >= 2
        types = [match['context_type'].value for match in matches]
        assert 'email' in types
        assert 'ip' in types

    def test_context_engine_web_patterns(self):
        """Test web-related pattern recognition."""
        engine = SmartContextEngine()
        
        message = "GET /api/users/123 returned 404 from https://example.com"
        matches = engine.analyze_message(message)
        
        # Should detect URL patterns
        types = [match['context_type'].value for match in matches]
        assert 'url' in types

    def test_context_engine_security_patterns(self):
        """Test security-related pattern recognition."""
        engine = SmartContextEngine()
        
        message = "Login attempt failed for user admin from 10.0.0.1"
        matches = engine.analyze_message(message)
        
        # Should detect IP address
        types = [match['context_type'].value for match in matches]
        assert 'ip' in types

    def test_adaptive_context_engine(self):
        """Test adaptive learning engine."""
        engine = AdaptiveContextEngine()
        
        # Simulate usage patterns
        message = "Processing transaction TX123456 for amount $1,234.56"
        
        # First analysis
        matches1 = engine.analyze_message(message)
        
        # Record usage - just record a pattern name that might be found
        if matches1:
            engine.record_usage(matches1[0]['pattern_name'])
        
        # Second analysis should potentially improve
        matches2 = engine.analyze_message(message)
        
        assert len(matches2) >= len(matches1)

    def test_context_confidence_scoring(self):
        """Test confidence scoring in context detection."""
        engine = SmartContextEngine()
        
        message = "Email: user@domain.com, Phone: +1-555-123-4567"
        matches = engine.analyze_message(message)
        
        # All matches should have priority scores (confidence equivalent)
        for match in matches:
            assert 'priority' in match
            assert match['priority'] >= 0

    def test_context_overlap_handling(self):
        """Test handling of overlapping context matches."""
        engine = SmartContextEngine()
        
        # This could match both URL and email patterns
        message = "Contact us at support@http://example.com"
        matches = engine.analyze_message(message)
        
        # Should handle overlaps intelligently
        assert len(matches) >= 1
        
        # Check that positions don't overlap inappropriately
        for i, match1 in enumerate(matches):
            for match2 in matches[i+1:]:
                start1, end1 = match1['start'], match1['end'] 
                start2, end2 = match2['start'], match2['end']
                # Ensure no improper overlaps
                assert not (start1 < start2 < end1 and start1 < end2 < end1)


class TestPerformanceOptimization:
    """Test suite for performance optimizations."""

    def test_template_caching_performance(self):
        """Test performance optimization through caching."""
        formatter = TemplateFormatter(
            format_string="{time} | {level} | {message}",
            template_name="hierarchical"
        )
        
        record = {
            "time": "2024-01-01T12:00:00",
            "level": {"name": "INFO"},
            "message": "Repeated message",
            "extra": {"key": "value"}
        }
        
        # First call should populate cache
        result1 = formatter.format_map(record)
        
        # Second call should use cache
        result2 = formatter.format_map(record)
        
        # Results should be identical
        assert result1 == result2
        
        # Verify cache was used
        assert formatter._cached_result is not None
        assert formatter._format_cache_key is not None

    def test_template_performance_with_patterns(self):
        """Test performance with context pattern matching."""
        formatter = TemplateFormatter(
            format_string="{message}",
            template_name="hierarchical"
        )
        
        # Message with multiple patterns
        record = {
            "message": "User john@example.com from 192.168.1.1 accessed /api/data",
            "level": {"name": "INFO"},
            "extra": {"user": "john", "ip": "192.168.1.1"}
        }
        
        start_time = time.perf_counter()
        result = formatter.format_map(record)
        duration = time.perf_counter() - start_time
        
        # Should complete reasonably quickly
        assert duration < 0.1  # 100ms threshold
        assert result is not None

    def test_pattern_compilation_caching(self):
        """Test that pattern compilation is cached."""
        from loguru._templates import TemplateEngine
        
        engine = TemplateEngine()
        template = template_registry.get("hierarchical")
        
        # First call should compile patterns
        message1 = "Test message with user@example.com"
        result1 = engine._apply_context_styling(message1, {}, template)
        
        # Check that patterns are cached
        template_id = id(template)
        assert template_id in engine._compiled_patterns_cache
        
        # Second call should use cached patterns
        message2 = "Another test with admin@test.org"
        result2 = engine._apply_context_styling(message2, {}, template)
        
        # Should still have cached patterns
        assert template_id in engine._compiled_patterns_cache


if __name__ == "__main__":
    pytest.main([__file__, "-v"])