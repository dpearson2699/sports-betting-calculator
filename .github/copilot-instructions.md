# Copilot Instructions: Sports Betting Calculator

## Project Overview
This is a research-driven Kelly Criterion betting calculator implementing Wharton School academic research. The system analyzes sports betting opportunities using rigorous expected value filtering, Half-Kelly position sizing, and platform-specific commission management with whole-contract constraints.

## Key Technologies & Architecture
- **Language**: Python 3.13+
- **Core Dependencies**: pandas, openpyxl 
- **Testing**: pytest with 176 tests across unit/integration layers
- **Package Management**: uv (required) with dependency groups
- **Entry Point**: `python run.py` or `uv run python run.py`

## Architecture Overview
- **Commission-First Design**: `CommissionManager` class provides platform-agnostic commission handling (Robinhood $0.02, Kalshi $0.00, PredictIt 10%, etc.)
- **Research-Driven Core**: `user_input_betting_framework()` implements Wharton School 10% EV threshold + Half-Kelly sizing
- **Excel Batch Pipeline**: Multi-game processing with bankroll allocation, EV ranking, and two-sheet output format
- **CLI-First UX**: Interactive menu system with validation, error handling, and commission configuration

## Core Data Flow
1. **Entry**: `run.py` → `src.main:main()` → menu options (Excel batch/single bet/commission config)
2. **Single Bet**: User inputs → `user_input_betting_framework()` → commission-adjusted EV → Kelly sizing → whole contract rounding
3. **Excel Batch**: File selection → `process_betting_excel()` → row normalization → framework application → EV ranking → `apply_bankroll_allocation()` → two-sheet output
4. **Commission System**: `commission_manager` global instance maintains rates across all calculations

## Critical Business Rules
- **10% EV Minimum**: Wharton research-based threshold; bets below this are rejected with `reason`
- **Half-Kelly Sizing**: `kelly_fraction * 0.5` then cap at 25% of bankroll (`MAX_BET_PERCENTAGE`)
- **Commission Integration**: Always include platform commission in price calculations before EV/Kelly math
- **Whole Contracts Only**: Round down fractional contracts; track `unused_amount` for transparency
- **Bankroll Allocation**: Process Excel games in descending EV order; mark PARTIAL/SKIP when funds exhausted

## Commission Architecture
- **Global Instance**: `commission_manager` singleton handles all rate management
- **Platform Presets**: Built-in rates for Robinhood ($0.02), Kalshi ($0.00), PredictIt (10%), Polymarket ($0.00)
- **Validation**: Rates must be 0.00-1.00; platform switching updates shared state
- **Integration Points**: All bet calculations call `commission_manager.get_commission_rate()`

## Input Format Conventions
- **Dual Format Support**: Percentages accept 68 or 0.68; prices accept 45 or 0.45 via `normalize_contract_price()`
- **Weekly Bankroll**: Float drives both single bet sizing and Excel allocation; test parity critical
- **Excel Columns**: Required: `Game`, `Model Win Percentage`, `Contract Price`; Optional: `Model Margin`
- **Missing Columns**: Raise `ValueError` immediately; don't attempt to continue processing

## Excel Processing Pipeline
- **Column Validation**: `get_required_input_columns()` enforces schema; `COLUMN_CONFIG` drives headers/comments
- **Output Format**: Two sheets - `Quick_View` (simplified) + `Betting_Results` (detailed with commission analysis)
- **Bankroll Flow**: Sort by EV descending → allocate sequentially → mark PARTIAL when <1% bankroll remains
- **Format Helpers**: `apply_excel_formatting()` + `adjust_column_widths()` must stay synchronized

## Development Workflow
- **Dependency Management**: `uv sync --group test` or `uv sync --group dev`; avoid raw pip
- **Test Execution**: `uv run pytest` (176 tests), `uv run pytest tests/unit/` (146 tests), `uv run pytest tests/integration/` (30 tests)
- **Coverage**: Target >80%, currently tracking via `scripts/generate_coverage_badge.py`
- **Code Quality**: `uv run black .`, `uv run flake8`, `uv run bandit -r src/`, `uv run safety check`

## Testing Architecture
- **176 Total Tests**: 146 unit + 30 integration, comprehensive coverage of business logic
- **Commission Testing**: Extensive platform-switching tests in `test_commission_manager.py`
- **Integration Tests**: End-to-end workflows including error recovery scenarios
- **Test Organization**: Use `tests/unit/` for isolated function tests, `tests/integration/` for complete workflows

## Common Pitfalls & Solutions
- **Commission Blindness**: Always use `commission_manager.get_commission_rate()` in calculations; don't hardcode
- **Return Dictionary Stability**: Functions return consistent keys (`decision`, `ev_percentage`, `bet_amount`, `reason`); tests assert on these
- **Path Configuration**: Use `config/settings.py` paths; never hardcode absolute paths
- **Excel Schema Drift**: Update `COLUMN_CONFIG` + `QUICK_VIEW_MAPPING` together to prevent test failures
- **Mathematical Precision**: Use existing normalization helpers; don't reinvent percentage/price parsing

## Key Files & Their Roles
- `src/betting_framework.py` - Kelly math, EV calculations, whole contract logic
- `src/commission_manager.py` - Platform-agnostic commission system with presets
- `src/excel_processor.py` - Batch processing, bankroll allocation, output formatting
- `src/main.py` - CLI menus, user interaction, error handling
- `config/settings.py` - Constants, directory management, commission defaults
- `tests/unit/test_betting_framework.py` - Core business logic validation (22 tests)
- `tests/unit/test_commission_manager.py` - Commission system validation (51 tests)
- `tests/integration/test_end_to_end.py` - Complete user workflows (15 tests)