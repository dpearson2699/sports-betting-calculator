# Copilot Instructions for Sports Betting Calculator Framework

## Project Architecture

This is an **academic research-based event contract betting framework** implementing Kelly Criterion with empirically-validated safety constraints. The codebase prioritizes mathematical rigor and risk management over general flexibility, with algorithms informed by comprehensive academic research (see `MATHEMATICAL-FOUNDATION.md`).

### Core Components & Data Flow

1. **`run.py`** - Main entry point that sets up Python path and launches application (PREFERRED entry point)
2. **`src/main.py`** - CLI interface with numbered menu system (Excel batch vs single bet interactive)
3. **`src/betting_framework.py`** - Core algorithmic engine implementing Wharton methodology with Kelly Criterion
4. **`src/excel_processor.py`** - Batch processing with sophisticated bankroll allocation and priority logic
5. **`config/settings.py`** - Configuration constants, directory auto-creation, and framework constraints
6. **`tests/`** - Comprehensive test suite (102 tests) with unit, integration, and property-based tests

**Data Flow**: Input → EV calculation → Wharton filtering (10% threshold) → Kelly sizing → Half-Kelly safety → 15% bankroll cap → Whole contract adjustment → Commission handling → Bankroll allocation → Output

**Key architectural decisions**: 
- Uses standard Python package structure with proper `__init__.py` exports and relative imports
- Auto-creates `data/input/` and `data/output/` directories on startup via `settings.py`
- `uv` package manager preferred over `pip` for dependency management
- Supports development installation via `uv pip install -e .` for proper IDE integration

### Critical Business Rules

These constraints are **non-negotiable** and encoded in `user_input_betting_framework()`:

- **10% minimum EV threshold** - No bets below this (Wharton research requirement)
- **Half-Kelly sizing** - Always use 50% of full Kelly for reduced volatility  
- **15% bankroll cap** - Hard maximum per bet regardless of Kelly recommendation
- **Whole contracts only** - Round down fractional contracts, adjusted via `calculate_whole_contracts()`
- **Minimum contract affordability** - If target bet can't buy 1 whole contract, becomes NO BET
- **Commission handling** - $0.02 per contract commission built into all calculations

**Robinhood-specific constraint**: All calculations account for whole contracts only (no fractional purchases).

## Key Patterns & Conventions

### Input Handling Pattern
The framework handles **dual format inputs** consistently:
```python
# Percentage: accepts both 68 and 0.68 for 68%
win_probability = model_win_percentage if model_win_percentage <= 1 else model_win_percentage / 100

# Price: accepts both 27 and 0.27 for 27 cents
normalized_price = contract_price / 100.0 if contract_price >= 1.0 else contract_price
```

### Return Dictionary Structure
All framework functions return structured dictionaries with:
- `decision`: "BET" or "NO BET"
- `ev_percentage`: Always calculated
- `bet_amount`: Actual amount (0 for NO BET)
- `reason`: Present for NO BET cases
- For BET decisions: `contracts_to_buy`, `target_bet_amount`, `unused_amount`

### Excel Processing Pattern
Excel operations follow this flow:
1. Read with column validation (required: `Game`, `Model Win Percentage`, `Contract Price`)
2. Process each row through `user_input_betting_framework()`
3. Sort by EV percentage (highest first)
4. Apply bankroll allocation with `apply_bankroll_allocation()`
5. Generate `*_RESULTS.xlsx` with summary

**Column handling**: Uses `COLUMN_CONFIG` dictionary in `excel_processor.py` for input/output column mapping and explanations.

## Development Commands

```powershell
# Setup (uses uv package manager - preferred over pip)
uv sync                           # Install all dependencies
uv sync --extra test              # Include test dependencies
uv sync --extra dev               # Include development tools

# Install in development mode (required for proper imports)
uv pip install -e .              # Enable proper package imports

# Run application 
python run.py                     # PREFERRED entry point
uv run sports-betting-calculator  # Alternative using package script

# Test suite (102 comprehensive tests with property-based validation)
uv run pytest                     # All tests with coverage report  
uv run pytest tests/unit/         # Unit tests only
uv run pytest tests/integration/  # Integration tests only  
uv run pytest tests/property/     # Property-based tests using Hypothesis
uv run pytest -m "not slow"       # Fast tests only (exclude @pytest.mark.slow)
uv run pytest -v                  # Verbose output
uv run pytest --no-cov            # Skip coverage reporting
uv run pytest --cov-report=html   # Generate test-results/coverage/ directory
uv run pytest --collect-only      # See all available tests without running

# Common test patterns for development
uv run pytest -k "test_wharton"   # Run Wharton methodology tests
uv run pytest -k "test_kelly"     # Run Kelly Criterion tests
uv run pytest -m "mathematical"   # Run mathematical accuracy tests

# Examples and validation (after development install)
python examples/basic_usage.py         # Demonstrate single bet patterns
python examples/excel_batch_example.py # Show batch processing workflow

# Manual testing validation patterns
# Single bet mode: Weekly bankroll: 100, Win %: 68, Contract price: 0.45 (should result in BET)
# Batch mode: Use bankroll: 100 with auto-generated sample file (tests allocation logic)
```

## Integration Points

### External Dependencies
- **pandas**: Excel I/O and data manipulation
- **openpyxl**: Excel engine (specifically required)
- **uv**: Package manager (preferred over pip)
- **pytest**: Testing framework with coverage, fixtures, and parametrized tests

