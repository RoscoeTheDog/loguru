# Hierarchical Templating Implementation Guide

*A comprehensive guide for implementing complex hierarchical logging templates with box-drawing characters*

## 🎯 Project Overview

This document outlines the key challenges, solutions, and lessons learned while implementing the hierarchical templating system for loguru. The goal was to port the beautiful box-drawing hierarchical output from the `logging_suite` library into loguru's templating framework.

**Expected Output:**
```
┌─ 12:34:56 │ 📋 INFO │ my_module
├─ User alice@example.com logged in successfully
├─ Context:
│  ├─ user_id: alice123
│  ├─ session_id: sess_abc123
│  ├─ duration: 45.0ms
│  └─ ip: 192.168.1.100
└──────────────────────────────────────────────────
```

## 🚧 Major Implementation Challenges

### 1. **Loguru Markup Compatibility**

**Problem:** Loguru has very specific markup requirements that differ from standard HTML-like tags.

**Issues Encountered:**
- Compound styles like `<bold blue>` are **invalid** in loguru
- Nested markup like `<blue><underline>text</underline></blue>` causes parsing errors
- Complex styles must be simplified to single attributes

**Solution:**
```python
# ❌ WRONG - Causes parsing errors
level_display = f"<bold blue>{level_name}</bold blue>"

# ✅ CORRECT - Single valid loguru color
level_display = f"<blue>{level_name}</blue>"
```

**Key Learning:** Always test markup with `Colorizer.ansify()` to validate compatibility.

### 2. **Template Rule Overlap Issues**

**Problem:** Multiple regex patterns matching the same text created malformed markup.

**Symptoms:**
```python
# Input: "alice@company.com"
# Multiple rules match:
# - Email rule: <cyan>alice@company.com</cyan> 
# - Generic path rule: <white>alice@company.com</white>
# Result: <cyan>alice@company.com<<white>/cyan></white>
```

**Solution:** Implement overlap detection to prevent double-styling:
```python
def _apply_context_styling(self, message: str, context: Dict[str, Any]) -> str:
    processed_ranges = []
    
    for rule in sorted(self.template.style_rules, key=lambda r: r.priority, reverse=True):
        matches = list(rule.pattern.finditer(styled_message))
        for match in reversed(matches):
            start, end = match.span()
            
            # Check for overlaps with already processed ranges
            overlap = any(
                (start < proc_end and end > proc_start)
                for proc_start, proc_end in processed_ranges
            )
            
            if not overlap:
                # Apply styling and track range
                processed_ranges.append((start, end))
```

### 3. **Unicode Box-Drawing Character Handling**

**Problem:** Box-drawing characters caused issues with:
- Terminal encoding (CP1252 vs UTF-8)
- Visual width calculations for footer lines
- Cross-platform compatibility

**Solution:**
```python
# Fixed-width footers to avoid encoding issues
footer_width = 50  # Fixed width instead of calculating from colored text
footer = "└" + "─" * footer_width

# Always use UTF-8 compatible Unicode chars
BOX_CHARS = {
    "top_left": "┌─",
    "middle": "├─", 
    "vertical": "│",
    "bottom": "└─"
}
```

### 4. **Colorizer Double-Processing**

**Problem:** Text was being processed twice - once by our template system and once by loguru's colorizer, causing corruption.

**Symptoms:**
```
┌─ 07:45:52 │ 📋 <bold blue>INFO</bold blue> │ __main__
```

**Root Cause:** Our hierarchical formatter was including raw markup in the final output, but loguru expected this to be processed.

**Solution:** Apply colorization at the end of hierarchical formatting:
```python
def format_record(self, ...):
    # Build hierarchical output with markup
    lines = []
    header = f"┌─ {timestamp} │ {level_symbol} {level_display} │ {logger_display}"
    # ... build rest of output
    
    full_output = '\n'.join(lines)
    
    # Apply colorization once at the end
    return Colorizer.ansify(full_output)
```

### 5. **Template Integration Architecture**

**Problem:** Determining when to use hierarchical formatting vs. standard loguru formatting.

**Challenge:** The hierarchical formatter needed to:
- Integrate seamlessly with loguru's existing formatter system
- Only activate for specific templates
- Fall back gracefully to standard formatting

**Solution:** Template-specific formatter dispatch:
```python
def format_map(self, record: Dict[str, Any]) -> str:
    if self.template.name == "hierarchical":
        # Use specialized hierarchical formatter
        return self.hierarchical_formatter.format_record(...)
    else:
        # Use standard template processing
        return self._standard_template_processing(record)
```

## 🔧 Architecture Decisions

### 1. **Separation of Concerns**

**Files Created:**
- `_hierarchical_formatter.py` - Pure hierarchical formatting logic
- `_template_formatters.py` - Integration with loguru's formatter system
- `_templates.py` - Template definitions and registry

