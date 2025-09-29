"""
Sports Betting Calculator Framework - Source Package

Academic research-based event contract betting framework implementing 
Kelly Criterion with empirically-validated safety constraints.

Core modules:
- betting_framework: Kelly Criterion calculations and Wharton methodology
- excel_processor: Batch processing and bankroll allocation logic  
- main: CLI interface and user interaction
"""

__version__ = "0.1.0"

# Import key functions for package-level access
from .betting_framework import (
    normalize_contract_price,
    calculate_whole_contracts,
    user_input_betting_framework,
)

# Make examples available at package level
from . import examples

from .excel_processor import (
    process_betting_excel,
    create_sample_excel_in_input_dir,
    list_available_input_files,
    get_input_file_path,
    apply_bankroll_allocation,
)

from .main import main

__all__ = [
    # Core betting functions
    "normalize_contract_price",
    "calculate_whole_contracts", 
    "user_input_betting_framework",
    
    # Excel processing functions
    "process_betting_excel",
    "create_sample_excel_in_input_dir",
    "list_available_input_files",
    "get_input_file_path",
    "apply_bankroll_allocation",
    
    # Main entry point
    "main",
    
    # Version
    "__version__",
]