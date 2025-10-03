"""
Enhanced tracing system with function pattern matching and performance monitoring.

This module provides sophisticated function tracing capabilities that extend
loguru's @catch decorator with pattern matching, performance monitoring, and
template-based output formatting.
"""

import functools
import time
import re
import inspect
from typing import Union, List, Optional, Dict, Any, Callable, Pattern
from dataclasses import dataclass, field
from ._templates import template_registry, TemplateConfig


@dataclass
class TracingRule:
    """Configuration rule for function tracing."""
    pattern: Union[str, Pattern]
    enabled: bool = True
    log_entry: bool = True
    log_exit: bool = True
    log_args: bool = True
    log_result: bool = False
    log_duration: bool = True
    log_exceptions: bool = True
    level: str = "DEBUG"
    template: str = "beautiful"
    
    def __post_init__(self):
        if isinstance(self.pattern, str):
            self.pattern = re.compile(self.pattern)


class FunctionTracer:
    """
    Advanced function tracer with pattern matching and configurable behavior.
    
    This tracer provides sophisticated function monitoring with template-based
    formatting and flexible configuration through pattern matching.
    """
    
    def __init__(self, logger, default_template: str = "beautiful"):
        """
        Initialize the function tracer.
        
        Args:
            logger: Loguru logger instance
            default_template: Default template for trace output
        """
        self.logger = logger
        self.default_template = default_template
        self.rules: List[TracingRule] = []
        self.global_enabled = True
        
    def add_rule(
        self, 
        pattern: Union[str, Pattern],
        enabled: bool = True,
        log_entry: bool = True,
        log_exit: bool = True,
        log_args: bool = True,
        log_result: bool = False,
        log_duration: bool = True,
        log_exceptions: bool = True,
        level: str = "DEBUG",
        template: str = "beautiful"
    ) -> None:
        """
        Add a tracing rule for function pattern matching.
        
        Args:
            pattern: Regex pattern to match function names
            enabled: Whether tracing is enabled for this pattern
            log_entry: Log function entry
            log_exit: Log function exit  
            log_args: Include function arguments in logs
            log_result: Include return value in logs
            log_duration: Include execution duration
            log_exceptions: Log exceptions that occur
            level: Log level to use
            template: Template for formatting
        """
        rule = TracingRule(
            pattern=pattern,
            enabled=enabled,
            log_entry=log_entry,
            log_exit=log_exit,
            log_args=log_args,
            log_result=log_result,
            log_duration=log_duration,
            log_exceptions=log_exceptions,
            level=level,
            template=template
        )
        self.rules.append(rule)
        
    def get_rule_for_function(self, func_name: str) -> Optional[TracingRule]:
        """
        Get the first matching rule for a function name.
        
        Args:
            func_name: Name of the function to check
            
        Returns:
            Matching TracingRule or None
        """
        for rule in self.rules:
            if rule.pattern.match(func_name):
                return rule
        return None
        
    def trace(
        self,
        func: Optional[Callable] = None,
        *,
        name: Optional[str] = None,
        level: str = "DEBUG",
        template: Optional[str] = None,
        log_args: bool = True,
        log_result: bool = False,
        log_duration: bool = True
    ):
        """
        Decorator for tracing function execution.
        
        Args:
            func: Function to trace (used when called without parentheses)
            name: Custom name for the function (default: func.__name__)
            level: Log level to use
            template: Template for formatting
            log_args: Include function arguments
            log_result: Include return value
            log_duration: Include execution duration
            
        Example:
            >>> @tracer.trace
            ... def my_function():
            ...     pass
            
            >>> @tracer.trace(log_result=True, template="minimal")
            ... def calculate_something(x, y):
            ...     return x + y
        """
        def decorator(f):
            func_name = name or f.__name__
            
            # Check if we have a rule for this function
            rule = self.get_rule_for_function(func_name)
            if rule and not rule.enabled:
                return f  # Don't trace if disabled by rule
                
            # Use rule settings if available, otherwise use parameters
            effective_level = rule.level if rule else level
            effective_template = rule.template if rule else (template or self.default_template)
            effective_log_args = rule.log_args if rule else log_args
            effective_log_result = rule.log_result if rule else log_result
            effective_log_duration = rule.log_duration if rule else log_duration
            effective_log_entry = rule.log_entry if rule else True
            effective_log_exit = rule.log_exit if rule else True
            effective_log_exceptions = rule.log_exceptions if rule else True
            
            @functools.wraps(f)
            def wrapper(*args, **kwargs):
                if not self.global_enabled:
                    return f(*args, **kwargs)
                    
                start_time = time.perf_counter()
                
                # Prepare context
                context = {
                    "function": func_name,
                    "template": effective_template,
                    "trace_id": id(f)  # Simple trace ID
                }
                
                # Add arguments to context if requested
                if effective_log_args:
                    try:
                        # Get function signature for parameter names
                        sig = inspect.signature(f)
                        bound_args = sig.bind(*args, **kwargs)
                        bound_args.apply_defaults()
                        
                        # Limit argument representation to prevent huge logs
                        arg_repr = {}
                        for param_name, value in bound_args.arguments.items():
                            try:
                                str_value = repr(value)
                                if len(str_value) <= 100:
                                    arg_repr[param_name] = value
                                else:
                                    arg_repr[param_name] = f"<{type(value).__name__} object>"
                            except:
                                arg_repr[param_name] = f"<{type(value).__name__} object>"
                        
                        context["args"] = arg_repr
                    except Exception:
                        context["args"] = {"error": "Could not bind arguments"}
                
                bound_logger = self.logger.bind(**context)
                
                # Log function entry
                if effective_log_entry:
                    entry_msg = f"Entering function {func_name}"
                    if effective_log_args and "args" in context:
                        entry_msg += f" with args: {context['args']}"
                    bound_logger.log(effective_level, entry_msg)
                
                try:
                    # Execute function
                    result = f(*args, **kwargs)
                    
                    # Log function exit
                    if effective_log_exit:
                        duration = time.perf_counter() - start_time
                        exit_msg = f"Exiting function {func_name}"
                        
                        exit_context = context.copy()
                        
                        if effective_log_duration:
                            exit_context["duration_ms"] = round(duration * 1000, 2)
                            exit_msg += f" (took {exit_context['duration_ms']}ms)"
                            
                        if effective_log_result:
                            try:
                                result_repr = repr(result)
                                if len(result_repr) <= 200:
                                    exit_context["result"] = result
                                    exit_msg += f" -> {result_repr}"
                                else:
                                    exit_context["result"] = f"<{type(result).__name__} object>"
                                    exit_msg += f" -> <{type(result).__name__} object>"
                            except:
                                exit_context["result"] = f"<{type(result).__name__} object>"
                        
                        self.logger.bind(**exit_context).log(effective_level, exit_msg)
                    
                    return result
                    
                except Exception as e:
                    if effective_log_exceptions:
                        duration = time.perf_counter() - start_time
                        error_context = context.copy()
                        error_context.update({
                            "exception_type": type(e).__name__,
                            "exception_message": str(e),
                            "duration_ms": round(duration * 1000, 2)
                        })
                        
                        self.logger.bind(**error_context).opt(exception=True).log(
                            "ERROR", 
                            f"Exception in function {func_name} after {error_context['duration_ms']}ms"
                        )
                    raise
                    
            return wrapper
            
        if func is None:
            return decorator
        else:
            return decorator(func)


