"""Configuration settings for the Wharton Betting Framework."""

import os
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"

# Ensure directories exist
INPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Default file names
DEFAULT_SAMPLE_FILE = "sample_games.xlsx"
DEFAULT_SHEET_NAME = "Games"

# Wharton framework constraints
MIN_EV_THRESHOLD = 10.0  # 10% minimum EV
HALF_KELLY_MULTIPLIER = 0.5  # Use half Kelly for safety
MAX_BET_PERCENTAGE = 0.15  # 15% maximum bet size
MIN_BANKROLL_FOR_PARTIAL = 0.01  # 1% minimum for partial bets

# Commission configuration (replaces hardcoded COMMISSION_PER_CONTRACT)
DEFAULT_COMMISSION_RATE = 0.02  # Robinhood default
CURRENT_COMMISSION_RATE = 0.1  # Will be set by CommissionManager
CURRENT_PLATFORM = "PredictIt"  # Current platform name

# Platform presets
PLATFORM_COMMISSION_RATES = {
    "Robinhood": 0.02,
    "Kalshi": 0.00,
    "PredictIt": 0.10,
    "Polymarket": 0.00,
    "Custom": None
}

def get_commission_rate() -> float:
    """
    Get the current commission rate per contract.
    
    Returns:
        float: Current commission rate, or default if not set
    """
    return CURRENT_COMMISSION_RATE if CURRENT_COMMISSION_RATE is not None else DEFAULT_COMMISSION_RATE

# Backward compatibility - COMMISSION_PER_CONTRACT now returns current rate
def _get_commission_per_contract() -> float:
    """Backward compatibility function that returns current commission rate."""
    return get_commission_rate()

# Keep COMMISSION_PER_CONTRACT as a property for backward compatibility
COMMISSION_PER_CONTRACT = _get_commission_per_contract()

# Excel formatting
MAX_COLUMN_WIDTH = 50
COLUMN_PADDING = 2