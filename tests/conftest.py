"""Test fixtures and utilities for the betting framework tests"""

import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path
from typing import Dict, Any, List, Optional


@pytest.fixture
def sample_bankroll():
    """Standard test bankroll amount"""
    return 100.0


@pytest.fixture
def wharton_test_cases():
    """Test cases that validate Wharton methodology constraints"""
    return [
        # Format: (win_percentage, contract_price, expected_decision, description)
        (68.0, 0.45, "BET", "High EV case from documentation"),
        (55.0, 0.50, "NO BET", "Below 10% EV threshold"),
        (75.0, 0.20, "BET", "High EV, should cap at 15% bankroll"),
        (60.0, 0.99, "NO BET", "Extremely low EV"),
        (51.0, 0.49, "NO BET", "Barely positive EV but below threshold"),
        (80.0, 0.10, "BET", "Very high EV case"),
    ]


@pytest.fixture
def edge_case_test_data():
    """Edge cases for input validation and boundary testing"""
    return [
        # Format: (win_percentage, contract_price, bankroll, expected_behavior)
        (0.68, 45, 100, "dual_format_percentage_and_price"),  # Both formats
        (100.0, 0.01, 100, "extreme_high_win_low_price"),
        (1.0, 0.99, 100, "extreme_low_win_high_price"),
        (50.0, 0.50, 1, "tiny_bankroll"),
        (70.0, 0.30, 1000000, "huge_bankroll"),
    ]


@pytest.fixture
def sample_excel_data():
    """Sample data for Excel processing tests"""
    return pd.DataFrame({
        'Game': [
            'Team A vs Team B',
            'Team C vs Team D', 
            'Team E vs Team F',
            'Team G vs Team H',
            'Team I vs Team J'
        ],
        'Model Win Percentage': [68.0, 75.0, 55.0, 80.0, 51.0],
        'Contract Price': [0.45, 0.20, 0.50, 0.10, 0.49],
        'Model Margin': [5.5, 8.2, 2.1, 15.3, 1.2]
    })


@pytest.fixture
def invalid_excel_data():
    """Invalid Excel data for testing error handling"""
    return pd.DataFrame({
        'Wrong Column': ['Game 1', 'Game 2'],
        'Bad Data': ['not a number', 'also not a number'],
        'Missing Required': [None, None]
    })


@pytest.fixture
def temp_excel_file(sample_excel_data):
    """Creates a temporary Excel file with sample data"""
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
        sample_excel_data.to_excel(tmp.name, sheet_name='Games', index=False)
        yield tmp.name
    os.unlink(tmp.name)


@pytest.fixture
def temp_invalid_excel_file(invalid_excel_data):
    """Creates a temporary Excel file with invalid data"""
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
        invalid_excel_data.to_excel(tmp.name, sheet_name='Games', index=False)
        yield tmp.name
    os.unlink(tmp.name)


@pytest.fixture
def expected_bet_result():
    """Expected structure for BET decision results"""
    return {
        'decision': 'BET',
        'ev_percentage': float,  # Will be calculated
        'bet_amount': float,     # Will be calculated 
        'contracts_to_buy': int, # Will be calculated
        'target_bet_amount': float,
        'unused_amount': float,
        'bet_percentage': float
    }


@pytest.fixture
def expected_no_bet_result():
    """Expected structure for NO BET decision results"""
    return {
        'decision': 'NO BET',
        'ev_percentage': float,  # Will be calculated
        'bet_amount': 0.0,
        'reason': str  # Will contain explanation
    }


@pytest.fixture
def bankroll_allocation_scenarios():
    """Test scenarios for bankroll allocation logic"""
    return [
        {
            'name': 'sufficient_bankroll',
            'bankroll': 1000,
            'games': [
                {'ev': 15.0, 'recommended_bet': 100},
                {'ev': 12.0, 'recommended_bet': 80},
                {'ev': 10.5, 'recommended_bet': 60}
            ],
            'expected_total_allocated': 240
        },
        {
            'name': 'insufficient_bankroll',
            'bankroll': 100,
            'games': [
                {'ev': 20.0, 'recommended_bet': 50},
                {'ev': 18.0, 'recommended_bet': 40},
                {'ev': 15.0, 'recommended_bet': 30},
                {'ev': 12.0, 'recommended_bet': 25}
            ],
            'expected_partial_bets': True
        }
    ]


@pytest.fixture
def mock_excel_paths():
    """Mock file paths for testing"""
    return {
        'input_dir': Path('data/input'),
        'output_dir': Path('data/output'),
        'sample_file': Path('data/input/sample_games.xlsx'),
        'output_file': Path('data/output/sample_games_RESULTS.xlsx')
    }


class TestDataBuilder:
    """Helper class to build test data dynamically"""
    
    @staticmethod
    def create_game_data(win_pct: float, price: float, margin: Optional[float] = None) -> Dict[str, Any]:
        """Create a single game data entry"""
        game_data = {
            'Game': f'Test Game (Win: {win_pct}%, Price: ${price})',
            'Model Win Percentage': win_pct,
            'Contract Price': price,
        }
        
        if margin is not None:
            game_data['Model Margin'] = margin
        
        return game_data
    
    @staticmethod
    def create_excel_dataframe(games: List[Dict[str, Any]]) -> pd.DataFrame:
        """Create a DataFrame from game data"""
        return pd.DataFrame(games)
    
    @staticmethod
    def expected_ev_calculation(win_pct: float, price: float) -> float:
        """Calculate expected EV for validation"""
        win_probability = win_pct / 100.0 if win_pct > 1 else win_pct
        normalized_price = price / 100.0 if price >= 1.0 else price
        return (win_probability * (1/normalized_price) - 1) * 100


@pytest.fixture
def test_data_builder():
    """Provides TestDataBuilder instance"""
    return TestDataBuilder()


# Pytest configuration helpers
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test") 
    config.addinivalue_line("markers", "excel: mark test as requiring Excel file operations")
    config.addinivalue_line("markers", "slow: mark test as slow running")


def pytest_collection_modifyitems(config, items):
    """Auto-mark tests based on location"""
    for item in items:
        # Mark unit tests
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        
        # Mark integration tests  
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # Mark Excel tests
        if "excel" in item.name.lower() or "excel" in str(item.fspath):
            item.add_marker(pytest.mark.excel)