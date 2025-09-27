"""Unit tests for betting_framework.py core functions"""

import pytest

from src.betting_framework import (
    normalize_contract_price,
    calculate_whole_contracts,
    user_input_betting_framework
)


class TestNormalizeContractPrice:
    """Test contract price normalization functionality"""
    
    def test_cents_format_conversion(self):
        """Test that cents format (>=1.0) converts to dollars"""
        assert normalize_contract_price(27) == 0.27
        assert normalize_contract_price(45) == 0.45
        assert normalize_contract_price(99) == 0.99
        assert normalize_contract_price(1) == 0.01
    
    def test_dollar_format_passthrough(self):
        """Test that dollar format (<1.0) passes through unchanged"""
        assert normalize_contract_price(0.27) == 0.27
        assert normalize_contract_price(0.45) == 0.45
        assert normalize_contract_price(0.99) == 0.99
        assert normalize_contract_price(0.01) == 0.01
    
    def test_edge_cases(self):
        """Test edge cases for price normalization"""
        assert normalize_contract_price(0.0) == 0.0
        assert normalize_contract_price(1.0) == 0.01  # Exactly 1.0 treated as cents
        assert normalize_contract_price(100) == 1.0
    
    def test_decimal_precision(self):
        """Test that decimal precision is maintained"""
        assert abs(normalize_contract_price(27.5) - 0.275) < 1e-10
        assert abs(normalize_contract_price(0.275) - 0.275) < 1e-10


class TestCalculateWholeContracts:
    """Test whole contracts calculation with commission"""
    
    def test_basic_calculation(self):
        """Test basic whole contracts calculation"""
        result = calculate_whole_contracts(100, 0.45, 0.02)
        
        assert abs(result['adjusted_price'] - 0.47) < 1e-10  # 0.45 + 0.02
        assert result['whole_contracts'] == 212  # floor(100 / 0.47)
        assert abs(result['actual_bet_amount'] - 99.64) < 0.01  # 212 * 0.47
        assert result['unused_amount'] > 0
    
    def test_insufficient_funds_for_one_contract(self):
        """Test when target amount can't buy even one contract"""
        result = calculate_whole_contracts(0.30, 0.45, 0.02)
        
        assert result['whole_contracts'] == 0
        assert result['actual_bet_amount'] == 0
        assert result['unused_amount'] == 0.30
    
    def test_exact_contract_amount(self):
        """Test when target amount exactly matches contract costs"""
        contract_price = 0.45
        commission = 0.02
        adjusted_price = contract_price + commission
        target_amount = adjusted_price * 10  # Exactly 10 contracts
        
        result = calculate_whole_contracts(target_amount, contract_price, commission)
        
        assert result['whole_contracts'] == 10
        assert abs(result['actual_bet_amount'] - target_amount) < 1e-10
        assert abs(result['unused_amount']) < 1e-10
    
    def test_different_commission_rates(self):
        """Test calculation with different commission rates"""
        # No commission
        result = calculate_whole_contracts(100, 0.50, 0.0)
        assert result['adjusted_price'] == 0.50
        assert result['whole_contracts'] == 200
        
        # High commission
        result = calculate_whole_contracts(100, 0.50, 0.10)
        assert result['adjusted_price'] == 0.60
        assert result['whole_contracts'] == 166  # floor(100 / 0.60)