class PerformanceTracer(FunctionTracer):
    """
    Specialized tracer for performance monitoring.
    
    Extends FunctionTracer with performance-specific features like
    timing statistics and performance alerts.
    """
    
    def __init__(self, logger, default_template: str = "beautiful"):
        super().__init__(logger, default_template)
        self.timing_stats: Dict[str, List[float]] = {}
        self.performance_thresholds: Dict[str, float] = {}
        
    def set_performance_threshold(self, pattern: str, threshold_ms: float) -> None:
        """
        Set performance threshold for function pattern.
        
        Args:
            pattern: Function name pattern
            threshold_ms: Threshold in milliseconds
        """
        self.performance_thresholds[pattern] = threshold_ms
        
    def trace_performance(
        self,
        func: Optional[Callable] = None,
        *,
        threshold_ms: Optional[float] = None,
        track_stats: bool = True,
        **kwargs
    ):
        """
        Decorator for performance-focused tracing.
        
        Args:
            func: Function to trace
            threshold_ms: Performance threshold in milliseconds
            track_stats: Whether to track timing statistics
            **kwargs: Additional tracing options
        """
        def decorator(f):
            func_name = f.__name__
            
            # Set threshold if provided
            if threshold_ms is not None:
                self.performance_thresholds[func_name] = threshold_ms
                
            # Use performance-focused defaults
            performance_kwargs = {
                "log_duration": True,
                "log_result": False,
                "level": "INFO",
                **kwargs
            }
            
            traced_func = self.trace(f, **performance_kwargs)
            
            @functools.wraps(traced_func)
            def wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                try:
                    result = traced_func(*args, **kwargs)
                    return result
                finally:
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    
                    # Track statistics
                    if track_stats:
                        if func_name not in self.timing_stats:
                            self.timing_stats[func_name] = []
                        self.timing_stats[func_name].append(duration_ms)
                        
                        # Keep only recent measurements (last 100)
                        if len(self.timing_stats[func_name]) > 100:
                            self.timing_stats[func_name] = self.timing_stats[func_name][-100:]
                    
                    # Check performance threshold
                    threshold = self.performance_thresholds.get(func_name)
                    if threshold and duration_ms > threshold:
                        self.logger.bind(
                            function=func_name,
                            duration_ms=round(duration_ms, 2),
                            threshold_ms=threshold,
                            template="beautiful"
                        ).warning(f"Performance threshold exceeded in {func_name}")
            
            return wrapper
            
        if func is None:
            return decorator
        else:
            return decorator(func)
            
    def get_performance_stats(self, func_name: str) -> Optional[Dict[str, float]]:
        """
        Get performance statistics for a function.
        
        Args:
            func_name: Name of the function
            
        Returns:
            Dictionary with timing statistics or None
        """
        if func_name not in self.timing_stats:
            return None
            
        timings = self.timing_stats[func_name]
        if not timings:
            return None
            
        return {
            "count": len(timings),
            "avg_ms": sum(timings) / len(timings),
            "min_ms": min(timings),
            "max_ms": max(timings),
            "recent_ms": timings[-1] if timings else 0
        }


