"""
Unit tests for betting_framework.py

Tests the core Kelly criterion calculations and betting logic functions
with clear arrange-act-assert structure.
"""

import pytest
import sys
import os

from src.betting_framework import (
    normalize_contract_price,
    calculate_whole_contracts,
    user_input_betting_framework
)


class TestNormalizeContractPrice:
    """Test contract price normalization functionality."""
    
    def test_normalize_cents_format(self):
        """Test normalization of prices in cents format (>=1.0)."""
        # Arrange
        price_in_cents = 27
        expected = 0.27
        
        # Act
        result = normalize_contract_price(price_in_cents)
        
        # Assert
        assert result == expected
    
    def test_normalize_dollar_format(self):
        """Test normalization of prices already in dollar format (<1.0)."""
        # Arrange
        price_in_dollars = 0.27
        expected = 0.27
        
        # Act
        result = normalize_contract_price(price_in_dollars)
        
        # Assert
        assert result == expected
    
    def test_normalize_edge_case_one_dollar(self):
        """Test normalization of exactly 1.0 (treated as cents)."""
        # Arrange
        price = 1.0
        expected = 0.01
        
        # Act
        result = normalize_contract_price(price)
        
        # Assert
        assert result == expected
    
    def test_normalize_large_cents_value(self):
        """Test normalization of large cents values."""
        # Arrange
        price_in_cents = 99
        expected = 0.99
        
        # Act
        result = normalize_contract_price(price_in_cents)
        
        # Assert
        assert result == expected
    
    def test_normalize_small_dollar_value(self):
        """Test normalization of small dollar values."""
        # Arrange
        price_in_dollars = 0.01
        expected = 0.01
        
        # Act
        result = normalize_contract_price(price_in_dollars)
        
        # Assert
        assert result == expected


class TestCalculateWholeContracts:
    """Test whole contract calculation functionality."""
    
    def test_calculate_whole_contracts_basic(self):
        """Test basic whole contract calculation without commission."""
        # Arrange
        target_bet_amount = 100.0
        contract_price = 0.25
        commission_per_contract = 0.0
        
        # Act
        result = calculate_whole_contracts(target_bet_amount, contract_price, commission_per_contract)
        
        # Assert
        assert result['whole_contracts'] == 400  # 100 / 0.25 = 400
        assert result['actual_bet_amount'] == 100.0
        assert result['unused_amount'] == 0.0
        assert result['adjusted_price'] == 0.25
    
    def test_calculate_whole_contracts_with_commission(self):
        """Test whole contract calculation with commission."""
        # Arrange
        target_bet_amount = 100.0
        contract_price = 0.25
        commission_per_contract = 0.05
        
        # Act
        result = calculate_whole_contracts(target_bet_amount, contract_price, commission_per_contract)
        
        # Assert
        expected_adjusted_price = 0.30  # 0.25 + 0.05
        expected_contracts = 333  # int(100 / 0.30) = 333
        expected_actual_amount = 333 * 0.30  # 99.9
        expected_unused = 100.0 - expected_actual_amount  # 0.1
        
        assert result['whole_contracts'] == expected_contracts
        assert abs(result['actual_bet_amount'] - expected_actual_amount) < 0.001
        assert abs(result['unused_amount'] - expected_unused) < 0.001
        assert result['adjusted_price'] == expected_adjusted_price
    
    def test_calculate_whole_contracts_insufficient_funds(self):
        """Test calculation when target amount is insufficient for one contract."""
        # Arrange
        target_bet_amount = 0.20
        contract_price = 0.25
        commission_per_contract = 0.05
        
        # Act
        result = calculate_whole_contracts(target_bet_amount, contract_price, commission_per_contract)
        
        # Assert
        assert result['whole_contracts'] == 0
        assert result['actual_bet_amount'] == 0.0
        assert result['unused_amount'] == 0.20
        assert result['adjusted_price'] == 0.30
    
    def test_calculate_whole_contracts_exact_amount(self):
        """Test calculation when target amount exactly matches contract cost."""
        # Arrange
        target_bet_amount = 30.0
        contract_price = 0.25
        commission_per_contract = 0.05
        
        # Act
        result = calculate_whole_contracts(target_bet_amount, contract_price, commission_per_contract)
        
        # Assert
        expected_contracts = 100  # 30.0 / 0.30 = 100
        assert result['whole_contracts'] == expected_contracts
        assert result['actual_bet_amount'] == 30.0
        assert result['unused_amount'] == 0.0


