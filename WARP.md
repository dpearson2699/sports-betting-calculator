# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

The Wharton Betting Framework is a professional sports betting framework based on academic research that implements the Kelly Criterion with safety constraints for optimal bankroll management. It focuses on expected value analysis with a 10% minimum threshold and uses Half-Kelly sizing for reduced volatility.

## Development Commands

### Setup and Dependencies
```powershell
# Install dependencies using uv (recommended)
uv sync

# Alternative: Install with pip
pip install pandas openpyxl
```

### Running the Application
```powershell
# Run interactive application (choose single bet or batch processing)
uv run main.py

# Alternative: Run with Python directly
python main.py
```

### Development and Testing
Since this project doesn't have formal tests, manual testing should be done with:
```powershell
# Test single bet analysis
uv run main.py
# Choose option 1, enter test values like:
# Weekly bankroll: 100
# Win percentage: 68
# Contract price: 0.45

# Test batch processing 
uv run main.py
# Choose option 2, create sample file first, then process it
```

## Code Architecture

### Core Components

**Main Application (`main.py`)**
- Entry point with interactive CLI interface
- Two modes: single bet analysis and Excel batch processing
- Handles user input validation and error handling

**Betting Framework (`betting_framework.py`)**
- Core algorithmic logic implementing Wharton research principles
- Single function `user_input_betting_framework()` that:
  - Calculates Expected Value: `EV = (Win_Probability / Contract_Price) - 1`
  - Applies 10% EV threshold filter (Wharton requirement)
  - Calculates Kelly Criterion sizing: `(b*p - q) / b`
  - Applies Half-Kelly safety (50% of full Kelly)
  - Enforces 15% maximum bet size cap

**Excel Processor (`excel_processor.py`)**
- Batch processing for multiple games via Excel files
- Handles input validation and file I/O
- Implements bankroll allocation logic (prioritizes by EV%)
- Generates detailed results with rankings and summaries

### Key Algorithms and Constraints

**Safety Features (Critical Business Rules)**
- 10% minimum Expected Value threshold
- Half-Kelly sizing (reduced volatility vs full Kelly)
- 15% maximum bet size (hard cap per bet)
- Bankroll allocation prevents over-betting

**Processing Flow**
1. Input validation (percentage format handling, required fields)
2. Expected Value calculation
3. Wharton threshold filtering
4. Kelly Criterion calculation with safety constraints
5. For batch mode: Ranking by EV% and bankroll allocation

### Excel File Format Requirements

When working with batch processing, Excel files must have these columns:
- `Game`: Game identifier (e.g., "Lakers vs Warriors")  
- `Model Win Percentage`: Model's win probability (0-100 or 0-1)
- `Model Margin`: Optional predicted margin
- `Contract Price`: Sportsbook price per unit

Output includes additional columns for decisions, bet amounts, EV percentages, and final recommendations after bankroll allocation.

## Important Context

### Business Logic Constraints
- This is an academic-based framework, not for production betting
- All calculations follow Wharton research methodology
- Risk management is paramount - multiple safety layers prevent over-betting
- Expected value must exceed 10% to trigger any bet recommendation

### File I/O Patterns
- Creates `*_RESULTS.xlsx` files for batch processing output
- Generates `sample_games.xlsx` for testing/demonstration
- All Excel operations use `openpyxl` engine with pandas

### Error Handling
- Robust input validation for all user inputs
- File existence checking for Excel processing
- Graceful handling of missing optional columns
- Clear error messages for invalid data formats

### Dependencies
- Python 3.11+ required
- Core dependencies: `pandas>=2.3.2`, `openpyxl>=3.1.5`
- Managed via `pyproject.toml` with uv as the recommended package manager