### File I/O Conventions
- **Directory Structure**: `data/input/` for Excel files, `data/output/` for results
- **Input Excel**: Sheet name defaults to `'Games'` (configurable via `DEFAULT_SHEET_NAME` in `settings.py`)
- **Required columns**: `Game`, `Model Win Percentage`, `Contract Price` (optional: `Model Margin`)
- **Output Excel**: Original filename + `_RESULTS.xlsx` in `data/output/`
- **Sample generation**: Creates `sample_games.xlsx` in `data/input/` directory when no files found
- **Auto-created directories**: `INPUT_DIR` and `OUTPUT_DIR` created on startup via `settings.py`
- **Excel comments**: Headers include explanatory comments for user guidance via `COLUMN_CONFIG`

### Test Infrastructure
- **Test Organization**: `tests/unit/`, `tests/integration/`, and `tests/property/` with shared fixtures in `conftest.py`
- **Fixtures**: Comprehensive test data including `wharton_test_cases`, `edge_case_test_data`, `sample_excel_data`
- **Markers**: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.excel`, `@pytest.mark.slow`, `@pytest.mark.property`, `@pytest.mark.mathematical`
- **Property-Based Testing**: Uses Hypothesis for mathematical validation and edge case discovery
- **Test Builder**: `TestDataBuilder` class in conftest.py for dynamic test data creation
- **Coverage**: HTML reports generated in `test-results/coverage/` directory

## Critical Implementation Details

### Bankroll Allocation Logic
In `apply_bankroll_allocation()`, games are processed in EV% order (highest first). Partial bets allowed only if remaining bankroll ≥ 1% of total bankroll.

**Priority system**: Higher EV bets get full allocation first; lower EV bets may become PARTIAL BET or SKIP if insufficient bankroll remains.

**Recent bug fix**: Fixed logic where remaining bankroll of exactly $0 incorrectly allowed subsequent BET decisions instead of marking them as 'SKIP - Insufficient Bankroll'.

### Error Handling Patterns
- Input validation uses `try/except ValueError` for numeric inputs
- File operations check `os.path.exists()` and validate Excel column presence
- Column validation raises `ValueError` with specific missing columns list
- Functions return `None, None` tuple for error states in batch processing
- Excel file selection includes bounds checking and file existence validation

### Mathematical Formulas
```python
# Expected Value (core calculation)
ev_per_dollar = win_probability * (1/normalized_price) - 1

# Kelly Criterion
b = (1 / normalized_price) - 1  # Net odds
full_kelly_fraction = (b * p - q) / b
half_kelly_fraction = full_kelly_fraction * 0.5

# Final bet sizing
final_fraction = min(half_kelly_fraction, 0.15)  # Cap at 15%
target_bet_amount = final_fraction * weekly_bankroll

# Whole Contracts Adjustment (Robinhood constraint)
fractional_contracts = target_bet_amount / contract_price
whole_contracts = int(fractional_contracts)  # Round down
actual_bet_amount = whole_contracts * contract_price
```

## When Modifying Code

- **Never bypass safety constraints** - The 10%/Half-Kelly/15% rules are research-backed
- **Preserve dual input formats** - Users expect both percentage and price flexibility  
- **Maintain Excel column contracts** - Existing users depend on current format
- **Keep bankroll allocation logic** - EV-based prioritization is core to the methodology
- **Test with sample data** - Use the built-in sample Excel generator for validation

## Testing Approach

**Comprehensive pytest test suite** with exactly 102 tests achieving high coverage:
- **Unit tests**: `tests/unit/` for individual component testing (covering `test_betting_framework.py`, `test_excel_processor.py`, `test_main.py`, `test_missing_coverage.py`)
- **Integration tests**: `tests/integration/` for end-to-end workflows (`test_end_to_end.py`)  
- **Property-based tests**: `tests/property/` using Hypothesis for mathematical validation and edge case discovery
- **Fixtures**: `tests/conftest.py` provides `wharton_test_cases`, `sample_excel_data`, `edge_case_test_data`
- **Test runners**: Use `uv run pytest` (primary method)
- **Coverage**: 97% on core betting logic (`src/betting_framework.py`), 99% on Excel processing (`src/excel_processor.py`), 95% overall

**Manual validation pattern** for quick verification:
1. Single bet mode with Weekly bankroll: 100, Win %: 68, Contract price: 0.45 (should result in BET)
2. Generate and process sample Excel file
3. Verify calculations match expected EV/Kelly formulas  
4. Check edge cases: low EV rejection, bankroll caps

## Configuration Management

**All constants in `config/settings.py`:**
- `MIN_EV_THRESHOLD = 10.0` - Wharton minimum EV requirement
- `HALF_KELLY_MULTIPLIER = 0.5` - Safety factor for Kelly sizing
- `MAX_BET_PERCENTAGE = 0.15` - Hard bankroll cap per bet
- `MIN_BANKROLL_FOR_PARTIAL = 0.01` - Minimum for partial bankroll allocation

**Path handling**: All imports use standard Python package structure with relative imports within packages

## CLI Interface Patterns

### Main Menu System
The application uses a simple numbered menu system in `main()`:
- Option 1: Excel Batch Processing (prioritized for multiple games)
- Option 2: Single Bet Analysis (interactive mode)
- Option 3: Exit

### File Selection Logic
Excel batch mode implements sophisticated file handling:
```python
# Lists available files in data/input/
available_files = list_available_input_files()
# Offers sample creation if no files found
# Supports custom file path input as fallback
```

### Input Validation Patterns
Consistent `try/except ValueError` blocks for all user inputs with specific error messages for guidance.

### IDE Configuration
**VS Code Python Path Resolution**: The project includes `.vscode/settings.json` with `"python.analysis.extraPaths": ["./src"]` to help Pylance resolve imports correctly. After installing with `uv pip install -e .`, full intellisense and navigation work properly with the standard package structure.