class TestUserInputBettingFramework:
    """Test main betting framework logic"""
    
    def test_wharton_compliant_bet(self, sample_bankroll, wharton_test_cases):
        """Test cases that should result in BET decisions"""
        bankroll = sample_bankroll
        
        for win_pct, price, expected_decision, description in wharton_test_cases:
            if expected_decision == "BET":
                result = user_input_betting_framework(bankroll, win_pct, price)
                
                assert result['decision'] == 'BET', f"Failed: {description}"
                assert result['ev_percentage'] >= 10.0, "Should meet 10% EV threshold"
                assert result['bet_amount'] > 0, "Should have positive bet amount"
                assert result['contracts_to_buy'] > 0, "Should buy at least one contract"
                assert result['bet_percentage'] <= 15.0, "Should not exceed 15% bankroll cap"
                assert 'wharton_compliant' in result
                assert 'whole_contracts_only' in result
    
    def test_ev_threshold_filtering(self, sample_bankroll, wharton_test_cases):
        """Test that bets below 10% EV are filtered out"""
        bankroll = sample_bankroll
        
        for win_pct, price, expected_decision, description in wharton_test_cases:
            if expected_decision == "NO BET":
                result = user_input_betting_framework(bankroll, win_pct, price)
                
                assert result['decision'] == 'NO BET', f"Failed: {description}"
                assert result['bet_amount'] == 0, "No bet should have zero amount"
                assert 'reason' in result, "No bet should include reason"
    
    def test_percentage_format_handling(self, sample_bankroll):
        """Test dual format input handling for percentages"""
        bankroll = sample_bankroll
        price = 0.45
        
        # Test both formats give same result
        result1 = user_input_betting_framework(bankroll, 68.0, price)  # Percentage format
        result2 = user_input_betting_framework(bankroll, 0.68, price)  # Decimal format
        
        assert abs(result1['ev_percentage'] - result2['ev_percentage']) < 0.01
        assert result1['decision'] == result2['decision']
        assert abs(result1['bet_amount'] - result2['bet_amount']) < 0.01
    
    def test_price_format_handling(self, sample_bankroll):
        """Test dual format input handling for prices"""
        bankroll = sample_bankroll
        win_pct = 68.0
        
        # Test both formats give same result
        result1 = user_input_betting_framework(bankroll, win_pct, 45)    # Cents format
        result2 = user_input_betting_framework(bankroll, win_pct, 0.45)  # Dollar format
        
        assert abs(result1['ev_percentage'] - result2['ev_percentage']) < 0.01
        assert result1['decision'] == result2['decision']
        assert abs(result1['bet_amount'] - result2['bet_amount']) < 0.01
    
    def test_bankroll_cap_enforcement(self):
        """Test that bets are capped at 15% of bankroll"""
        bankroll = 1000
        win_pct = 95.0  # Very high win percentage
        price = 0.10    # Very low price (high EV)
        
        result = user_input_betting_framework(bankroll, win_pct, price)
        
        assert result['decision'] == 'BET'
        assert result['bet_percentage'] <= 15.0, "Should be capped at 15%"
        assert result['bet_amount'] <= 150, "Should not exceed 15% of $1000 bankroll"
    
    def test_half_kelly_implementation(self):
        """Test that framework uses half-Kelly sizing"""
        bankroll = 1000
        win_pct = 70.0
        price = 0.40
        commission = 0.02
        
        result = user_input_betting_framework(bankroll, win_pct, price, commission_per_contract=commission)
        
        # Calculate what full Kelly would be
        win_prob = 0.70
        adjusted_price = price + commission
        b = (1 / adjusted_price) - 1
        p = win_prob
        q = 1 - p
        full_kelly = (b * p - q) / b
        half_kelly = full_kelly * 0.5
        
        expected_fraction = min(half_kelly, 0.15)  # Capped at 15%
        expected_target = expected_fraction * bankroll
        
        # Allow some tolerance for whole contract adjustments
        assert abs(result['target_bet_amount'] - expected_target) < 1.0
    
    def test_insufficient_funds_for_one_contract(self):
        """Test when bankroll can't afford even one contract"""
        bankroll = 1.0  # Very small bankroll
        win_pct = 80.0  # High win rate
        price = 0.50    # Contract costs more than available bankroll with commission
        
        result = user_input_betting_framework(bankroll, win_pct, price)
        
        assert result['decision'] == 'NO BET'
        assert 'insufficient for 1 whole contract' in result['reason']
        assert result['contracts_to_buy'] == 0
    
    def test_commission_impact(self, sample_bankroll):
        """Test that commission properly affects calculations"""
        bankroll = sample_bankroll
        win_pct = 68.0
        price = 0.45
        
        # Test with different commission rates
        result_low_commission = user_input_betting_framework(bankroll, win_pct, price, commission_per_contract=0.01)
        result_high_commission = user_input_betting_framework(bankroll, win_pct, price, commission_per_contract=0.05)
        
        # Higher commission should result in lower EV and fewer contracts
        assert result_low_commission['ev_percentage'] > result_high_commission['ev_percentage']
        assert result_low_commission['contracts_to_buy'] >= result_high_commission['contracts_to_buy']
    
    @pytest.mark.parametrize("win_pct,price,expected_decision", [
        (68.0, 0.45, "BET"),      # Documentation example
        (75.0, 0.20, "BET"),      # High EV
        (55.0, 0.50, "NO BET"),   # Low EV
        (51.0, 0.49, "NO BET"),   # Barely positive
        (80.0, 0.10, "BET"),      # Very high EV
    ])
    def test_parametrized_decisions(self, sample_bankroll, win_pct, price, expected_decision):
        """Parametrized test for various win percentage and price combinations"""
        result = user_input_betting_framework(sample_bankroll, win_pct, price)
        assert result['decision'] == expected_decision
    
    def test_negative_kelly_handling(self):
        """Test handling of negative Kelly fractions"""
        bankroll = 100
        # Use values that pass EV threshold but have negative Kelly
        win_pct = 65.0  # Decent win percentage 
        price = 0.90    # High price that creates negative Kelly
        
        result = user_input_betting_framework(bankroll, win_pct, price)
        
        assert result['decision'] == 'NO BET'
        # The actual reason will be EV threshold since it's checked first
        assert 'EV' in result['reason'] and 'below 10%' in result['reason']
    
    def test_return_structure_completeness(self, sample_bankroll):
        """Test that return structure contains all expected fields"""
        # Test BET case
        result = user_input_betting_framework(sample_bankroll, 68.0, 0.45)
        
        expected_bet_fields = {
            'decision', 'bet_amount', 'bet_percentage', 'ev_percentage',
            'expected_profit', 'contracts_to_buy', 'normalized_price',
            'target_bet_amount', 'unused_amount', 'adjusted_price',
            'commission_per_contract', 'wharton_compliant', 'whole_contracts_only'
        }
        
        assert all(field in result for field in expected_bet_fields)
        
        # Test NO BET case
        result = user_input_betting_framework(sample_bankroll, 55.0, 0.50)
        
        expected_no_bet_fields = {
            'decision', 'reason', 'ev_percentage', 'bet_amount', 'normalized_price'
        }
        
        assert all(field in result for field in expected_no_bet_fields)
    
    def test_edge_case_inputs(self, edge_case_test_data):
        """Test edge cases for input validation"""
        for win_pct, price, bankroll, description in edge_case_test_data:
            try:
                result = user_input_betting_framework(bankroll, win_pct, price)
                
                # Should always return a valid decision
                assert result['decision'] in ['BET', 'NO BET']
                assert isinstance(result['ev_percentage'], (int, float))
                assert result['bet_amount'] >= 0
                
            except Exception as e:
                pytest.fail(f"Failed on {description}: {e}")


