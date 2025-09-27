# Contributing to Event Contract Betting Framework

Thank you for your interest in contributing to the Event Contract Betting Framework! This document provides guidelines for contributing to this project.

## Getting Started

### Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager (recommended)
- Basic understanding of sports betting and Kelly Criterion

### Development Setup

1. Fork and clone the repository:

```bash
git clone https://github.com/your-username/betting-framework.git
cd betting-framework
```

2. Install dependencies:

```bash
uv sync
```

3. Run tests to ensure everything works:

```bash
python run_tests.py
```

## Development Workflow

### Running Tests

```bash
# Run all tests with coverage
python run_tests.py

# Run specific test types
python run_tests.py unit          # Unit tests only
python run_tests.py integration   # Integration tests only
python run_tests.py quick         # Fast tests only

# Generate HTML coverage report
uv run pytest --cov=src --cov-report=html
```

### Code Style

- Follow PEP 8 Python style guidelines
- Use descriptive variable names
- Add docstrings to all public functions
- Keep functions focused and single-purpose

### Testing Requirements

- All new features must include comprehensive tests
- Maintain test coverage above 90% for core modules
- Include both unit tests and integration tests
- Test edge cases and error conditions

## Project Architecture

### Core Principles

This framework implements **Wharton research-backed constraints**:

- 10% minimum expected value threshold
- Half-Kelly sizing for reduced volatility
- 15% maximum bankroll allocation per bet
- Whole contract enforcement (Robinhood constraint)

**These safety constraints are non-negotiable and should never be bypassed.**

### Key Files

- `src/betting_framework.py` - Core Kelly/Wharton calculations
- `src/excel_processor.py` - Batch processing and allocation logic
- `src/main.py` - CLI interface
- `config/settings.py` - Configuration constants

## Making Contributions

### Types of Contributions Welcome

- Bug fixes
- Performance improvements
- Additional test coverage
- Documentation improvements
- New features (discuss in issues first)

### Pull Request Process

1. **Create an Issue**: For significant changes, create an issue first to discuss the approach
2. **Create a Branch**: Use descriptive branch names like `fix-kelly-calculation` or `add-csv-support`
3. **Write Tests**: Ensure new code is fully tested
4. **Update Documentation**: Update README.md and docstrings as needed
5. **Run Full Test Suite**: Ensure all tests pass
6. **Submit Pull Request**: Include clear description of changes

### Pull Request Guidelines

- Provide clear description of what the PR does and why
- Reference any related issues
- Include tests for new functionality
- Ensure all existing tests still pass
- Update documentation if needed

## Mathematical Accuracy

This framework implements financial mathematics for sports betting. When contributing:

- **Verify calculations** against academic sources
- **Test edge cases** thoroughly (extreme probabilities, small bankrolls)
- **Maintain precision** in floating-point arithmetic
- **Document formulas** with references to academic literature

## Reporting Issues

### Bug Reports

Include:

- Python version and OS
- Steps to reproduce
- Expected vs actual behavior
- Sample data if applicable

### Feature Requests

Include:

- Clear description of the feature
- Use case or problem it solves
- How it fits with Wharton methodology

## Questions and Support

- Create an issue for questions about the codebase
- Reference the comprehensive documentation in `.github/copilot-instructions.md`
- Check existing issues before creating new ones

## Code of Conduct

- Be respectful and professional
- Focus on constructive feedback
- Help maintain a welcoming environment for all contributors

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