class TestUserInputBettingFramework:
    """Test the main betting framework function."""
    
    def test_profitable_bet_basic(self):
        """Test a basic profitable bet scenario."""
        # Arrange
        weekly_bankroll = 1000.0
        model_win_percentage = 0.65  # 65% win probability
        contract_price = 0.27  # 27 cents
        commission_per_contract = 0.0
        
        # Act
        result = user_input_betting_framework(
            weekly_bankroll, model_win_percentage, contract_price, 
            commission_per_contract=commission_per_contract
        )
        
        # Assert
        assert result['decision'] == 'BET'
        assert result['bet_amount'] > 0
        assert result['ev_percentage'] > 10.0  # Above Wharton threshold
        assert 'contracts_to_buy' in result
        assert result['contracts_to_buy'] > 0
        assert result['wharton_compliant'] is True
    
    def test_unprofitable_bet_low_ev(self):
        """Test rejection of bet with EV below Wharton threshold."""
        # Arrange
        weekly_bankroll = 1000.0
        model_win_percentage = 0.52  # 52% win probability (low)
        contract_price = 0.48  # 48 cents (high price)
        commission_per_contract = 0.0
        
        # Act
        result = user_input_betting_framework(
            weekly_bankroll, model_win_percentage, contract_price,
            commission_per_contract=commission_per_contract
        )
        
        # Assert
        assert result['decision'] == 'NO BET'
        assert result['bet_amount'] == 0
        assert result['ev_percentage'] < 10.0
        assert 'EV' in result['reason']
        assert 'threshold' in result['reason']
    
    def test_negative_kelly_fraction(self):
        """Test rejection of bet with negative Kelly fraction."""
        # Arrange
        weekly_bankroll = 1000.0
        model_win_percentage = 0.30  # 30% win probability (lower)
        contract_price = 0.60  # 60 cents (higher price)
        commission_per_contract = 0.0
        
        # Act
        result = user_input_betting_framework(
            weekly_bankroll, model_win_percentage, contract_price,
            commission_per_contract=commission_per_contract
        )
        
        # Assert
        assert result['decision'] == 'NO BET'
        assert result['bet_amount'] == 0
        assert 'Kelly' in result['reason'] or result['ev_percentage'] < 10.0
    
    def test_insufficient_funds_for_one_contract(self):
        """Test rejection when target bet amount can't buy one whole contract."""
        # Arrange
        weekly_bankroll = 1.0  # Very small bankroll
        model_win_percentage = 0.65
        contract_price = 0.27
        commission_per_contract = 0.05  # High commission
        
        # Act
        result = user_input_betting_framework(
            weekly_bankroll, model_win_percentage, contract_price,
            commission_per_contract=commission_per_contract
        )
        
        # Assert
        assert result['decision'] == 'NO BET'
        assert result['bet_amount'] == 0
        assert 'insufficient' in result['reason']
        assert 'whole contract' in result['reason']
    
    def test_percentage_format_conversion(self):
        """Test conversion of win percentage from percentage format (>1) to decimal."""
        # Arrange
        weekly_bankroll = 1000.0
        model_win_percentage = 65.0  # 65% in percentage format
        contract_price = 0.27
        commission_per_contract = 0.0
        
        # Act
        result = user_input_betting_framework(
            weekly_bankroll, model_win_percentage, contract_price,
            commission_per_contract=commission_per_contract
        )
        
        # Assert
        assert result['decision'] == 'BET'
        assert result['bet_amount'] > 0
        # Should produce same result as 0.65 decimal format
    
    def test_cents_format_price_conversion(self):
        """Test conversion of contract price from cents format to dollars."""
        # Arrange
        weekly_bankroll = 1000.0
        model_win_percentage = 0.65
        contract_price = 27  # 27 cents in cents format
        commission_per_contract = 0.0
        
        # Act
        result = user_input_betting_framework(
            weekly_bankroll, model_win_percentage, contract_price,
            commission_per_contract=commission_per_contract
        )
        
        # Assert
        assert result['decision'] == 'BET'
        assert result['normalized_price'] == 0.27
        assert result['bet_amount'] > 0
    
    def test_commission_impact_on_ev(self):
        """Test how commission affects EV calculations."""
        # Arrange
        weekly_bankroll = 1000.0
        model_win_percentage = 0.60
        contract_price = 0.30
        commission_per_contract = 0.10  # High commission
        
        # Act
        result = user_input_betting_framework(
            weekly_bankroll, model_win_percentage, contract_price,
            commission_per_contract=commission_per_contract
        )
        
        # Assert
        # Commission should reduce EV significantly
        assert 'commission_per_contract' in result
        assert result['commission_per_contract'] == 0.10
        if result['decision'] == 'NO BET':
            assert 'commission' in result.get('reason', '').lower() or result['ev_percentage'] < 10.0
    
    def test_maximum_bet_constraint(self):
        """Test that bet amount is capped at 15% of bankroll."""
        # Arrange
        weekly_bankroll = 1000.0
        model_win_percentage = 0.90  # Very high win probability
        contract_price = 0.10  # Very low price (high EV)
        commission_per_contract = 0.0
        
        # Act
        result = user_input_betting_framework(
            weekly_bankroll, model_win_percentage, contract_price,
            commission_per_contract=commission_per_contract
        )
        
        # Assert
        if result['decision'] == 'BET':
            # Bet percentage should not exceed 15%
            assert result['bet_percentage'] <= 15.1  # Small tolerance for rounding
    
    def test_half_kelly_application(self):
        """Test that Half Kelly (Wharton optimal) is applied."""
        # Arrange
        weekly_bankroll = 1000.0
        model_win_percentage = 0.65
        contract_price = 0.27
        commission_per_contract = 0.0
        
        # Act
        result = user_input_betting_framework(
            weekly_bankroll, model_win_percentage, contract_price,
            commission_per_contract=commission_per_contract
        )
        
        # Assert
        if result['decision'] == 'BET':
            # Should be using Half Kelly (not Full Kelly)
            assert result['wharton_compliant'] is True
            # Bet percentage should be reasonable (not too aggressive)
            assert result['bet_percentage'] < 20.0
    
    def test_whole_contracts_only_constraint(self):
        """Test that only whole contracts are purchased."""
        # Arrange
        weekly_bankroll = 1000.0
        model_win_percentage = 0.65
        contract_price = 0.27
        commission_per_contract = 0.02
        
        # Act
        result = user_input_betting_framework(
            weekly_bankroll, model_win_percentage, contract_price,
            commission_per_contract=commission_per_contract
        )
        
        # Assert
        if result['decision'] == 'BET':
            assert isinstance(result['contracts_to_buy'], int)
            assert result['contracts_to_buy'] > 0
            assert result['whole_contracts_only'] is True
            assert 'unused_amount' in result  # Some money left over due to rounding
    
    def test_edge_case_zero_commission(self):
        """Test behavior with zero commission."""
        # Arrange
        weekly_bankroll = 1000.0
        model_win_percentage = 0.65
        contract_price = 0.27
        commission_per_contract = 0.0
        
        # Act
        result = user_input_betting_framework(
            weekly_bankroll, model_win_percentage, contract_price,
            commission_per_contract=commission_per_contract
        )
        
        # Assert
        assert result['commission_per_contract'] == 0.0
        if result['decision'] == 'BET':
            assert result['adjusted_price'] == result['normalized_price']
    
    def test_edge_case_100_percent_win_probability(self):
        """Test behavior with 100% win probability."""
        # Arrange
        weekly_bankroll = 1000.0
        model_win_percentage = 1.0  # 100% win probability
        contract_price = 0.27
        commission_per_contract = 0.0
        
        # Act
        result = user_input_betting_framework(
            weekly_bankroll, model_win_percentage, contract_price,
            commission_per_contract=commission_per_contract
        )
        
        # Assert
        assert result['decision'] == 'BET'
        # Should hit maximum bet constraint (15%)
        assert result['bet_percentage'] <= 15.1
    
    def test_edge_case_very_small_bankroll(self):
        """Test behavior with very small bankroll."""
        # Arrange
        weekly_bankroll = 1.0  # $1 bankroll
        model_win_percentage = 0.65
        contract_price = 0.27
        commission_per_contract = 0.0
        
        # Act
        result = user_input_betting_framework(
            weekly_bankroll, model_win_percentage, contract_price,
            commission_per_contract=commission_per_contract
        )
        
        # Assert
        # Should likely result in NO BET due to insufficient funds for one contract
        if result['decision'] == 'NO BET':
            assert 'insufficient' in result['reason'] or result['ev_percentage'] < 10.0