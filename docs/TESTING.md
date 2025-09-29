# Testing Guide

## Overview

This project uses a streamlined, maintainable testing approach focused on essential functionality. The testing suite has been completely rebuilt to prioritize simplicity, speed, and clarity while maintaining comprehensive coverage of core business logic.

## Quick Start

```bash
# Run all tests (< 30 seconds)
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=term-missing

# Run specific test types
uv run pytest tests/unit/          # Unit tests only
uv run pytest tests/integration/   # Integration tests only
```

## Test Architecture

### Design Principles

1. **Simplicity First**: Minimal configuration and straightforward test structure
2. **Standard Tools**: Uses pytest without custom frameworks
3. **Essential Coverage**: Focus on core business logic and critical paths
4. **Fast Execution**: Optimized for quick feedback cycles
5. **Easy Maintenance**: Clear, readable tests that are easy to modify

### Test Structure

```text
tests/
├── unit/                         # Fast unit tests (< 10 seconds)
│   ├── test_betting_framework.py # Kelly criterion calculations
│   ├── test_commission_manager.py # Commission calculations
│   ├── test_excel_processor.py   # Excel file processing
│   └── test_main.py              # User interface functions
├── integration/                  # Workflow tests (< 20 seconds)
│   ├── test_excel_workflow.py    # Excel processing pipeline
│   └── test_end_to_end.py        # Complete application workflows
├── conftest.py                   # Minimal shared fixtures
└── __init__.py                   # Test package initialization
```

## Test Categories

### Unit Tests (146 tests)

**Purpose**: Test individual functions and classes in isolation

- **test_betting_framework.py** (22 tests): Kelly criterion calculations, contract normalization
- **test_commission_manager.py** (51 tests): Commission calculations, platform management
- **test_excel_processor.py** (30 tests): Excel file processing, data validation
- **test_main.py** (43 tests): User interface functions, input handling

**Execution Time**: < 10 seconds

### Integration Tests (30 tests)

**Purpose**: Test component interactions and complete workflows

- **test_excel_workflow.py** (15 tests): End-to-end Excel processing pipeline
- **test_end_to_end.py** (15 tests): Complete betting calculation workflows

**Execution Time**: < 20 seconds additional

## Testing Commands

### Local Development (Primary)

```bash
# Basic test execution
uv run pytest                     # All tests (< 30 seconds)
uv run pytest -v                  # Verbose output
uv run pytest -x                  # Stop on first failure

# Coverage reporting
uv run pytest --cov=src                           # Basic coverage
uv run pytest --cov=src --cov-report=term-missing # Missing lines
uv run pytest --cov=src --cov-report=html         # HTML report

# Specific test selection
uv run pytest tests/unit/test_betting_framework.py    # Single file
uv run pytest tests/unit/ -k "test_kelly"             # Pattern matching
uv run pytest tests/integration/                      # Integration only
```

### CI/CD Environment

```bash
# Parallel execution for faster CI/CD
uv run pytest -n auto             # Parallel execution
uv run pytest --cov=src --cov-report=xml  # XML coverage for CI
```

## Test Configuration

### pytest Configuration (pyproject.toml)

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = [
    "--cov=src",
    "--cov-report=term-missing",
    "--cov-report=html"
]
markers = [
    "unit: Unit tests",
    "integration: Integration tests"
]
```

### Test Dependencies

```toml
[project.optional-dependencies]
test = [
    "pytest>=8.0.0",
    "pytest-cov>=5.0.0",
    "pytest-xdist>=3.5.0"  # For parallel execution
]
```

## Test Data and Fixtures

### Shared Fixtures (conftest.py)

```python
@pytest.fixture
def sample_betting_data():
    """Sample betting data for unit tests."""
    return {
        'weekly_bankroll': 1000.0,
        'model_win_percentage': 0.65,
        'contract_price': 0.27
    }

@pytest.fixture
def sample_excel_data():
    """Sample Excel data as DataFrame for testing."""
    return pd.DataFrame({
        'Game': ['Team A vs Team B'],
        'Model Win %': [0.65],
        'Contract Price': [0.27]
    })

@pytest.fixture
def temp_excel_file(tmp_path):
    """Create temporary Excel file for integration tests."""
    # Creates temporary Excel files for testing
