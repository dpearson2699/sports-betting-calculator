# Copilot Instructions for Wharton Betting Framework

## Project Architecture

This is a **Wharton-optimized sports betting framework** implementing Kelly Criterion with academic-backed safety constraints. The codebase prioritizes mathematical rigor and risk management over general flexibility.

### Core Components & Data Flow

1. **`run.py`** - Main entry point that sets up Python path and launches application
2. **`src/main.py`** - CLI interface with two modes (single bet vs Excel batch)
3. **`src/betting_framework.py`** - Core algorithmic engine implementing Wharton methodology
4. **`src/excel_processor.py`** - Batch processing with bankroll allocation logic
5. **`config/settings.py`** - Configuration constants and directory setup

Data flows: Input → EV calculation → Wharton filtering → Kelly sizing → Whole contract adjustment → Safety constraints → Output

**Key architectural decision**: Uses `sys.path.insert(0, str(PROJECT_ROOT / "src"))` for module imports due to `src/` structure without making it a package.

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
# Setup
uv sync

# Run application (PREFERRED - use this entry point)
python run.py
# Alternative (direct source)
uv run src/main.py

# Test suite (47 comprehensive tests with 93% coverage)
python run_tests.py               # All tests with coverage
python run_tests.py unit          # Unit tests only  
python run_tests.py integration   # Integration tests only
python run_tests.py quick         # Fast tests only (exclude slow)
uv run pytest -v                  # Direct pytest with verbose output
uv run pytest --cov=src --cov-report=html  # Generate HTML coverage report

# Manual testing patterns for validation
# Single bet mode: Weekly bankroll: 100, Win %: 68, Contract price: 0.45
# Batch mode: Use bankroll: 50 with auto-generated sample file
```

## Integration Points

### External Dependencies
- **pandas**: Excel I/O and data manipulation
- **openpyxl**: Excel engine (specifically required)
- **uv**: Package manager (preferred over pip)
- **pytest**: Testing framework with coverage, fixtures, and parametrized tests

### File I/O Conventions
- **Directory Structure**: `data/input/` for Excel files, `data/output/` for results
- **Input Excel**: Sheet name defaults to `'Games'` (configurable in `settings.py`)
- **Required columns**: `Game`, `Model Win Percentage`, `Contract Price` (optional: `Model Margin`)
- **Output Excel**: Original filename + `_RESULTS.xlsx` in `data/output/`
- **Sample generation**: Creates `sample_games.xlsx` in `data/input/` directory
- **Auto-created directories**: `INPUT_DIR` and `OUTPUT_DIR` created on startup via `settings.py`
- **Excel comments**: Headers include explanatory comments for user guidance

### Test Infrastructure
- **Test Organization**: `tests/unit/` and `tests/integration/` with shared fixtures in `conftest.py`
- **Fixtures**: Comprehensive test data including `wharton_test_cases`, `edge_case_test_data`, `sample_excel_data`
- **Markers**: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.excel`, `@pytest.mark.slow`
- **Coverage**: 47 tests achieving 97% coverage on core betting logic, 93% on Excel processing

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

**Comprehensive pytest test suite** with 47 tests achieving high coverage:
- **Unit tests**: `tests/unit/` for individual component testing
- **Integration tests**: `tests/integration/` for end-to-end workflows  
- **Fixtures**: `tests/conftest.py` provides `wharton_test_cases`, `sample_excel_data`, `edge_case_test_data`
- **Test runners**: Use `python run_tests.py [unit|integration|quick]` or direct `uv run pytest`
- **Coverage**: 97% on core betting logic, 93% on Excel processing

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

**Path handling**: All imports use `sys.path.insert()` for cross-module imports due to `src/` structure