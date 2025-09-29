# Configuration settings for the sports betting calculator

from pathlib import Path
from typing import TypedDict, Dict

# Directory paths
PROJECT_ROOT = Path(__file__).parent.parent.parent  # Go up from src/config/settings.py to project root
BASE_DIR = PROJECT_ROOT
DATA_DIR = BASE_DIR / "data"
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"

# Ensure directories exist
INPUT_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# File settings
DEFAULT_SAMPLE_FILE = "sample_betting_data.xlsx"
DEFAULT_SHEET_NAME = "Games"

# Wharton framework constraints
MIN_EV_THRESHOLD = 0.10  # 10% minimum EV threshold
HALF_KELLY_MULTIPLIER = 0.5  # Use half-Kelly for conservative betting
MAX_BET_PERCENTAGE = 0.25  # Maximum 25% of bankroll per bet
MIN_BANKROLL_FOR_PARTIAL = 100  # Minimum bankroll for partial bet allocation

# Commission settings
DEFAULT_COMMISSION_RATE = 0.02
CURRENT_COMMISSION_RATE = 0.02  # Will be set by CommissionManager
CURRENT_PLATFORM = "Robinhood"  # Current platform name
PLATFORM_COMMISSION_RATES = {
    "Robinhood": 0.02,
    "Kalshi": 0.00,
    "PredictIt": 0.05,
    "Custom": 0.02
}

def get_commission_rate():
    """Get current commission rate."""
    return CURRENT_COMMISSION_RATE or DEFAULT_COMMISSION_RATE

# Backward compatibility
COMMISSION_PER_CONTRACT = DEFAULT_COMMISSION_RATE

# Column width settings (legacy - kept for backward compatibility)
MAX_COLUMN_WIDTH = 50
COLUMN_PADDING = 2

# Autofit configuration system
class FontConfig(TypedDict):
    name: str
    size: int

class ColumnOverride(TypedDict):
    min: int
    max: int

class AutofitConfig(TypedDict):
    default_font: FontConfig
    padding: int
    min_width: int
    max_width: int
    column_overrides: Dict[str, ColumnOverride]

AUTOFIT_CONFIG: AutofitConfig = {
    'default_font': {
        'name': 'Calibri',
        'size': 11
    },
    'padding': 2,  # Extra space around content
    'min_width': 8,  # Minimum column width
    'max_width': 50,  # Maximum column width
    'column_overrides': {
        # Column-specific min/max overrides based on content analysis
        'Game': {'min': 10, 'max': 30},
        'Model Win Percentage': {'min': 15, 'max': 20},
        'Model Margin': {'min': 10, 'max': 15},
        'Contract Price': {'min': 12, 'max': 18},
        'Win %': {'min': 8, 'max': 12},
        'Contract Price (¢)': {'min': 12, 'max': 18},
        'Price (¢)': {'min': 8, 'max': 12},
        'Margin': {'min': 8, 'max': 15},
        'EV Percentage': {'min': 10, 'max': 16},
        'Edge %': {'min': 8, 'max': 10},
        'Expected Value EV': {'min': 10, 'max': 18},
        'EV $': {'min': 8, 'max': 12},
        'Net Profit': {'min': 10, 'max': 15},
        'Win Profit $': {'min': 10, 'max': 15},
        'Target Bet Amount': {'min': 12, 'max': 18},
        'Bet Amount': {'min': 10, 'max': 18},
        'Cumulative Bet Amount': {'min': 15, 'max': 22},
        'Allocated $': {'min': 10, 'max': 15},
        'Bet Percentage': {'min': 12, 'max': 18},
        'Stake % Bankroll': {'min': 12, 'max': 18},
        'Unused Amount': {'min': 10, 'max': 15},
        'Contracts To Buy': {'min': 10, 'max': 15},
        'Contracts': {'min': 8, 'max': 12},
        'Adjusted Price': {'min': 10, 'max': 15},
        'Contract Cost': {'min': 10, 'max': 15},
        'Decision': {'min': 10, 'max': 16},
        'Final Recommendation': {'min': 15, 'max': 35},
        'Final': {'min': 8, 'max': 25},
        'Reason': {'min': 15, 'max': 50},
        'Commission Rate': {'min': 12, 'max': 18},
        'Platform': {'min': 8, 'max': 15}
    }
}

# Configuration flag to control autofit behavior
USE_NEW_AUTOFIT = True  # Set to False to use legacy character-count method

def migrate_legacy_column_width_rules(legacy_rules: Dict[str, Dict[str, int]]) -> AutofitConfig:
    """
    Convert legacy column_width_rules format to new AUTOFIT_CONFIG format.
    
    Args:
        legacy_rules (dict): Dictionary with column names as keys and 
                           {'min': int, 'max': int} as values
    
    Returns:
        dict: Updated AUTOFIT_CONFIG with migrated column overrides
    """
    import copy
    
    # Start with current AUTOFIT_CONFIG
    migrated_config = copy.deepcopy(AUTOFIT_CONFIG)
    
    # Add legacy rules to column_overrides
    if legacy_rules:
        for column_name, rules in legacy_rules.items():
            if 'min' in rules and 'max' in rules:
                migrated_config['column_overrides'][column_name] = {
                    'min': rules['min'],
                    'max': rules['max']
                }
    
    return migrated_config

def get_autofit_config():
    """
    Get the current autofit configuration, applying any legacy migrations if needed.
    
    Returns:
        dict: Current autofit configuration (copy to prevent modification)
    """
    import copy
    return copy.deepcopy(AUTOFIT_CONFIG)