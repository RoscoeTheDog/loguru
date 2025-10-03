"""
Simple programmatic API for log analysis and metrics collection.

This module provides an easy-to-use interface for analyzing loguru logs
without requiring CLI knowledge.
"""

from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from ._log_analyzer import LogAnalyzer, LogMetrics, LogReporter


def analyze_log_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Analyze a single log file and return comprehensive metrics.
    
    Args:
        file_path: Path to the log file (JSON or text format)
        
    Returns:
        Dictionary containing analysis results
        
    Example:
        >>> results = analyze_log_file("app.json")
        >>> print(f"Total entries: {results['total_entries']}")
        >>> print(f"Error rate: {results['error_rate']:.2f}%")
    """
    analyzer = LogAnalyzer()
    metrics = analyzer.analyze_file(file_path)
    
    # Convert to simple dictionary format
    total_entries = sum(metrics.level_counts.values())
    error_count = metrics.level_counts.get('ERROR', 0) + metrics.level_counts.get('CRITICAL', 0)
    
    return {
        'total_entries': metrics.total_entries,
        'level_counts': dict(metrics.level_counts),
        'error_rate': (error_count / total_entries * 100) if total_entries > 0 else 0,
        'time_range': {
            'start': metrics.time_range[0],
            'end': metrics.time_range[1],
            'duration': metrics.time_range[1] - metrics.time_range[0] if all(metrics.time_range) else None
        },
        'top_modules': dict(metrics.modules.most_common(10)),
        'top_functions': dict(metrics.functions.most_common(10)),
        'error_patterns': dict(metrics.error_patterns.most_common(10)),
        'exception_types': dict(metrics.exception_types.most_common(10)),
        'context_fields': dict(metrics.context_fields.most_common(10)),
        'performance': {
            'entries_with_timing': len(metrics.performance_data),
            'avg_duration': sum(metrics.performance_data) / len(metrics.performance_data) if metrics.performance_data else 0,
            'min_duration': min(metrics.performance_data) if metrics.performance_data else 0,
            'max_duration': max(metrics.performance_data) if metrics.performance_data else 0
        },
        'hourly_distribution': dict(metrics.hourly_distribution),
        'daily_distribution': dict(metrics.daily_distribution)
    }


def analyze_log_files(file_paths: List[Union[str, Path]]) -> Dict[str, Any]:
    """
    Analyze multiple log files and return combined metrics.
    
    Args:
        file_paths: List of paths to log files
        
    Returns:
        Dictionary containing combined analysis results
    """
    analyzer = LogAnalyzer()
    metrics = analyzer.analyze_files(file_paths)
    
    total_entries = sum(metrics.level_counts.values())
    error_count = metrics.level_counts.get('ERROR', 0) + metrics.level_counts.get('CRITICAL', 0)
    
    return {
        'total_entries': metrics.total_entries,
        'files_analyzed': len(file_paths),
        'level_counts': dict(metrics.level_counts),
        'error_rate': (error_count / total_entries * 100) if total_entries > 0 else 0,
        'time_range': {
            'start': metrics.time_range[0],
            'end': metrics.time_range[1],
            'duration': metrics.time_range[1] - metrics.time_range[0] if all(metrics.time_range) else None
        },
        'top_modules': dict(metrics.modules.most_common(10)),
        'top_functions': dict(metrics.functions.most_common(10)),
        'error_patterns': dict(metrics.error_patterns.most_common(10)),
        'exception_types': dict(metrics.exception_types.most_common(10)),
        'context_fields': dict(metrics.context_fields.most_common(10)),
        'performance': {
            'entries_with_timing': len(metrics.performance_data),
            'avg_duration': sum(metrics.performance_data) / len(metrics.performance_data) if metrics.performance_data else 0,
            'min_duration': min(metrics.performance_data) if metrics.performance_data else 0,
            'max_duration': max(metrics.performance_data) if metrics.performance_data else 0
        },
        'hourly_distribution': dict(metrics.hourly_distribution),
        'daily_distribution': dict(metrics.daily_distribution)
    }


def get_error_summary(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Get a focused error analysis for a log file.
    
    Args:
        file_path: Path to the log file
        
    Returns:
        Dictionary with error-focused metrics
    """
    analyzer = LogAnalyzer()
    metrics = analyzer.analyze_file(file_path)
    
    total_entries = sum(metrics.level_counts.values())
    error_count = metrics.level_counts.get('ERROR', 0) + metrics.level_counts.get('CRITICAL', 0)
    warning_count = metrics.level_counts.get('WARNING', 0)
    
    return {
        'total_entries': total_entries,
        'error_count': error_count,
        'warning_count': warning_count,
        'error_rate': (error_count / total_entries * 100) if total_entries > 0 else 0,
        'warning_rate': (warning_count / total_entries * 100) if total_entries > 0 else 0,
        'top_error_patterns': dict(metrics.error_patterns.most_common(5)),
        'exception_types': dict(metrics.exception_types),
        'error_modules': {module: count for module, count in metrics.modules.items() if count > 0}
    }


