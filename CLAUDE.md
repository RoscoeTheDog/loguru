# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Loguru is a Python logging library that aims to bring enjoyable logging to Python. It provides a single, pre-configured logger that simplifies the logging setup process while offering powerful features like structured logging, file rotation, exception catching, and enhanced debugging capabilities.

## Development Commands

### Environment Setup
```bash
# Install development dependencies
pip install -e ".[dev]"
```

### Testing
```bash
# Run all tests with coverage
pytest -vv --cov loguru/ --cov-report=
coverage report -m
coverage xml

# Run tests via tox (recommended)
tox -e tests

# Run a single test file
pytest tests/test_specific.py

# Run a specific test
pytest tests/test_specific.py::test_function_name
```

### Linting and Code Quality
```bash
# Run all linting checks
tox -e lint

# Run pre-commit hooks manually
pre-commit run --show-diff-on-failure --all-files

# Run individual linters
black .                    # Format code
ruff check --fix .         # Lint and fix issues
typos                      # Check spelling
```

### Documentation
```bash
# Build documentation
tox -e docs

# Or directly with Sphinx
sphinx-build -a -b html -W --keep-going docs/ docs/build
```

### Building and Packaging
```bash
# Build package and check
tox -e build

# Or manually
python -m build .
twine check --strict dist/*
```

## Code Architecture

### Core Components

- **`_logger.py`**: Contains the `Logger` and `Core` classes - the heart of Loguru's functionality
- **`_handler.py`**: Implements the `Handler` class that manages different sink types and formatting
- **`__init__.py`**: Exposes the pre-configured global `logger` instance

### Key Internal Modules

- **`_file_sink.py`**: File-based logging with rotation, retention, and compression
- **`_colorizer.py`**: ANSI color formatting for terminal output  
- **`_better_exceptions.py`**: Enhanced exception formatting with variable values
- **`_string_parsers.py`**: Log message parsing functionality
- **`_filters.py`**: Message filtering logic
- **`_locks_machinery.py`**: Thread-safety mechanisms
- **`_datetime.py`**: Date/time handling utilities
- **`_defaults.py`**: Default configuration values

### Architecture Pattern

Loguru follows a centralized logging pattern with a single global logger instance that dispatches messages to multiple configured handlers (called "sinks"). Each handler can format messages differently and apply various options like filtering, colorization, serialization, etc.

The `Core` class manages handler registration/removal and message dispatch, while the `Logger` class provides the public API for logging operations.

## Testing Strategy

- **Unit tests**: Located in `tests/` directory with comprehensive coverage
- **Exception testing**: Special test cases in `tests/exceptions/` with source/output comparisons
- **Type safety**: Tests in `tests/typesafety/` for mypy validation
- **Platform testing**: Tests run across multiple Python versions (3.5-3.14) and PyPy

## Code Style Guidelines

- **Line length**: 100 characters (configured in pyproject.toml)
- **Formatting**: Black with target Python 3.5 compatibility
- **Docstring style**: NumPy convention
- **Import order**: Handled by ruff
- **Type hints**: Defined in `__init__.pyi` stub file

## Key Development Notes

- Type checking is disabled in pyproject.toml due to stub file limitations
- Exception test outputs are compared against expected files in `tests/exceptions/output/`
- The library maintains compatibility with Python 3.5+ including PyPy
- Pre-commit hooks enforce code quality and consistency
- Development requires relatively recent Python version due to tooling dependencies

## Token-Efficient Implementation Strategy

### Core Principles for Large Feature Development

**Batch Operations for Efficiency**
```bash
# Use parallel tool calls to minimize context switching
Read file1.py + Read file2.py + Read file3.py  # Single response
Glob "**/*template*" + Grep "class.*Formatter"  # Combined discovery
```

**Strategic File Access Pattern**
```bash
# Phase 1: Discovery
Glob **/*.py | head -10                    # Find relevant files
Grep "key_pattern" --files-with-matches    # Target specific functionality

# Phase 2: Focused Reading
Read essential_file.py --offset=100 --limit=50  # Read only needed sections
```

**Modular Development Approach**
- Work in isolated, self-contained phases
- Complete one component fully before moving to next
- Use TodoWrite to maintain context between sessions
- Reference existing code via `file_path:line_number` patterns

**Minimal Integration Strategy**
- Create new files rather than heavily modifying existing ones
- Extend classes rather than changing them
- Use composition over inheritance
- Add new methods rather than altering existing functionality

### Implementation Phase Budget

**Phase 1: Core Infrastructure (~15k tokens)**
- Focus on isolated template engine development
- No loguru dependencies during initial development
- Self-contained testing and validation

**Phase 2: Integration (~20k tokens)**
- Read only essential loguru files (`_handler.py`, `_logger.py`)
- Minimal modification approach with extension patterns
- Targeted integration point testing

**Phase 3: Testing & Polish (~10k tokens)**
- Focused test creation for new functionality
- Targeted bug fixes and performance optimization
- Documentation updates

**Total Estimated Budget: ~45k tokens vs 100k+ without optimization**

### File Organization for Token Efficiency

**New Files (Minimal loguru modifications)**
```
loguru/
├─ _templates.py          # New: Template engine core
├─ _template_formatters.py # New: Template-aware formatters
├─ _style_manager.py      # New: Style configuration system
└─ _logger.py             # Modify: Add new methods only
```

**Development Session Structure**
- Day 1-2: Template foundation (single focused session)
- Day 3-4: Integration (read essential files once, implement)
- Day 5: Polish & test (focused validation)

### Key Success Metrics
- Linear token usage rather than exponential
- Each session builds on previous work without re-reading context
- Complete functionality delivered within 60k token budget
- Maintainable, well-structured codebase

### Progress Tracking Protocol

**For Long-Term Implementation Projects:**
- Maintain a `plan.md` file in the project root to track implementation progress
- Update the plan.md file at each milestone with:
  - **Completed phases**: Mark with status and compress into concise summaries
  - **Key decisions made**: Document architectural choices and patterns discovered
  - **Token usage actuals**: Update estimates based on real implementation costs
  - **Refined future phases**: Adjust upcoming work based on lessons learned
  - **Context for new sessions**: Provide optimized starting points for fresh chat instances

**Plan.md Update Pattern:**
```markdown
## Phase 1: Template Engine Foundation ✅ COMPLETED
- **Status**: Implemented core template system in `_templates.py`
- **Key Decision**: Used composition over inheritance for template flexibility
- **Token Usage**: 12k actual vs 15k estimated
- **Files Created**: `_templates.py` (345 lines), `test_templates.py` (120 lines)
- **Next Session Starting Point**: Begin Phase 2 integration with loguru handlers

## Phase 2: Integration [IN PROGRESS]
- **Current Focus**: Extending loguru formatters with template support
- **Blockers**: None identified
- **Next Steps**: Read `_handler.py:50-150` for formatter integration points
```

This approach ensures continuity across chat sessions and prevents re-implementation of completed work.