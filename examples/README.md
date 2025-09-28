# Examples Directory

This directory contains practical examples demonstrating how to use the Sports Betting Calculator.

## Available Examples

### 1. Basic Usage (`basic_usage.py`)

Demonstrates fundamental single-bet analysis:

- Single bet evaluation
- Safety constraint demonstrations
- Dual format input handling (percentage vs decimal, cents vs dollars)

**Run with:**

```bash
python examples/basic_usage.py
```

### 2. Excel Batch Processing (`excel_batch_example.py`)

Shows advanced batch processing capabilities:

- Multiple game analysis from Excel data
- Bankroll allocation priority system
- Wharton constraint enforcement in batch mode

**Run with:**

```bash
python examples/excel_batch_example.py
```

## What These Examples Teach

### Core Concepts

- **Expected Value Calculation**: How the calculator determines betting edges
- **Kelly Criterion**: Optimal bet sizing methodology
- **Wharton Safety Constraints**: Academic-backed risk management
- **Whole Contract Logic**: Robinhood-specific adjustments

### Practical Applications

- Single bet analysis workflow
- Multi-game bankroll allocation
- Input format flexibility
- Error handling and edge cases

## Learning Path

1. **Start with `basic_usage.py`** - Learn fundamental concepts
2. **Move to `excel_batch_example.py`** - Understand batch processing
3. **Try the real application**: `python run.py`
4. **Create your own Excel files** using the sample format

## Example Data Format

All examples use this Excel structure:

| Column | Description | Example |
|--------|-------------|---------|
| Game | Game identifier | "Lakers vs Warriors" |
| Model Win Percentage | Win probability | 68 (or 0.68) |
| Contract Price | Price per contract | 0.45 (or 45) |
| Model Margin | Predicted margin (optional) | 5.5 |

## Key Features Demonstrated

### Input Flexibility

- **Percentages**: 68 or 0.68 for 68%
- **Prices**: 45 or 0.45 for 45 cents
- **Mixed formats**: Framework handles all combinations

### Safety Features

- **10% EV Threshold**: Minimum expected value (Wharton research)
- **Half-Kelly Sizing**: 50% of full Kelly for reduced volatility
- **15% Bankroll Cap**: Maximum bet size regardless of Kelly recommendation
- **Whole Contracts**: Integer contract purchases only
- **Commission Handling**: $0.02 per contract included in all calculations

### Batch Processing Intelligence

- **EV-Based Ranking**: Highest expected value games prioritized
- **Bankroll Allocation**: Prevents over-betting across multiple games
- **Partial Bet Logic**: Smart handling of insufficient funds
- **Priority System**: Better opportunities get full allocation first

## Running the Examples

### Prerequisites

```bash
# From the project root directory
uv sync  # Install dependencies
```

### Individual Examples

```bash
# Basic usage patterns
python examples/basic_usage.py

# Excel batch processing
python examples/excel_batch_example.py
```

### Expected Output

Each example provides:

- Clear explanations of what's being demonstrated
- Step-by-step analysis results
- Key insights about the framework's behavior
- Next steps for further exploration

## Next Steps

After running these examples:

1. **Try the main application**: `python run.py`
2. **Create your own Excel files** with real game data
3. **Experiment with different bankroll amounts** to see allocation effects
4. **Read the comprehensive documentation** in `README.md`
5. **Explore the test suite** in `tests/` for more usage patterns

## Common Questions

**Q: Why do some high-EV bets get rejected?**
A: The framework enforces a 10% minimum EV threshold based on Wharton research. Lower EV bets don't meet academic standards for profitable long-term betting.

**Q: Why are bet amounts sometimes smaller than recommended?**
A: Two reasons: (1) 15% bankroll cap for safety, (2) whole contract constraint rounds down fractional contracts.

**Q: How does bankroll allocation work?**
A: Games are ranked by EV percentage (highest first), then allocated sequentially until bankroll is exhausted. Higher EV games get priority.

**Q: What if I want to bet more aggressively?**
A: The safety constraints are non-negotiable and based on academic research. The framework prioritizes long-term profitability over short-term gains.
