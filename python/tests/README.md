# Test Suite for Modular PDF Converter

This directory contains comprehensive tests for the modular PDF converter components.

## Test Structure

```
tests/
├── __init__.py
├── README.md              # This file
├── unit/                  # Unit tests for individual modules
│   ├── __init__.py
│   ├── test_token_counter.py
│   ├── test_text_utils.py
│   ├── test_file_utils.py
│   ├── test_chunking_engine.py
│   └── test_concept_mapper.py
├── integration/           # Integration tests
│   ├── __init__.py
│   └── test_modular_converter.py
└── fixtures/              # Test data and fixtures
```

## Running Tests

### Quick Start

```bash
# Run all tests
python run_tests.py

# Run only unit tests
python run_tests.py --unit

# Run only integration tests  
python run_tests.py --integration

# Run a specific test module
python run_tests.py --test tests.unit.test_token_counter

# Check dependencies before running
python run_tests.py --check-deps
```

### Using Standard unittest

```bash
# Run all tests
python -m unittest discover tests

# Run specific test module
python -m unittest tests.unit.test_token_counter

# Run with verbose output
python -m unittest discover tests -v
```

## Test Categories

### Unit Tests

Test individual modules in isolation:

- **test_token_counter.py**: Token counting, model recommendations, batch processing
- **test_text_utils.py**: Text processing, header detection, markdown handling
- **test_file_utils.py**: File operations, safe filenames, JSON/markdown I/O
- **test_chunking_engine.py**: Content chunking, size optimization, file generation
- **test_concept_mapper.py**: Term extraction, categorization, relationship mapping

### Integration Tests

Test complete workflows and module interactions:

- **test_modular_converter.py**: End-to-end conversion process, file coordination

## Test Coverage

### Utils Module Coverage

| Module | Functions Tested | Coverage |
|--------|------------------|----------|
| TokenCounter | ✅ Token counting<br>✅ Model recommendations<br>✅ Batch processing<br>✅ Section analysis | ~95% |
| TextUtils | ✅ Header detection<br>✅ Code block parsing<br>✅ Table formatting<br>✅ Text cleaning | ~90% |
| FileUtils | ✅ File I/O operations<br>✅ Directory management<br>✅ Safe filename generation<br>✅ Metadata handling | ~95% |

### Processor Module Coverage

| Module | Functions Tested | Coverage |
|--------|------------------|----------|
| ChunkingEngine | ✅ Strategy determination<br>✅ Content splitting<br>✅ File generation<br>✅ Metadata creation | ~85% |
| ConceptMapper | ✅ Term extraction<br>✅ Categorization<br>✅ Relationship building<br>✅ Glossary generation | ~80% |
| CrossReferencer | ⚠️ Basic structure only | ~30% |
| SummaryGenerator | ⚠️ Basic structure only | ~30% |
| PDFExtractor | ⚠️ Requires PyMuPDF | ~20% |
| TableProcessor | ⚠️ Requires pandas/PyMuPDF | ~20% |

## Test Fixtures

Test fixtures and sample data are stored in the `fixtures/` directory:

- Sample PDF content structures
- Mock API responses
- Reference markdown files
- Test configuration files

## Writing New Tests

### Unit Test Template

```python
import unittest
import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from module_to_test import ClassToTest

class TestClassName(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.instance = ClassToTest()
    
    def test_method_name(self):
        """Test specific functionality"""
        result = self.instance.method_to_test()
        self.assertEqual(result, expected_value)

if __name__ == '__main__':
    unittest.main()
```

### Integration Test Template

```python
import unittest
import tempfile
import shutil
from pathlib import Path

class TestIntegration(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        """Clean up test environment"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_workflow(self):
        """Test complete workflow"""
        # Test implementation
        pass
```

## Best Practices

### Test Organization

1. **One test class per module**: Each module should have its own test class
2. **Descriptive test names**: Use `test_verb_noun_condition` format
3. **Setup and teardown**: Use `setUp()` and `tearDown()` for common initialization
4. **Test isolation**: Each test should be independent and not rely on others

### Test Data Management

1. **Use temporary directories**: Create temporary files/directories for tests
2. **Clean up after tests**: Always remove temporary data in `tearDown()`
3. **Mock external dependencies**: Use mocks for external services/files
4. **Small test data**: Keep test data minimal and focused

### Assertion Guidelines

1. **Specific assertions**: Use the most specific assertion available
2. **Clear error messages**: Include meaningful messages in assertions
3. **Test edge cases**: Include tests for boundary conditions and error cases
4. **Positive and negative tests**: Test both success and failure scenarios

## Test Environment

### Dependencies

The test suite requires:

- Python 3.8+
- unittest (built-in)
- tempfile (built-in)
- pathlib (built-in)

Optional dependencies for full coverage:
- PyMuPDF (for PDF extraction tests)
- pandas (for table processing tests)
- tiktoken (for accurate token counting)

### Virtual Environment

Tests should be run within the project's virtual environment:

```bash
# Activate virtual environment
source ../venv/bin/activate  # Linux/Mac
# or
../venv/Scripts/activate     # Windows

# Run tests
python run_tests.py
```

## Continuous Integration

### Test Automation

The test suite is designed to work with CI/CD systems:

```bash
# CI-friendly test command
python run_tests.py --no-summary --verbose 1
```

### Coverage Reports

To generate coverage reports:

```bash
# Install coverage tool
pip install coverage

# Run tests with coverage
coverage run run_tests.py
coverage report
coverage html  # Generate HTML report
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure Python path includes the parent directory
2. **Missing Dependencies**: Run `python run_tests.py --check-deps`
3. **File Permission Errors**: Ensure write permissions in test directory
4. **Temporary Directory Issues**: Check available disk space

### Debug Mode

For detailed debugging:

```bash
# Maximum verbosity
python run_tests.py -vvv

# Run single test with debugging
python -m unittest tests.unit.test_token_counter.TestTokenCounter.test_count_tokens_simple -v
```

### Test Data Issues

If tests fail due to data issues:

1. Check that test fixtures exist
2. Verify file permissions
3. Ensure temporary directories are writable
4. Clear any cached test data

## Contributing

When adding new modules or features:

1. **Write tests first**: Use TDD approach when possible
2. **Maintain coverage**: Aim for >80% coverage on new code
3. **Update documentation**: Add test descriptions to this README
4. **Run full suite**: Ensure all tests pass before committing

### Test Review Checklist

- [ ] Tests cover main functionality
- [ ] Edge cases are tested
- [ ] Error conditions are handled
- [ ] Tests are independent
- [ ] Temporary data is cleaned up
- [ ] Test names are descriptive
- [ ] Documentation is updated