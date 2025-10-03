# Loguru Examples

This directory contains demonstration scripts showcasing Loguru's advanced features including template-based styling, hierarchical logging, exception hooks, and function tracing.

## Prerequisites

For Windows users, install the required dependency:
```bash
pip install win32-setctime
```

For full development setup:
```bash
pip install -e ".[dev]"
```

## Available Examples

### 1. Hierarchical Logging Demo (`hierarchical_logging_demo.py`)

Demonstrates the hierarchical template styling system with context-aware formatting.

**Features shown:**
- Multi-level hierarchical formatting
- Automatic context detection and styling
- Parent-child relationship visualization
- Smart indentation and visual hierarchy

**Run:**
```bash
python examples/hierarchical_logging_demo.py
```

**Expected output:**
- Beautifully formatted hierarchical log messages
- Visual distinction between different logging levels
- Color-coded context sections

---

### 2. Template Styling Demo (`template_styling_demo.py`)

Shows template-based styling with custom format functions.

**Features shown:**
- Custom template creation
- Style rules and formatters
- Template registry usage
- Dynamic styling based on log context

**Run:**
```bash
python examples/template_styling_demo.py
```

**Expected output:**
- Various styled log messages
- Custom format applications
- Template switching demonstrations

---

### 3. Exception Hook Demo (`exception_hook_demo.py`)

Demonstrates global exception hook integration for uncaught exceptions.

**Features shown:**
- Automatic uncaught exception logging
- Enhanced exception formatting
- Stack trace integration
- Context preservation during crashes

**Run:**
```bash
python examples/exception_hook_demo.py
```

**Expected behavior:**
- Script will intentionally raise an exception
- Exception will be caught by Loguru's global hook
- Enhanced exception details will be logged before exit

---

### 4. Caught Exception Demo (`caught_exception_demo.py`)

Shows how Loguru handles explicitly caught exceptions with context.

**Features shown:**
- Exception logging with `logger.exception()`
- Variable inspection in exception context
- Stack trace formatting
- Exception chaining

**Run:**
```bash
python examples/caught_exception_demo.py
```

**Expected behavior:**
- Exceptions are caught and logged gracefully
- Full context and variable states are preserved
- Application continues after handled exceptions

---

## Common Patterns

### Basic Template Usage
```python
from loguru import logger
from loguru._templates import TemplateRegistry

# Register a custom template
registry = TemplateRegistry()
registry.register_template("my_template", format_function)

# Configure logger with template
logger.configure(handlers=[{"sink": sys.stdout, "template": "my_template"}])
```

### Hierarchical Logging
```python
from loguru._template_formatters import create_hierarchical_format_function

formatter = create_hierarchical_format_function(
    level_styles={
        "INFO": {"color": "blue", "indent": 2},
        "ERROR": {"color": "red", "indent": 0}
    }
)
```

### Exception Hook Installation
```python
from loguru._exception_hook import install_exception_hook

# Install global exception hook
install_exception_hook(logger)

# Now all uncaught exceptions will be logged
```

## Troubleshooting

**Import errors:**
- Ensure you're running from the repository root
- Install loguru in development mode: `pip install -e .`

**Windows file time issues:**
- Install: `pip install win32-setctime`

**Color display issues:**
- Install colorama: `pip install colorama` (should be automatic on Windows)
- Some terminals may not support ANSI colors

## Further Documentation

See `/docs/implementation/` for detailed implementation guides:
- `template_system.md` - Template API reference
- `hierarchical_logging.md` - Hierarchical formatting details
- `features_complete.md` - Complete feature overview

## Questions or Issues?

Refer to the main README.md or open an issue on the Loguru repository.
