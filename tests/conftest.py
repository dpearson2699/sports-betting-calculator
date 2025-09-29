"""
Minimal pytest configuration and fixtures for the testing suite.
"""

import pytest
import pandas as pd
from pathlib import Path

@pytest.fixture
def sample_betting_data():
    """Sample betting data for unit tests."""
    return {
        'weekly_bankroll': 1000.0,
        'model_win_percentage': 0.65,
        'contract_price': 0.27
    }


@pytest.fixture
def sample_excel_data():
    """Sample Excel data as DataFrame for testing."""
    return pd.DataFrame({
        'Game': ['Team A vs Team B'],
        'Model Win %': [0.65],
        'Contract Price': [0.27]
    })


@pytest.fixture
def temp_excel_file(tmp_path: Path) -> Path:
    """Create a temporary Excel file for integration tests."""
    excel_path: Path = tmp_path / "test_data.xlsx"
    df = pd.DataFrame({
        'Game': ['Team A vs Team B', 'Team C vs Team D'],
        'Model Win %': [0.65, 0.58],
        'Contract Price': [0.27, 0.45]
    })
    df.to_excel(excel_path, index=False)
    return excel_path