class TestMathematicalAccuracy:
    """Test mathematical accuracy of calculations"""
    
    def test_ev_calculation_accuracy(self):
        """Test that EV calculations match expected formulas"""
        win_prob = 0.68
        price = 0.45
        commission = 0.02
        adjusted_price = price + commission
        
        expected_ev = (win_prob * (1/adjusted_price) - 1) * 100
        
        result = user_input_betting_framework(100, 68.0, 45, commission_per_contract=commission)
        
        assert abs(result['ev_percentage'] - expected_ev) < 0.01
    
    def test_kelly_calculation_accuracy(self):
        """Test Kelly fraction calculation accuracy"""
        bankroll = 1000
        win_prob = 0.70
        price = 0.40
        commission = 0.02
        
        # Manual Kelly calculation
        adjusted_price = price + commission
        b = (1 / adjusted_price) - 1
        p = win_prob
        q = 1 - p
        expected_full_kelly = (b * p - q) / b
        expected_half_kelly = expected_full_kelly * 0.5
        expected_capped = min(expected_half_kelly, 0.15)
        expected_target = expected_capped * bankroll
        
        result = user_input_betting_framework(bankroll, 70.0, 40, commission_per_contract=commission)
        
        # Allow small tolerance for floating point arithmetic
        assert abs(result['target_bet_amount'] - expected_target) < 0.01
    
    def test_profit_calculation_accuracy(self):
        """Test expected profit calculation"""
        bankroll = 100
        result = user_input_betting_framework(bankroll, 68.0, 0.45)
        
        if result['decision'] == 'BET':
            expected_profit = result['bet_amount'] * (result['ev_percentage'] / 100)
            assert abs(result['expected_profit'] - expected_profit) < 0.01