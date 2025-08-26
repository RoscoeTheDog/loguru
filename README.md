<p align="center">
    <a href="#readme">
        <img alt="Loguru logo" src="https://raw.githubusercontent.com/Delgan/loguru/master/docs/_static/img/logo.png">
        <!-- Logo credits: Sambeet from Pixabay -->
        <!-- Logo fonts: Comfortaa + Raleway -->
    </a>
</p>
<p align="center">
    <a href="https://pypi.python.org/pypi/loguru"><img alt="Pypi version" src="https://img.shields.io/pypi/v/loguru.svg"></a>
    <a href="https://pypi.python.org/pypi/loguru"><img alt="Python versions" src="https://img.shields.io/badge/python-3.5%2B%20%7C%20PyPy-blue.svg"></a>
    <a href="https://loguru.readthedocs.io/en/stable/index.html"><img alt="Documentation" src="https://img.shields.io/readthedocs/loguru.svg"></a>
    <a href="https://github.com/Delgan/loguru/actions/workflows/tests.yml?query=branch:master"><img alt="Build status" src="https://img.shields.io/github/actions/workflow/status/Delgan/loguru/tests.yml?branch=master"></a>
    <a href="https://codecov.io/gh/delgan/loguru/branch/master"><img alt="Coverage" src="https://img.shields.io/codecov/c/github/delgan/loguru/master.svg"></a>
    <a href="https://app.codacy.com/gh/Delgan/loguru/dashboard"><img alt="Code quality" src="https://img.shields.io/codacy/grade/be7337df3c0d40d1929eb7f79b1671a6.svg"></a>
    <a href="https://github.com/Delgan/loguru/blob/master/LICENSE"><img alt="License" src="https://img.shields.io/github/license/delgan/loguru.svg"></a>
</p>
<p align="center">
    <a href="#readme">
        <img alt="Loguru logo" src="https://raw.githubusercontent.com/Delgan/loguru/master/docs/_static/img/demo.gif">
    </a>
</p>

______________________________________________________________________

**Loguru** is a library which aims to bring enjoyable logging in Python.

Did you ever feel lazy about configuring a logger and used `print()` instead?... I did, yet logging is fundamental to every application and eases the process of debugging. Using **Loguru** you have no excuse not to use logging from the start, this is as simple as `from loguru import logger`.

Also, this library is intended to make Python logging less painful by adding a bunch of useful functionalities that solve caveats of the standard loggers. Using logs in your application should be an automatism, **Loguru** tries to make it both pleasant and powerful.

🎨 **New in this version**: Loguru now includes a **beautiful template-based styling system** with smart context recognition, advanced function tracing, and global exception hooks - all while maintaining 100% backward compatibility. Get gorgeous, informative logs with zero configuration!

<!-- end-of-readme-intro -->

## Installation

```
pip install loguru
```

## Features