```

### Test Data Strategy

- **Unit Tests**: Simple, hardcoded test data for predictable results
- **Integration Tests**: Temporary files using pytest's `tmp_path` fixture
- **No External Dependencies**: All test data is generated or embedded

## Coverage Requirements

### Current Coverage (87% overall)

- **betting_framework.py**: 89% coverage
- **commission_manager.py**: 82% coverage  
- **excel_processor.py**: 91% coverage
- **Target**: 80% minimum (exceeded)

### Coverage Focus Areas

1. **Core Business Logic**: 100% coverage for Kelly criterion calculations
2. **Critical Paths**: Complete coverage for main user workflows
3. **Error Handling**: Validation and exception handling paths
4. **Integration Points**: Module interactions and data flow

## Performance Requirements

### Local Testing Performance

- **Total Execution Time**: < 30 seconds for complete suite
- **Unit Tests**: < 10 seconds
- **Integration Tests**: < 20 seconds additional
- **Coverage Generation**: < 5 seconds additional

### CI/CD Performance

- **Total Pipeline Time**: < 2 minutes (down from 10+ minutes)
- **Test Execution**: < 1 minute with parallel execution
- **Multi-Platform**: Ubuntu, Windows validation

## Writing New Tests

### Unit Test Pattern

```python
class TestFunctionName:
    """Test class for specific functionality."""
    
    def test_specific_behavior(self):
        """Test description with expected behavior."""
        # Arrange
        input_data = "test_input"
        expected = "expected_output"
        
        # Act
        result = function_under_test(input_data)
        
        # Assert
        assert result == expected
```

### Integration Test Pattern

```python
def test_workflow_name(tmp_path):
    """Test complete workflow with temporary files."""
    # Arrange
    test_file = tmp_path / "test.xlsx"
    # Create test data
    
    # Act
    result = process_workflow(test_file)
    
    # Assert
    assert result.is_successful()
    assert result.output_exists()
```

### Best Practices

1. **Clear Test Names**: Describe what is being tested and expected behavior
2. **Arrange-Act-Assert**: Structure tests with clear sections
3. **Single Responsibility**: One test per behavior/scenario
4. **Minimal Setup**: Use simple, focused test data
5. **Good Error Messages**: Clear assertions with descriptive failure messages

## Troubleshooting

### Common Issues

#### Tests Running Slowly
```bash
# Check for inefficient tests
uv run pytest --durations=10
```

#### Coverage Issues
```bash
# Generate detailed coverage report
uv run pytest --cov=src --cov-report=html
# Open htmlcov/index.html to see missing coverage
```

#### Import Errors
```bash
# Ensure proper Python path setup
uv run pytest -v  # Should show proper module imports
```

#### Temporary File Issues
```bash
# Clean up test artifacts
rm -rf .pytest_cache/
rm -rf htmlcov/
```

### Test Debugging

```python
# Add debugging to tests
import pytest

def test_with_debugging():
    result = function_under_test()
    print(f"Debug: result = {result}")  # Will show with -s flag
    assert result.is_valid()

# Run with output
uv run pytest -s -v tests/unit/test_file.py::test_with_debugging
```

## Migration from Previous Testing Suite

### What Was Removed

- Complex custom mock frameworks
- Performance monitoring utilities  
- Property-based testing with Hypothesis
- Constraint validation framework
- Multiple test configuration files
- Over-engineered test utilities

### What Was Kept/Simplified

- Core business logic tests (simplified)
- Essential integration tests (streamlined)
- Basic pytest configuration
- Standard fixtures and test data

### Benefits of New Approach

- **87% faster execution** (30 seconds vs 300+ seconds)
- **90% fewer lines of test code** (maintainable)
- **Standard tooling** (no custom frameworks)
- **Clear structure** (easy for new developers)
- **Focused coverage** (essential functionality)

## CI/CD Integration

### GitHub Actions Workflow

The `.github/workflows/test-suite.yml` provides:

- Automated testing on push/PR to master
- Multi-platform validation (Ubuntu)
- Coverage reporting to Codecov
- Fast execution (< 2 minutes total)
- Integration with badge generation

### Badge Generation

The `.github/workflows/badges.yml` workflow:

- Runs after successful test completion
- Generates coverage and Python version badges
- Updates repository badges automatically
- Uses test suite coverage data

## Summary

This testing approach prioritizes:

✅ **Speed**: < 30 seconds local execution  
✅ **Simplicity**: Standard pytest without custom frameworks  
✅ **Coverage**: 87% coverage of essential functionality  
✅ **Maintainability**: Clear, readable tests  
✅ **Reliability**: Consistent results across platforms  
✅ **Developer Experience**: Fast feedback loop with `uv run pytest`

The testing suite provides comprehensive coverage while remaining simple to understand, maintain, and extend.