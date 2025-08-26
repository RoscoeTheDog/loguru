# logging_suite/analysis.py
"""
Log analysis tools for cross-platform log filtering and monitoring
"""

import json
import re
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Generator
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict, Counter
import argparse


@dataclass
class LogEntry:
    """Structured representation of a log entry"""
    timestamp: datetime
    level: str
    logger: str
    message: str
    context: Dict[str, Any]
    raw_line: str
    file_path: str
    line_number: int

    @classmethod
    def from_json_line(cls, line: str, file_path: str, line_number: int) -> Optional['LogEntry']:
        """Create LogEntry from JSON log line"""
        try:
            data = json.loads(line.strip())

            # Parse timestamp
            timestamp_str = data.get('timestamp', '')
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except ValueError:
                timestamp = datetime.now()

            # Extract main fields
            level = data.get('level', 'UNKNOWN')
            logger = data.get('logger', 'unknown')
            message = data.get('message', '')

            # Everything else goes into context
            context = {k: v for k, v in data.items()
                       if k not in ['timestamp', 'level', 'logger', 'message']}

            return cls(
                timestamp=timestamp,
                level=level,
                logger=logger,
                message=message,
                context=context,
                raw_line=line.strip(),
                file_path=file_path,
                line_number=line_number
            )
        except json.JSONDecodeError:
            return None


