# logging_suite/global_exception_hook.py
"""
Simplified, framework-independent global exception handler
Provides comprehensive debugging information through sys.excepthook replacement
"""

import sys
import threading
import traceback
import platform
import psutil
import os
import json
import pprint
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Type
from datetime import datetime

from .exceptions.backend_adapter import create_exception_handler_for_backend
from .config import get_global_config


class DataFormatter:
    """Utility class for formatting data with pretty printing options"""
    
    def __init__(self, max_length: int = 200, max_depth: int = 3, pretty_print: bool = True):
        self.max_length = max_length
        self.max_depth = max_depth
        self.pretty_print = pretty_print
    
    def format_value(self, value: Any, current_depth: int = 0) -> str:
        """Format a value with truncation and depth limits"""
        try:
            if current_depth >= self.max_depth:
                return f"<max_depth_reached: {type(value).__name__}>"
            
            # Handle different types
            if isinstance(value, (str, int, float, bool, type(None))):
                formatted = repr(value)
            elif isinstance(value, (list, tuple)):
                if not value:
                    formatted = str(value)
                elif len(value) > 10:  # Limit list/tuple length
                    items = [self.format_value(item, current_depth + 1) for item in value[:5]]
                    formatted = f"{type(value).__name__}([{', '.join(items)}, ... +{len(value) - 5} more])"
                else:
                    items = [self.format_value(item, current_depth + 1) for item in value]
                    formatted = f"{type(value).__name__}([{', '.join(items)}])"
            elif isinstance(value, dict):
                if not value:
                    formatted = "{}"
                elif len(value) > 10:  # Limit dict items
                    items = []
                    for i, (k, v) in enumerate(value.items()):
                        if i >= 5:
                            break
                        items.append(f"{repr(k)}: {self.format_value(v, current_depth + 1)}")
                    formatted = f"{{{', '.join(items)}, ... +{len(value) - 5} more}}"
                else:
                    items = [f"{repr(k)}: {self.format_value(v, current_depth + 1)}" for k, v in value.items()]
                    formatted = f"{{{', '.join(items)}}}"
            else:
                # For complex objects, show type and basic info
                if hasattr(value, '__dict__'):
                    formatted = f"<{type(value).__name__} object>"
                else:
                    formatted = f"<{type(value).__name__}: {str(value)[:50]}>"
            
            # Truncate if too long
            if len(formatted) > self.max_length:
                formatted = formatted[:self.max_length - 3] + "..."
            
            return formatted
            
        except Exception:
            return f"<formatting_error: {type(value).__name__}>"
    
    def format_locals_dict(self, locals_dict: Dict[str, Any]) -> Dict[str, str]:
        """Format a locals dictionary with pretty printing"""
        formatted = {}
        for name, value in locals_dict.items():
            formatted[name] = self.format_value(value)
        return formatted


class SystemInfoCollector:
    """Collects system information for debugging context"""

    def __init__(self):
        self._process = psutil.Process()
        self._boot_time = psutil.boot_time()

    def collect_system_info(self) -> Dict[str, Any]:
        """Collect comprehensive system information"""
        try:
            # Memory information
            memory_info = self._process.memory_info()
            virtual_memory = psutil.virtual_memory()

            # Process information
            process_info = {
                'pid': self._process.pid,
                'ppid': self._process.ppid(),
                'name': self._process.name(),
                'exe': self._process.exe(),
                'cmdline': ' '.join(self._process.cmdline()),
                'create_time': datetime.fromtimestamp(self._process.create_time()).isoformat(),
                'num_threads': self._process.num_threads(),
                'memory_rss': memory_info.rss,  # Resident Set Size
                'memory_vms': memory_info.vms,  # Virtual Memory Size
                'memory_percent': self._process.memory_percent(),
                'cpu_percent': self._process.cpu_percent(),
                'status': self._process.status(),
            }

            # System information
            system_info = {
                'platform': platform.platform(),
                'python_version': platform.python_version(),
                'python_implementation': platform.python_implementation(),
                'architecture': platform.architecture()[0],
                'processor': platform.processor(),
                'hostname': platform.node(),
                'system_memory_total': virtual_memory.total,
                'system_memory_available': virtual_memory.available,
                'system_memory_percent': virtual_memory.percent,
                'system_uptime': datetime.now().timestamp() - self._boot_time,
                'cwd': os.getcwd(),
            }

            # Environment context
            environment_info = {
                'python_path': sys.path[:5],  # First 5 entries to avoid too much noise
                'environment_vars': self._get_relevant_env_vars(),
            }

            return {
                'process': process_info,
                'system': system_info,
                'environment': environment_info,
                'collection_time': datetime.now().isoformat(),
            }

        except Exception as e:
            return {
                'error': f"Failed to collect system info: {e}",
                'collection_time': datetime.now().isoformat(),
            }

    def _get_relevant_env_vars(self) -> Dict[str, str]:
        """Get relevant environment variables (excluding sensitive ones)"""
        relevant_vars = [
            'PATH', 'PYTHONPATH', 'VIRTUAL_ENV', 'CONDA_DEFAULT_ENV',
            'DJANGO_SETTINGS_MODULE', 'FLASK_APP', 'FLASK_ENV',
            'DEBUG', 'ENVIRONMENT', 'NODE_ENV', 'STAGE'
        ]

        env_vars = {}
        for var in relevant_vars:
            if var in os.environ:
                env_vars[var] = os.environ[var]

        return env_vars


