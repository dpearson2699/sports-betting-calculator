# Sports Betting Calculator: Find Mispriced Event Contracts Using Kelly Criterion

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Coverage](https://img.shields.io/badge/coverage-93%25-green.svg)](#-testing--development)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A professional sports betting framework based on academic research, implementing the Kelly Criterion with safety constraints for optimal bankroll management.

> ⚠️ **Educational Purpose**: This framework is for educational and research purposes. Sports betting involves risk. Never bet more than you can afford to lose.

## 🎯 Features

- **📚 Research-Based EV Filtering**: Only recommends bets with 10%+ expected value (based on academic studies)
- **📊 Kelly Criterion**: Uses Half-Kelly sizing for optimal risk-adjusted returns
- **🛡️ Safety Constraints**: Maximum 15% of bankroll per bet
- **📈 Batch Processing**: Analyze multiple games via Excel with automatic ranking
- **💰 Bankroll Allocation**: Prevents over-betting by prioritizing highest EV opportunities
- **🧪 Comprehensive Testing**: 47 unit tests with 93% code coverage
- **🔧 Robinhood Integration**: Whole contract calculations with commission handling

## 🚀 Quick Start

### Installation

```bash
# Clone or download this project
cd betting-framework

# Install dependencies with uv (recommended)
uv sync

# Or use pip
pip install pandas openpyxl
```

### Usage

#### Running the Application

```bash
# Run the application (recommended)
python run.py

# Or use uv
uv run run.py
```

#### Interactive Mode (Single Bet)

Choose option 1 for single bet analysis

#### Excel Batch Mode (Multiple Games)

Choose option 2 for batch processing. The application will:

1. Show available Excel files in `data/input/` directory
2. Let you select a file or create a sample
3. Process the selected file and save results to `data/output/`

## 📁 Project Structure

```text
sports-betting-calculator/
├── .github/                      # GitHub configuration
├── .vscode/                      # VS Code settings
├── config/                       # Configuration files
│   └── settings.py               # Framework settings & constants
├── data/                         # Data directories (auto-created)
│   ├── input/                    # Excel files for batch processing
│   └── output/                   # Generated results files
├── examples/                     # Usage examples
│   ├── basic_usage.py            # Single bet example
│   ├── excel_batch_example.py    # Batch processing example
│   └── README.md                 # Examples documentation
├── src/                          # Core source code
│   ├── __init__.py               # Package initialization
│   ├── betting_framework.py      # Kelly Criterion & EV calculations
│   ├── excel_processor.py        # Excel I/O & bankroll allocation
│   └── main.py                   # CLI interface
├── test-results/                 # Test output (auto-generated)
│   └── coverage/                 # HTML coverage reports
├── tests/                        # Comprehensive test suite
│   ├── __init__.py               # Test package initialization
│   ├── conftest.py               # Shared fixtures & test configuration
│   ├── integration/              # End-to-end workflow tests
│   │   ├── __init__.py
│   │   └── test_end_to_end.py
│   └── unit/                     # Unit tests for individual components
│       ├── __init__.py
│       ├── test_betting_framework.py
│       └── test_excel_processor.py
├── CONTRIBUTING.md               # Contribution guidelines
├── LICENSE                       # MIT license
├── mathematical-foundation.md    # Academic research documentation
├── pyproject.toml                # Dependencies & project configuration
├── README.md                     # This file
├── run.py                        # Main application entry point
├── SECURITY.md                   # Security policy
└── uv.lock                       # Dependency lock file
```

## 🧪 Testing & Development

### Running Tests

```bash
# Install test dependencies
uv sync --extra test

# Run all tests
python run_tests.py

# Run only unit tests
python run_tests.py unit

# Run quick tests (fast only)
python run_tests.py quick

# Generate coverage report
uv run pytest --cov=src --cov-report=html
```

### Test Coverage

- **47 comprehensive tests** covering all major functionality
- **97% coverage** on core betting framework logic
- **93% coverage** on Excel processing and allocation
- Tests include: mathematical accuracy, Wharton compliance, edge cases, error handling

### Recent Improvements

- ✅ **Bug Fix**: Fixed bankroll allocation logic for zero remaining funds
- ✅ **Enhanced Testing**: Added comprehensive test suite with fixtures
- ✅ **Code Quality**: Improved error handling and validation
- ✅ **Documentation**: Added detailed testing guides and API docs

## 📊 Excel File Format

Your Excel file should have these columns:

| Column | Description | Example |
|--------|-------------|----------|
| `Game` | Game identifier | "Lakers vs Warriors" |
| `Model Win Percentage` | Your model's win probability | 68 (or 0.68) |
| `Model Margin` | Predicted margin (optional) | 3.5 |
| `Contract Price` | Sportsbook price per unit | 0.45 |

## 🔧 How It Works

### Core Algorithm

1. **Expected Value Calculation**: `EV = (Win_Probability × (1/Contract_Price)) - 1`
2. **Wharton Filter**: Only bet if EV ≥ 10% (academic research requirement)
3. **Kelly Sizing**: Calculate optimal bet size using Kelly Criterion
4. **Half-Kelly Safety**: Use 50% of Kelly for reduced volatility
5. **Bankroll Cap**: Never bet more than 15% of bankroll
6. **Whole Contracts**: Round down to whole contracts (Robinhood constraint)
7. **Commission Handling**: Include $0.02 per contract commission
8. **Allocation**: Rank by EV%, allocate bankroll to best opportunities first

### Mathematical Formula

```python
# Expected Value
ev_per_dollar = win_probability * (1/adjusted_price) - 1

# Kelly Criterion
b = (1 / adjusted_price) - 1  # Net odds
full_kelly_fraction = (b * p - q) / b
half_kelly_fraction = full_kelly_fraction * 0.5

# Final bet sizing with safety constraints
final_fraction = min(half_kelly_fraction, 0.15)  # Cap at 15%
target_bet_amount = final_fraction * weekly_bankroll

# Robinhood whole contract adjustment
whole_contracts = int(target_bet_amount / adjusted_price)
actual_bet_amount = whole_contracts * adjusted_price
```

## 📈 Output Files

The Excel processor creates a `*_RESULTS.xlsx` file with two sheets:

### Quick View Sheet

- Simplified overview with key metrics
- Game, Win %, Edge %, Stake $, Expected Value
- Final recommendations after bankroll allocation

### Detailed Results Sheet

- Complete analysis with all calculations
- Original game data and betting recommendations
- Expected value percentages and bet amounts
- Target vs actual bet amounts (whole contract adjustments)
- Commission details and unused amounts
- Games automatically ranked by EV% (highest first)

## 💡 Example Results

```text
BETTING ANALYSIS SUMMARY
============================================================
Total Games Analyzed: 6
Initial BET Opportunities: 5
Final Recommended Bets: 4
Weekly Bankroll: $100.00
Total Allocated: $83.28
Remaining Bankroll: $16.72
Total Expected Profit: $25.15

TOP RECOMMENDED BETS (by EV%):
Chiefs vs Bills: $15.00 (EV: 114.3%)
Cowboys vs Giants: $15.00 (EV: 80.0%)
Lakers vs Warriors: $15.00 (EV: 51.1%)
Yankees vs Red Sox: $15.00 (EV: 12.4%)
```

## 🛠️ Development

### Key Files

- `src/betting_framework.py` - Core betting logic and Kelly calculations
- `src/excel_processor.py` - Excel file processing and batch analysis  
- `src/main.py` - Interactive CLI interface
- `config/settings.py` - Configuration constants and directory setup
- `run.py` - Main application entry point
- `tests/` - Comprehensive test suite with 47 tests

### Configuration

Edit `config/settings.py` to modify:

- `MIN_EV_THRESHOLD = 10.0` - Minimum expected value percentage
- `HALF_KELLY_MULTIPLIER = 0.5` - Kelly fraction multiplier  
- `MAX_BET_PERCENTAGE = 0.15` - Maximum bet as fraction of bankroll
- `COMMISSION_PER_CONTRACT = 0.02` - Commission per contract

## ⚙️ Requirements

- Python 3.11+
- pandas ≥ 2.3.2
- openpyxl ≥ 3.1.5
- pytest ≥ 8.0.0 (for testing)

## 🛡️ Safety Features

- ✅ **10% minimum expected value threshold** (Wharton research)
- ✅ **Half-Kelly sizing** (reduced volatility vs full Kelly)
- ✅ **15% maximum bet size cap** (prevents excessive risk)
- ✅ **Whole contract enforcement** (Robinhood constraint)
- ✅ **Commission integration** (realistic cost calculations)
- ✅ **Bankroll allocation** (prevents over-betting across multiple games)
- ✅ **Input validation** (dual format support, error handling)
- ✅ **Mathematical verification** (comprehensive test coverage)

## 🎓 Academic Foundation

This framework implements methodology based on:

- **Kelly Criterion**: Optimal bet sizing for maximum logarithmic growth
- **Wharton Research**: 10% EV threshold for sustainable profitability
- **Half-Kelly Strategy**: Reduced volatility while maintaining growth
- **Modern Portfolio Theory**: Risk management through position sizing

## 🔧 Troubleshooting

### Common Issues

#### "No Excel files found in data/input/"

- Solution: Use option to create sample file, or add your Excel files to `data/input/` directory

#### "Missing required columns" error

- Solution: Ensure Excel file has columns: `Game`, `Model Win Percentage`, `Contract Price`
- Optional column: `Model Margin`

#### All bets showing "NO BET"

- Cause: Expected values below 10% threshold (Wharton requirement)
- Solution: Check your win percentages and contract prices for accuracy

#### Import errors in VS Code

- Solution: The `.vscode/settings.json` file should resolve Python path issues
- Alternative: Use `python run.py` instead of running files directly

#### Tests failing

- Run: `python run_tests.py` to see detailed output
- Check: Python version (requires 3.11+) and dependencies (`uv sync`)

### Getting Help

1. **Check the examples**: `python examples/basic_usage.py`
2. **Run tests**: `python run_tests.py` to verify installation
3. **Review documentation**: See `.github/copilot-instructions.md` for detailed technical info
4. **Create an issue**: Use GitHub issues for bug reports or questions

### Performance Tips

- **Large datasets**: Framework handles 100+ games efficiently
- **Memory usage**: Results are optimized for reasonable memory footprint
- **Processing speed**: Typical processing time < 1 second for most datasets

---

**⚠️ Disclaimer**: This framework is for educational purposes. Sports betting involves risk. Never bet more than you can afford to lose. Past performance does not guarantee future results.