class LogAnalyzer:
    """Cross-platform log analysis and filtering tool"""

    def __init__(self, log_directory: Union[str, Path] = 'logs'):
        """
        Initialize log analyzer

        Args:
            log_directory: Directory containing log files
        """
        self.log_directory = Path(log_directory)
        self.entries: List[LogEntry] = []

    def load_logs(self,
                  pattern: str = "*.log",
                  recursive: bool = True,
                  max_files: int = None) -> int:
        """
        Load log files from directory

        Args:
            pattern: File pattern to match (e.g., "*.log", "error_*.jsonl")
            recursive: Whether to search subdirectories
            max_files: Maximum number of files to process

        Returns:
            Number of log entries loaded
        """
        self.entries.clear()

        if recursive:
            files = self.log_directory.rglob(pattern)
        else:
            files = self.log_directory.glob(pattern)

        files = list(files)
        if max_files:
            files = files[:max_files]

        print(f"Loading logs from {len(files)} files...")

        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        if line.strip():
                            entry = LogEntry.from_json_line(line, str(file_path), line_num)
                            if entry:
                                self.entries.append(entry)
            except Exception as e:
                print(f"Warning: Could not read {file_path}: {e}")

        # Sort by timestamp
        self.entries.sort(key=lambda x: x.timestamp)

        print(f"Loaded {len(self.entries)} log entries")
        return len(self.entries)

    def filter_by_level(self, levels: Union[str, List[str]]) -> 'LogAnalyzer':
        """Filter logs by level(s)"""
        if isinstance(levels, str):
            levels = [levels]

        levels = [level.upper() for level in levels]
        filtered_entries = [entry for entry in self.entries if entry.level.upper() in levels]

        new_analyzer = LogAnalyzer(self.log_directory)
        new_analyzer.entries = filtered_entries
        return new_analyzer

    def filter_by_time_range(self,
                             start_time: Optional[datetime] = None,
                             end_time: Optional[datetime] = None,
                             last_hours: Optional[int] = None,
                             last_minutes: Optional[int] = None) -> 'LogAnalyzer':
        """Filter logs by time range"""
        if last_hours:
            start_time = datetime.now() - timedelta(hours=last_hours)
        elif last_minutes:
            start_time = datetime.now() - timedelta(minutes=last_minutes)

        filtered_entries = []
        for entry in self.entries:
            if start_time and entry.timestamp < start_time:
                continue
            if end_time and entry.timestamp > end_time:
                continue
            filtered_entries.append(entry)

        new_analyzer = LogAnalyzer(self.log_directory)
        new_analyzer.entries = filtered_entries
        return new_analyzer

    def filter_by_message(self, pattern: str, case_sensitive: bool = False) -> 'LogAnalyzer':
        """Filter logs by message content (supports regex)"""
        flags = 0 if case_sensitive else re.IGNORECASE
        regex = re.compile(pattern, flags)

        filtered_entries = [entry for entry in self.entries
                            if regex.search(entry.message)]

        new_analyzer = LogAnalyzer(self.log_directory)
        new_analyzer.entries = filtered_entries
        return new_analyzer

    def filter_by_context(self, key: str, value: Any = None) -> 'LogAnalyzer':
        """Filter logs by context field"""
        filtered_entries = []
        for entry in self.entries:
            if key in entry.context:
                if value is None or entry.context[key] == value:
                    filtered_entries.append(entry)

        new_analyzer = LogAnalyzer(self.log_directory)
        new_analyzer.entries = filtered_entries
        return new_analyzer

    def filter_by_logger(self, logger_pattern: str) -> 'LogAnalyzer':
        """Filter logs by logger name (supports regex)"""
        regex = re.compile(logger_pattern, re.IGNORECASE)

        filtered_entries = [entry for entry in self.entries
                            if regex.search(entry.logger)]

        new_analyzer = LogAnalyzer(self.log_directory)
        new_analyzer.entries = filtered_entries
        return new_analyzer

    def get_error_analysis(self) -> Dict[str, Any]:
        """Analyze error patterns in logs"""
        error_entries = [entry for entry in self.entries
                         if entry.level.upper() in ['ERROR', 'CRITICAL']]

        if not error_entries:
            return {'total_errors': 0}

        # Count errors by type
        error_types = Counter()
        error_messages = Counter()
        error_loggers = Counter()
        error_functions = Counter()

        for entry in error_entries:
            # Exception type from context
            exception_type = entry.context.get('exception_type', 'Unknown')
            error_types[exception_type] += 1

            # Error message patterns
            error_messages[entry.message] += 1

            # Logger names
            error_loggers[entry.logger] += 1

            # Function names from context
            function = entry.context.get('function', 'unknown')
            error_functions[function] += 1

        return {
            'total_errors': len(error_entries),
            'error_rate_per_hour': len(error_entries) / max(1,
                                                            (error_entries[-1].timestamp - error_entries[
                                                                0].timestamp).total_seconds() / 3600),
            'top_error_types': error_types.most_common(10),
            'top_error_messages': error_messages.most_common(10),
            'top_error_loggers': error_loggers.most_common(10),
            'top_error_functions': error_functions.most_common(10),
            'first_error': error_entries[0].timestamp.isoformat(),
            'last_error': error_entries[-1].timestamp.isoformat()
        }

    def get_performance_analysis(self) -> Dict[str, Any]:
        """Analyze performance metrics from logs"""
        # Find entries with execution time
        perf_entries = [entry for entry in self.entries
                        if 'execution_time_seconds' in entry.context]

        if not perf_entries:
            return {'total_timed_operations': 0}

        # Collect execution times
        execution_times = [entry.context['execution_time_seconds']
                           for entry in perf_entries]

        # Group by function
        function_times = defaultdict(list)
        for entry in perf_entries:
            function = entry.context.get('function', 'unknown')
            function_times[function].append(entry.context['execution_time_seconds'])

        # Calculate statistics
        def calculate_stats(times):
            if not times:
                return {}
            return {
                'count': len(times),
                'min': min(times),
                'max': max(times),
                'avg': sum(times) / len(times),
                'total': sum(times)
            }

        overall_stats = calculate_stats(execution_times)

        # Function-specific stats
        function_stats = {}
        for func, times in function_times.items():
            function_stats[func] = calculate_stats(times)

        # Find slow operations (>1 second)
        slow_operations = [entry for entry in perf_entries
                           if entry.context['execution_time_seconds'] > 1.0]

        return {
            'total_timed_operations': len(perf_entries),
            'overall_performance': overall_stats,
            'function_performance': dict(sorted(function_stats.items(),
                                                key=lambda x: x[1].get('avg', 0), reverse=True)),
            'slow_operations_count': len(slow_operations),
            'slowest_operations': [
                {
                    'function': entry.context.get('function', 'unknown'),
                    'execution_time': entry.context['execution_time_seconds'],
                    'timestamp': entry.timestamp.isoformat(),
                    'message': entry.message
                }
                for entry in sorted(slow_operations,
                                    key=lambda x: x.context['execution_time_seconds'],
                                    reverse=True)[:10]
            ]
        }

    def get_activity_summary(self) -> Dict[str, Any]:
        """Get overall activity summary"""
        if not self.entries:
            return {'total_entries': 0}

        # Count by level
        level_counts = Counter(entry.level for entry in self.entries)

        # Count by logger
        logger_counts = Counter(entry.logger for entry in self.entries)

        # Count by hour
        hourly_counts = Counter()
        for entry in self.entries:
            hour_key = entry.timestamp.strftime('%Y-%m-%d %H:00')
            hourly_counts[hour_key] += 1

        # Time range
        start_time = self.entries[0].timestamp
        end_time = self.entries[-1].timestamp
        duration = end_time - start_time

        return {
            'total_entries': len(self.entries),
            'time_range': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat(),
                'duration_hours': duration.total_seconds() / 3600
            },
            'levels': dict(level_counts.most_common()),
            'top_loggers': dict(logger_counts.most_common(10)),
            'activity_by_hour': dict(hourly_counts.most_common(24)),
            'average_logs_per_minute': len(self.entries) / max(1, duration.total_seconds() / 60)
        }

    def print_entries(self,
                      limit: int = 50,
                      format_style: str = 'compact',
                      show_context: bool = True) -> None:
        """Print log entries in various formats"""

        entries_to_show = self.entries[:limit] if limit else self.entries

        print(f"\nShowing {len(entries_to_show)} of {len(self.entries)} log entries:\n")

        for i, entry in enumerate(entries_to_show, 1):
            if format_style == 'compact':
                context_str = ""
                if show_context and entry.context:
                    # Show only important context fields
                    important_fields = ['user_id', 'function', 'action', 'error_type',
                                        'execution_time_seconds', 'status_code']
                    important_context = {k: v for k, v in entry.context.items()
                                         if k in important_fields}
                    if important_context:
                        context_str = f" | {important_context}"

                print(f"{i:3d}. {entry.timestamp.strftime('%H:%M:%S')} "
                      f"{entry.level:8s} {entry.logger:20s} {entry.message}{context_str}")

            elif format_style == 'detailed':
                print(f"{i:3d}. {entry.timestamp.isoformat()}")
                print(f"     Level: {entry.level}")
                print(f"     Logger: {entry.logger}")
                print(f"     Message: {entry.message}")
                if show_context and entry.context:
                    print(f"     Context: {json.dumps(entry.context, indent=8, default=str)}")
                print(f"     File: {entry.file_path}:{entry.line_number}")
                print()

            elif format_style == 'json':
                print(entry.raw_line)

    def export_to_file(self,
                       output_file: str,
                       format_type: str = 'json') -> None:
        """Export filtered logs to file"""

        with open(output_file, 'w') as f:
            if format_type == 'json':
                for entry in self.entries:
                    f.write(entry.raw_line + '\n')
            elif format_type == 'csv':
                import csv
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'level', 'logger', 'message', 'context'])
                for entry in self.entries:
                    writer.writerow([
                        entry.timestamp.isoformat(),
                        entry.level,
                        entry.logger,
                        entry.message,
                        json.dumps(entry.context)
                    ])

        print(f"Exported {len(self.entries)} entries to {output_file}")


