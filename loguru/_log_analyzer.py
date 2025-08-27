"""
Comprehensive log analysis toolkit for loguru.

This module provides powerful log analysis capabilities for both JSON and text
log files, with support for metrics collection, pattern detection, performance
analysis, and trend reporting.
"""

import json
import re
import argparse
import sys
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Iterator, Tuple
from dataclasses import dataclass, field
import statistics


@dataclass
class LogEntry:
    """Structured representation of a log entry."""
    timestamp: datetime
    level: str
    logger_name: str
    message: str
    module: Optional[str] = None
    function: Optional[str] = None
    line: Optional[int] = None
    extra: Dict[str, Any] = field(default_factory=dict)
    exception: Optional[str] = None
    elapsed_seconds: Optional[float] = None
    
    @property
    def level_number(self) -> int:
        """Convert level name to number for comparison."""
        level_map = {
            'DEBUG': 10, 'INFO': 20, 'SUCCESS': 25, 
            'WARNING': 30, 'ERROR': 40, 'CRITICAL': 50
        }
        return level_map.get(self.level, 20)


@dataclass
class LogMetrics:
    """Comprehensive log metrics collection."""
    total_entries: int = 0
    level_counts: Dict[str, int] = field(default_factory=Counter)
    time_range: Tuple[Optional[datetime], Optional[datetime]] = (None, None)
    modules: Dict[str, int] = field(default_factory=Counter)
    functions: Dict[str, int] = field(default_factory=Counter)
    error_patterns: Dict[str, int] = field(default_factory=Counter)
    performance_data: List[float] = field(default_factory=list)
    hourly_distribution: Dict[int, int] = field(default_factory=Counter)
    daily_distribution: Dict[str, int] = field(default_factory=Counter)
    exception_types: Dict[str, int] = field(default_factory=Counter)
    context_fields: Dict[str, int] = field(default_factory=Counter)
    
    def add_entry(self, entry: LogEntry) -> None:
        """Add a log entry to metrics collection."""
        self.total_entries += 1
        self.level_counts[entry.level] += 1
        
        # Update time range
        if self.time_range[0] is None or entry.timestamp < self.time_range[0]:
            self.time_range = (entry.timestamp, self.time_range[1])
        if self.time_range[1] is None or entry.timestamp > self.time_range[1]:
            self.time_range = (self.time_range[0], entry.timestamp)
            
        # Module and function tracking
        if entry.module:
            self.modules[entry.module] += 1
        if entry.function:
            self.functions[entry.function] += 1
            
        # Time distribution
        self.hourly_distribution[entry.timestamp.hour] += 1
        self.daily_distribution[entry.timestamp.strftime('%Y-%m-%d')] += 1
        
        # Performance tracking
        if entry.elapsed_seconds is not None:
            self.performance_data.append(entry.elapsed_seconds)
            
        # Exception tracking
        if entry.exception:
            # Extract exception type from traceback
            exception_match = re.search(r'(\w+Error|\w+Exception): ', entry.exception)
            if exception_match:
                self.exception_types[exception_match.group(1)] += 1
                
        # Error pattern detection
        if entry.level in ['ERROR', 'CRITICAL']:
            # Simple error pattern extraction
            words = re.findall(r'\b[A-Za-z]+\b', entry.message.lower())
            key_words = [w for w in words if len(w) > 3 and w not in ['the', 'and', 'for', 'with', 'from']]
            if key_words:
                pattern = ' '.join(key_words[:3])  # First 3 significant words
                self.error_patterns[pattern] += 1
                
        # Context field tracking
        for field in entry.extra.keys():
            self.context_fields[field] += 1


