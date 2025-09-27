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

# Robinhood commission
COMMISSION_PER_CONTRACT = 0.02  # $0.02 commission per contract

# Excel formatting
MAX_COLUMN_WIDTH = 50
COLUMN_PADDING = 2