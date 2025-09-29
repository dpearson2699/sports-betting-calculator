"""
End-to-end integration tests for complete application workflow

Tests the full betting calculation pipeline from input to output, including
configuration integration and complete user workflows. These tests verify
that all components work together correctly in realistic scenarios.
"""

import pytest
import pandas as pd
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import tempfile
import shutil
import io
from contextlib import redirect_stdout, redirect_stderr

from src.betting_framework import user_input_betting_framework
from src.excel_processor import process_betting_excel
from src.commission_manager import commission_manager, CommissionManager

# Import the correct sheet name from config
try:
    from src.config.settings import DEFAULT_SHEET_NAME
except ImportError:
    # Fallback if import fails
    DEFAULT_SHEET_NAME = 'Games'


class TestCompleteApplicationWorkflow:
    """Test complete application workflows from start to finish."""
    
    def test_single_bet_workflow_profitable(self):
        """Test complete single bet workflow with profitable bet."""
        # Arrange - Test profitable bet parameters
        weekly_bankroll = 1000.0
        model_win_percentage = 75.0
        contract_price = 0.25
        model_win_margin = None
        
        # Act - Run through betting framework
        result = user_input_betting_framework(
            weekly_bankroll=weekly_bankroll,
            model_win_percentage=model_win_percentage,
            contract_price=contract_price,
            model_win_margin=model_win_margin
        )
        
        # Assert - Verify profitable bet decision
        assert result['decision'] == 'BET'
        assert result['bet_amount'] > 0
        assert result['bet_percentage'] > 0
        assert result['contracts_to_buy'] > 0
        assert result['ev_percentage'] >= 10.0  # Should meet Wharton threshold
        assert 'expected_profit' in result
        assert 'commission_per_contract' in result
        assert 'adjusted_price' in result
    
    def test_single_bet_workflow_unprofitable(self):
        """Test complete single bet workflow with unprofitable bet."""
        # Arrange - Test unprofitable bet parameters
        weekly_bankroll = 1000.0
        model_win_percentage = 45.0  # Low win percentage
        contract_price = 0.65        # High contract price
        model_win_margin = 2.5
        
        # Act - Run through betting framework
        result = user_input_betting_framework(
            weekly_bankroll=weekly_bankroll,
            model_win_percentage=model_win_percentage,
            contract_price=contract_price,
            model_win_margin=model_win_margin
        )
        
        # Assert - Verify NO BET decision
        assert result['decision'] == 'NO BET'
        assert result['bet_amount'] == 0
        assert 'reason' in result
        assert result['ev_percentage'] < 10.0  # Below Wharton threshold
        assert 'commission_per_contract' in result
    
    def test_excel_batch_workflow_complete(self, tmp_path):
        """Test complete Excel batch processing workflow."""
        # Arrange - Create test Excel file
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()
        
        test_file = input_dir / "test_games.xlsx"
        test_data = pd.DataFrame({
            'Game': ['Lakers vs Warriors', 'Cowboys vs Giants'],
            'Model Win Percentage': [72, 68],
            'Model Margin': [4.5, 3.2],
            'Contract Price': [0.28, 0.35]
        })
        test_data.to_excel(test_file, sheet_name=DEFAULT_SHEET_NAME, index=False)
        
        with patch('src.excel_processor.INPUT_DIR', input_dir):
            with patch('src.excel_processor.OUTPUT_DIR', output_dir):
                # Act
                results_df, output_file = process_betting_excel(test_file, 2000.0)
        
        # Assert - Verify processing completed
        assert results_df is not None
        assert len(results_df) == 2
        assert output_file is not None
        
        # Verify output file was created
        output_files = list(output_dir.glob("*_RESULTS.xlsx"))
        assert len(output_files) > 0
    
    def test_commission_configuration_workflow(self):
        """Test complete commission configuration workflow."""
        # Save original state
        original_rate = commission_manager.get_commission_rate()
        original_platform = commission_manager.get_current_platform()
        
        try:
            # Test platform change
            available_platforms = list(commission_manager.get_platform_presets().keys())
            if len(available_platforms) > 1:
                # Change to second platform
                new_platform = available_platforms[1]
                commission_manager.set_platform(new_platform)
                
                # Verify change
                assert commission_manager.get_current_platform() == new_platform
                assert commission_manager.get_commission_rate() == commission_manager.get_platform_presets()[new_platform]
            
            # Test custom rate setting
            custom_rate = 0.03
            commission_manager.set_commission_rate(custom_rate, "Test Custom Platform")
            
            # Verify custom rate
            assert commission_manager.get_commission_rate() == custom_rate
            assert commission_manager.get_current_platform() == "Test Custom Platform"
            
            # Test reset to default
            commission_manager.reset_to_default()
            assert commission_manager.get_current_platform() == "Robinhood"
            assert commission_manager.get_commission_rate() == 0.02
            
        finally:
            # Restore original settings
            commission_manager.set_commission_rate(original_rate, original_platform)


