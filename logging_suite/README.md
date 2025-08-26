## 🎛️ Advanced Logging Control# logging_suite

A unified, framework-agnostic logging package with pluggable backends, advanced decorators, and cross-platform analysis tools.

## 🚀 Key Features

- **Multi-Backend Support**: Works with structlog, loguru, or Python's standard logging
- **JSON-First Design**: Structured logging by default for log aggregation
- **Framework Agnostic**: Works with Django, Flask, FastAPI, CLI tools, or any Python application
- **Advanced Decorators**: Exception handling with timing, database operation detection, API logging
- **Cross-Platform Analysis**: Built-in log filtering and analysis tools
- **Backwards Compatibility**: Drop-in replacement for existing logging setups
- **Unified Styling**: Consistent beautiful output across all backends

## 📦 Installation

```bash
# Copy the logging_suite package to your project
cp -r logging_suite/ /path/to/your/project/

# Optional: Install enhanced backends
pip install structlog loguru
```

## 🔧 Quick Start

### Basic Usage

```python
from logging_suite import configure_json_logging, LoggerFactory

# One-line setup
configure_json_logging(level='INFO', console=True)

# Use anywhere in your application
logger = LoggerFactory.create_logger(__name__)
logger.info("Application started", version="1.0", user_count=150)
```

### With Decorators

```python
from logging_suite.decorators import catch_and_log, log_execution_time

@catch_and_log(reraise=True, include_args=True)
@log_execution_time()
def process_payment(amount, payment_method):
    # Automatic exception logging and timing
    return {"status": "success", "amount": amount}
```

### Django Integration

```python
# settings.py
from logging_suite import configure_json_logging

configure_json_logging(
    base_directory='/var/log/django-app',
    level='INFO',
    rotation='50 MB'
)

# models.py  
from logging_suite.mixins import DjangoLoggingMixin

class Order(models.Model, DjangoLoggingMixin):
    # Each order gets individual log file with context
    pass
```

## 🛠️ Configuration

### Development Setup
```python
from logging_suite import configure_development_logging

configure_development_logging()  # Human-readable, colorized output
```

### Production Setup  
```python
from logging_suite import configure_json_logging

configure_json_logging(
    level='WARNING',
    console=False,
    base_directory='/var/log/myapp',
    rotation='100 MB',
    retention='30 days'
)
```

### Custom Backend
```python
from logging_suite import configure_global_logging

configure_global_logging(
    backend='structlog',     # Preferred backend
    level='INFO',
    format='json',
    console=True,
    base_directory='logs'
)
```

## 🎨 Advanced Features

### Exception Decorators with Timing

```python
from logging_suite.decorators import catch_and_log_with_timing

@catch_and_log_with_timing(
    reraise=True,
    include_args=True,
    sanitize_sensitive=True,
    log_execution_time=True,
    message="Payment processing failed after {execution_time:.3f}s: {exception}"
)
def process_payment(amount, payment_method, card_token=None):
    # Function logic here
    # Timing captured even when exceptions occur
    pass
```

### Smart Database Operation Detection

```python
from logging_suite.decorators import smart_log_database_operations

@smart_log_database_operations(
    detect_db_operations=True,
    log_no_operations=True
)
def calculate_user_score(user_id):
    # This method only does calculations, no database access
    # Decorator will detect and log this appropriately
    return some_calculation()
```

### Mixins for Classes

```python
from logging_suite.mixins import LoggingMixin

class PaymentProcessor(LoggingMixin):
    def process(self, amount):
        self.logger.info("Processing payment", amount=amount)
        # Each instance gets its own logger with context
```

### Smart Decorator Conflict Detection

logging_suite decorators now intelligently detect when mixins are already handling logging to prevent duplication:

```python
from logging_suite.decorators import smart_log_database_operations, log_api_calls
from logging_suite.mixins import DjangoLoggingMixin

class MyService(DjangoLoggingMixin):
    # Decorator detects mixin and skips duplicate logging
    @smart_log_database_operations(detect_existing_logging=True)  # Default: True
    def save_data(self, data):
        self.logger.info("Processing data")  # Mixin handles this
        # DB operations...
    
    @log_api_calls(detect_existing_logging=True)
    def call_api(self, endpoint):
        # Decorator detects mixin logging is active and skips its own logging
        # Mixin will handle the logging instead
        pass

# In logs, you'll see:
# "Skipping DB operation logging for save_data - logging_suite mixin already handles logging"
```

### Intelligent Detection Logic

The decorators check:
1. **Mixin Presence**: Is a logging_suite mixin in the class hierarchy?
2. **Logging Status**: Is mixin logging enabled for this operation?
3. **Conflict Avoidance**: Skip decorator logging if mixin will handle it

