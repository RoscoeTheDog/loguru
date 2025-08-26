# logging_suite/processors.py
# Relative path: LoggingSuite/processors.py
"""
Log entry processing and enhancement utilities
Handles data transformation, filtering, and enrichment before formatting
"""

import re
import time
from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class ProcessingRule:
    """Definition of a log processing rule"""
    name: str
    condition: Callable[[Dict[str, Any]], bool]
    action: Callable[[Dict[str, Any]], Dict[str, Any]]
    priority: int = 10
    enabled: bool = True


class LogEntryProcessor:
    """Process and enhance log entries before formatting"""

    def __init__(self):
        self.rules: List[ProcessingRule] = []
        self.performance_thresholds = {
            'fast': 0.1,
            'medium': 1.0,
            'slow': 5.0
        }

    def add_rule(self, rule: ProcessingRule):
        """Add a processing rule"""
        self.rules.append(rule)
        # Sort by priority (lower numbers = higher priority)
        self.rules.sort(key=lambda r: r.priority)

    def remove_rule(self, rule_name: str):
        """Remove a processing rule by name"""
        self.rules = [r for r in self.rules if r.name != rule_name]

    def process_entry(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a log entry through all enabled rules"""
        processed_data = log_data.copy()

        for rule in self.rules:
            if rule.enabled and rule.condition(processed_data):
                try:
                    processed_data = rule.action(processed_data)
                except Exception as e:
                    # Don't let processing rules break logging
                    processed_data['_processing_error'] = f"Rule '{rule.name}' failed: {e}"

        return processed_data

    @staticmethod
    def extract_performance_metrics(context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and format performance metrics"""
        metrics = {}

        if 'execution_time_seconds' in context:
            exec_time = context['execution_time_seconds']
            metrics['duration'] = f"{exec_time:.3f}s"

            # Categorize performance
            if exec_time > 5.0:
                metrics['performance'] = 'slow'
            elif exec_time > 1.0:
                metrics['performance'] = 'medium'
            else:
                metrics['performance'] = 'fast'

        if 'execution_time_ms' in context:
            exec_time_ms = context['execution_time_ms']
            metrics['duration_ms'] = f"{exec_time_ms:.1f}ms"

        if 'db_operations_count' in context:
            metrics['db_ops'] = context['db_operations_count']

        if 'memory_usage_mb' in context:
            metrics['memory'] = f"{context['memory_usage_mb']:.1f}MB"

        return metrics

    @staticmethod
    def extract_error_info(context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and format error information"""
        error_info = {}

        if 'exception_type' in context:
            error_info['error_type'] = context['exception_type']

        if 'exception_message' in context:
            error_info['error_msg'] = context['exception_message']

        if 'line_number' in context:
            error_info['line'] = context['line_number']

        if 'file' in context:
            # Extract just the filename, not full path
            file_path = context['file']
            if '/' in file_path or '\\' in file_path:
                error_info['file'] = file_path.split('/')[-1].split('\\')[-1]
            else:
                error_info['file'] = file_path

        return error_info

    @staticmethod
    def categorize_log_entry(level: str, message: str, context: Dict[str, Any]) -> str:
        """Categorize log entry for better organization"""
        level_upper = level.upper()

        if level_upper in ['ERROR', 'CRITICAL']:
            return 'error'

        if 'execution_time_seconds' in context or 'execution_time_ms' in context:
            return 'performance'

        if any(key in context for key in ['user_id', 'session_id', 'request_id']):
            return 'user_activity'

        if 'db_operations_count' in context or any(
                keyword in message.lower() for keyword in ['database', 'query', 'sql']):
            return 'database'

        if any(keyword in message.lower() for keyword in ['api', 'request', 'response', 'http', 'endpoint']):
            return 'api'

        if any(keyword in message.lower() for keyword in ['auth', 'login', 'logout', 'permission']):
            return 'security'

        return 'general'

    @staticmethod
    def sanitize_sensitive_data(context: Dict[str, Any],
                                sensitive_keys: List[str] = None) -> Dict[str, Any]:
        """Remove or mask sensitive data from context"""
        if sensitive_keys is None:
            sensitive_keys = [
                'password', 'token', 'secret', 'key', 'auth', 'credential',
                'ssn', 'social_security', 'credit_card', 'api_key'
            ]

        sanitized = context.copy()

        for key, value in context.items():
            key_lower = key.lower()

            # Check if key contains sensitive terms
            if any(sensitive in key_lower for sensitive in sensitive_keys):
                if isinstance(value, str) and len(value) > 4:
                    # Mask all but last 4 characters
                    sanitized[key] = '*' * (len(value) - 4) + value[-4:]
                else:
                    sanitized[key] = '***'

            # Check for email-like patterns
            elif isinstance(value, str) and '@' in value and '.' in value:
                parts = value.split('@')
                if len(parts) == 2:
                    username, domain = parts
                    if username:
                        masked_username = username[0] + '*' * (len(username) - 2) + username[-1] if len(
                            username) > 2 else '***'
                        sanitized[key] = f"{masked_username}@{domain}"

        return sanitized

    @staticmethod
    def enrich_with_context(log_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich log entry with additional context"""
        enriched = log_data.copy()
        context = enriched.get('context', {})

        # Add timestamp if missing
        if 'timestamp' not in enriched:
            enriched['timestamp'] = datetime.now().isoformat()

        # Add category
        category = LogEntryProcessor.categorize_log_entry(
            enriched.get('level', 'INFO'),
            enriched.get('message', ''),
            context
        )
        enriched['category'] = category

        # Add performance metrics if available
        if any(key in context for key in ['execution_time_seconds', 'execution_time_ms']):
            metrics = LogEntryProcessor.extract_performance_metrics(context)
            enriched['performance_metrics'] = metrics

        # Add error info if this is an error
        if enriched.get('level', '').upper() in ['ERROR', 'CRITICAL']:
            error_info = LogEntryProcessor.extract_error_info(context)
            if error_info:
                enriched['error_details'] = error_info

        return enriched

    @staticmethod
    def filter_by_level(min_level: str) -> Callable[[Dict[str, Any]], bool]:
        """Create a filter function for minimum log level"""
        level_order = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        min_index = level_order.index(min_level.upper())

        def filter_func(log_data: Dict[str, Any]) -> bool:
            level = log_data.get('level', 'INFO').upper()
            try:
                return level_order.index(level) >= min_index
            except ValueError:
                return True  # Unknown levels pass through

        return filter_func

    @staticmethod
    def filter_by_pattern(pattern: str, field: str = 'message') -> Callable[[Dict[str, Any]], bool]:
        """Create a filter function for regex pattern matching"""
        compiled_pattern = re.compile(pattern, re.IGNORECASE)

        def filter_func(log_data: Dict[str, Any]) -> bool:
            value = log_data.get(field, '')
            if isinstance(value, str):
                return bool(compiled_pattern.search(value))
            return False

        return filter_func

    @staticmethod
    def create_enrichment_rule(name: str, priority: int = 5) -> ProcessingRule:
        """Create a rule for enriching log entries"""
        return ProcessingRule(
            name=name,
            condition=lambda data: True,  # Always apply enrichment
            action=LogEntryProcessor.enrich_with_context,
            priority=priority
        )

    @staticmethod
    def create_sanitization_rule(name: str, sensitive_keys: List[str] = None, priority: int = 1) -> ProcessingRule:
        """Create a rule for sanitizing sensitive data"""

        def sanitize_action(log_data: Dict[str, Any]) -> Dict[str, Any]:
            sanitized = log_data.copy()
            if 'context' in sanitized:
                sanitized['context'] = LogEntryProcessor.sanitize_sensitive_data(
                    sanitized['context'], sensitive_keys
                )
            return sanitized

        return ProcessingRule(
            name=name,
            condition=lambda data: 'context' in data,
            action=sanitize_action,
            priority=priority
        )

    @staticmethod
    def create_performance_rule(name: str, threshold: float = 1.0, priority: int = 3) -> ProcessingRule:
        """Create a rule for flagging slow operations"""

        def performance_action(log_data: Dict[str, Any]) -> Dict[str, Any]:
            processed = log_data.copy()
            context = processed.get('context', {})

            exec_time = context.get('execution_time_seconds', 0)
            if exec_time > threshold:
                processed['performance_warning'] = True
                processed['slow_operation'] = True

                # Upgrade log level for very slow operations
                if exec_time > threshold * 5:
                    processed['level'] = 'WARNING'

            return processed

        def has_execution_time(log_data: Dict[str, Any]) -> bool:
            return 'execution_time_seconds' in log_data.get('context', {})

        return ProcessingRule(
            name=name,
            condition=has_execution_time,
            action=performance_action,
            priority=priority
        )


class ProcessingPipeline:
    """Manages a pipeline of log processors"""

    def __init__(self):
        self.processors: List[LogEntryProcessor] = []
        self.enabled = True

    def add_processor(self, processor: LogEntryProcessor):
        """Add a processor to the pipeline"""
        self.processors.append(processor)

    def remove_processor(self, processor: LogEntryProcessor):
        """Remove a processor from the pipeline"""
        if processor in self.processors:
            self.processors.remove(processor)

    def process(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process log data through all processors in the pipeline"""
        if not self.enabled:
            return log_data

        processed_data = log_data
        for processor in self.processors:
            try:
                processed_data = processor.process_entry(processed_data)
            except Exception as e:
                # Don't let processor errors break logging
                processed_data['_pipeline_error'] = f"Processor failed: {e}"

        return processed_data

    def enable(self):
        """Enable the processing pipeline"""
        self.enabled = True

    def disable(self):
        """Disable the processing pipeline"""
        self.enabled = False


# Default processor instances for common use cases
class DefaultProcessors:
    """Collection of commonly used processors"""

    @staticmethod
    def create_development_processor() -> LogEntryProcessor:
        """Create a processor optimized for development"""
        processor = LogEntryProcessor()

        # Add enrichment rule
        processor.add_rule(LogEntryProcessor.create_enrichment_rule('dev_enrichment'))

        # Add sensitive data sanitization
        processor.add_rule(LogEntryProcessor.create_sanitization_rule('dev_sanitization'))

        # Flag slow operations (lower threshold for dev)
        processor.add_rule(LogEntryProcessor.create_performance_rule('dev_performance', threshold=0.5))

        return processor

    @staticmethod
    def create_production_processor() -> LogEntryProcessor:
        """Create a processor optimized for production"""
        processor = LogEntryProcessor()

        # Add enrichment rule with higher priority
        processor.add_rule(LogEntryProcessor.create_enrichment_rule('prod_enrichment', priority=1))

        # Add strict sensitive data sanitization
        sensitive_keys = [
            'password', 'token', 'secret', 'key', 'auth', 'credential',
            'ssn', 'social_security', 'credit_card', 'api_key', 'private_key',
            'access_token', 'refresh_token', 'session_key'
        ]
        processor.add_rule(LogEntryProcessor.create_sanitization_rule(
            'prod_sanitization', sensitive_keys, priority=0
        ))

        # Flag slow operations (higher threshold for prod)
        processor.add_rule(LogEntryProcessor.create_performance_rule('prod_performance', threshold=2.0))

        return processor


# Export all processing utilities
__all__ = [
    'ProcessingRule',
    'LogEntryProcessor',
    'ProcessingPipeline',
    'DefaultProcessors'
]