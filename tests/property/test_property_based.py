"""Property-based tests using Hypothesis for mathematical validation"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from hypothesis.stateful import Bundle, RuleBasedStateMachine, rule, invariant
import math

from src.betting_framework import (
    normalize_contract_price,
    calculate_whole_contracts,
    user_input_betting_framework
)
from src.excel_processor import apply_bankroll_allocation
import pandas as pd


class TestMathematicalProperties:
    """Property-based tests for mathematical correctness"""
    
    @given(
        price=st.floats(min_value=0.01, max_value=100.0).filter(lambda x: not (math.isnan(x) or math.isinf(x)))
    )
    @pytest.mark.property
    def test_normalize_contract_price_properties(self, price):
        """Test properties of contract price normalization"""
        normalized = normalize_contract_price(price)
        
        # Property 1: Result should always be positive
        assert normalized > 0
        
        # Property 2: Result should be <= 1.0 (dollar format)
        assert normalized <= 1.0
        
        # Property 3: If input >= 1.0, result should be input/100
        if price >= 1.0:
            assert abs(normalized - price/100.0) < 1e-10
        else:
            # Property 4: If input < 1.0, result should be unchanged
            assert abs(normalized - price) < 1e-10
    
    @given(
        target_amount=st.floats(min_value=0.01, max_value=10000.0),
        contract_price=st.floats(min_value=0.01, max_value=1.0),
        commission=st.floats(min_value=0.0, max_value=0.10)
    )
    @pytest.mark.property
    def test_calculate_whole_contracts_properties(self, target_amount, contract_price, commission):
        """Test properties of whole contracts calculation"""
        result = calculate_whole_contracts(target_amount, contract_price, commission)
        
        # Property 1: Result should always have required keys
        required_keys = ['adjusted_price', 'whole_contracts', 'actual_bet_amount', 'unused_amount']
        for key in required_keys:
            assert key in result
        
        # Property 2: Adjusted price should be contract_price + commission
        expected_adjusted = contract_price + commission
        assert abs(result['adjusted_price'] - expected_adjusted) < 1e-10
        
        # Property 3: Whole contracts should be non-negative integer
        assert result['whole_contracts'] >= 0
        assert isinstance(result['whole_contracts'], int)
        
        # Property 4: Actual bet amount should not exceed target amount
        assert result['actual_bet_amount'] <= target_amount + 1e-10  # Allow for floating point precision
        
        # Property 5: Unused amount should be non-negative
        assert result['unused_amount'] >= -1e-10  # Allow for floating point precision
        
        # Property 6: actual_bet_amount + unused_amount should equal target_amount
        total = result['actual_bet_amount'] + result['unused_amount']
        assert abs(total - target_amount) < 1e-6
        
        # Property 7: If we can afford at least one contract, whole_contracts > 0
        if target_amount >= expected_adjusted:
            assert result['whole_contracts'] > 0
        else:
            assert result['whole_contracts'] == 0
    
    @given(
        bankroll=st.floats(min_value=1.0, max_value=100000.0),
        win_pct=st.floats(min_value=1.0, max_value=99.0),  # Reasonable win percentages
        price=st.floats(min_value=0.01, max_value=0.99)    # Contract prices in cents
    )
    @pytest.mark.property
    @settings(max_examples=50)  # Reduce examples for faster testing
    def test_user_input_betting_framework_properties(self, bankroll, win_pct, price):
        """Test properties of the main betting framework"""
        result = user_input_betting_framework(bankroll, win_pct, price)
        
        # Property 1: Result should always have required keys
        required_keys = ['decision', 'ev_percentage', 'bet_amount']
        for key in required_keys:
            assert key in result
        
        # Property 2: Decision should be either 'BET' or 'NO BET'
        assert result['decision'] in ['BET', 'NO BET']
        
        # Property 3: bet_amount should be non-negative
        assert result['bet_amount'] >= 0
        
        # Property 4: EV percentage should be calculated
        assert isinstance(result['ev_percentage'], (int, float))
        
        # Property 5: If decision is 'NO BET', bet_amount should be 0
        if result['decision'] == 'NO BET':
            assert result['bet_amount'] == 0
            assert 'reason' in result
        
        # Property 6: If decision is 'BET', should have additional keys
        if result['decision'] == 'BET':
            bet_keys = ['contracts_to_buy', 'bet_percentage', 'expected_profit']
            for key in bet_keys:
                assert key in result
            
            # Property 7: bet_amount should not exceed 15% of bankroll (safety constraint)
            assert result['bet_amount'] <= bankroll * 0.15 + 1e-6
            
            # Property 8: contracts_to_buy should be positive integer
            assert result['contracts_to_buy'] > 0
            assert isinstance(result['contracts_to_buy'], int)
    
    @given(
        win_pct=st.floats(min_value=50.1, max_value=95.0),  # Winning scenarios
        price=st.floats(min_value=0.01, max_value=0.49)     # Favorable prices
    )
    @pytest.mark.property
    def test_kelly_criterion_mathematical_consistency(self, win_pct, price):
        """Test Kelly criterion calculations for mathematical consistency"""
        bankroll = 1000.0  # Fixed bankroll for consistency
        
        result = user_input_betting_framework(bankroll, win_pct, price)
        
        # Calculate expected Kelly fraction manually
        p = win_pct / 100.0
        normalized_price = price / 100.0 if price >= 1.0 else price
        b = (1 / normalized_price) - 1  # Net odds
        
        full_kelly = (b * p - (1 - p)) / b
        
        if full_kelly > 0 and result['decision'] == 'BET':
            # Property: Half-Kelly should be applied (safety constraint)
            half_kelly = full_kelly * 0.5
            expected_fraction = min(half_kelly, 0.15)  # Cap at 15%
            expected_bet = expected_fraction * bankroll
            
            # Allow for whole contract adjustments
            assert result['bet_amount'] <= expected_bet + price * 100  # Allow for contract rounding


class TestInputValidationProperties:
    """Property-based tests for input validation and edge cases"""
    
    @given(
        percentage=st.one_of(
            st.floats(min_value=0.01, max_value=0.99),   # Decimal format (excluding 1.0)
            st.floats(min_value=1.01, max_value=99.0)    # Percentage format (excluding 100.0)
        )
    )
    @pytest.mark.property
    def test_percentage_format_handling(self, percentage):
        """Test that percentage format handling is consistent"""
        result = user_input_betting_framework(100.0, percentage, 0.50)
        
        # Property: Should handle both percentage formats correctly
        assert result is not None
        assert 'decision' in result
        
        # The EV calculation should be consistent regardless of format
        expected_win_prob = percentage if percentage <= 1.0 else percentage / 100.0
        assert 0 < expected_win_prob < 1
    
    @given(
        price=st.one_of(
            st.floats(min_value=0.01, max_value=0.99),   # Dollar format  
            st.floats(min_value=1.0, max_value=99.0)     # Cents format
        )
    )
    @pytest.mark.property
    def test_price_format_handling(self, price):
        """Test that price format handling is consistent"""
        result = user_input_betting_framework(100.0, 70.0, price)
        
        # Property: Should handle both price formats correctly
        assert result is not None
        assert 'decision' in result
        
        # The normalized price should always be in dollar format (< 1.0)
        normalized = normalize_contract_price(price)
        assert 0 < normalized <= 1.0


class TestBankrollAllocationProperties:
    """Property-based tests for bankroll allocation logic"""
    
    @given(
        bankroll=st.floats(min_value=10.0, max_value=10000.0),
        num_games=st.integers(min_value=1, max_value=20)
    )
    @pytest.mark.property
    @settings(max_examples=30)
    def test_bankroll_allocation_properties(self, bankroll, num_games):
        """Test properties of bankroll allocation"""
        # Generate test data with varying EV percentages
        games_data = []
        
        for i in range(num_games):
            # Create games with different EV levels
            ev_pct = 15.0 - (i * 1.0)  # Decreasing EV from 15% down
            games_data.append({
                'Game': f'Game {i+1}',
                'Model Win Percentage': min(85.0, 50.0 + ev_pct),
                'Contract Price': 0.40,
                'Model Margin': 5.0,
                'EV Percentage': max(ev_pct, 5.0),  # Keep above some minimum
                'Decision': 'BET' if ev_pct >= 10.0 else 'NO BET',
                'Final Recommendation': 'BET' if ev_pct >= 10.0 else 'NO BET',
                'Bet Amount': min(bankroll * 0.1, 50.0) if ev_pct >= 10.0 else 0.0
            })
        
        df = pd.DataFrame(games_data)
        
        # Apply bankroll allocation with error handling
        result_df = apply_bankroll_allocation(df, bankroll)
        
        # Check if function returned None (error condition)
        assert result_df is not None, f"apply_bankroll_allocation returned None for bankroll={bankroll}, num_games={num_games}"
        
        # Ensure we have a valid DataFrame
        assert isinstance(result_df, pd.DataFrame), f"Expected DataFrame, got {type(result_df)}"
        assert len(result_df) == num_games, f"Expected {num_games} rows, got {len(result_df)}"
        
        # Property 1: Total allocated should not exceed bankroll
        bet_mask = result_df['Final Recommendation'].isin(['BET', 'PARTIAL BET'])
        total_allocated = result_df[bet_mask]['Bet Amount'].sum()
        assert total_allocated <= bankroll + 1e-6, f"Total allocated {total_allocated} exceeds bankroll {bankroll}"
        
        # Property 2: Games should be processed in EV order (highest first)
        bet_games = result_df[result_df['Final Recommendation'] == 'BET']
        if len(bet_games) > 1:
            ev_values = bet_games['EV Percentage'].values
            # Should be in descending order (highest EV first)
            assert all(ev_values[i] >= ev_values[i+1] for i in range(len(ev_values)-1)), \
                f"EV values not in descending order: {ev_values}"
        
        # Property 3: No individual bet should exceed 15% of bankroll
        for _, row in result_df.iterrows():
            if row['Final Recommendation'] in ['BET', 'PARTIAL BET']:
                assert row['Bet Amount'] <= bankroll * 0.15 + 1e-6


class TestEdgeCaseProperties:
    """Property-based tests for edge cases and boundary conditions"""
    
    @given(
        bankroll=st.floats(min_value=0.01, max_value=1.0),  # Very small bankrolls
        win_pct=st.floats(min_value=60.0, max_value=90.0),
        price=st.floats(min_value=0.30, max_value=0.70)
    )
    @pytest.mark.property
    def test_small_bankroll_properties(self, bankroll, win_pct, price):
        """Test behavior with very small bankrolls"""
        result = user_input_betting_framework(bankroll, win_pct, price)
        
        # Property: Should handle small bankrolls gracefully
        assert result is not None
        assert result['bet_amount'] >= 0
        
        # If the bankroll is too small to afford one contract, should be NO BET
        adjusted_price = price + 0.02  # Include commission
        if bankroll < adjusted_price:
            assert result['decision'] == 'NO BET'
    
    @given(
        bankroll=st.floats(min_value=10000.0, max_value=1000000.0),  # Very large bankrolls
        win_pct=st.floats(min_value=70.0, max_value=85.0),
        price=st.floats(min_value=0.20, max_value=0.40)
    )
    @pytest.mark.property
    @settings(max_examples=20)
    def test_large_bankroll_properties(self, bankroll, win_pct, price):
        """Test behavior with very large bankrolls"""
        result = user_input_betting_framework(bankroll, win_pct, price)
        
        # Property: 15% bankroll cap should still be enforced
        if result['decision'] == 'BET':
            max_allowed = bankroll * 0.15
            assert result['bet_amount'] <= max_allowed + 1e-6
            
            # Property: Should be able to buy a reasonable number of contracts
            assert result['contracts_to_buy'] > 0


@pytest.mark.property
class TestNumericalStability:
    """Test numerical stability and precision"""
    
    @given(
        bankroll=st.floats(min_value=1.0, max_value=1000.0),
        win_pct=st.floats(min_value=51.0, max_value=99.0),
        price=st.floats(min_value=0.01, max_value=0.99)
    )
    def test_floating_point_consistency(self, bankroll, win_pct, price):
        """Test that floating point operations are consistent"""
        # Run the same calculation multiple times
        results = []
        for _ in range(3):
            result = user_input_betting_framework(bankroll, win_pct, price)
            results.append(result)
        
        # All results should be identical
        for i in range(1, len(results)):
            assert results[i]['decision'] == results[0]['decision']
            assert abs(results[i]['bet_amount'] - results[0]['bet_amount']) < 1e-10
            assert abs(results[i]['ev_percentage'] - results[0]['ev_percentage']) < 1e-10


# Benchmark tests for performance validation
@pytest.mark.performance
class TestPerformanceBenchmarks:
    """Performance benchmark tests"""
    
    def test_single_bet_performance(self, benchmark):
        """Benchmark single bet calculation performance"""
        def single_bet():
            return user_input_betting_framework(100.0, 68.0, 0.45)
        
        result = benchmark(single_bet)
        assert result['decision'] == 'BET'
    
    def test_batch_processing_performance(self, benchmark):
        """Benchmark batch processing performance"""
        # Create test DataFrame
        games_data = []
        for i in range(100):  # 100 games
            games_data.append({
                'Game': f'Game {i+1}',
                'Model Win Percentage': 60.0 + (i % 30),  # Vary win percentage
                'Contract Price': 0.30 + (i % 50) * 0.01,  # Vary price
                'Model Margin': 3.0 + (i % 10),
                'EV Percentage': 12.0 + (i % 20),
                'Decision': 'BET',
                'Final Recommendation': 'BET',  
                'Bet Amount': 10.0 + (i % 40)
            })
        
        df = pd.DataFrame(games_data)
        
        def batch_allocation():
            return apply_bankroll_allocation(df, 1000.0)
        
        result_df = benchmark(batch_allocation)
        assert len(result_df) == 100
        
        # Performance assertion: should complete in reasonable time
        # The benchmark will automatically measure and report timing