```python
# Manual control over conflict detection
@smart_log_database_operations(detect_existing_logging=False)  # Force decorator logging
def always_log_this_operation(self):
    # Decorator will log regardless of mixin presence
    pass

# Mixin logging can be disabled to let decorators take over
service = MyService()
service.disable_logging(all_automatic=True)  # Now decorators will log instead
```

### Smart Decorator Conflict Detection

logging_suite decorators now intelligently detect when mixins are already handling logging to prevent duplication:

```python
from logging_suite.decorators import smart_log_database_operations, log_api_calls
from logging_suite.mixins import DjangoLoggingMixin

class MyService(DjangoLoggingMixin):
    # Decorator detects mixin and skips duplicate logging
    @smart_log_database_operations(detect_existing_logging=True)  # Default: True
    def save_data(self, data):
        self.logger.info("Processing data")  # Mixin handles this
        # DB operations...
    
    @log_api_calls(detect_existing_logging=True)
    def call_api(self, endpoint):
        # Decorator detects mixin logging is active and skips its own logging
        # Mixin will handle the logging instead
        pass

# In logs, you'll see:
# "Skipping DB operation logging for save_data - logging_suite mixin already handles logging"
```

### Intelligent Detection Logic

The decorators check:
1. **Mixin Presence**: Is a logging_suite mixin in the class hierarchy?
2. **Logging Status**: Is mixin logging enabled for this operation?
3. **Conflict Avoidance**: Skip decorator logging if mixin will handle it

```python
# Manual control over conflict detection
@smart_log_database_operations(detect_existing_logging=False)  # Force decorator logging
def always_log_this_operation(self):
    # Decorator will log regardless of mixin presence
    pass

# Mixin logging can be disabled to let decorators take over
service = MyService()
service.disable_logging(all_automatic=True)  # Now decorators will log instead
```


## 📊 Log Analysis Tools

### Programmatic Analysis

```python
from logging_suite.analysis import LogAnalyzer

# Load and filter logs
analyzer = LogAnalyzer('logs')
analyzer.load_logs(pattern="*.log", recursive=True)

# Chain filters
payment_errors = (analyzer
    .filter_by_logger('payment')
    .filter_by_level('ERROR')
    .filter_by_time_range(last_hours=24))

# Get analysis reports
error_analysis = analyzer.get_error_analysis()
performance_analysis = analyzer.get_performance_analysis()

# Export results
payment_errors.export_to_file('payment_errors.jsonl')
```

### Command Line Interface

```bash
# Show all errors from last 2 hours
python -m logging_suite.analysis --level ERROR --last-hours 2

# Performance analysis
python -m logging_suite.analysis --analysis performance

# Find payment-related logs
python -m logging_suite.analysis --logger payment --limit 20

# Search error messages (regex support)
python -m logging_suite.analysis --message "connection.*failed" --level ERROR

# Export filtered results
python -m logging_suite.analysis --level ERROR --export error_report.jsonl
```

## 🔄 Migration from Existing Setups

### From Django Logging

```python
from logging_suite.compatibility import BackwardsCompatibleLogger

# Drop-in replacement that enhances your existing logger
logger = BackwardsCompatibleLogger('myapp', existing_django_config)
logger.info("Enhanced logging", user_id=123, action="login")  # Now works with structured data!
```

### Migration Analysis

```python
from logging_suite.compatibility import migrate_from_django_logging

# Analyze your existing setup
migration_info = migrate_from_django_logging('myproject.settings')
print(migration_info['summary'])  # Shows what will change
print(migration_info['migration_code'])  # Generated code to use
```

## 🎯 Use Cases

### Web API Logging
```python
@log_api_calls()
@catch_and_log(sanitize_sensitive=True)
def login_endpoint(request):
    logger.info("Login attempt", username=request.username)
    # API logic...
```

### Background Jobs
```python
class JobProcessor(LoggingMixin):
    @log_execution_time(threshold_seconds=60)
    @catch_and_log(reraise=False)  # Don't crash job queue
    def process_job(self, job_data):
        self.logger.info("Processing job", job_id=job_data['id'])
        # Job processing...
```

### CLI Tools
```python
@click.command()
@catch_and_log(reraise=False, level='error')
def cli_command(input_file):
    logger = LoggerFactory.create_logger('cli.tool')
    logger.info("Processing file", file=input_file)
    # CLI logic...
```

## 🎛️ Advanced Logging Control

logging_suite provides comprehensive control over automatic logging to prevent conflicts with existing extended models and frameworks.

### Three-Level Control System

#### 1. Global Configuration (Lowest Priority)
```python
from logging_suite.mixins import configure_mixin_logging, disable_automatic_logging

# Master switches for all logging
disable_automatic_logging()  # Turn off everything globally

# Granular global control
configure_mixin_logging(
    enable_automatic_logging=True,
    enable_save_logging=False,      # Disable save logging globally
    enable_delete_logging=True,     # Keep delete logging
    enable_refresh_logging=False,   # Disable refresh logging
    log_level='debug',
    log_performance=True
)
```

