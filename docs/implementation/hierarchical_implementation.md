# Hierarchical Logging Implementation Notes

## Critical Implementation Issues Discovered

### The Newline Spacing Problem

**Issue**: Hierarchical log statements were concatenating without proper separation:
```
└──────────────────────────────────────────────────────────
┌─ 00:20:44 │ 📋 INFO │ __main__
```

**Root Cause**: Loguru strips/modifies trailing newlines from formatter output, causing hierarchical footers to concatenate with subsequent headers.

**Failed Attempts**:
1. ❌ Adding trailing newlines (`\n`, `\n\n`) - Loguru strips them
2. ❌ Adding leading blank lines in content - Inconsistent behavior
3. ❌ Embedding newlines in footer strings - Still stripped
4. ❌ Prepending newlines to formatted output - Worked with template formatters but not format functions

**Final Solution**: ✅ **Format Function Approach**
- Use `create_hierarchical_format_function()` instead of template formatters
- Format functions have complete control over line endings
- Add explicit `\n` line ending in the format function
- This follows loguru's documented pattern where custom formatters "take care of appending the line ending"

### Key Code Changes

**Before (Broken)**:
```python
formatter = create_template_formatter(template="hierarchical")
logger.add(sys.stderr, format=formatter.format_map)
```

**After (Fixed)**:
```python
format_func = create_hierarchical_format_function(template="hierarchical")
logger.add(sys.stderr, format=format_func)
```

**Format Function Implementation**:
```python
def hierarchical_format_function(record):
    # ... format processing ...
    # CRITICAL: Add explicit line ending as required by loguru
    if not formatted_output.endswith('\n'):
        formatted_output += '\n'
    return formatted_output
```

## Common Issues and Solutions

### Loguru Markup Limitations

**Issue**: Compound markup styles don't work
```python
# ❌ WRONG - loguru doesn't support compound styles
return f"<blue underline>{value}</blue underline>"
return f"<dim white>{value}</dim white>"
```

**Solution**: Use simple single styles
```python
# ✅ CORRECT - use single style tags
return f"<blue>{value}</blue>"
return f"<dim>{value}</dim>"
```

### Exception Hook Not Catching Exceptions

**Issue**: Exception hook doesn't catch exceptions that are handled by try/except blocks.

**Wrong**:
```python
try:
    trigger_uncaught_exception()  # This will be caught by except block
except Exception as e:
    print(f"Caught: {e}")  # Hook never gets called
```

**Correct**:
```python
# Let the exception be truly uncaught for the hook to handle it
trigger_uncaught_exception()  # Hook will handle this
```

### Markup Conflicts in Exception Tracebacks

**Issue**: Function names like `<module>` in Python tracebacks create invalid loguru markup tags.

**Error**: `ValueError: Tag "<module>" does not correspond to any known color directive`

**Solution**: Escape angle brackets in function names
```python
# In exception formatting
safe_function = function.replace('<', '&lt;').replace('>', '&gt;')
file_link = f'File "{filename}", line {lineno}, in {safe_function}'
```

**Result**: IDE links still work but markup conflicts are avoided (`&lt;module&gt;`)

## Architecture Decisions

### Why Format Functions Work Better

1. **Complete Control**: Format functions receive the raw record and return final output
2. **No Intermediate Processing**: Loguru doesn't modify the returned string
3. **Explicit Line Endings**: Custom formatters are responsible for line endings
4. **Future-Proof**: Follows loguru maintainer's documented guidance

### Template System Integration

**Hierarchical Formatter Flow**:
```
Record → HierarchicalTemplateFormatter → HierarchicalFormatter → Colorized Output
```

**Key Components**:
- `create_hierarchical_format_function()`: Factory function in `_template_formatters.py`
- `HierarchicalTemplateFormatter`: Bridges loguru records to hierarchical formatting
- `HierarchicalFormatter`: Core hierarchical logic with box-drawing characters
- `Colorizer.ansify()`: Applies loguru markup colorization

## Cache Management

**Issue**: Template changes not taking effect due to caching.

**Solution**: Version-based cache busting:
```python
cache_key = cache_key + ("format_function_v1",)
```

## Best Practices for New Template Styles

### 1. Use Format Functions for Complex Layouts
- Any template with multi-line output should use format functions
- Simple single-line templates can use template formatters
- Format functions prevent loguru's newline processing interference

### 2. Line Ending Strategy
```python
def custom_format_function(record):
    # Build your formatted output
    output = build_complex_format(record)
    
    # ALWAYS add explicit line ending
    if not output.endswith('\n'):
        output += '\n'
    
    return output
```

### 3. Colorization Timing
- Apply loguru markup (`<color>text</color>`) during formatting
- Call `Colorizer.ansify()` at the very end
- Don't mix ANSI codes with loguru markup

### 4. Exception Integration
- Hierarchical templates should handle both regular logs and exceptions
- Use `record.get("exception")` to detect exception context
- Format exceptions with same visual hierarchy as regular logs

## Testing Methodology

**Spacing Verification**:
```python
# Look for clean separation between log blocks
logger.info("First message", field="value1")
logger.info("Second message", field="value2")

# Expected output:
# ┌─ timestamp │ INFO │ name
# ├─ First message
# ├─ Context: field: value1
# └──────────────────────────
# ┌─ timestamp │ INFO │ name  # <- Clean separation here
# ├─ Second message
# ├─ Context: field: value2
# └──────────────────────────
```

## Migration Guide

### From Template Formatters to Format Functions

**Old Code**:
```python
from loguru._template_formatters import create_template_formatter

formatter = create_template_formatter(template="hierarchical")
logger.add(sink, format=formatter.format_map)
```

**New Code**:
```python
from loguru._template_formatters import create_hierarchical_format_function

format_func = create_hierarchical_format_function(template="hierarchical")
logger.add(sink, format=format_func)
```

## Research References

- **Loguru GitHub Issues**: Custom formatters must handle line endings
- **Maintainer Guidance**: "you should take care of appending the line ending"
- **Format Function Pattern**: Documented approach for complex custom formatters

## Implementation Timeline

1. ✅ **Initial Template System**: Template formatters with `.format_map`
2. ❌ **Newline Workarounds**: Multiple failed attempts with prepended/trailing newlines
3. 🔬 **Research Phase**: GitHub issue analysis and loguru behavior study
4. ✅ **Format Function Solution**: Complete rewrite using format function approach
5. ✅ **Cleanup & Documentation**: Remove legacy code and document learnings

This documentation serves as a guide for future template implementations and troubleshooting similar newline/formatting issues.