def create_log_analyzer_cli():
    """Create command-line interface for log analysis"""

    parser = argparse.ArgumentParser(description='logging_suite Log Analyzer')
    parser.add_argument('--log-dir', default='logs', help='Log directory path')
    parser.add_argument('--pattern', default='*.log', help='File pattern to match')
    parser.add_argument('--level', help='Filter by log level (ERROR, WARNING, etc.)')
    parser.add_argument('--last-hours', type=int, help='Show logs from last N hours')
    parser.add_argument('--message', help='Filter by message pattern (regex)')
    parser.add_argument('--logger', help='Filter by logger name pattern')
    parser.add_argument('--function', help='Filter by function name')
    parser.add_argument('--limit', type=int, default=50, help='Limit number of entries shown')
    parser.add_argument('--format', choices=['compact', 'detailed', 'json'],
                        default='compact', help='Output format')
    parser.add_argument('--export', help='Export results to file')
    parser.add_argument('--analysis', choices=['errors', 'performance', 'summary'],
                        help='Show analysis report')

    return parser


def main():
    """Main CLI entry point"""
    parser = create_log_analyzer_cli()
    args = parser.parse_args()

    # Create analyzer
    analyzer = LogAnalyzer(args.log_dir)

    # Load logs
    analyzer.load_logs(pattern=args.pattern)

    if not analyzer.entries:
        print("No log entries found!")
        return

    # Apply filters
    if args.level:
        analyzer = analyzer.filter_by_level(args.level)

    if args.last_hours:
        analyzer = analyzer.filter_by_time_range(last_hours=args.last_hours)

    if args.message:
        analyzer = analyzer.filter_by_message(args.message)

    if args.logger:
        analyzer = analyzer.filter_by_logger(args.logger)

    if args.function:
        analyzer = analyzer.filter_by_context('function', args.function)

    # Show analysis or entries
    if args.analysis == 'errors':
        analysis = analyzer.get_error_analysis()
        print("\n=== ERROR ANALYSIS ===")
        print(json.dumps(analysis, indent=2, default=str))

    elif args.analysis == 'performance':
        analysis = analyzer.get_performance_analysis()
        print("\n=== PERFORMANCE ANALYSIS ===")
        print(json.dumps(analysis, indent=2, default=str))

    elif args.analysis == 'summary':
        analysis = analyzer.get_activity_summary()
        print("\n=== ACTIVITY SUMMARY ===")
        print(json.dumps(analysis, indent=2, default=str))

    else:
        # Show log entries
        analyzer.print_entries(limit=args.limit, format_style=args.format)

    # Export if requested
    if args.export:
        analyzer.export_to_file(args.export)


if __name__ == '__main__':
    main()