class TestConfigurationIntegration:
    """Test integration with configuration system and settings."""
    
    def test_commission_manager_integration(self):
        """Test commission manager integration across components."""
        # Test that commission manager works with betting framework
        original_rate = commission_manager.get_commission_rate()
        original_platform = commission_manager.get_current_platform()
        
        try:
            # Change commission settings
            commission_manager.set_commission_rate(0.05, "Test Platform")
            
            # Test betting framework uses new rate
            result = user_input_betting_framework(
                weekly_bankroll=1000,
                model_win_percentage=70,
                contract_price=0.30
            )
            
            # Verify commission is included in calculations
            assert 'adjusted_price' in result
            assert result['adjusted_price'] == 0.30 + 0.05  # price + commission
            assert result.get('commission_per_contract') == 0.05
            
        finally:
            # Restore original settings
            commission_manager.set_commission_rate(original_rate, original_platform)
    
    def test_directory_configuration_integration(self, tmp_path):
        """Test integration with directory configuration."""
        # Test that components use configured directories
        input_dir = tmp_path / "test_input"
        output_dir = tmp_path / "test_output"
        input_dir.mkdir()
        output_dir.mkdir()
        
        # Create test file
        test_file = input_dir / "config_test.xlsx"
        test_data = pd.DataFrame({
            'Game': ['Config Test Game'],
            'Model Win Percentage': [65],
            'Contract Price': [0.40]
        })
        test_data.to_excel(test_file, sheet_name=DEFAULT_SHEET_NAME, index=False)
        
        # Test Excel processing with custom directories
        with patch('src.excel_processor.INPUT_DIR', input_dir):
            with patch('src.excel_processor.OUTPUT_DIR', output_dir):
                results_df, output_file = process_betting_excel(test_file, 1000.0)
        
        # Verify processing worked with custom directories
        assert results_df is not None
        assert output_file is not None
        assert output_file.parent == output_dir
        assert output_file.exists()
    
    def test_settings_persistence_integration(self):
        """Test that settings persist across component interactions."""
        # Save original state
        original_rate = commission_manager.get_commission_rate()
        original_platform = commission_manager.get_current_platform()
        
        try:
            # Change settings through commission manager
            test_rate = 0.04
            test_platform = "Integration Test Platform"
            commission_manager.set_commission_rate(test_rate, test_platform)
            
            # Create new instance to test persistence
            new_manager = CommissionManager()
            
            # Verify settings persisted (through shared state)
            assert new_manager.get_commission_rate() == test_rate
            assert new_manager.get_current_platform() == test_platform
            
        finally:
            # Restore original settings
            commission_manager.set_commission_rate(original_rate, original_platform)