class LogParser:
    """Parse different log file formats."""
    
    def __init__(self):
        # Common timestamp patterns
        self.timestamp_patterns = [
            r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})',  # YYYY-MM-DD HH:MM:SS
            r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})',  # ISO format
            r'(\d{2}:\d{2}:\d{2})',  # HH:MM:SS only
        ]
        
        # Text log pattern (from demo_output.log format)
        self.text_pattern = re.compile(
            r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \| (\w+)\s* \| ([^|]+) \| (.+)'
        )
    
    def parse_json_file(self, file_path: Path) -> Iterator[LogEntry]:
        """Parse loguru JSON format log file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    data = json.loads(line)
                    record = data.get('record', {})
                    
                    # Parse timestamp
                    time_data = record.get('time', {})
                    if isinstance(time_data, dict) and 'timestamp' in time_data:
                        timestamp = datetime.fromtimestamp(time_data['timestamp'])
                    else:
                        # Fallback parsing
                        time_str = time_data.get('repr', '') if isinstance(time_data, dict) else str(time_data)
                        timestamp = self._parse_timestamp(time_str)
                    
                    # Extract level info
                    level_data = record.get('level', {})
                    level = level_data.get('name', 'INFO') if isinstance(level_data, dict) else str(level_data)
                    
                    # Extract elapsed time
                    elapsed_data = record.get('elapsed', {})
                    elapsed_seconds = elapsed_data.get('seconds') if isinstance(elapsed_data, dict) else None
                    
                    entry = LogEntry(
                        timestamp=timestamp,
                        level=level,
                        logger_name=record.get('name', ''),
                        message=record.get('message', ''),
                        module=record.get('module'),
                        function=record.get('function'),
                        line=record.get('line'),
                        extra=record.get('extra', {}),
                        exception=str(record.get('exception')) if record.get('exception') else None,
                        elapsed_seconds=elapsed_seconds
                    )
                    yield entry
                    
                except json.JSONDecodeError as e:
                    print(f"Warning: Invalid JSON at line {line_num}: {e}", file=sys.stderr)
                    continue
                except Exception as e:
                    print(f"Warning: Error parsing line {line_num}: {e}", file=sys.stderr)
                    continue
    
    def parse_text_file(self, file_path: Path) -> Iterator[LogEntry]:
        """Parse text format log file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    match = self.text_pattern.match(line)
                    if match:
                        timestamp_str, level, logger_name, message = match.groups()
                        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                        
                        entry = LogEntry(
                            timestamp=timestamp,
                            level=level.strip(),
                            logger_name=logger_name.strip(),
                            message=message.strip()
                        )
                        yield entry
                    else:
                        # Try to extract basic info with flexible parsing
                        timestamp = self._extract_timestamp(line)
                        level = self._extract_level(line)
                        
                        if timestamp and level:
                            entry = LogEntry(
                                timestamp=timestamp,
                                level=level,
                                logger_name='unknown',
                                message=line
                            )
                            yield entry
                            
                except Exception as e:
                    print(f"Warning: Error parsing text line {line_num}: {e}", file=sys.stderr)
                    continue
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse timestamp from various formats."""
        # Remove timezone info for simplicity
        timestamp_str = re.sub(r'[+-]\d{2}:\d{2}$', '', str(timestamp_str))
        
        formats = [
            '%Y-%m-%d %H:%M:%S.%f',
            '%Y-%m-%d %H:%M:%S', 
            '%Y-%m-%dT%H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%S',
            '%H:%M:%S'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue
                
        # Fallback to current time
        return datetime.now()
    
    def _extract_timestamp(self, line: str) -> Optional[datetime]:
        """Extract timestamp from line using patterns."""
        for pattern in self.timestamp_patterns:
            match = re.search(pattern, line)
            if match:
                return self._parse_timestamp(match.group(1))
        return None
    
    def _extract_level(self, line: str) -> Optional[str]:
        """Extract log level from line."""
        levels = ['DEBUG', 'INFO', 'SUCCESS', 'WARNING', 'ERROR', 'CRITICAL']
        line_upper = line.upper()
        for level in levels:
            if level in line_upper:
                return level
        return None


class LogAnalyzer:
    """Main log analysis engine."""
    
    def __init__(self):
        self.parser = LogParser()
        self.metrics = LogMetrics()
    
    def analyze_file(self, file_path: Union[str, Path]) -> LogMetrics:
        """Analyze a single log file."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Log file not found: {file_path}")
        
        # Reset metrics
        self.metrics = LogMetrics()
        
        # Determine file type and parse accordingly
        if file_path.suffix == '.json' or self._is_json_format(file_path):
            entries = self.parser.parse_json_file(file_path)
        else:
            entries = self.parser.parse_text_file(file_path)
        
        # Process all entries
        for entry in entries:
            self.metrics.add_entry(entry)
            
        return self.metrics
    
    def analyze_files(self, file_paths: List[Union[str, Path]]) -> LogMetrics:
        """Analyze multiple log files."""
        self.metrics = LogMetrics()
        
        for file_path in file_paths:
            file_path = Path(file_path)
            if not file_path.exists():
                print(f"Warning: File not found: {file_path}", file=sys.stderr)
                continue
                
            try:
                if file_path.suffix == '.json' or self._is_json_format(file_path):
                    entries = self.parser.parse_json_file(file_path)
                else:
                    entries = self.parser.parse_text_file(file_path)
                
                for entry in entries:
                    self.metrics.add_entry(entry)
                    
            except Exception as e:
                print(f"Warning: Error analyzing {file_path}: {e}", file=sys.stderr)
                continue
                
        return self.metrics
    
    def _is_json_format(self, file_path: Path) -> bool:
        """Check if file contains JSON format logs."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                if first_line:
                    json.loads(first_line)
                    return True
        except:
            pass
        return False
    
    def filter_entries(self, 
                      file_path: Union[str, Path],
                      level: Optional[str] = None,
                      start_time: Optional[datetime] = None,
                      end_time: Optional[datetime] = None,
                      message_pattern: Optional[str] = None,
                      module: Optional[str] = None) -> Iterator[LogEntry]:
        """Filter log entries based on criteria."""
        file_path = Path(file_path)
        
        if file_path.suffix == '.json' or self._is_json_format(file_path):
            entries = self.parser.parse_json_file(file_path)
        else:
            entries = self.parser.parse_text_file(file_path)
        
        pattern = re.compile(message_pattern) if message_pattern else None
        
        for entry in entries:
            # Level filter
            if level and entry.level != level:
                continue
                
            # Time range filter
            if start_time and entry.timestamp < start_time:
                continue
            if end_time and entry.timestamp > end_time:
                continue
                
            # Message pattern filter
            if pattern and not pattern.search(entry.message):
                continue
                
            # Module filter
            if module and entry.module != module:
                continue
                
            yield entry


class LogReporter:
    """Generate analysis reports."""
    
    def __init__(self, metrics: LogMetrics):
        self.metrics = metrics
    
    def generate_summary(self) -> str:
        """Generate summary report."""
        lines = []
        lines.append("LOG ANALYSIS SUMMARY")
        lines.append("=" * 50)
        lines.append(f"Total Entries: {self.metrics.total_entries:,}")
        
        if self.metrics.time_range[0] and self.metrics.time_range[1]:
            duration = self.metrics.time_range[1] - self.metrics.time_range[0]
            lines.append(f"Time Range: {self.metrics.time_range[0]} to {self.metrics.time_range[1]}")
            lines.append(f"Duration: {duration}")
        
        lines.append("")
        lines.append("LEVEL DISTRIBUTION:")
        lines.append("-" * 30)
        total = sum(self.metrics.level_counts.values())
        for level, count in sorted(self.metrics.level_counts.items()):
            percentage = (count / total * 100) if total > 0 else 0
            lines.append(f"  {level:>8}: {count:>6,} ({percentage:>5.1f}%)")
        
        if self.metrics.modules:
            lines.append("")
            lines.append("TOP MODULES:")
            lines.append("-" * 20)
            for module, count in self.metrics.modules.most_common(10):
                lines.append(f"  {module}: {count:,}")
        
        if self.metrics.error_patterns:
            lines.append("")
            lines.append("TOP ERROR PATTERNS:")
            lines.append("-" * 25)
            for pattern, count in self.metrics.error_patterns.most_common(5):
                lines.append(f"  {pattern}: {count}")
        
        if self.metrics.performance_data:
            lines.append("")
            lines.append("PERFORMANCE METRICS:")
            lines.append("-" * 25)
            perf_data = self.metrics.performance_data
            lines.append(f"  Entries with timing: {len(perf_data):,}")
            lines.append(f"  Average duration: {statistics.mean(perf_data):.3f}s")
            lines.append(f"  Median duration: {statistics.median(perf_data):.3f}s")
            if len(perf_data) > 1:
                lines.append(f"  Std deviation: {statistics.stdev(perf_data):.3f}s")
            lines.append(f"  Min duration: {min(perf_data):.3f}s")
            lines.append(f"  Max duration: {max(perf_data):.3f}s")
        
        return "\n".join(lines)
    
    def generate_time_analysis(self) -> str:
        """Generate time-based analysis report."""
        lines = []
        lines.append("TIME ANALYSIS")
        lines.append("=" * 30)
        
        if self.metrics.hourly_distribution:
            lines.append("")
            lines.append("HOURLY DISTRIBUTION:")
            lines.append("-" * 25)
            for hour in range(24):
                count = self.metrics.hourly_distribution.get(hour, 0)
                if count > 0:
                    bar = "#" * min(50, count * 50 // max(self.metrics.hourly_distribution.values()))
                    lines.append(f"  {hour:02d}:00 |{bar:<50} {count:,}")
        
        if self.metrics.daily_distribution:
            lines.append("")
            lines.append("DAILY DISTRIBUTION:")
            lines.append("-" * 25)
            for day, count in sorted(self.metrics.daily_distribution.items()):
                lines.append(f"  {day}: {count:,}")
        
        return "\n".join(lines)
    
    def generate_error_analysis(self) -> str:
        """Generate error analysis report."""
        lines = []
        lines.append("ERROR ANALYSIS")
        lines.append("=" * 30)
        
        error_count = self.metrics.level_counts.get('ERROR', 0) + self.metrics.level_counts.get('CRITICAL', 0)
        total = sum(self.metrics.level_counts.values())
        error_rate = (error_count / total * 100) if total > 0 else 0
        
        lines.append(f"Total Errors: {error_count:,}")
        lines.append(f"Error Rate: {error_rate:.2f}%")
        
        if self.metrics.exception_types:
            lines.append("")
            lines.append("EXCEPTION TYPES:")
            lines.append("-" * 20)
            for exc_type, count in self.metrics.exception_types.most_common(10):
                lines.append(f"  {exc_type}: {count}")
        
        if self.metrics.error_patterns:
            lines.append("")
            lines.append("ERROR PATTERNS:")
            lines.append("-" * 20)
            for pattern, count in self.metrics.error_patterns.most_common(10):
                lines.append(f"  {pattern}: {count}")
        
        return "\n".join(lines)
    
    def generate_context_analysis(self) -> str:
        """Generate context field analysis."""
        lines = []
        lines.append("CONTEXT ANALYSIS")
        lines.append("=" * 30)
        
        if self.metrics.context_fields:
            lines.append("")
            lines.append("CONTEXT FIELDS:")
            lines.append("-" * 20)
            for field, count in self.metrics.context_fields.most_common(20):
                lines.append(f"  {field}: {count:,}")
        else:
            lines.append("No context fields found in logs.")
        
        return "\n".join(lines)


def create_cli_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Analyze loguru log files - supports both JSON and text formats",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s demo_output.json                    # Analyze JSON log file
  %(prog)s demo_output.log                     # Analyze text log file  
  %(prog)s *.log *.json                        # Analyze multiple files
  %(prog)s --level ERROR app.json              # Show only ERROR entries
  %(prog)s --pattern "connection.*failed" app.json  # Filter by message pattern
  %(prog)s --summary --time-analysis app.json  # Generate multiple reports
        """
    )
    
    parser.add_argument('files', nargs='+', help='Log files to analyze')
    
    # Analysis options
    parser.add_argument('--level', 
                       choices=['DEBUG', 'INFO', 'SUCCESS', 'WARNING', 'ERROR', 'CRITICAL'],
                       help='Filter by log level')
    
    parser.add_argument('--pattern', help='Filter by message pattern (regex)')
    parser.add_argument('--module', help='Filter by module name')
    
    parser.add_argument('--start-time', type=str,
                       help='Start time (YYYY-MM-DD HH:MM:SS)')
    parser.add_argument('--end-time', type=str,
                       help='End time (YYYY-MM-DD HH:MM:SS)')
    
    # Report options
    parser.add_argument('--summary', action='store_true',
                       help='Generate summary report (default)')
    parser.add_argument('--time-analysis', action='store_true',
                       help='Generate time-based analysis')
    parser.add_argument('--error-analysis', action='store_true',
                       help='Generate error analysis')
    parser.add_argument('--context-analysis', action='store_true',
                       help='Generate context field analysis')
    parser.add_argument('--all-reports', action='store_true',
                       help='Generate all available reports')
    
    parser.add_argument('--output', '-o', help='Output file (default: stdout)')
    
    return parser


