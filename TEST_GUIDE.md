# Test Configuration and Usage

## Overview

This project now has a comprehensive test suite using pytest with coverage reporting. The tests are organized into:

- **Unit Tests** (`tests/unit/`): Test individual functions and components
- **Integration Tests** (`tests/integration/`): Test complete workflows and system interactions
- **Fixtures** (`tests/conftest.py`): Reusable test data and utilities

## Running Tests

### Install Test Dependencies

```powershell
uv sync --extra test
```

### Quick Test Commands

```powershell
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run only unit tests
uv run pytest tests/unit

# Run only integration tests
uv run pytest tests/integration

# Run specific test file
uv run pytest tests/unit/test_betting_framework.py

# Run with verbose output
uv run pytest -v

# Run quick tests (excluding slow ones)
uv run pytest -m "not slow"
```

### Using the Test Runner Script

```powershell
# Run all tests with coverage
python run_tests.py

# Run only unit tests
python run_tests.py unit

# Run only integration tests  
python run_tests.py integration

# Run quick tests (fast unit tests only)
python run_tests.py quick

# Run with verbose output
python run_tests.py --verbose

# Run without coverage
python run_tests.py --no-cov
```

## Test Structure

### Unit Tests

- `test_betting_framework.py`: Tests core betting logic, Kelly calculations, Wharton constraints
- `test_excel_processor.py`: Tests Excel I/O, bankroll allocation, formatting

### Integration Tests

- `test_end_to_end.py`: Complete workflow testing, error handling, performance

### Fixtures (`conftest.py`)

Provides reusable test data including:
- `sample_bankroll`: Standard test bankroll ($100)
- `wharton_test_cases`: Pre-defined test scenarios for Wharton methodology
- `sample_excel_data`: Test DataFrame for Excel processing
- `temp_excel_file`: Temporary Excel files for testing
- `edge_case_test_data`: Boundary condition tests

## Test Markers

Tests are organized with markers:

- `@pytest.mark.unit`: Unit tests
- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.slow`: Slower running tests
- `@pytest.mark.excel`: Tests requiring Excel file operations

Run specific markers:
```powershell
# Run only unit tests
uv run pytest -m unit

# Run only integration tests
uv run pytest -m integration

# Skip slow tests
uv run pytest -m "not slow"
```

## Coverage Reporting

Coverage reports are generated in multiple formats:

- **Terminal**: Shows missing lines during test run
- **HTML**: Detailed report in `htmlcov/index.html`
- **XML**: Machine-readable format for CI/CD

View HTML coverage report:
```powershell
# After running tests with coverage
start htmlcov/index.html  # Windows
```

## Test Development Guidelines

### Writing New Tests

1. **Unit Tests**: Test individual functions with clear inputs/outputs
2. **Integration Tests**: Test complete workflows and system interactions
3. **Use Fixtures**: Leverage existing fixtures for consistent test data
4. **Mark Tests**: Add appropriate pytest markers
5. **Mock External Dependencies**: Use `unittest.mock` for file I/O and external calls

### Test Naming Convention

- Test files: `test_*.py`
- Test classes: `Test*`
- Test methods: `test_*`

### Example Test Structure

```python
class TestFeatureName:
    """Test specific feature or component"""
    
    def test_normal_case(self, fixture_name):
        """Test normal operation"""
        # Arrange
        input_data = setup_test_data()
        
        # Act
        result = function_under_test(input_data)
        
        # Assert
        assert result['expected_field'] == expected_value
    
    def test_edge_case(self):
        """Test boundary conditions"""
        # Test implementation
        
    def test_error_handling(self):
        """Test error conditions"""
        with pytest.raises(ExpectedError):
            function_under_test(invalid_input)
```

## Continuous Integration

The test configuration is ready for CI/CD integration:

- **Coverage XML**: Machine-readable coverage data
- **Pytest XML**: Test result reporting
- **Multiple Python versions**: Configured to support Python 3.11+

## Mathematical Validation

Tests include mathematical accuracy verification:

- **EV Calculations**: Verify expected value formulas
- **Kelly Criterion**: Validate Kelly fraction calculations  
- **Wharton Constraints**: Ensure 10%/Half-Kelly/15% rules
- **Whole Contract Math**: Verify Robinhood-specific adjustments
- **Commission Impact**: Test commission effects on calculations

## Performance Testing

Integration tests include basic performance validation:

- **Large Dataset Processing**: 100+ games
- **Memory Usage**: Stability over multiple runs
- **Processing Time**: Reasonable execution speed

## Error Handling Testing

Comprehensive error scenario coverage:

- **Invalid Excel Files**: Missing columns, corrupt data
- **Boundary Conditions**: Extreme values, edge cases
- **File System Issues**: Missing files, permission errors
- **Data Validation**: Type errors, out-of-range values

## Configuration Testing

Tests verify configuration integration:

- **Settings Constants**: MIN_EV_THRESHOLD, MAX_BET_PERCENTAGE
- **Directory Structure**: INPUT_DIR, OUTPUT_DIR usage
- **Commission Rates**: COMMISSION_PER_CONTRACT integration

## Debugging Tests

For debugging specific tests:

```powershell
# Run single test with maximum verbosity
uv run pytest tests/unit/test_betting_framework.py::TestUserInputBettingFramework::test_wharton_compliant_bet -vvv

# Run with Python debugger
uv run pytest --pdb tests/unit/test_betting_framework.py::test_function_name

# Run with print statements (pytest captures output)
uv run pytest -s tests/unit/test_betting_framework.py
```