class TestCompleteUserWorkflows:
    """Test complete user workflows from start to finish."""
    
    def test_new_user_complete_workflow(self, tmp_path):
        """Test complete workflow for a new user from setup to results."""
        # Simulate new user workflow:
        # 1. Configure commission settings
        # 2. Create sample Excel file
        # 3. Process Excel file
        # 4. Analyze single bet
        
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()
        
        # Step 1: Configure commission (use Robinhood default)
        commission_manager.reset_to_default()
        
        # Step 2: Create and process Excel file
        test_file = input_dir / "new_user_games.xlsx"
        test_data = pd.DataFrame({
            'Game': ['First Game', 'Second Game', 'Third Game'],
            'Model Win Percentage': [68, 72, 58],
            'Contract Price': [0.32, 0.28, 0.55]
        })
        test_data.to_excel(test_file, sheet_name=DEFAULT_SHEET_NAME, index=False)
        
        with patch('src.excel_processor.INPUT_DIR', input_dir):
            with patch('src.excel_processor.OUTPUT_DIR', output_dir):
                results_df, output_file = process_betting_excel(test_file, 1500.0)
        
        # Verify Excel processing worked
        assert results_df is not None
        assert len(results_df) == 3
        assert output_file is not None
        assert output_file.exists()
        
        # Step 3: Analyze single bet
        single_bet_result = user_input_betting_framework(
            weekly_bankroll=1500,
            model_win_percentage=75,
            contract_price=0.25
        )
        
        # Verify single bet analysis worked
        assert single_bet_result['decision'] in ['BET', 'NO BET']
        assert 'ev_percentage' in single_bet_result
        assert 'commission_per_contract' in single_bet_result
        
        # Step 4: Verify consistency between Excel and single bet
        # Both should use same commission rate
        excel_commission = results_df.iloc[0]['Commission Rate']
        single_commission = single_bet_result['commission_per_contract']
        assert excel_commission == single_commission
    
    def test_experienced_user_workflow(self, tmp_path):
        """Test workflow for experienced user with custom settings."""
        # Simulate experienced user workflow:
        # 1. Set custom commission rate
        # 2. Process large Excel file
        # 3. Verify advanced features work
        
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()
        
        # Step 1: Set custom commission
        original_rate = commission_manager.get_commission_rate()
        original_platform = commission_manager.get_current_platform()
        
        try:
            commission_manager.set_commission_rate(0.03, "Custom High Commission")
            
            # Step 2: Create larger dataset
            games = [f'Game {i}' for i in range(1, 21)]  # 20 games
            win_percentages = [55 + (i % 25) for i in range(20)]  # 55-79%
            contract_prices = [0.20 + (i % 40) * 0.01 for i in range(20)]  # 0.20-0.59
            margins = [1.0 + (i % 10) * 0.5 for i in range(20)]  # 1.0-5.5
            
            test_data = pd.DataFrame({
                'Game': games,
                'Model Win Percentage': win_percentages,
                'Model Margin': margins,
                'Contract Price': contract_prices
            })
            
            test_file = input_dir / "experienced_user_games.xlsx"
            test_data.to_excel(test_file, sheet_name=DEFAULT_SHEET_NAME, index=False)
            
            # Step 3: Process with limited bankroll to test allocation
            with patch('src.excel_processor.INPUT_DIR', input_dir):
                with patch('src.excel_processor.OUTPUT_DIR', output_dir):
                    results_df, output_file = process_betting_excel(test_file, 2000.0)
            
            # Verify advanced features
            assert results_df is not None
            assert len(results_df) == 20
            
            # Check bankroll allocation worked
            total_allocated = results_df['Cumulative Bet Amount'].sum()
            assert total_allocated <= 2000.0
            
            # Check commission impact is visible
            assert 'Commission Rate' in results_df.columns
            assert results_df.iloc[0]['Commission Rate'] == 0.03
            
            # Check margin data is preserved
            assert 'Margin' in results_df.columns
            
            # Verify some bets and some skips due to bankroll limits
            final_recommendations = results_df['Final Recommendation'].unique()
            assert len(final_recommendations) > 1  # Should have variety
            
        finally:
            # Restore original settings
            commission_manager.set_commission_rate(original_rate, original_platform)
    
    def test_error_recovery_workflow(self, tmp_path):
        """Test user workflow with error conditions and recovery."""
        # Test workflow that encounters errors and recovers
        
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()
        
        # Test 1: Invalid Excel file
        invalid_file = input_dir / "invalid.xlsx"
        invalid_data = pd.DataFrame({
            'Game': ['Test Game'],
            'Model Win Percentage': [65]
            # Missing Contract Price column
        })
        invalid_data.to_excel(invalid_file, sheet_name=DEFAULT_SHEET_NAME, index=False)
        
        with patch('src.excel_processor.INPUT_DIR', input_dir):
            with patch('src.excel_processor.OUTPUT_DIR', output_dir):
                results_df, output_file = process_betting_excel(invalid_file, 1000.0)
        
        # Should handle error gracefully
        assert results_df is None
        assert output_file is None
        
        # Test 2: Recovery with valid file
        valid_file = input_dir / "valid.xlsx"
        valid_data = pd.DataFrame({
            'Game': ['Recovery Game'],
            'Model Win Percentage': [70],
            'Contract Price': [0.30]
        })
        valid_data.to_excel(valid_file, sheet_name=DEFAULT_SHEET_NAME, index=False)
        
        with patch('src.excel_processor.INPUT_DIR', input_dir):
            with patch('src.excel_processor.OUTPUT_DIR', output_dir):
                results_df, output_file = process_betting_excel(valid_file, 1000.0)
        
        # Should work after error
        assert results_df is not None
        assert len(results_df) == 1
        assert output_file is not None
        assert output_file.exists()
        
        # Test 3: Invalid commission rate recovery
        original_rate = commission_manager.get_commission_rate()
        
        try:
            # Try to set invalid rate
            with pytest.raises(ValueError):
                commission_manager.set_commission_rate(-0.01)  # Negative rate
            
            # Verify original rate is preserved
            assert commission_manager.get_commission_rate() == original_rate
            
            # Set valid rate after error
            commission_manager.set_commission_rate(0.025, "Recovery Test")
            assert commission_manager.get_commission_rate() == 0.025
            
        finally:
            commission_manager.reset_to_default()