class EnhancedConsoleFormatter:
    """Creates rich, readable console formatting for exception output"""

    def __init__(self, colorize: bool = True, config: Dict[str, Any] = None):
        self.colorize = colorize
        self.config = config or {}
        
        # Section control flags
        self.show_exception_details = self.config.get('show_exception_details', True)
        self.show_system_state = self.config.get('show_system_state', True)
        self.show_stack_trace = self.config.get('show_stack_trace', True)
        self.show_code_context = self.config.get('show_code_context', True)
        self.show_environment_vars = self.config.get('show_environment_vars', True)
        
        # Data formatting
        self.data_formatter = DataFormatter(
            max_length=self.config.get('stack_data_max_length', 200),
            max_depth=self.config.get('stack_data_max_depth', 3),
            pretty_print=self.config.get('pretty_print_stack_data', True)
        )
        self._colors = {
            'red': '\033[91m' if colorize else '',
            'green': '\033[92m' if colorize else '',
            'yellow': '\033[93m' if colorize else '',
            'blue': '\033[94m' if colorize else '',
            'magenta': '\033[95m' if colorize else '',
            'cyan': '\033[96m' if colorize else '',
            'white': '\033[97m' if colorize else '',
            'bold': '\033[1m' if colorize else '',
            'dim': '\033[2m' if colorize else '',
            'reset': '\033[0m' if colorize else '',
        }

    def format_comprehensive_output(self, 
                                  exc_type: Type[BaseException],
                                  exc_value: BaseException,
                                  exc_traceback,
                                  system_info: Dict[str, Any],
                                  exception_context: Dict[str, Any]) -> str:
        """Format comprehensive exception output with visual organization"""

        sections = []

        # Main exception header (always shown)
        sections.append(self._format_exception_header(exc_type, exc_value))

        # Exception details with file/line info
        if self.show_exception_details:
            sections.append(self._format_exception_details(exception_context))

        # System state section
        if self.show_system_state and system_info:
            sections.append(self._format_system_state(system_info))

        # Full traceback with enhanced formatting
        if self.show_stack_trace:
            sections.append(self._format_enhanced_traceback(exc_traceback, exception_context))

        # Code context section
        if self.show_code_context:
            context_section = self._format_code_context(exception_context)
            if context_section:  # Only add if content exists
                sections.append(context_section)

        # Environment variables section
        if self.show_environment_vars and system_info.get('environment', {}).get('environment_vars'):
            sections.append(self._format_environment_section(system_info['environment']['environment_vars']))

        return '\n\n'.join(sections)

    def _format_exception_header(self, exc_type: Type[BaseException], exc_value: BaseException) -> str:
        """Format the main exception header with visual emphasis"""
        lines = []
        lines.append(f"{self._colors['red']}{self._colors['bold']}{'═' * 60}{self._colors['reset']}")
        lines.append(f"{self._colors['red']}{self._colors['bold']}💀 UNHANDLED EXCEPTION OCCURRED 💀{self._colors['reset']}")
        lines.append(f"{self._colors['red']}{self._colors['bold']}{'═' * 60}{self._colors['reset']}")
        lines.append(f"{self._colors['red']}{exc_type.__name__}: {self._colors['white']}{exc_value}{self._colors['reset']}")
        return '\n'.join(lines)

    def _format_exception_details(self, context: Dict[str, Any]) -> str:
        """Format exception details with location information"""
        lines = []
        lines.append(f"{self._colors['yellow']}{'─' * 30} Exception Details {'─' * 30}{self._colors['reset']}")
        lines.append(f"🎯 {self._colors['bold']}Location:{self._colors['reset']} {context.get('exception_location', 'unknown')}")
        lines.append(f"🔧 {self._colors['bold']}Function:{self._colors['reset']} {context.get('exception_function', 'unknown')}")
        lines.append(f"📁 {self._colors['bold']}Module:{self._colors['reset']} {context.get('exception_module', 'unknown')}")

        if context.get('exception_locals'):
            lines.append(f"📋 {self._colors['bold']}Local Variables at Exception Point:{self._colors['reset']}")
            formatted_locals = self.data_formatter.format_locals_dict(context['exception_locals'])
            for name, formatted_value in formatted_locals.items():
                if any(sensitive in name.lower() for sensitive in ['password', 'token', 'key', 'secret']):
                    lines.append(f"    🔒 {name} = {self._colors['dim']}***{self._colors['reset']}")
                elif formatted_value.startswith('<') and formatted_value.endswith('>'):
                    lines.append(f"    📦 {name} = {self._colors['cyan']}{formatted_value}{self._colors['reset']}")
                else:
                    lines.append(f"    📝 {name} = {self._colors['green']}{formatted_value}{self._colors['reset']}")

        return '\n'.join(lines)

    def _format_system_state(self, system_info: Dict[str, Any]) -> str:
        """Format system state with memory, CPU, and process information"""
        lines = []
        lines.append(f"{self._colors['blue']}{'─' * 30} System State {'─' * 30}{self._colors['reset']}")

        if 'process' in system_info:
            proc = system_info['process']
            lines.append(f"🖥️  {self._colors['bold']}Process Info:{self._colors['reset']}")
            lines.append(f"    PID: {proc.get('pid', 'unknown')}")
            lines.append(f"    Memory: {self._format_bytes(proc.get('memory_rss', 0))} RSS, {proc.get('memory_percent', 0):.1f}% of system")
            lines.append(f"    CPU: {proc.get('cpu_percent', 0):.1f}%")
            lines.append(f"    Threads: {proc.get('num_threads', 'unknown')}")
            lines.append(f"    Status: {proc.get('status', 'unknown')}")

        if 'system' in system_info:
            sys_info = system_info['system']
            lines.append(f"🌐 {self._colors['bold']}System Info:{self._colors['reset']}")
            lines.append(f"    Python: {sys_info.get('python_version', 'unknown')} ({sys_info.get('python_implementation', 'unknown')})")
            lines.append(f"    Platform: {sys_info.get('platform', 'unknown')}")
            lines.append(f"    Memory: {self._format_bytes(sys_info.get('system_memory_available', 0))} available of {self._format_bytes(sys_info.get('system_memory_total', 0))}")
            uptime = sys_info.get('system_uptime', 0)
            lines.append(f"    Uptime: {self._format_duration(uptime)}")

        return '\n'.join(lines)

    def _format_enhanced_traceback(self, tb, context: Dict[str, Any]) -> str:
        """Format enhanced traceback with hierarchical structure"""
        lines = []
        lines.append(f"{self._colors['magenta']}{'─' * 30} Stack Trace {'─' * 30}{self._colors['reset']}")

        if context.get('stack_frames'):
            for i, frame in enumerate(context['stack_frames']):
                is_last = i == len(context['stack_frames']) - 1
                prefix = "└─" if is_last else "├─"

                location = frame.get('location', 'unknown')
                function = frame.get('function', 'unknown')

                if is_last:
                    lines.append(f"    {prefix} {self._colors['red']}{self._colors['bold']}💥 {location} in {function}(){self._colors['reset']}")
                else:
                    lines.append(f"    {prefix} {location} in {function}()")

                # Show locals for the exception frame
                if is_last and frame.get('locals'):
                    formatted_locals = self.data_formatter.format_locals_dict(frame['locals'])
                    for name, formatted_value in formatted_locals.items():
                        if any(sensitive in name.lower() for sensitive in ['password', 'token', 'key', 'secret']):
                            lines.append(f"         🔒 {name} = {self._colors['dim']}***{self._colors['reset']}")
                        else:
                            lines.append(f"         📝 {name} = {formatted_value}")
        else:
            # Fallback to standard traceback
            tb_lines = traceback.format_tb(tb)
            for line in tb_lines:
                lines.append(f"    {line.rstrip()}")

        return '\n'.join(lines)

    def _format_code_context(self, context: Dict[str, Any]) -> str:
        """Format code context showing lines around error"""
        lines = []

        if context.get('exception_file_path') and context.get('exception_line'):
            try:
                file_path = context['exception_file_path']
                error_line = context['exception_line']

                lines.append(f"{self._colors['cyan']}{'─' * 30} Code Context {'─' * 30}{self._colors['reset']}")

                with open(file_path, 'r', encoding='utf-8') as f:
                    file_lines = f.readlines()

                start_line = max(0, error_line - 4)
                end_line = min(len(file_lines), error_line + 3)

                for i in range(start_line, end_line):
                    line_num = i + 1
                    line_content = file_lines[i].rstrip()

                    if line_num == error_line:
                        lines.append(f"  {self._colors['red']}{self._colors['bold']}► {line_num:3d} │ {line_content}{self._colors['reset']}")
                    else:
                        lines.append(f"    {line_num:3d} │ {self._colors['dim']}{line_content}{self._colors['reset']}")

            except Exception:
                lines.append(f"{self._colors['cyan']}Code context unavailable{self._colors['reset']}")

        return '\n'.join(lines) if lines else ""

    def _format_environment_section(self, env_vars: Dict[str, str]) -> str:
        """Format relevant environment variables"""
        lines = []
        lines.append(f"{self._colors['green']}{'─' * 30} Environment {'─' * 30}{self._colors['reset']}")

        for key, value in env_vars.items():
            lines.append(f"🌍 {key} = {self._colors['dim']}{value}{self._colors['reset']}")

        return '\n'.join(lines)

    def _format_bytes(self, bytes_value: int) -> str:
        """Format bytes value to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f}{unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f}TB"

    def _format_duration(self, seconds: float) -> str:
        """Format duration in seconds to human readable format"""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.0f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"


class GlobalExceptionHook:
    """
    Simplified global exception handler that replaces sys.excepthook
    Framework-independent with comprehensive debugging information
    """

    def __init__(self):
        self.config = get_global_config()
        self.original_hook = None
        self.installed = False
        self.lock = threading.Lock()

        # Initialize components
        self.system_collector = SystemInfoCollector()
        self.console_formatter = EnhancedConsoleFormatter(
            colorize=self.config.get('use_colors', True),
            config=self.config
        )
        
        # Get output styling preference
        self.output_style = self.config.get('exception_output_style', 'beautiful')

        # Create backend-aware exception handler
        backend = self.config.get('backend', 'standard')
        self.exception_handler = create_exception_handler_for_backend(backend, self.config)

        # Create logger for exception logging - use lazy import to avoid circular imports
        self.logger = None

    def _get_logger(self):
        """Get logger instance with lazy initialization to avoid circular imports"""
        if self.logger is None:
            # Import here to avoid circular imports
            from .factory import LoggerFactory
            factory = LoggerFactory()
            self.logger = factory.create_logger('global_exception_hook', self.config)
        return self.logger

    def _format_exception_pprint(self, exc_type: Type[BaseException], 
                                exc_value: BaseException, 
                                exc_traceback,
                                system_info: Dict[str, Any], 
                                exception_context: Dict[str, Any]) -> str:
        """Format exception output using pretty-printed JSON style"""
        output_data = {
            "timestamp": datetime.now().isoformat(),
            "exception": {
                "type": exc_type.__name__,
                "message": str(exc_value),
                "location": exception_context.get('exception_location', 'unknown'),
                "function": exception_context.get('exception_function', 'unknown'),
                "module": exception_context.get('exception_module', 'unknown')
            }
        }
        
        # Add local variables if available
        if exception_context.get('exception_locals'):
            formatted_locals = self.console_formatter.data_formatter.format_locals_dict(
                exception_context['exception_locals']
            )
            output_data["exception"]["locals"] = formatted_locals
        
        # Add system info if enabled and available
        if self.config.get('show_system_state', True) and system_info:
            output_data["system_info"] = system_info
            
        # Add stack frames if enabled
        if self.config.get('show_stack_trace', True) and exception_context.get('stack_frames'):
            output_data["stack_frames"] = exception_context['stack_frames']
        
        # Add code context if enabled
        if (self.config.get('show_code_context', True) and 
            exception_context.get('exception_file_path') and 
            exception_context.get('exception_line')):
            try:
                file_path = exception_context['exception_file_path']
                error_line = exception_context['exception_line']
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_lines = f.readlines()
                
                start_line = max(0, error_line - 3)
                end_line = min(len(file_lines), error_line + 2)
                
                code_context = []
                for i in range(start_line, end_line):
                    line_num = i + 1
                    line_content = file_lines[i].rstrip()
                    is_error_line = line_num == error_line
                    code_context.append({
                        "line_number": line_num,
                        "content": line_content,
                        "is_error_line": is_error_line
                    })
                
                output_data["code_context"] = code_context
            except Exception:
                output_data["code_context"] = "unavailable"
        
        # Add environment variables if enabled
        if (self.config.get('show_environment_vars', True) and 
            system_info.get('environment', {}).get('environment_vars')):
            output_data["environment_vars"] = system_info['environment']['environment_vars']
        
        # Format as pretty-printed JSON
        try:
            return json.dumps(output_data, indent=2, separators=(', ', ': '), default=str)
        except Exception:
            # Fallback to basic representation
            return f"Exception formatting failed: {exc_type.__name__}: {exc_value}"

    def install(self):
        """Install the global exception hook"""
        with self.lock:
            if not self.installed:
                self.original_hook = sys.excepthook
                sys.excepthook = self.handle_exception
                self.installed = True

    def uninstall(self):
        """Uninstall the global exception hook"""
        with self.lock:
            if self.installed:
                sys.excepthook = self.original_hook
                self.original_hook = None
                self.installed = False

    def handle_exception(self, exc_type: Type[BaseException], 
                        exc_value: BaseException, 
                        exc_traceback):
        """
        Handle unhandled exceptions with comprehensive debugging information

        Args:
            exc_type: Exception type
            exc_value: Exception instance
            exc_traceback: Traceback object
        """
        try:
            # Always collect system info if enabled
            system_info = {}
            if self.config.get('include_system_info', True):
                system_info = self.system_collector.collect_system_info()

            # Get exception context using existing backend-aware handler
            exc_info = (exc_type, exc_value, exc_traceback)
            exception_context = self.exception_handler.get_exception_context(exc_info)

            # Format output based on style preference
            if self.output_style == 'pprint':
                console_output = self._format_exception_pprint(
                    exc_type, exc_value, exc_traceback, system_info, exception_context
                )
            else:  # 'beautiful' or fallback
                console_output = self.console_formatter.format_comprehensive_output(
                    exc_type, exc_value, exc_traceback, system_info, exception_context
                )

            # Print to stderr for immediate visibility
            print(console_output, file=sys.stderr)
            sys.stderr.flush()

            # Log through the configured backend at specified level
            log_level = self.config.get('exception_hook_level', 'error')
            log_message = f"Unhandled exception: {exc_type.__name__}: {exc_value}"

            # Log with full context
            log_context = {
                **exception_context,
                **({'system_info': system_info} if system_info else {})
            }

            # Use the logger to ensure backend consistency
            logger = self._get_logger()
            getattr(logger, log_level.lower(), logger.error)(
                log_message, 
                exc_info=exc_info,
                **log_context
            )

        except Exception as handler_error:
            # Fallback: don't let our handler break exception handling
            try:
                print(f"GlobalExceptionHook failed: {handler_error}", file=sys.stderr)
                print("Original exception:", file=sys.stderr)
                traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
            except Exception:
                # Ultimate fallback
                pass

        # Exit with error code
        sys.exit(1)


# Module-level instance for singleton pattern
_global_hook_instance: Optional[GlobalExceptionHook] = None


def install_global_exception_hook(config: Dict[str, Any] = None) -> bool:
    """
    Install the global exception hook

    Args:
        config: Optional configuration override

    Returns:
        True if installed successfully
    """
    global _global_hook_instance

    try:
        if _global_hook_instance is None:
            _global_hook_instance = GlobalExceptionHook()

        # Update config if provided
        if config:
            _global_hook_instance.config.update(config)

        _global_hook_instance.install()
        return True
    except Exception:
        return False


def uninstall_global_exception_hook() -> bool:
    """
    Uninstall the global exception hook

    Returns:
        True if uninstalled successfully
    """
    global _global_hook_instance

    try:
        if _global_hook_instance:
            _global_hook_instance.uninstall()
        return True
    except Exception:
        return False


def is_global_exception_hook_installed() -> bool:
    """
    Check if the global exception hook is installed

    Returns:
        True if hook is installed
    """
    global _global_hook_instance
    return _global_hook_instance is not None and _global_hook_instance.installed
