# Copilot Instructions: Sports Betting Calculator

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