def main():
    """CLI entry point."""
    parser = create_cli_parser()
    args = parser.parse_args()
    
    analyzer = LogAnalyzer()
    
    try:
        # Parse time filters
        start_time = None
        end_time = None
        if args.start_time:
            start_time = datetime.strptime(args.start_time, '%Y-%m-%d %H:%M:%S')
        if args.end_time:
            end_time = datetime.strptime(args.end_time, '%Y-%m-%d %H:%M:%S')
        
        # If filters are specified, show filtered entries
        if any([args.level, args.pattern, args.module, start_time, end_time]):
            print("FILTERED LOG ENTRIES")
            print("=" * 50)
            
            for file_path in args.files:
                print(f"\nFile: {file_path}")
                print("-" * 30)
                
                entries = analyzer.filter_entries(
                    file_path,
                    level=args.level,
                    start_time=start_time,
                    end_time=end_time,
                    message_pattern=args.pattern,
                    module=args.module
                )
                
                for entry in entries:
                    print(f"{entry.timestamp} | {entry.level:8} | {entry.logger_name:15} | {entry.message}")
        
        # Generate analysis reports
        metrics = analyzer.analyze_files(args.files)
        reporter = LogReporter(metrics)
        
        # Determine which reports to generate
        reports = []
        if args.all_reports or not any([args.summary, args.time_analysis, args.error_analysis, args.context_analysis]):
            # Default to summary if no specific reports requested
            reports.append(reporter.generate_summary())
        
        if args.all_reports or args.summary:
            reports.append(reporter.generate_summary())
        if args.all_reports or args.time_analysis:
            reports.append(reporter.generate_time_analysis())
        if args.all_reports or args.error_analysis:
            reports.append(reporter.generate_error_analysis())
        if args.all_reports or args.context_analysis:
            reports.append(reporter.generate_context_analysis())
        
        # Output results
        output_content = "\n\n".join(reports)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output_content)
            print(f"Analysis report written to: {args.output}")
        else:
            print(output_content)
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()