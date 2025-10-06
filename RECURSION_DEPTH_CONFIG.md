# Configurable Format String Recursion Depth

## Overview

Loguru's colorizer uses recursion to parse complex format specifications. The recursion depth determines how deeply nested format specs can be processed before raising a "Max string recursion exceeded" error.

## Default Value

**Default:** `20`

This lenient default handles most use cases, including:
- Standard logging messages
- Moderate exception tracebacks
- Nested context data (including very deep nesting)

## Configuration

### Via Environment Variable (Recommended)

Set the `LOGURU_FORMAT_RECURSION_DEPTH` environment variable before importing loguru:

```python
import os
os.environ['LOGURU_FORMAT_RECURSION_DEPTH'] = '50'

from loguru import logger
```

Or via shell:

```bash
export LOGURU_FORMAT_RECURSION_DEPTH=50
python your_script.py
```

### When to Increase

Increase the recursion depth if you encounter:

1. **"Max string recursion exceeded" errors** with complex format specifications
2. **Very deep exception tracebacks** (e.g., recursive function errors with 50+ stack frames)
3. **Highly nested structured logging** with many levels of context data

### Recommended Values

| Use Case | Recommended Value |
|----------|-------------------|
| Standard logging | `200` (default) |
| Reduce for performance | `50` |
| Very deep recursion errors | `500` |
| Extreme edge cases | `1000` |

## Example

```python
import os
os.environ['LOGURU_FORMAT_RECURSION_DEPTH'] = '50'

from loguru import logger
import sys

logger.remove()
logger.add(sys.stderr, format="{time} | {level} | {message}", backtrace=True, diagnose=True)

# This will now handle deeper exception tracebacks
try:
    def recursive_function(n):
        if n > 0:
            return recursive_function(n - 1)
        raise ValueError("Deep recursion example")
    
    recursive_function(40)
except ValueError:
    logger.exception("Caught deep recursion error")
```

## Performance Considerations

- **Lower values** (10-20): Faster parsing, less memory usage
- **Higher values** (50-200): Slower parsing, more memory usage, handles complex cases

The default of `200` provides lenient handling for edge cases for typical applications.

## Troubleshooting

### Still getting "Max string recursion exceeded"?

1. Check that you set the environment variable **before** importing loguru
2. Verify the value with:
   ```python
   from loguru._defaults import LOGURU_FORMAT_RECURSION_DEPTH
   print(f"Current recursion depth: {LOGURU_FORMAT_RECURSION_DEPTH}")
   ```
3. Try increasing the value to `50` or `100`

### Performance issues?

If logging is slow with very high recursion depths:

1. Reduce the recursion depth if not needed
2. Simplify format specifications
3. Consider using structured logging with `logger.bind()` instead of deeply nested kwargs

## Related

- Issue #1: Original recursion depth bug
- `loguru/_colorizer.py`: Implementation
- `loguru/_defaults.py`: Configuration defaults
