#!/usr/bin/env python3
"""
Wharton Betting Framework - Entry Point

Run this file to start the betting framework application.
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

if __name__ == "__main__":
    from main import main
    main()