#### 2. Class-Level Control (Medium Priority)
```python
from logging_suite.mixins import with_logging_control

# Using decorator
@with_logging_control(disable_save=True, disable_delete=True)
class MyModel(models.Model, DjangoLoggingMixin):
    pass

# Or set directly on class
class MyModel(models.Model, DjangoLoggingMixin):
    _disable_save_logging = True
    _disable_delete_logging = True
    _disable_refresh_logging = False
```

#### 3. Instance-Level Control (Highest Priority)
```python
# Control per instance
model = MyModel()
model.disable_logging(save=True, delete=True, all_automatic=False)
model.enable_logging(refresh=True)

# Check current settings
should_log = model._should_log_operation('save')  # Returns False
```

#### 4. Method-Level Control (Per-Call Override)
```python
# Disable logging for specific method calls
model.save(disable_logging=True)
model.delete(disable_logging=True, log_level='error')
model.refresh_from_db(disable_logging=True)

# Add custom context
model.save(log_level='debug', log_custom_field='value')
```

### Automatic Conflict Detection

The `DjangoLoggingMixin` includes intelligent conflict detection to prevent double-logging:

```python
# Your existing extended model
class CoreModelExtended(models.Model):
    def save(self, *args, **kwargs):
        # Custom save logic with logging
        super().save(*args, **kwargs)

# logging_suite integration - auto-detects conflicts
class MyModel(CoreModelExtended, DjangoLoggingMixin):
    pass

# DjangoLoggingMixin automatically detects CoreModelExtended's custom methods
# and disables conflicting logging to prevent double-logging
```

### Conflict Analysis Tool

```python
from logging_suite.mixins import check_logging_conflicts

conflicts = check_logging_conflicts(MyExtendedModel)
print(conflicts)
# {
#   'has_custom_save': True,
#   'has_custom_delete': True, 
#   'detected_extensions': ['CoreModelExtended.save()', 'CoreModelExtended.delete()'],
#   'recommendations': [
#     'Disable save logging: instance.disable_logging(save=True)',
#     'Disable delete logging: instance.disable_logging(delete=True)'
#   ]
# }
```

### Integration Examples

#### With Existing Extended Models
```python
# Your existing model with custom save/delete/refresh
class Deal(CoreModelExtended):
    # Already has enhanced save/delete/refresh with callbacks and event tracking
    pass

# Enhanced with logging_suite (auto-detects conflicts)
class Deal(CoreModelExtended, DjangoLoggingMixin):
    pass

# Usage - logging_suite logging is automatically disabled for save/delete/refresh
deal = Deal()
deal.logger.info("Processing deal", deal_id=deal.id, amount=1000)

# Uses CoreModelExtended's implementation (no double logging)
deal.save(
    save_callback=my_callback,
    custom_event_callback=my_event_callback,
    track_events=True
)

# logging_suite logger still available for manual logging
deal.logger.info("Deal processing completed", success=True)
```

#### Environment-Specific Configuration
```python
# settings.py
from logging_suite.mixins import configure_mixin_logging

if DEBUG:
    # Development: Enable all logging for debugging
    configure_mixin_logging(
        enable_automatic_logging=True,
        log_level='debug',
        log_performance=True
    )
else:
    # Production: Minimal automatic logging
    configure_mixin_logging(
        enable_automatic_logging=False,  # Disable auto-logging
        log_level='error'
    )
```

#### Performance-Critical Sections
```python
class HighVolumeModel(models.Model, DjangoLoggingMixin):
    def bulk_process(self, items):
        # Temporarily disable logging for bulk operations
        self.disable_logging(all_automatic=True)
        
        for item in items:
            self.save()  # No logging overhead
        
        # Re-enable for important operations
        self.enable_logging(all_automatic=True)
        self.logger.info("Bulk processing completed", processed=len(items))
```

## 📈 Analysis Capabilities

### Error Analysis
- Error rates and trends over time
- Top error types and messages
- Most error-prone functions and loggers
- Error distribution analysis

### Performance Analysis
- Function execution time statistics
- Slowest operations identification
- Performance trends over time
- Bottleneck detection

### Activity Analysis
- Log volume and patterns
- Logger activity distribution
- Time-based activity analysis
- Service health monitoring

## 🌐 Cross-Platform Compatibility

**Works on:**
- ✅ Windows (PowerShell, CMD)
- ✅ macOS (Terminal, zsh, bash)
- ✅ Linux (bash, zsh, fish)
- ✅ Docker containers
- ✅ CI/CD environments
- ✅ Jupyter notebooks

