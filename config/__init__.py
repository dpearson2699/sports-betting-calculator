"""
Configuration package for Sports Betting Calculator Framework.

Contains settings and constants for the betting framework including
directory paths, Wharton constraints, and Excel formatting options.
"""

from .settings import (
    # Directory paths
    PROJECT_ROOT,
    DATA_DIR,
    INPUT_DIR,
    OUTPUT_DIR,
    
    # File names
    DEFAULT_SAMPLE_FILE,
    DEFAULT_SHEET_NAME,
    
    # Wharton framework constraints
    MIN_EV_THRESHOLD,
    HALF_KELLY_MULTIPLIER,
    MAX_BET_PERCENTAGE,
    MIN_BANKROLL_FOR_PARTIAL,
    
    # Robinhood commission
    COMMISSION_PER_CONTRACT,
    
    # Excel formatting
    MAX_COLUMN_WIDTH,
    COLUMN_PADDING,
)

__all__ = [
    "PROJECT_ROOT",
    "DATA_DIR", 
    "INPUT_DIR",
    "OUTPUT_DIR",
    "DEFAULT_SAMPLE_FILE",
    "DEFAULT_SHEET_NAME",
    "MIN_EV_THRESHOLD",
    "HALF_KELLY_MULTIPLIER", 
    "MAX_BET_PERCENTAGE",
    "MIN_BANKROLL_FOR_PARTIAL",
    "COMMISSION_PER_CONTRACT",
    "MAX_COLUMN_WIDTH",
    "COLUMN_PADDING",
]