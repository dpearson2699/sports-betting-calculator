# Sports Betting Calculator: Find Mispriced Event Contracts Using Kelly Criterion

[![Python](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/dpearson2699/sports-betting-calculator/master/.github/badges/python-badge.json)](https://www.python.org/downloads/)
[![Coverage](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/dpearson2699/sports-betting-calculator/master/.github/badges/coverage-badge.json)](#-testing--development)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A professional sports betting framework based on academic research, implementing the Kelly Criterion with safety constraints for optimal bankroll management.

> ⚠️ **Educational Purpose**: This framework is for educational and research purposes. Sports betting involves risk. Never bet more than you can afford to lose.

## 🎯 Features

- **📚 Research-Based EV Filtering**: Only recommends bets with 10%+ expected value (based on academic studies)
- **📊 Kelly Criterion**: Uses Half-Kelly sizing for optimal risk-adjusted returns
- **🛡️ Safety Constraints**: Maximum 15% of bankroll per bet
- **📈 Batch Processing**: Analyze multiple games via Excel with automatic ranking
- **💰 Bankroll Allocation**: Prevents over-betting by prioritizing highest EV opportunities
- **🧪 Comprehensive Testing**: 102 tests including property-based validation with 95% code coverage
- **🔧 Robinhood Integration**: Whole contract calculations with commission handling

## 🚀 Quick Start

Pick the track that matches your experience:

- **Already set up with Python 3.13+ and `uv`?** Jump straight to the commands in [Fast path](#fast-path).
- **Need a refresher or starting from scratch?** Follow the [Full setup](#full-setup) checklist.

### Fast path

```bash
uv sync
uv run python run.py
```

The menu offers Excel batch processing (option 1), single-bet analysis (option 2), and exit (option 3). Excel runs write results to `data/output/` with “_RESULTS” in the filename.

### Full setup

1. **Install Python 3.13+**
   - Using `uv`: If you already have `uv` available, run `uv python install 3.13` to download and manage a Python interpreter specifically for this project.
   - Windows: Download the latest 3.13 release from the [Python download page](https://www.python.org/downloads/), run the installer, and select **Add python.exe to PATH** before clicking *Install Now*.
   - macOS: Download the macOS installer from the same page, open the `.pkg`, and follow the prompts.
   If you're unsure which version you have, reinstalling 3.13 is the simplest path.

2. **Install `uv`**
   - `uv` manages virtual environments and dependencies for this project. Follow the instructions for your operating system in the [official installation guide](https://docs.astral.sh/uv/getting-started/installation/), then restart your terminal so the new command is available.

3. **Get the project files**
   - Developers comfortable with Git can clone the repository: `git clone https://github.com/dpearson2699/sports-betting-calculator.git`
   - Otherwise, download the ZIP from GitHub (green **Code** button → **Download ZIP**) and extract it. The extracted folder should be named `sports-betting-calculator`.

4. **Open a terminal in the project directory**
   - Windows: In File Explorer, open the project folder, click the address bar, type `powershell`, and press Enter.
   - macOS: In Finder, right-click the folder and choose **New Terminal at Folder** (or open Terminal and `cd` to the folder).

5. **Install the dependencies**

   ```bash
   uv sync
   ```

   `uv` creates an isolated environment and downloads the required packages. The first run may take a couple of minutes; later runs are fast.

6. **Launch the calculator**

   ```bash
   uv run python run.py
   ```

   Choose the workflow you need from the on-screen menu and follow the prompts. Excel batch runs save their output to `data/output/`.

### 📊 Excel File Format

Your Excel file should have these columns:

| Column | Description | Example |
|--------|-------------|----------|
| `Game` | Game identifier | "Lakers vs Warriors" |
| `Model Win Percentage` | Your model's win probability | 68 (or 0.68) |
| `Model Margin` | Predicted margin (optional) | 3.5 |
| `Contract Price` | Sportsbook price per unit | 0.45 |

> 💡 **Tip**: When you first run the application and choose Excel batch mode, if no Excel files are found, you'll see the prompt: `"No Excel files found in data/input/ directory. Create sample Excel file? (y/n)"`. Choose 'y' to create a `sample_games.xlsx` file that shows the exact format required and includes example data you can use for testing.

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
├── tests/                        # Streamlined test suite
│   ├── __init__.py               # Test package initialization
│   ├── conftest.py               # Minimal shared fixtures
│   ├── integration/              # End-to-end workflow tests
│   │   ├── test_excel_workflow.py
│   │   └── test_end_to_end.py
│   └── unit/                     # Unit tests for core modules
│       ├── test_betting_framework.py
│       ├── test_commission_manager.py
│       ├── test_excel_processor.py
│       └── test_main.py
├── CONTRIBUTING.md               # Contribution guidelines
├── LICENSE                       # MIT license
├── MATHEMATICAL-FOUNDATION.md    # Academic research documentation
├── pyproject.toml                # Dependencies & project configuration
├── README.md                     # This file
├── run.py                        # Main application entry point
├── SECURITY.md                   # Security policy
└── uv.lock                       # Dependency lock file
```

## 🧪 Testing & Development

### Streamlined Test Suite

The project features a comprehensive yet maintainable test suite focused on essential functionality:

```bash
# Run all tests locally (< 30 seconds)
uv run pytest

# Run with coverage report
uv run pytest --cov=src --cov-report=term-missing --cov-report=html

# Run specific test categories
uv run pytest tests/unit/          # Unit tests only
uv run pytest tests/integration/   # Integration tests only

# Run tests in parallel (CI/CD)
uv run pytest -n auto
```

### Test Architecture

- **Simple Structure**: Clean unit and integration test organization
- **Fast Execution**: Complete test suite runs in under 30 seconds locally
- **Essential Coverage**: 87% coverage focusing on core business logic
- **Standard Tools**: Uses pytest without complex custom frameworks
- **UV Integration**: Consistent dependency management with `uv run` commands
- **Offline Testing**: Works completely offline after initial setup

### Test Coverage & Performance

- **176 comprehensive tests** covering all major functionality
  - **146 unit tests** across 4 core modules
  - **30 integration tests** for end-to-end workflows
- **87% overall coverage** exceeding the 80% target
- **Local-First Development**: Immediate feedback with `uv run pytest`
- **CI/CD Integration**: Automated testing on GitHub Actions (< 2 minutes)
- **Multi-Platform**: Validated on Ubuntu, Windows, and macOS

### Testing Commands

| Command | Purpose | Execution Time |
|---------|---------|----------------|
| `uv run pytest` | Run all tests locally | < 30 seconds |
| `uv run pytest tests/unit/` | Unit tests only | < 10 seconds |
| `uv run pytest tests/integration/` | Integration tests only | < 20 seconds |
| `uv run pytest --cov=src` | Tests with coverage | < 35 seconds |

### Test Organization

```text
tests/
├── unit/                         # Fast unit tests for core modules
│   ├── test_betting_framework.py # Kelly criterion calculations (22 tests)
│   ├── test_commission_manager.py # Commission logic (51 tests)
│   ├── test_excel_processor.py   # Excel processing (30 tests)
│   └── test_main.py              # User interface (43 tests)
├── integration/                  # End-to-end workflow tests
│   ├── test_excel_workflow.py    # Excel processing pipeline (15 tests)
│   └── test_end_to_end.py        # Complete application flows (15 tests)
├── conftest.py                   # Minimal shared fixtures
└── __init__.py                   # Test package initialization
```

Tests focus on: mathematical accuracy, input validation, Excel processing workflows, user interface functionality, and error handling.

## 🔧 How It Works

### Core Algorithm

1. **Expected Value Calculation**: $EV = (p \times \frac{1}{\text{Contract Price}}) - 1$
2. **Wharton Filter**: Only bet if EV ≥ 10% (academic research requirement)
3. **Kelly Sizing**: Calculate optimal bet size using Kelly Criterion
4. **Half-Kelly Safety**: Use 50% of Kelly for reduced volatility
5. **Bankroll Cap**: Never bet more than 15% of bankroll
6. **Whole Contracts**: Round down to whole contracts (Robinhood constraint)
7. **Commission Handling**: Include $0.02 per contract commission
8. **Allocation**: Rank by EV%, allocate bankroll to best opportunities first

> 📚 **For detailed mathematical formulas and theoretical foundation**, see the comprehensive **[Mathematical Foundation Documentation](docs/MATHEMATICAL-FOUNDATION.md)**.

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
- `tests/` - Comprehensive test suite with 102 tests including property-based validation

### Configuration

Edit `config/settings.py` to modify:

- `MIN_EV_THRESHOLD = 10.0` - Minimum expected value percentage
- `HALF_KELLY_MULTIPLIER = 0.5` - Kelly fraction multiplier  
- `MAX_BET_PERCENTAGE = 0.15` - Maximum bet as fraction of bankroll
- `COMMISSION_PER_CONTRACT = 0.02` - Commission per contract

## ⚙️ Requirements

- Python 3.13+
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

This framework is built on rigorous academic research and proven mathematical principles. For complete details on the theoretical foundation, empirical validation, and mathematical derivations, see **[Mathematical Foundation Documentation](docs/MATHEMATICAL-FOUNDATION.md)**.

The methodology is primarily based on:

- **Wharton School empirical study** analyzing 10,000+ betting opportunities
- **Kelly Criterion** with Half-Kelly safety implementation
- **Expected value thresholds** validated through academic research
- **Risk management principles** from modern portfolio theory

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

- Run: `uv run pytest -v` to see detailed test output
- Check: Python version (requires 3.13+) and dependencies (`uv sync`)

### Getting Help

1. **Check the examples**: `python -m src.examples.basic_usage`
2. **Run tests**: `uv run pytest` to verify installation  
3. **Review documentation**: See `docs/` directory for comprehensive documentation
4. **Read the guides**: Check `docs/CONTRIBUTING.md` for development info
5. **Create an issue**: Use GitHub issues for bug reports or questions### Performance Tips

- **Large datasets**: Framework handles 100+ games efficiently
- **Memory usage**: Results are optimized for reasonable memory footprint
- **Processing speed**: Typical processing time < 1 second for most datasets

---

**⚠️ Disclaimer**: This framework is for educational purposes. Sports betting involves risk. Never bet more than you can afford to lose. Past performance does not guarantee future results.