**No Dependencies on:**
- ❌ `cat`, `grep`, `awk`, `sed`
- ❌ `jq` or JSON command-line tools
- ❌ Unix-specific utilities

## 🧪 Testing Your Integration

```python
def test_logging_integration():
    from logging_suite import LoggerFactory, get_available_backends
    
    # Check available backends
    backends = get_available_backends()
    print(f"Available backends: {backends}")
    
    # Test each backend
    for backend in backends:
        logger = LoggerFactory.create_logger(f'test.{backend}', backend)
        logger.info("Test message", backend=backend, test=True)
        print(f"✅ {backend} backend working")
    
    print("🎉 logging_suite integration verified!")

test_logging_integration()
```

## 📚 API Reference

### Core Functions
```python
# Configuration
configure_json_logging(level, console, base_directory, rotation, retention)
configure_development_logging()  # Human-readable setup
configure_production_logging()   # JSON, file-only setup

# Logger Creation
LoggerFactory.create_logger(name, backend=None, config=None)
get_available_backends()  # ['standard', 'structlog', 'loguru']

# Backwards Compatibility
BackwardsCompatibleLogger(name, existing_config)
migrate_from_django_logging(settings_module)
```

### Decorators
```python
@catch_and_log(reraise=True, level='error')  # Simple exception logging
@catch_and_log_with_timing(...)  # Full-featured with timing
@log_execution_time(threshold_seconds=1.0)
@log_api_calls()  # API endpoint logging
@smart_log_database_operations()  # Smart DB detection
```

### Mixins
```python
class MyModel(LoggingMixin):           # Generic mixin
class MyDjangoModel(DjangoLoggingMixin):  # Django-specific mixin

# Usage
instance.logger.info("Message", key=value)
instance.bind_logger_context(user_id=123)
```

## 🔍 Log Format Examples

### JSON Output (Default)
```json
{
  "timestamp": "2024-06-21T10:30:45.123",
  "level": "INFO",
  "logger": "payment.processor",
  "message": "Payment processed successfully",
  "transaction_id": "txn_123",
  "amount": 99.99,
  "user_id": 456,
  "execution_time_seconds": 0.234
}
```

### Console Output (Development)
```
10:30:45 ✅ INFO     payment.processor: Payment processed successfully
  Context: transaction_id=txn_123 | amount=99.99 | execution_time_seconds=0.234s
```

## 📋 Complete Example

```python
from logging_suite import configure_json_logging, LoggerFactory
from logging_suite.decorators import catch_and_log, log_execution_time
from logging_suite.mixins import LoggingMixin

# Configure globally
configure_json_logging(level='INFO', console=True, base_directory='logs')

# Service class with logging
class PaymentService(LoggingMixin):
    
    @catch_and_log(reraise=True, include_args=True, sanitize_sensitive=True)
    @log_execution_time()
    def process_payment(self, amount, card_token):
        self.logger.info("Processing payment", amount=amount)
        
        # Payment processing logic
        if amount <= 0:
            raise ValueError("Invalid amount")
        
        # Simulate processing
        import time
        time.sleep(0.1)
        
        transaction_id = f"txn_{int(time.time())}"
        self.logger.info("Payment completed", 
                        transaction_id=transaction_id,
                        success=True)
        
        return {"transaction_id": transaction_id, "status": "completed"}

# Usage
service = PaymentService()
try:
    result = service.process_payment(99.99, "card_token_123")
    print(f"Success: {result}")
except Exception as e:
    print(f"Failed: {e}")

# Analyze logs
from logging_suite.analysis import LogAnalyzer
analyzer = LogAnalyzer('logs')
analyzer.load_logs()
performance = analyzer.get_performance_analysis()
print(f"Average execution time: {performance['overall_performance']['avg']:.3f}s")
```

## 🤝 Contributing

logging_suite is designed to be self-contained and framework-agnostic. To extend or modify:

1. **Add new backends**: Implement `LoggingBackend` interface
2. **Add new decorators**: Follow existing patterns in `decorators.py`
3. **Enhance analysis**: Extend `LogAnalyzer` class
4. **Improve styling**: Modify `UnifiedConsoleFormatter`

## 📄 License

MIT License - Use freely in commercial and open-source projects.

## 🎯 Why logging_suite?

- **One API, Multiple Backends**: Write once, run with any logging library
- **Production Ready**: JSON structured logging with rotation and retention
- **Developer Friendly**: Beautiful console output with colors and symbols
- **Framework Agnostic**: Works with Django, Flask, FastAPI, CLI tools, anything
- **Zero Lock-in**: Gradual adoption, backwards compatible
- **Rich Analysis**: Built-in tools for log analysis and monitoring
- **Cross-Platform**: Pure Python, works everywhere

Your logging is now future-proof and framework-agnostic! 🚀