def create_development_tracer(logger) -> FunctionTracer:
    """
    Create a tracer configured for development use.
    
    Args:
        logger: Loguru logger instance
        
    Returns:
        FunctionTracer with development-friendly settings
    """
    tracer = FunctionTracer(logger, "beautiful")
    
    # Add common development patterns
    tracer.add_rule(
        pattern=r"^test_.*",
        log_entry=True,
        log_exit=True,
        log_args=True,
        log_result=True,
        log_duration=True,
        level="DEBUG"
    )
    
    tracer.add_rule(
        pattern=r".*debug.*",
        log_entry=True,
        log_exit=True,
        log_args=True,
        log_result=True,
        level="DEBUG"
    )
    
    tracer.add_rule(
        pattern=r"^_.*",  # Private functions
        enabled=False     # Disabled by default
    )
    
    return tracer


def create_production_tracer(logger) -> FunctionTracer:
    """
    Create a tracer configured for production use.
    
    Args:
        logger: Loguru logger instance
        
    Returns:
        FunctionTracer with production-friendly settings
    """
    tracer = FunctionTracer(logger, "minimal")
    
    # Add production-focused patterns
    tracer.add_rule(
        pattern=r".*api.*",
        log_entry=True,
        log_exit=True,
        log_args=False,  # Don't log args in production
        log_result=False,
        log_duration=True,
        level="INFO"
    )
    
    tracer.add_rule(
        pattern=r".*handler.*", 
        log_entry=True,
        log_exit=True,
        log_args=False,
        log_duration=True,
        level="INFO"
    )
    
    tracer.add_rule(
        pattern=r"^_.*",  # Private functions
        enabled=False     # Disabled
    )
    
    return tracer


# Convenience functions for common use cases
def trace_with_template(template_name: str):
    """
    Decorator factory for tracing with a specific template.
    
    Args:
        template_name: Name of template to use
        
    Example:
        >>> @trace_with_template("beautiful")
        ... def my_function():
        ...     pass
    """
    def decorator(func):
        # This is a simplified version - in practice would need logger access
        from . import logger
        tracer = FunctionTracer(logger, template_name)
        return tracer.trace(func)
    return decorator


def performance_trace(threshold_ms: float = 1000):
    """
    Decorator for performance monitoring with threshold.
    
    Args:
        threshold_ms: Performance threshold in milliseconds
        
    Example:
        >>> @performance_trace(500)  # Alert if takes > 500ms
        ... def expensive_function():
        ...     pass
    """
    def decorator(func):
        from . import logger
        tracer = PerformanceTracer(logger)
        return tracer.trace_performance(func, threshold_ms=threshold_ms)
    return decorator