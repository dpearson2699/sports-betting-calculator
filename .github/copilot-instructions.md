# Copilot Instructions: Sports Betting Calculator

## Project Overview
This is a research-driven Kelly Criterion betting calculator with Robinhood whole-contract constraints. The system analyzes sports betting opportunities using academic research principles to identify profitable betting opportunities while maintaining strict risk management.

## Key Technologies & Architecture
- **Language**: Python 3.11+
- **Core Dependencies**: pandas, openpyxl 
- **Testing**: pytest with 102 tests, 95% coverage
- **Package Management**: uv (preferred) or pip
- **Entry Point**: `python run.py`

## Orientation
- Research-driven Kelly calculator with Robinhood whole-contract constraints; entry point is `python run.py`.
- `config/settings.py` sets constants, commissions, and auto-creates `data/input` & `data/output`.
- Keeps returns as dictionaries (`decision`, `ev_percentage`, `bet_amount`, `reason`, ...).

## Core flow
- `run.py` wires `src.main:main`; CLI lives in `src/main.py` with option 1 = Excel batch, option 2 = single bet.
- `user_input_betting_framework()` in `src/betting_framework.py` handles EV filter, Kelly sizing, and contract rounding.
- `process_betting_excel()` in `src/excel_processor.py` normalizes rows, runs the framework, then sorts by EV% before allocation.
- `apply_bankroll_allocation()` flips `Final Recommendation` to BET / PARTIAL / SKIP and keeps `Cumulative Bet Amount` in sync.

## Non-negotiable constraints
- Enforce EV ≥ 10% (`MIN_EV_THRESHOLD`) and exit early with `reason` for failures.
- Kelly fraction is halved and capped by `MAX_BET_PERCENTAGE` (15% bankroll).
- Always add `$0.02` commission (`COMMISSION_PER_CONTRACT`) before calculating odds and whole contracts.
- Reject bets that cannot fund at least one contract; propagate the NO BET details to Excel outputs and CLI prints.

## Input conventions
- Percentages accept either 68 or 0.68; prices accept 45 or 0.45—see `normalize_contract_price()` helpers.
- Weekly bankroll floats drive both single bet sizing and Excel allocation; maintain parity with tests.
- `COLUMN_CONFIG` drives Excel headers, comments, and validation; update alongside any schema changes.

## Excel workflow
- Required columns: `Game`, `Model Win Percentage`, `Contract Price` (margin optional). Missing columns raise `ValueError`.
- Output workbook writes `Quick_View` + `Betting_Results`; keep formatting helpers (`apply_excel_formatting`, `adjust_column_widths`) aligned.
- Bankroll allocation assumes descending EV order and requires ≥1% remaining bankroll for partial bets (`MIN_BANKROLL_FOR_PARTIAL`).
- `examples/excel_batch_example.py` and `create_sample_excel_in_input_dir()` mirror the expected file shape.

## CLI habits
- Option 1 enumerates `data/input/*.xlsx`, offers sample creation, and pipes into `process_betting_excel`.
- Option 2 reports bet diagnostics including `target_bet_amount` versus `unused_amount`.
- Console summary comes from `display_summary()`; adjust totals there when altering allocation math.

## Dev workflow
- Use `uv sync` (add `--extra test` or `--extra dev` as needed) and avoid raw `pip`.
- Preferred runs: `python run.py`, or `uv run sports-betting-calculator`.
- Tests: `uv run pytest`, `uv run pytest tests/unit/`, and `uv run pytest tests/integration/`; 102 tests should stay green.
- Coverage badge derives from `scripts/generate_coverage_badge.py` and pushes to `coverage-badge.json`.

## Gotchas & tips
- Folder paths are relative; never hardcode absolute locations outside `config`.
- Keep return payloads stable for downstream Excel formatting and tests (`tests/unit/test_betting_framework.py` asserts keys).
- When touching Excel logic, sync `QUICK_VIEW_MAPPING` and column order blocks to avoid regression in `test_excel_processor.py`.
- Property tests in `tests/property/test_property_based.py` enforce EV / bankroll invariants—update strategies if constraints move.

## Code Style & Standards
- Follow existing patterns in the codebase for consistency
- Use descriptive variable names that match domain terminology (`bet_amount`, `ev_percentage`, etc.)
- Maintain existing function signatures to preserve API compatibility
- All functions should return dictionaries with consistent key names for downstream processing
- Add docstrings to new functions following existing patterns

## Testing Requirements
- All new features must include comprehensive tests
- Unit tests go in `tests/unit/`
- Integration tests go in `tests/integration/` 
- Property-based tests use Hypothesis in `tests/property/`
- Run `uv run pytest` or `python -m pytest` to execute full test suite
- Maintain 95%+ code coverage
- Test both success and failure cases, especially for betting logic

## Security & Safety
- Never commit sensitive data (API keys, real betting amounts, personal information)
- Validate all user inputs, especially financial amounts and percentages
- Ensure EV threshold and bankroll caps are always enforced
- Commission calculations must always be included in bet sizing

## Common Issues & Debugging
- **Import errors**: Ensure Python path includes `src/` directory; use `python run.py` for consistent behavior
- **Excel errors**: Verify required columns (`Game`, `Model Win Percentage`, `Contract Price`) exist; optional `Model Margin`
- **All "NO BET" results**: Check that win percentages and prices result in EV ≥ 10%
- **Test failures**: Run `uv sync` first, then `uv run pytest -v` for detailed output
- **Mathematical precision**: Use existing helper functions for percentage/price normalization to maintain consistency

## Files You'll Work With Most
- `src/betting_framework.py` - Core Kelly Criterion and EV calculations
- `src/excel_processor.py` - Excel I/O, bankroll allocation, and batch processing
- `src/main.py` - CLI interface and user interaction
- `config/settings.py` - All constants, thresholds, and configuration
- `tests/unit/test_betting_framework.py` - Key business logic tests
- `tests/integration/test_end_to_end.py` - Full workflow validation