- [Ready to use out of the box without boilerplate](#ready-to-use-out-of-the-box-without-boilerplate)
- [No Handler, no Formatter, no Filter: one function to rule them all](#no-handler-no-formatter-no-filter-one-function-to-rule-them-all)
- [Beautiful template-based styling system](#beautiful-template-based-styling-system) 🆕
- [Smart context auto-styling and recognition](#smart-context-auto-styling-and-recognition) 🆕
- [Advanced function tracing and performance monitoring](#advanced-function-tracing-and-performance-monitoring) 🆕
- [Global exception hook integration](#global-exception-hook-integration) 🆕
- [Easier file logging with rotation / retention / compression](#easier-file-logging-with-rotation--retention--compression)
- [Modern string formatting using braces style](#modern-string-formatting-using-braces-style)
- [Exceptions catching within threads or main](#exceptions-catching-within-threads-or-main)
- [Pretty logging with colors](#pretty-logging-with-colors)
- [Asynchronous, Thread-safe, Multiprocess-safe](#asynchronous-thread-safe-multiprocess-safe)
- [Fully descriptive exceptions](#fully-descriptive-exceptions)
- [Structured logging as needed](#structured-logging-as-needed)
- [Lazy evaluation of expensive functions](#lazy-evaluation-of-expensive-functions)
- [Customizable levels](#customizable-levels)
- [Better datetime handling](#better-datetime-handling)
- [Suitable for scripts and libraries](#suitable-for-scripts-and-libraries)
- [Entirely compatible with standard logging](#entirely-compatible-with-standard-logging)
- [Personalizable defaults through environment variables](#personalizable-defaults-through-environment-variables)
- [Convenient parser](#convenient-parser)
- [Exhaustive notifier](#exhaustive-notifier)
- <s>[10x faster than built-in logging](#10x-faster-than-built-in-logging)</s>

## Take the tour

### Ready to use out of the box without boilerplate

The main concept of Loguru is that **there is one and only one** [`logger`](https://loguru.readthedocs.io/en/stable/api/logger.html#loguru._logger.Logger).

For convenience, it is pre-configured and outputs to `stderr` to begin with (but that's entirely configurable).

```python
from loguru import logger

logger.debug("That's it, beautiful and simple logging!")
```

The [`logger`](https://loguru.readthedocs.io/en/stable/api/logger.html#loguru._logger.Logger) is just an interface which dispatches log messages to configured handlers. Simple, right?

### No Handler, no Formatter, no Filter: one function to rule them all

How to add a handler? How to set up logs formatting? How to filter messages? How to set level?

One answer: the [`add()`](https://loguru.readthedocs.io/en/stable/api/logger.html#loguru._logger.Logger.add) function.

```python
logger.add(sys.stderr, format="{time} {level} {message}", filter="my_module", level="INFO")
```

This function should be used to register [sinks](https://loguru.readthedocs.io/en/stable/api/logger.html#sink) which are responsible for managing [log messages](https://loguru.readthedocs.io/en/stable/api/logger.html#message) contextualized with a [record dict](https://loguru.readthedocs.io/en/stable/api/logger.html#record). A sink can take many forms: a simple function, a string path, a file-like object, a coroutine function or a built-in Handler.

Note that you may also [`remove()`](https://loguru.readthedocs.io/en/stable/api/logger.html#loguru._logger.Logger.remove) a previously added handler by using the identifier returned while adding it. This is particularly useful if you want to supersede the default `stderr` handler: just call `logger.remove()` to make a fresh start.

### Beautiful template-based styling system

Loguru now includes a powerful template-based styling system that provides beautiful, hierarchical output with zero configuration. The template system automatically enhances your logs with intelligent styling while maintaining full backward compatibility.

#### Zero-config beautiful output

Simply use loguru as always, and get beautiful styled output automatically:

```python
from loguru import logger

# Beautiful output by default
logger.info("Application started")
logger.bind(user="alice", action="login").info("User logged in")
logger.error("Database connection failed")
```

#### Configure beautiful styling

Use the new `configure_style()` method for quick template-based setup:

```python
# Use built-in templates: "beautiful", "minimal", "classic"
logger.configure_style("beautiful")

# Console and file with different templates
logger.configure_style(
    "beautiful", 
    file_path="app.log", 
    console_level="INFO", 
    file_level="DEBUG"
)
```

#### Independent console and file formatting

Set up dual-stream logging with different templates for each output:

```python
logger.configure_streams(
    console=dict(template="beautiful", level="INFO"),
    file=dict(sink="app.log", template="minimal", level="DEBUG"),
    json=dict(sink="data.jsonl", serialize=True)
)
```

#### Runtime template switching

Switch templates dynamically at runtime:

```python
# Per-message template override
logger.bind(template="minimal").info("Simple output")

# Change default template
handler_id = logger.add(sys.stderr, format="{time} | {level} | {message}")
logger.set_template(handler_id, "beautiful")
```

### Smart context auto-styling and recognition

Loguru's smart context engine automatically detects and styles different types of content in your log messages, making important information stand out without any configuration.

#### Automatic pattern recognition

The system recognizes 15+ context types and applies appropriate styling:

```python
logger.info("User john@example.com logged in from 192.168.1.1")
# Automatically styles: email addresses, IP addresses

logger.info("Processing order #12345 for $1,234.56")
# Automatically styles: order numbers, currency amounts

logger.info("GET /api/users/123 returned 404")
# Automatically styles: HTTP methods, API endpoints, status codes

logger.info("Error in /home/user/app.py at line 42")
# Automatically styles: file paths, line numbers
```

#### Contextual information enhancement

Use context binding to provide rich, styled information:

```python
logger.bind(
    user="alice", 
    ip="10.0.1.100", 
    action="purchase",
    amount="$99.99"
).info("Transaction completed successfully")

# Smart styling automatically applied to context values
```

#### Adaptive learning system

The context engine learns from your usage patterns and improves recognition over time:

```python
from loguru._context_styling import AdaptiveContextEngine

# Engine adapts to your application's specific patterns
engine = AdaptiveContextEngine()
# Learns domain-specific terms and improves styling accuracy
```

### Advanced function tracing and performance monitoring

Loguru provides sophisticated function tracing with pattern matching, performance monitoring, and configurable behavior - perfect for debugging and performance analysis.

#### Basic function tracing

Trace function execution with beautiful, template-styled output:

```python
from loguru._tracing import FunctionTracer

tracer = FunctionTracer(logger, "beautiful")

@tracer.trace
def process_order(order_id, customer_id):
    # Function entry/exit automatically logged with arguments
    return f"Order {order_id} processed for customer {customer_id}"

result = process_order("12345", "alice")
```

#### Pattern-based tracing rules

Configure tracing behavior based on function name patterns:

```python
tracer = FunctionTracer(logger)

# Trace all test functions with full details
tracer.add_rule(
    pattern=r"^test_.*",
    log_args=True,
    log_result=True,
    log_duration=True,
    level="DEBUG"
)

# Disable tracing for private functions
tracer.add_rule(pattern=r"^_.*", enabled=False)

@tracer.trace
def test_user_login():  # Will be traced with full details
    return authenticate_user("alice")

@tracer.trace  
def _helper_function():  # Will not be traced
    return "internal logic"
```

#### Performance monitoring

Monitor function performance with automatic threshold alerts:

```python
from loguru._tracing import PerformanceTracer

perf_tracer = PerformanceTracer(logger)

@perf_tracer.trace_performance(threshold_ms=500)
def slow_database_query():
    # Automatic performance alert if takes > 500ms
    time.sleep(0.6)  # Simulated slow operation
    return "query results"

# Get performance statistics
stats = perf_tracer.get_performance_stats("slow_database_query")
print(f"Average: {stats['avg_ms']}ms, Max: {stats['max_ms']}ms")
```

#### Pre-configured tracers

Use development and production optimized tracers:

```python
from loguru._tracing import create_development_tracer, create_production_tracer

# Development: verbose tracing with full details
dev_tracer = create_development_tracer(logger)

# Production: minimal tracing, performance focused
prod_tracer = create_production_tracer(logger)
```

### Global exception hook integration

Loguru can automatically capture and beautifully format all unhandled exceptions in your application, including those in threads, with template-based styling.

#### Basic exception hook

Install a global exception hook for beautiful error reporting:

```python
from loguru._exception_hook import install_exception_hook

# Install global exception hook with template styling
hook = install_exception_hook(logger, template="beautiful")

# Now all unhandled exceptions are beautifully formatted
def risky_function():
    return 1 / 0  # This will be caught and styled

risky_function()  # Beautiful exception output with context
```

#### Context manager for temporary hooks

Use exception hooks temporarily for specific code blocks:

```python
from loguru._exception_hook import ExceptionContext

with ExceptionContext(logger, "beautiful") as ctx:
    # Any unhandled exception in this block gets beautiful formatting
    risky_operation()
    another_risky_operation()
# Hook automatically removed when exiting context
```

#### Smart exception filtering

Use advanced exception hooks with filtering and context extraction:

```python
from loguru._exception_hook import create_development_hook

# Development hook with enhanced context extraction
dev_hook = create_development_hook(logger)
dev_hook.install()

# Captures local variables and provides rich debugging context
```

#### Thread-aware exception handling

The exception hook system automatically handles both main thread and background thread exceptions:

```python
import threading

# Hook captures exceptions from all threads
hook = install_exception_hook(logger, "beautiful")

def background_task():
    raise ValueError("Background thread error")  # Also captured!

thread = threading.Thread(target=background_task)
thread.start()
thread.join()
```

### Easier file logging with rotation / retention / compression

If you want to send logged messages to a file, you just have to use a string path as the sink. It can be automatically timed too for convenience:

```python
logger.add("file_{time}.log")
```

It is also [easily configurable](https://loguru.readthedocs.io/en/stable/api/logger.html#file) if you need rotating logger, if you want to remove older logs, or if you wish to compress your files at closure.

```python
logger.add("file_1.log", rotation="500 MB")    # Automatically rotate too big file
logger.add("file_2.log", rotation="12:00")     # New file is created each day at noon
logger.add("file_3.log", rotation="1 week")    # Once the file is too old, it's rotated

logger.add("file_X.log", retention="10 days")  # Cleanup after some time

logger.add("file_Y.log", compression="zip")    # Save some loved space
```

### Modern string formatting using braces style

Loguru favors the much more elegant and powerful `{}` formatting over `%`, logging functions are actually equivalent to `str.format()`.

```python
logger.info("If you're using Python {}, prefer {feature} of course!", 3.6, feature="f-strings")
```

### Exceptions catching within threads or main

Have you ever seen your program crashing unexpectedly without seeing anything in the log file? Did you ever notice that exceptions occurring in threads were not logged? This can be solved using the [`catch()`](https://loguru.readthedocs.io/en/stable/api/logger.html#loguru._logger.Logger.catch) decorator / context manager which ensures that any error is correctly propagated to the [`logger`](https://loguru.readthedocs.io/en/stable/api/logger.html#loguru._logger.Logger).

```python
@logger.catch
def my_function(x, y, z):
    # An error? It's caught anyway!
    return 1 / (x + y + z)
```

### Pretty logging with colors

Loguru automatically adds colors to your logs if your terminal is compatible. You can define your favorite style by using [markup tags](https://loguru.readthedocs.io/en/stable/api/logger.html#color) in the sink format.

```python
logger.add(sys.stdout, colorize=True, format="<green>{time}</green> <level>{message}</level>")
```

### Asynchronous, Thread-safe, Multiprocess-safe

All sinks added to the [`logger`](https://loguru.readthedocs.io/en/stable/api/logger.html#loguru._logger.Logger) are thread-safe by default. They are not multiprocess-safe, but you can `enqueue` the messages to ensure logs integrity. This same argument can also be used if you want async logging.

```python
logger.add("somefile.log", enqueue=True)
```

Coroutine functions used as sinks are also supported and should be awaited with [`complete()`](https://loguru.readthedocs.io/en/stable/api/logger.html#loguru._logger.Logger.complete).

### Fully descriptive exceptions

Logging exceptions that occur in your code is important to track bugs, but it's quite useless if you don't know why it failed. Loguru helps you identify problems by allowing the entire stack trace to be displayed, including values of variables (thanks [`better_exceptions`](https://github.com/Qix-/better-exceptions) for this!).

The code:

```python
# Caution, "diagnose=True" is the default and may leak sensitive data in prod
logger.add("out.log", backtrace=True, diagnose=True)

def func(a, b):
    return a / b

def nested(c):
    try:
        func(5, c)
    except ZeroDivisionError:
        logger.exception("What?!")

nested(0)
```

Would result in:

```none
2018-07-17 01:38:43.975 | ERROR    | __main__:nested:10 - What?!
Traceback (most recent call last):

  File "test.py", line 12, in <module>
    nested(0)
    └ <function nested at 0x7f5c755322f0>

> File "test.py", line 8, in nested
    func(5, c)
    │       └ 0
    └ <function func at 0x7f5c79fc2e18>

  File "test.py", line 4, in func
    return a / b
           │   └ 0
           └ 5

ZeroDivisionError: division by zero
```

Note that this feature won't work on default Python REPL due to unavailable frame data.

See also: [Security considerations when using Loguru](https://loguru.readthedocs.io/en/stable/resources/recipes.html#security-considerations-when-using-loguru).

### Structured logging as needed

Want your logs to be serialized for easier parsing or to pass them around? Using the `serialize` argument, each log message will be converted to a JSON string before being sent to the configured sink.

```python
logger.add(custom_sink_function, serialize=True)
```

Using [`bind()`](https://loguru.readthedocs.io/en/stable/api/logger.html#loguru._logger.Logger.bind) you can contextualize your logger messages by modifying the `extra` record attribute.

```python
logger.add("file.log", format="{extra[ip]} {extra[user]} {message}")
context_logger = logger.bind(ip="192.168.0.1", user="someone")
context_logger.info("Contextualize your logger easily")
context_logger.bind(user="someone_else").info("Inline binding of extra attribute")
context_logger.info("Use kwargs to add context during formatting: {user}", user="anybody")
```

It is possible to modify a context-local state temporarily with [`contextualize()`](https://loguru.readthedocs.io/en/stable/api/logger.html#loguru._logger.Logger.contextualize):

```python
with logger.contextualize(task=task_id):
    do_something()
    logger.info("End of task")
```

You can also have more fine-grained control over your logs by combining [`bind()`](https://loguru.readthedocs.io/en/stable/api/logger.html#loguru._logger.Logger.bind) and `filter`:

```python
logger.add("special.log", filter=lambda record: "special" in record["extra"])
logger.debug("This message is not logged to the file")
logger.bind(special=True).info("This message, though, is logged to the file!")
```

Finally, the [`patch()`](https://loguru.readthedocs.io/en/stable/api/logger.html#loguru._logger.Logger.patch) method allows dynamic values to be attached to the record dict of each new message:

```python
logger.add(sys.stderr, format="{extra[utc]} {message}")
logger = logger.patch(lambda record: record["extra"].update(utc=datetime.utcnow()))
```

### Lazy evaluation of expensive functions

Sometime you would like to log verbose information without performance penalty in production, you can use the [`opt()`](https://loguru.readthedocs.io/en/stable/api/logger.html#loguru._logger.Logger.opt) method to achieve this.

```python
logger.opt(lazy=True).debug("If sink level <= DEBUG: {x}", x=lambda: expensive_function(2**64))

# By the way, "opt()" serves many usages
logger.opt(exception=True).info("Error stacktrace added to the log message (tuple accepted too)")
logger.opt(colors=True).info("Per message <blue>colors</blue>")
logger.opt(record=True).info("Display values from the record (eg. {record[thread]})")
logger.opt(raw=True).info("Bypass sink formatting\n")
logger.opt(depth=1).info("Use parent stack context (useful within wrapped functions)")
logger.opt(capture=False).info("Keyword arguments not added to {dest} dict", dest="extra")
```

### Customizable levels

Loguru comes with all standard [logging levels](https://loguru.readthedocs.io/en/stable/api/logger.html#levels) to which [`trace()`](https://loguru.readthedocs.io/en/stable/api/logger.html#loguru._logger.Logger.trace) and [`success()`](https://loguru.readthedocs.io/en/stable/api/logger.html#loguru._logger.Logger.success) are added. Do you need more? Then, just create it by using the [`level()`](https://loguru.readthedocs.io/en/stable/api/logger.html#loguru._logger.Logger.level) function.

```python
new_level = logger.level("SNAKY", no=38, color="<yellow>", icon="🐍")

logger.log("SNAKY", "Here we go!")
```

### Better datetime handling

The standard logging is bloated with arguments like `datefmt` or `msecs`, `%(asctime)s` and `%(created)s`, naive datetimes without timezone information, not intuitive formatting, etc. Loguru [fixes it](https://loguru.readthedocs.io/en/stable/api/logger.html#time):

```python
logger.add("file.log", format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}")
```

### Suitable for scripts and libraries

Using the logger in your scripts is easy, and you can [`configure()`](https://loguru.readthedocs.io/en/stable/api/logger.html#loguru._logger.Logger.configure) it at start. To use Loguru from inside a library, remember to never call [`add()`](https://loguru.readthedocs.io/en/stable/api/logger.html#loguru._logger.Logger.add) but use [`disable()`](https://loguru.readthedocs.io/en/stable/api/logger.html#loguru._logger.Logger.disable) instead so logging functions become no-op. If a developer wishes to see your library's logs, they can [`enable()`](https://loguru.readthedocs.io/en/stable/api/logger.html#loguru._logger.Logger.enable) it again.

```python
# For scripts
config = {
    "handlers": [
        {"sink": sys.stdout, "format": "{time} - {message}"},
        {"sink": "file.log", "serialize": True},
    ],
    "extra": {"user": "someone"}
}
logger.configure(**config)

# For libraries, should be your library's `__name__`
logger.disable("my_library")
logger.info("No matter added sinks, this message is not displayed")

# In your application, enable the logger in the library
logger.enable("my_library")
logger.info("This message however is propagated to the sinks")
```

For additional convenience, you can also use the [`loguru-config`](https://github.com/erezinman/loguru-config) library to setup the `logger` directly from a configuration file.

### Entirely compatible with standard logging

Wish to use built-in logging `Handler` as a Loguru sink?

```python
handler = logging.handlers.SysLogHandler(address=('localhost', 514))
logger.add(handler)
```

Need to propagate Loguru messages to standard `logging`?

```python
class PropagateHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        logging.getLogger(record.name).handle(record)

logger.add(PropagateHandler(), format="{message}")
```

Want to intercept standard `logging` messages toward your Loguru sinks?

```python
class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists.
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message.
        frame, depth = inspect.currentframe(), 0
        while frame:
            filename = frame.f_code.co_filename
            is_logging = filename == logging.__file__
            is_frozen = "importlib" in filename and "_bootstrap" in filename
            if depth > 0 and not (is_logging or is_frozen):
                break
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
```

### Personalizable defaults through environment variables

Don't like the default logger formatting? Would prefer another `DEBUG` color? [No problem](https://loguru.readthedocs.io/en/stable/api/logger.html#env):

```bash
# Linux / OSX
export LOGURU_FORMAT="{time} | <lvl>{message}</lvl>"

# Windows
setx LOGURU_DEBUG_COLOR "<green>"
```

### Convenient parser

It is often useful to extract specific information from generated logs, this is why Loguru provides a [`parse()`](https://loguru.readthedocs.io/en/stable/api/logger.html#loguru._logger.Logger.parse) method which helps to deal with logs and regexes.

```python
pattern = r"(?P<time>.*) - (?P<level>[0-9]+) - (?P<message>.*)"  # Regex with named groups
caster_dict = dict(time=dateutil.parser.parse, level=int)        # Transform matching groups

for groups in logger.parse("file.log", pattern, cast=caster_dict):
    print("Parsed:", groups)
    # {"level": 30, "message": "Log example", "time": datetime(2018, 12, 09, 11, 23, 55)}
```

### Exhaustive notifier

Loguru can easily be combined with the great [`apprise`](https://github.com/caronc/apprise) library (must be installed separately) to receive an e-mail when your program fail unexpectedly or to send many other kind of notifications.

```python
import apprise

# Define the configuration constants.
WEBHOOK_ID = "123456790"
WEBHOOK_TOKEN = "abc123def456"

# Prepare the object to send Discord notifications.
notifier = apprise.Apprise()
notifier.add(f"discord://{WEBHOOK_ID}/{WEBHOOK_TOKEN}")

# Install a handler to be alerted on each error.
# You can filter out logs from "apprise" itself to avoid recursive calls.
logger.add(notifier.notify, level="ERROR", filter={"apprise": False})
```

This can be seamlessly integrated using the [`logprise`](https://github.com/svaningelgem/logprise) library.

<s>

### 10x faster than built-in logging

</s>

Although logging impact on performances is in most cases negligible, a zero-cost logger would allow to use it anywhere without much concern. In an upcoming release, Loguru's critical functions will be implemented in C for maximum speed.

<!-- end-of-readme-usage -->

## New Template System Migration

The new template system is **100% backward compatible** - all existing loguru code continues to work unchanged. You can gradually adopt the new features:

### Instant Enhancement
```python
# Your existing code works unchanged
from loguru import logger
logger.info("This still works exactly as before")

# But now gets beautiful styling automatically with templates enabled
logger.configure_style("beautiful")
logger.info("This now has beautiful styled output!")
```

### Available Templates

- **`beautiful`**: Elegant hierarchical styling with rich colors and Unicode symbols
- **`minimal`**: Clean, minimal styling for production environments  
- **`classic`**: Traditional logging appearance with basic styling

### New API Methods

The template system adds three new optional methods to the Logger class:

- **`configure_style(template, file_path=None, console_level="INFO", file_level="DEBUG")`**: Quick setup with template styling
- **`configure_streams(**streams)`**: Configure multiple output streams with different templates
- **`set_template(handler_id, template_name)`**: Change template for an existing handler

### Performance

The template system is highly optimized with:
- **Caching**: Template results cached to reduce repeated computation
- **Pre-compilation**: Regex patterns compiled once and reused
- **Smart detection**: Minimal overhead when templates are disabled
- **Backward compatibility**: Zero overhead for existing code

## Documentation

- [API Reference](https://loguru.readthedocs.io/en/stable/api/logger.html)
- [Template System Guide](#beautiful-template-based-styling-system) 🆕
- [Function Tracing Guide](#advanced-function-tracing-and-performance-monitoring) 🆕
- [Exception Hook Guide](#global-exception-hook-integration) 🆕
- [Help & Guides](https://loguru.readthedocs.io/en/stable/resources.html)
- [Type hints](https://loguru.readthedocs.io/en/stable/api/type_hints.html)
- [Contributing](https://loguru.readthedocs.io/en/stable/project/contributing.html)
- [License](https://loguru.readthedocs.io/en/stable/project/license.html)
- [Changelog](https://loguru.readthedocs.io/en/stable/project/changelog.html)