def get_performance_summary(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Get performance-focused analysis for a log file.
    
    Args:
        file_path: Path to the log file
        
    Returns:
        Dictionary with performance metrics
    """
    analyzer = LogAnalyzer()
    metrics = analyzer.analyze_file(file_path)
    
    if not metrics.performance_data:
        return {
            'entries_with_timing': 0,
            'message': 'No performance timing data found in log file'
        }
    
    import statistics
    perf_data = metrics.performance_data
    
    return {
        'entries_with_timing': len(perf_data),
        'total_entries': metrics.total_entries,
        'coverage_rate': (len(perf_data) / metrics.total_entries * 100) if metrics.total_entries > 0 else 0,
        'avg_duration': statistics.mean(perf_data),
        'median_duration': statistics.median(perf_data),
        'min_duration': min(perf_data),
        'max_duration': max(perf_data),
        'std_deviation': statistics.stdev(perf_data) if len(perf_data) > 1 else 0,
        'slow_operations': len([d for d in perf_data if d > 1.0]),  # Operations > 1 second
        'fast_operations': len([d for d in perf_data if d < 0.1]),  # Operations < 100ms
    }


def find_log_patterns(file_path: Union[str, Path], pattern: str) -> List[Dict[str, Any]]:
    """
    Find log entries matching a specific pattern.
    
    Args:
        file_path: Path to the log file
        pattern: Regex pattern to search for
        
    Returns:
        List of matching log entries
    """
    analyzer = LogAnalyzer()
    entries = list(analyzer.filter_entries(file_path, message_pattern=pattern))
    
    return [
        {
            'timestamp': entry.timestamp,
            'level': entry.level,
            'logger': entry.logger_name,
            'message': entry.message,
            'module': entry.module,
            'function': entry.function,
            'line': entry.line,
            'extra': entry.extra
        }
        for entry in entries
    ]


def get_time_distribution(file_path: Union[str, Path], 
                         granularity: str = 'hour') -> Dict[str, int]:
    """
    Get time-based distribution of log entries.
    
    Args:
        file_path: Path to the log file
        granularity: 'hour', 'day', or 'minute'
        
    Returns:
        Dictionary mapping time periods to entry counts
    """
    analyzer = LogAnalyzer()
    metrics = analyzer.analyze_file(file_path)
    
    if granularity == 'hour':
        return dict(metrics.hourly_distribution)
    elif granularity == 'day':
        return dict(metrics.daily_distribution)
    else:
        # For minute granularity, we'd need to modify the metrics collection
        # For now, return hourly as fallback
        return dict(metrics.hourly_distribution)


def generate_report(file_path: Union[str, Path], 
                   report_type: str = 'summary',
                   output_file: Optional[str] = None) -> str:
    """
    Generate a formatted text report.
    
    Args:
        file_path: Path to the log file
        report_type: 'summary', 'time', 'error', 'context', or 'all'
        output_file: Optional file to write report to
        
    Returns:
        Formatted report string
    """
    analyzer = LogAnalyzer()
    metrics = analyzer.analyze_file(file_path)
    reporter = LogReporter(metrics)
    
    report_generators = {
        'summary': reporter.generate_summary,
        'time': reporter.generate_time_analysis,
        'error': reporter.generate_error_analysis,
        'context': reporter.generate_context_analysis
    }
    
    if report_type == 'all':
        reports = [gen() for gen in report_generators.values()]
        report = "\n\n".join(reports)
    else:
        generator = report_generators.get(report_type, reporter.generate_summary)
        report = generator()
    
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
    
    return report


# Convenience functions for common use cases
def quick_stats(file_path: Union[str, Path]) -> str:
    """Get quick statistics as a formatted string."""
    results = analyze_log_file(file_path)
    
    lines = [
        f"Total Entries: {results['total_entries']:,}",
        f"Error Rate: {results['error_rate']:.1f}%",
        f"Time Range: {results['time_range']['start']} to {results['time_range']['end']}",
        f"Top Module: {list(results['top_modules'].keys())[0] if results['top_modules'] else 'N/A'}"
    ]
    
    return " | ".join(lines)


def check_health(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Perform a health check on the log file.
    
    Returns:
        Dictionary with health indicators
    """
    results = analyze_log_file(file_path)
    
    # Define health thresholds
    error_threshold = 5.0  # 5% error rate
    performance_threshold = 1.0  # 1 second average
    
    health_score = 100
    issues = []
    
    # Check error rate
    if results['error_rate'] > error_threshold:
        health_score -= 30
        issues.append(f"High error rate: {results['error_rate']:.1f}%")
    
    # Check performance
    if results['performance']['avg_duration'] > performance_threshold:
        health_score -= 20
        issues.append(f"Slow performance: {results['performance']['avg_duration']:.2f}s avg")
    
    # Check if there are any entries at all
    if results['total_entries'] == 0:
        health_score = 0
        issues.append("No log entries found")
    
    return {
        'health_score': max(0, health_score),
        'status': 'healthy' if health_score >= 80 else 'warning' if health_score >= 60 else 'critical',
        'issues': issues,
        'total_entries': results['total_entries'],
        'error_rate': results['error_rate'],
        'avg_performance': results['performance']['avg_duration']
    }