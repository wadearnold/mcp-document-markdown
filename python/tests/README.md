# Test Suite for Python MCP Server

This directory contains tests for the refactored Python-based MCP PDF to Markdown server.

## Test Structure

```
tests/
├── __init__.py
├── README.md              # This file  
├── test_essentials.py     # Core functionality tests
└── test_mcp_server.py     # MCP server handler tests
```

## Running Tests

### Quick Start

```bash
# Run all tests
cd python
../venv/bin/python -m unittest discover tests -v

# Run specific test file  
../venv/bin/python -m unittest tests.test_essentials -v
../venv/bin/python -m unittest tests.test_mcp_server -v
```

### Using Pytest (if installed)

```bash
cd python
../venv/bin/python -m pytest tests/ -v
```

## Test Coverage

Our tests focus on:

1. **Import Validation** - All critical modules can be imported
2. **Component Instantiation** - All classes can be created
3. **MCP Handler Integration** - Server handlers work correctly
4. **Library Compatibility** - Required dependencies are available

## Test Philosophy

After the major refactor from Go+embedded Python to pure Python, we focus on:

- **Integration over Unit Tests** - Ensuring components work together
- **Import Health Checks** - The biggest risk is broken imports after refactoring
- **MCP Handler Functionality** - The user-facing API must work
- **Mocked Heavy Operations** - PDF processing is mocked for speed

This approach ensures the refactored system works while maintaining fast test execution.