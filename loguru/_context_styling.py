"""
Smart context auto-styling engine for intelligent log message enhancement.

This module provides advanced context recognition and automatic styling
capabilities that can intelligently identify and style different types of
content within log messages.
"""

import re
import json
import ipaddress
from typing import Dict, List, Tuple, Any, Optional, Pattern, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime
from email.utils import parseaddr
from urllib.parse import urlparse
from ._templates import StyleMode, StyleRule, ContextType


@dataclass
class ContextPattern:
    """A pattern for recognizing context in log messages."""
    name: str
    pattern: Union[str, Pattern]
    context_type: ContextType
    extractor: Optional[Callable[[str], Dict[str, Any]]] = None
    priority: int = 0
    style: str = ""
    
    def __post_init__(self):
        if isinstance(self.pattern, str):
            self.pattern = re.compile(self.pattern, re.IGNORECASE)


class SmartContextEngine:
    """
    Advanced context recognition engine with ML-inspired pattern matching.
    
    This engine can automatically detect various types of content within
    log messages and apply appropriate styling based on context.
    """
    
    def __init__(self):
        """Initialize the smart context engine."""
        self.patterns: List[ContextPattern] = []
        self.style_cache: Dict[str, str] = {}
        self.load_default_patterns()
        
    def load_default_patterns(self) -> None:
        """Load default context recognition patterns."""
        
        # Network patterns
        self.add_pattern(
            name="ipv4_address",
            pattern=r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b',
            context_type=ContextType.IP,
            style="magenta",
            priority=10,
            extractor=self._extract_ip_info
        )
        
        self.add_pattern(
            name="ipv6_address", 
            pattern=r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b',
            context_type=ContextType.IP,
            style="magenta",
            priority=10
        )
        
        self.add_pattern(
            name="url",
            pattern=r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/[^?\s]*)?(?:\?[^#\s]*)?(?:#[^\s]*)?',
            context_type=ContextType.URL,
            style="blue underline",
            priority=10,
            extractor=self._extract_url_info
        )
        
        self.add_pattern(
            name="email",
            pattern=r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            context_type=ContextType.EMAIL,
            style="cyan",
            priority=10,
            extractor=self._extract_email_info
        )
        
        # File system patterns
        self.add_pattern(
            name="unix_path",
            pattern=r'(?:/[^/\s]+)+/?',
            context_type=ContextType.FILEPATH,
            style="dim white",
            priority=5
        )
        
        self.add_pattern(
            name="windows_path",
            pattern=r'[A-Za-z]:\\(?:[^\\/:*?"<>|\s]+\\)*[^\\/:*?"<>|\s]*',
            context_type=ContextType.FILEPATH,
            style="dim white",
            priority=5
        )
        
        # Database patterns
        self.add_pattern(
            name="sql_query",
            pattern=r'\b(?:SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER)\b.*?;?',
            context_type=ContextType.SQL,
            style="yellow",
            priority=8,
            extractor=self._extract_sql_info
        )
        
        # Data patterns
        self.add_pattern(
            name="json_object",
            pattern=r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',
            context_type=ContextType.JSON,
            style="green",
            priority=7,
            extractor=self._extract_json_info
        )
        
        self.add_pattern(
            name="uuid",
            pattern=r'\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b',
            context_type=ContextType.DEFAULT,
            style="dim cyan",
            priority=6
        )
        
        # Time patterns
        self.add_pattern(
            name="iso_datetime",
            pattern=r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})',
            context_type=ContextType.DATETIME,
            style="blue",
            priority=8,
            extractor=self._extract_datetime_info
        )
        
        self.add_pattern(
            name="timestamp",
            pattern=r'\b\d{10}(?:\.\d+)?\b',
            context_type=ContextType.DATETIME,
            style="blue",
            priority=6
        )
        
        # Numeric patterns
        self.add_pattern(
            name="percentage",
            pattern=r'\b\d+(?:\.\d+)?%\b',
            context_type=ContextType.NUMERIC,
            style="yellow",
            priority=7
        )
        
        self.add_pattern(
            name="currency",
            pattern=r'[$£€¥]\d+(?:,\d{3})*(?:\.\d{2})?',
            context_type=ContextType.NUMERIC,
            style="green bold",
            priority=8
        )
        
        # User/Identity patterns
        self.add_pattern(
            name="user_mention",
            pattern=r'@[a-zA-Z0-9_]+',
            context_type=ContextType.USER,
            style="bold cyan",
            priority=7
        )
        
        self.add_pattern(
            name="session_id",
            pattern=r'\bsess(?:ion)?[_-]?(?:id)?[:\s=]*([a-zA-Z0-9]+)\b',
            context_type=ContextType.USER,
            style="dim yellow",
            priority=6
        )
        
        # Error patterns  
        self.add_pattern(
            name="error_code",
            pattern=r'\b(?:ERR|ERROR|FAIL)[-_]?\d+\b',
            context_type=ContextType.ERROR,
            style="red bold",
            priority=9
        )
        
        self.add_pattern(
            name="http_status",
            pattern=r'\b[45]\d{2}\b',  # 4xx and 5xx status codes
            context_type=ContextType.ERROR,
            style="red",
            priority=8
        )
        
    def add_pattern(
        self,
        name: str,
        pattern: Union[str, Pattern],
        context_type: ContextType,
        style: str = "",
        priority: int = 0,
        extractor: Optional[Callable[[str], Dict[str, Any]]] = None
    ) -> None:
        """
        Add a new context recognition pattern.
        
        Args:
            name: Unique name for the pattern
            pattern: Regex pattern to match
            context_type: Type of context this pattern recognizes
            style: Style to apply to matches
            priority: Priority for pattern matching (higher = more priority)
            extractor: Optional function to extract additional context
        """
        context_pattern = ContextPattern(
            name=name,
            pattern=pattern,
            context_type=context_type,
            style=style,
            priority=priority,
            extractor=extractor
        )
        self.patterns.append(context_pattern)
        # Sort by priority (descending)
        self.patterns.sort(key=lambda p: p.priority, reverse=True)
        
    def analyze_message(self, message: str) -> List[Dict[str, Any]]:
        """
        Analyze a message and identify contexts.
        
        Args:
            message: Message to analyze
            
        Returns:
            List of context matches with positions and extracted data
        """
        matches = []
        processed_ranges = []  # Track processed character ranges to avoid overlaps
        
        for pattern in self.patterns:
            for match in pattern.pattern.finditer(message):
                start, end = match.span()
                
                # Check for overlaps with already processed ranges
                overlap = any(
                    (start < proc_end and end > proc_start)
                    for proc_start, proc_end in processed_ranges
                )
                
                if not overlap:
                    match_info = {
                        'pattern_name': pattern.name,
                        'context_type': pattern.context_type,
                        'text': match.group(),
                        'start': start,
                        'end': end,
                        'style': pattern.style,
                        'priority': pattern.priority
                    }
                    
                    # Extract additional context if extractor available
                    if pattern.extractor:
                        try:
                            extracted = pattern.extractor(match.group())
                            match_info['extracted'] = extracted
                        except Exception:
                            # Don't let extraction errors break analysis
                            match_info['extracted'] = {}
                    
                    matches.append(match_info)
                    processed_ranges.append((start, end))
        
        # Sort matches by position
        matches.sort(key=lambda m: m['start'])
        return matches
        
    def apply_smart_styling(self, message: str, existing_context: Dict[str, Any] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Apply smart styling to a message based on context analysis.
        
        Args:
            message: Message to style
            existing_context: Existing context data
            
        Returns:
            Tuple of (styled_message, enhanced_context)
        """
        if not message:
            return message, existing_context or {}
        
        # Analyze the message
        matches = self.analyze_message(message)
        if not matches:
            return message, existing_context or {}
        
        # Build styled message
        styled_message = message
        offset = 0  # Track offset due to added markup
        enhanced_context = (existing_context or {}).copy()
        
        for match in matches:
            if not match['style']:
                continue
                
            original_text = match['text']
            styled_text = f"<{match['style']}>{original_text}</{match['style']}>"
            
            # Calculate position with offset
            start_pos = match['start'] + offset
            end_pos = match['end'] + offset
            
            # Replace in styled message
            styled_message = (
                styled_message[:start_pos] + 
                styled_text + 
                styled_message[end_pos:]
            )
            
            # Update offset
            offset += len(styled_text) - len(original_text)
            
            # Add to enhanced context
            context_key = f"{match['context_type'].value}_{match['pattern_name']}"
            enhanced_context[context_key] = original_text
            
            # Add extracted data
            if 'extracted' in match:
                for key, value in match['extracted'].items():
                    enhanced_context[f"{context_key}_{key}"] = value
        
        return styled_message, enhanced_context
        
    def get_context_summary(self, message: str) -> Dict[str, List[str]]:
        """
        Get a summary of contexts found in a message.
        
        Args:
            message: Message to analyze
            
        Returns:
            Dictionary mapping context types to found values
        """
        matches = self.analyze_message(message)
        summary: Dict[str, List[str]] = {}
        
        for match in matches:
            context_type = match['context_type'].value
            if context_type not in summary:
                summary[context_type] = []
            summary[context_type].append(match['text'])
            
        return summary
    
    # Context extractors
    def _extract_ip_info(self, ip_str: str) -> Dict[str, Any]:
        """Extract information about an IP address."""
        try:
            ip = ipaddress.ip_address(ip_str)
            return {
                'version': ip.version,
                'is_private': ip.is_private,
                'is_loopback': ip.is_loopback,
                'is_multicast': ip.is_multicast
            }
        except Exception:
            return {}
            
    def _extract_url_info(self, url_str: str) -> Dict[str, Any]:
        """Extract information about a URL."""
        try:
            parsed = urlparse(url_str)
            return {
                'scheme': parsed.scheme,
                'domain': parsed.netloc,
                'path': parsed.path,
                'has_query': bool(parsed.query),
                'has_fragment': bool(parsed.fragment)
            }
        except Exception:
            return {}
            
    def _extract_email_info(self, email_str: str) -> Dict[str, Any]:
        """Extract information about an email address."""
        try:
            name, addr = parseaddr(email_str)
            if '@' in addr:
                local, domain = addr.rsplit('@', 1)
                return {
                    'local_part': local,
                    'domain': domain,
                    'has_name': bool(name)
                }
        except Exception:
            pass
        return {}
        
    def _extract_datetime_info(self, datetime_str: str) -> Dict[str, Any]:
        """Extract information about a datetime string."""
        try:
            # Try to parse ISO format
            dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            return {
                'year': dt.year,
                'month': dt.month,
                'day': dt.day,
                'hour': dt.hour,
                'weekday': dt.strftime('%A'),
                'has_timezone': dt.tzinfo is not None
            }
        except Exception:
            return {}
            
    def _extract_sql_info(self, sql_str: str) -> Dict[str, Any]:
        """Extract information about a SQL query."""
        sql_upper = sql_str.upper().strip()
        operation = None
        for op in ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER']:
            if sql_upper.startswith(op):
                operation = op
                break
        
        return {
            'operation': operation,
            'length': len(sql_str),
            'has_where': 'WHERE' in sql_upper,
            'has_join': any(join in sql_upper for join in ['JOIN', 'INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN'])
        }
        
    def _extract_json_info(self, json_str: str) -> Dict[str, Any]:
        """Extract information about a JSON object."""
        try:
            data = json.loads(json_str)
            return {
                'type': type(data).__name__,
                'length': len(json_str),
                'keys': list(data.keys()) if isinstance(data, dict) else None,
                'size': len(data) if isinstance(data, (dict, list)) else None
            }
        except Exception:
            return {'valid_json': False}


class AdaptiveContextEngine(SmartContextEngine):
    """
    Adaptive version of context engine that learns from usage patterns.
    
    This engine can adapt its behavior based on frequently occurring
    patterns and user preferences.
    """
    
    def __init__(self):
        super().__init__()
        self.usage_stats: Dict[str, int] = {}
        self.user_preferences: Dict[str, Dict[str, Any]] = {}
        
    def record_usage(self, pattern_name: str) -> None:
        """Record usage of a pattern for adaptive learning."""
        self.usage_stats[pattern_name] = self.usage_stats.get(pattern_name, 0) + 1
        
    def set_user_preference(self, pattern_name: str, preferences: Dict[str, Any]) -> None:
        """
        Set user preferences for a specific pattern.
        
        Args:
            pattern_name: Name of the pattern
            preferences: Dictionary of preference overrides
        """
        self.user_preferences[pattern_name] = preferences
        
    def analyze_message(self, message: str) -> List[Dict[str, Any]]:
        """Enhanced analysis that records usage and applies preferences."""
        matches = super().analyze_message(message)
        
        # Record usage and apply preferences
        for match in matches:
            pattern_name = match['pattern_name']
            self.record_usage(pattern_name)
            
            # Apply user preferences
            if pattern_name in self.user_preferences:
                prefs = self.user_preferences[pattern_name]
                match.update(prefs)
        
        return matches
        
    def get_popular_patterns(self, limit: int = 10) -> List[Tuple[str, int]]:
        """
        Get most frequently used patterns.
        
        Args:
            limit: Maximum number of patterns to return
            
        Returns:
            List of (pattern_name, usage_count) tuples
        """
        return sorted(
            self.usage_stats.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:limit]


def create_context_engine_for_domain(domain: str) -> SmartContextEngine:
    """
    Create a context engine optimized for a specific domain.
    
    Args:
        domain: Domain type ("web", "security", "finance", "general")
        
    Returns:
        SmartContextEngine configured for the domain
    """
    engine = SmartContextEngine()
    
    if domain == "web":
        # Add web-specific patterns
        engine.add_pattern(
            name="http_method",
            pattern=r'\b(?:GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\b',
            context_type=ContextType.DEFAULT,
            style="bold blue",
            priority=8
        )
        
        engine.add_pattern(
            name="user_agent",
            pattern=r'Mozilla/\d+\.\d+.*',
            context_type=ContextType.DEFAULT,
            style="dim white",
            priority=6
        )
        
    elif domain == "security":
        # Add security-specific patterns
        engine.add_pattern(
            name="hash_md5",
            pattern=r'\b[a-fA-F0-9]{32}\b',
            context_type=ContextType.DEFAULT,
            style="dim red",
            priority=7
        )
        
        engine.add_pattern(
            name="hash_sha256",
            pattern=r'\b[a-fA-F0-9]{64}\b',
            context_type=ContextType.DEFAULT,
            style="dim red",
            priority=8
        )
        
    elif domain == "finance":
        # Add finance-specific patterns
        engine.add_pattern(
            name="account_number",
            pattern=r'\b\d{10,16}\b',
            context_type=ContextType.DEFAULT,
            style="bold green",
            priority=7
        )
        
        engine.add_pattern(
            name="transaction_id",
            pattern=r'\bTXN[-_]?[A-Z0-9]+\b',
            context_type=ContextType.DEFAULT,
            style="cyan",
            priority=8
        )
    
    return engine