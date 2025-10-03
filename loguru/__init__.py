"""
The Loguru library provides a pre-instanced logger to facilitate dealing with logging in Python.

Just ``from loguru import logger``.
"""

import atexit as _atexit
import sys as _sys

from . import _defaults
from ._logger import Core as _Core
from ._logger import Logger as _Logger

__version__ = "0.7.3"

# Import log analysis functionality
from ._log_metrics import (
    analyze_log_file,
    analyze_log_files,
    get_error_summary,
    get_performance_summary,
    find_log_patterns,
    get_time_distribution,
    generate_report,
    quick_stats,
    check_health
)

__all__ = [
    "logger",
    # Analysis functions
    "analyze_log_file",
    "analyze_log_files", 
    "get_error_summary",
    "get_performance_summary",
    "find_log_patterns",
    "get_time_distribution",
    "generate_report",
    "quick_stats",
    "check_health"
]

logger = _Logger(
    core=_Core(),
    exception=None,
    depth=0,
    record=False,
    lazy=False,
    colors=False,
    raw=False,
    capture=True,
    patchers=[],
    extra={},
)

if _defaults.LOGURU_AUTOINIT and _sys.stderr:
    logger.add(_sys.stderr)

_atexit.register(logger.remove)
