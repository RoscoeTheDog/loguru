#!/usr/bin/env python3
"""
Unified Exception Formatter
Provides both 'beautiful' and 'pprint' styling options for exception output
Used by decorators, middleware, and global exception handler
"""

import json
import sys
from typing import Dict, Any, Type, Optional
from datetime import datetime

from .config import get_global_config
from .global_exception_hook import EnhancedConsoleFormatter, DataFormatter


class UnifiedExceptionFormatter:
    """
    Unified exception formatter supporting multiple output styles:
    - 'beautiful': Enhanced console formatting with colors and visual elements
    - 'pprint': Pretty-printed JSON format
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or get_global_config()
        self.data_formatter = DataFormatter(
            max_length=self.config.get('stack_data_max_length', 200),
            max_depth=self.config.get('stack_data_max_depth', 3),
            pretty_print=self.config.get('pretty_print_stack_data', True)
        )
        
        # Initialize console formatter for beautiful output
        self.console_formatter = EnhancedConsoleFormatter(
            colorize=self.config.get('use_colors', True),
            config=self.config
        )
    
    def format_exception(self, 
                        exc_info: tuple,
                        context: Optional[Dict[str, Any]] = None,
                        system_info: Optional[Dict[str, Any]] = None,
                        style: Optional[str] = None) -> str:
        """
        Format exception using specified style
        
        Args:
            exc_info: (exc_type, exc_value, exc_traceback) tuple
            context: Additional context information
            system_info: System information (optional)
            style: 'beautiful' or 'pprint' (uses config if not specified)
            
        Returns:
            Formatted exception string
        """
        exc_type, exc_value, exc_traceback = exc_info
        
        # Determine output style
        if style is None:
            style = self.config.get('console_output_style', 'beautiful')
        
        # Get exception context if not provided
        if context is None:
            try:
                from .exceptions.backend_adapter import create_exception_handler_for_backend
                backend = self.config.get('backend', 'standard')
                exception_handler = create_exception_handler_for_backend(backend, self.config)
                context = exception_handler.get_exception_context(exc_info)
            except Exception:
                context = {}
        
        # Format based on style
        if style == 'pprint':
            return self._format_pprint(exc_type, exc_value, exc_traceback, context, system_info)
        else:  # 'beautiful' or fallback
            return self._format_beautiful(exc_type, exc_value, exc_traceback, context, system_info)
    
    def _format_beautiful(self, 
                         exc_type: Type[BaseException],
                         exc_value: BaseException, 
                         exc_traceback,
                         context: Dict[str, Any],
                         system_info: Optional[Dict[str, Any]]) -> str:
        """Format using beautiful console output"""
        try:
            return self.console_formatter.format_comprehensive_output(
                exc_type, exc_value, exc_traceback, system_info or {}, context
            )
        except Exception:
            # Fallback to basic formatting
            return f"🚨 Beautiful formatting failed\n{exc_type.__name__}: {exc_value}"
    
    def _format_pprint(self, 
                      exc_type: Type[BaseException],
                      exc_value: BaseException, 
                      exc_traceback,
                      context: Dict[str, Any],
                      system_info: Optional[Dict[str, Any]]) -> str:
        """Format using pretty-printed JSON style"""
        output_data = {
            "timestamp": datetime.now().isoformat(),
            "exception": {
                "type": exc_type.__name__,
                "message": str(exc_value),
                "location": context.get('exception_location', 'unknown'),
                "function": context.get('exception_function', 'unknown'), 
                "module": context.get('exception_module', 'unknown')
            }
        }
        
        # Add local variables if available and enabled
        if (self.config.get('show_exception_details', True) and 
            context.get('exception_locals')):
            formatted_locals = self.data_formatter.format_locals_dict(
                context['exception_locals']
            )
            output_data["exception"]["locals"] = formatted_locals
        
        # Add caller information if available
        if context.get('caller'):
            output_data["caller"] = context['caller']
        
        # Add stack frames if enabled and available
        if (self.config.get('show_stack_trace', True) and 
            context.get('stack_frames')):
            output_data["stack_frames"] = context['stack_frames']
        
        # Add system info if enabled and available
        if (self.config.get('show_system_state', True) and 
            system_info):
            output_data["system_info"] = system_info
            
        # Add code context if enabled
        if (self.config.get('show_code_context', True) and 
            context.get('exception_file_path') and 
            context.get('exception_line')):
            output_data["code_context"] = self._get_code_context(
                context['exception_file_path'], 
                context['exception_line']
            )
        
        # Add environment variables if enabled
        if (self.config.get('show_environment_vars', True) and 
            system_info and 
            system_info.get('environment', {}).get('environment_vars')):
            output_data["environment_vars"] = system_info['environment']['environment_vars']
        
        # Add additional context
        if context.get('context'):
            output_data["additional_context"] = context['context']
        
        # Format as pretty JSON
        try:
            return json.dumps(output_data, indent=2, separators=(', ', ': '), default=str)
        except Exception:
            return f"JSON formatting failed: {exc_type.__name__}: {exc_value}"
    
    def _get_code_context(self, file_path: str, error_line: int) -> Dict[str, Any]:
        """Get code context around error line"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_lines = f.readlines()
            
            start_line = max(0, error_line - 3)
            end_line = min(len(file_lines), error_line + 2)
            
            code_lines = []
            for i in range(start_line, end_line):
                line_num = i + 1
                line_content = file_lines[i].rstrip()
                is_error_line = line_num == error_line
                code_lines.append({
                    "line_number": line_num,
                    "content": line_content,
                    "is_error_line": is_error_line
                })
            
            return {
                "file_path": file_path,
                "error_line": error_line,
                "lines": code_lines
            }
        except Exception:
            return {"error": "Code context unavailable"}

    def format_for_console(self, 
                           exc_info: tuple,
                           context: Optional[Dict[str, Any]] = None,
                           system_info: Optional[Dict[str, Any]] = None) -> str:
        """
        Format exception for console output using configured console style
        
        Args:
            exc_info: Exception info tuple
            context: Additional context
            system_info: System information
            
        Returns:
            Formatted string for console output
        """
        console_style = self.config.get('console_output_style', 'beautiful')
        return self.format_exception(exc_info, context, system_info, style=console_style)
    
    def format_for_logging(self, 
                          exc_info: tuple,
                          context: Optional[Dict[str, Any]] = None,
                          system_info: Optional[Dict[str, Any]] = None) -> str:
        """
        Format exception for logging output using configured exception style
        
        Args:
            exc_info: Exception info tuple
            context: Additional context
            system_info: System information
            
        Returns:
            Formatted string for logging
        """
        exception_style = self.config.get('exception_output_style', 'beautiful') 
        return self.format_exception(exc_info, context, system_info, style=exception_style)


# Convenience function for quick access
def format_exception(exc_info: tuple, 
                    context: Optional[Dict[str, Any]] = None,
                    system_info: Optional[Dict[str, Any]] = None,
                    style: Optional[str] = None,
                    config: Optional[Dict[str, Any]] = None) -> str:
    """
    Quick exception formatting function
    
    Args:
        exc_info: Exception info tuple
        context: Additional context
        system_info: System information
        style: Output style ('beautiful' or 'pprint')
        config: Configuration override
        
    Returns:
        Formatted exception string
    """
    formatter = UnifiedExceptionFormatter(config)
    return formatter.format_exception(exc_info, context, system_info, style)