class TestPerformanceIntegration:
    """Test performance of integrated workflows."""
    
    def test_large_dataset_performance(self, tmp_path):
        """Test performance with large dataset through complete workflow."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()
        
        # Create large dataset (100 games)
        games = [f'Performance Game {i}' for i in range(1, 101)]
        win_percentages = [50 + (i % 40) for i in range(100)]  # 50-89%
        contract_prices = [0.15 + (i % 70) * 0.01 for i in range(100)]  # 0.15-0.84
        
        test_data = pd.DataFrame({
            'Game': games,
            'Model Win Percentage': win_percentages,
            'Contract Price': contract_prices
        })
        
        test_file = input_dir / "large_dataset.xlsx"
        test_data.to_excel(test_file, sheet_name=DEFAULT_SHEET_NAME, index=False)
        
        # Time the complete workflow
        import time
        start_time = time.time()
        
        with patch('src.excel_processor.INPUT_DIR', input_dir):
            with patch('src.excel_processor.OUTPUT_DIR', output_dir):
                results_df, output_file = process_betting_excel(test_file, 10000.0)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Verify performance and correctness
        assert results_df is not None
        assert len(results_df) == 100
        assert processing_time < 30.0  # Should complete within 30 seconds
        
        # Verify all games were processed correctly
        assert len(results_df) == len(test_data)
        
        # Verify output file structure
        assert output_file is not None
        assert output_file.exists()
        
        # Read output file to verify it's complete
        with pd.ExcelFile(output_file) as excel_file:
            sheet_names = excel_file.sheet_names
            assert 'Quick_View' in sheet_names
            assert 'Betting_Results' in sheet_names
            
            betting_results = pd.read_excel(excel_file, sheet_name='Betting_Results')
            assert len(betting_results) == 100
    
    def test_memory_efficiency_workflow(self, tmp_path):
        """Test memory efficiency of complete workflow."""
        # Test that workflow doesn't consume excessive memory
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()
        
        # Create moderately large dataset
        test_data = pd.DataFrame({
            'Game': [f'Memory Test Game {i}' for i in range(50)],
            'Model Win Percentage': [60 + (i % 30) for i in range(50)],
            'Contract Price': [0.25 + (i % 40) * 0.01 for i in range(50)]
        })
        
        test_file = input_dir / "memory_test.xlsx"
        test_data.to_excel(test_file, sheet_name=DEFAULT_SHEET_NAME, index=False)
        
        # Process multiple times to check for memory leaks
        for i in range(5):
            with patch('src.excel_processor.INPUT_DIR', input_dir):
                with patch('src.excel_processor.OUTPUT_DIR', output_dir):
                    results_df, output_file = process_betting_excel(test_file, 2000.0)
            
            # Verify each iteration works
            assert results_df is not None
            assert len(results_df) == 50
            
            # Clean up output file for next iteration
            if output_file and output_file.exists():
                output_file.unlink()
        
        # Test should complete without memory issues


class TestRealWorldScenarios:
    """Test realistic user scenarios and edge cases."""
    
    def test_mixed_profitability_scenario(self, tmp_path):
        """Test scenario with mix of profitable and unprofitable bets."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()
        
        # Create realistic mixed scenario
        test_data = pd.DataFrame({
            'Game': [
                'High EV Opportunity',      # Should be BET
                'Marginal Opportunity',     # Might be BET or NO BET
                'Overpriced Market',        # Should be NO BET
                'Close Call',               # Edge case
                'Clear Value',              # Should be BET
                'Obvious Trap'              # Should be NO BET
            ],
            'Model Win Percentage': [78, 62, 45, 58, 82, 35],
            'Contract Price': [0.22, 0.45, 0.70, 0.52, 0.18, 0.75]
        })
        
        test_file = input_dir / "mixed_scenario.xlsx"
        test_data.to_excel(test_file, sheet_name=DEFAULT_SHEET_NAME, index=False)
        
        with patch('src.excel_processor.INPUT_DIR', input_dir):
            with patch('src.excel_processor.OUTPUT_DIR', output_dir):
                results_df, output_file = process_betting_excel(test_file, 1500.0)
        
        # Verify realistic decision distribution
        assert results_df is not None
        
        bet_count = len(results_df[results_df['Decision'] == 'BET'])
        no_bet_count = len(results_df[results_df['Decision'] == 'NO BET'])
        
        # Should have both BET and NO BET decisions
        assert bet_count > 0
        assert no_bet_count > 0
        
        # High EV games should be BET
        high_ev_game = results_df[results_df['Game'] == 'High EV Opportunity'].iloc[0]
        clear_value_game = results_df[results_df['Game'] == 'Clear Value'].iloc[0]
        assert high_ev_game['Decision'] == 'BET'
        assert clear_value_game['Decision'] == 'BET'
        
        # Obvious trap should be NO BET
        trap_game = results_df[results_df['Game'] == 'Obvious Trap'].iloc[0]
        overpriced_game = results_df[results_df['Game'] == 'Overpriced Market'].iloc[0]
        assert trap_game['Decision'] == 'NO BET'
        assert overpriced_game['Decision'] == 'NO BET'
    
    def test_bankroll_constraint_scenario(self, tmp_path):
        """Test scenario where bankroll constraints affect decisions."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()
        
        # Create scenario with many good opportunities but limited bankroll
        test_data = pd.DataFrame({
            'Game': [f'Good Opportunity {i}' for i in range(1, 11)],
            'Model Win Percentage': [70 + i for i in range(10)],  # All profitable
            'Contract Price': [0.25 + i * 0.02 for i in range(10)]  # Varying prices
        })
        
        test_file = input_dir / "bankroll_constraint.xlsx"
        test_data.to_excel(test_file, sheet_name=DEFAULT_SHEET_NAME, index=False)
        
        # Use limited bankroll
        limited_bankroll = 800.0
        
        with patch('src.excel_processor.INPUT_DIR', input_dir):
            with patch('src.excel_processor.OUTPUT_DIR', output_dir):
                results_df, output_file = process_betting_excel(test_file, limited_bankroll)
        
        # Verify bankroll allocation worked correctly
        assert results_df is not None
        
        total_allocated = results_df['Cumulative Bet Amount'].sum()
        assert total_allocated <= limited_bankroll
        
        # Should prioritize highest EV opportunities
        bet_games = results_df[results_df['Final Recommendation'] == 'BET']
        if len(bet_games) > 1:
            ev_values = bet_games['EV Percentage'].tolist()
            assert ev_values == sorted(ev_values, reverse=True)
        
        # Some games should be skipped due to insufficient bankroll
        skipped_games = results_df[results_df['Final Recommendation'].str.contains('SKIP', na=False)]
        assert len(skipped_games) > 0
    
    def test_commission_impact_scenario(self, tmp_path):
        """Test scenario showing commission impact on decisions."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()
        
        # Create scenario with marginal opportunities affected by commission
        test_data = pd.DataFrame({
            'Game': [
                'Marginal Without Commission',
                'Marginal With Commission', 
                'Strong Despite Commission'
            ],
            'Model Win Percentage': [58, 56, 75],  # Lower win percentages
            'Contract Price': [0.48, 0.52, 0.28]   # Higher prices for marginal games
        })
        
        test_file = input_dir / "commission_impact.xlsx"
        test_data.to_excel(test_file, sheet_name=DEFAULT_SHEET_NAME, index=False)
        
        # Test with high commission
        original_rate = commission_manager.get_commission_rate()
        original_platform = commission_manager.get_current_platform()
        
        try:
            commission_manager.set_commission_rate(0.08, "High Commission Test")
            
            with patch('src.excel_processor.INPUT_DIR', input_dir):
                with patch('src.excel_processor.OUTPUT_DIR', output_dir):
                    results_df, output_file = process_betting_excel(test_file, 1000.0)
            
            # Verify commission impact is visible
            assert results_df is not None
            assert results_df.iloc[0]['Commission Rate'] == 0.08
            
            # Strong opportunity should still be BET despite commission
            strong_game = results_df[results_df['Game'] == 'Strong Despite Commission'].iloc[0]
            assert strong_game['Decision'] == 'BET'
            
            # Marginal opportunities might be NO BET due to commission
            marginal_games = results_df[results_df['Game'].str.contains('Marginal')]
            no_bet_count = len(marginal_games[marginal_games['Decision'] == 'NO BET'])
            assert no_bet_count > 0  # At least some should be NO BET due to commission
            
        finally:
            commission_manager.set_commission_rate(original_rate, original_platform)