**Rationale:** Keeping hierarchical formatting separate makes it easier to test and maintain.

### 2. **Template Registry Pattern**

```python
BUILT_IN_TEMPLATES = {
    "hierarchical": TemplateConfig(...),
    "minimal": TemplateConfig(...),
    "classic": TemplateConfig(...)
}
```

**Benefits:**
- Easy to add new templates
- Centralized template management
- Consistent template structure

### 3. **Context Priority System**

```python
important_fields = [
    'user_id', 'user', 'username', 'request_id', 'session_id', 
    'action', 'method', 'path', 'status_code', 'response_time',
    'execution_time_seconds', 'duration', 'error_type', 'function'
]
```

**Why:** Ensures the most relevant context information appears first in the hierarchical display.

## ⚠️ Common Pitfalls & Solutions

### 1. **Markup Nesting Violations**
```python
# ❌ WRONG - Nested tags not properly closed
"<blue><underline>text</blue></underline>"

# ✅ CORRECT - Simplified single style
"<blue>text</blue>"
```

### 2. **Template Name Consistency**
- Always use consistent template names across all files
- Use replace-all when renaming templates to avoid missed references
- Test template loading after any name changes

### 3. **Performance Considerations**
```python
# ❌ WRONG - Creates formatter for each message
def format_map(self, record):
    hierarchical_formatter = HierarchicalTemplateFormatter(...)
    return hierarchical_formatter.format_record(...)

# ✅ CORRECT - Reuse formatter instance
def __init__(self, ...):
    self.hierarchical_formatter = HierarchicalFormatter(template)

def format_map(self, record):
    return self.hierarchical_formatter.format_record(...)
```

## 🧪 Testing Strategy

### 1. **Incremental Testing**
- Test markup processing separately from full formatting
- Verify each template rule individually
- Test colorization pipeline in isolation

### 2. **Visual Validation**
Create simple test files to visually verify output:
```python
# test_visual.py
logger.info("Test message", user="alice", ip="192.168.1.1")
# Manually verify box-drawing appears correctly
```

### 3. **Cross-Platform Testing**
- Test on Windows (CP1252 encoding)
- Test on Linux/macOS (UTF-8 encoding)
- Verify Unicode character display

## 📋 Implementation Checklist

When implementing similar hierarchical templates:

- [ ] **Template Definition**
  - [ ] Create TemplateConfig with proper style rules
  - [ ] Test all regex patterns for overlaps
  - [ ] Use simple, single-attribute styles only

- [ ] **Formatter Implementation** 
  - [ ] Separate hierarchical logic from standard formatting
  - [ ] Apply colorization once at the end
  - [ ] Handle Unicode characters carefully

- [ ] **Integration**
  - [ ] Integrate with existing formatter system
  - [ ] Add template-specific dispatch logic
  - [ ] Maintain backward compatibility

- [ ] **Testing**
  - [ ] Test markup processing individually
  - [ ] Visual verification of output
  - [ ] Cross-platform compatibility
  - [ ] Performance benchmarking

- [ ] **Documentation**
  - [ ] Update template registry documentation
  - [ ] Provide usage examples
  - [ ] Document any platform-specific issues

## 🚀 Performance Optimizations

1. **Template Caching**
   ```python
   # Cache compiled templates to avoid repeated processing
   self._template_cache = {}
   ```

2. **Range Overlap Detection**
   ```python
   # Efficient overlap detection for style rules
   processed_ranges = []  # Track styled text ranges
   ```

3. **Fixed-Width Calculations**
   ```python
   # Use fixed widths instead of calculating from colored text
   footer_width = 50  # Avoids ANSI code counting issues
   ```

## 📝 Key Takeaways

1. **Loguru markup is restrictive** - Always validate with `Colorizer.ansify()`
2. **Regex overlap is common** - Implement proper conflict resolution
3. **Unicode requires careful handling** - Test cross-platform compatibility  
4. **Architecture matters** - Separate concerns for maintainability
5. **Visual testing is essential** - Automated tests miss display issues

## 🔍 Debugging Tips

1. **Markup Issues:** Use `repr()` to see raw markup strings
2. **Unicode Problems:** Check terminal encoding settings
3. **Template Loading:** Verify template names are consistent across all files
4. **Performance:** Profile formatter creation vs. message formatting

## 📚 Related Files

- `_hierarchical_formatter.py` - Core hierarchical formatting logic
- `_template_formatters.py` - Loguru integration layer
- `_templates.py` - Template definitions and registry
- `tests/test_template_integration.py` - Integration tests
- `demo_final.py` - Working example and demonstration

---

This guide represents lessons learned from successfully implementing hierarchical templating with Unicode box-drawing characters in a production logging system. Future implementers should reference this document to avoid common pitfalls and achieve faster, more reliable implementations.