"""
Integration tests for Excel workflow - End-to-end Excel processing pipeline

Tests the complete Excel processing workflow from file input through betting 
recommendation output, using temporary files to test the full pipeline.
"""

import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import shutil
from typing import Any

from src.excel_processor import (
    process_betting_excel,
    create_sample_excel_in_input_dir,
    apply_bankroll_allocation,
    COLUMN_CONFIG
)
from src.betting_framework import user_input_betting_framework
from src.commission_manager import commission_manager

# Import the correct sheet name from config
try:
    from src.config.settings import DEFAULT_SHEET_NAME
    sheet_name = DEFAULT_SHEET_NAME
except ImportError:
    # Fallback if import fails
    sheet_name = 'Games'


class TestExcelWorkflowIntegration:
    """Test complete Excel processing workflow integration."""
    
    def test_complete_excel_processing_workflow(self, tmp_path: Path) -> None:
        """Test complete workflow from Excel input to results output."""
        # Arrange - Create test Excel file
        input_file = tmp_path / "test_games.xlsx"
        test_data = pd.DataFrame({
            'Game': ['Lakers vs Warriors', 'Cowboys vs Giants', 'Yankees vs Red Sox'],
            'Model Win Percentage': [68, 72, 55],
            'Model Margin': [3.5, 7.2, 1.8],
            'Contract Price': [45, 0.40, 52]  # Mixed format: cents and dollars
        })
        test_data.to_excel(input_file, sheet_name=sheet_name, index=False)
        
        weekly_bankroll = 1000.0
        
        # Mock the output directory to use tmp_path
        with patch('src.excel_processor.OUTPUT_DIR', tmp_path):
            # Act
            results_df, output_file = process_betting_excel(input_file, weekly_bankroll)
        
        # Assert - Check that processing completed successfully
        assert results_df is not None
        assert output_file is not None
        assert len(results_df) == 3
        
        # Verify required columns exist in results
        required_output_columns = [
            'Game', 'Win %', 'Contract Price (¢)', 'Decision', 
            'EV Percentage', 'Bet Amount', 'Final Recommendation'
        ]
        for col in required_output_columns:
            assert col in results_df.columns
        
        # Verify data transformation occurred correctly
        # Results are sorted by EV percentage, so check that all games are present
        game_names = results_df['Game'].tolist()
        assert 'Lakers vs Warriors' in game_names
        assert 'Cowboys vs Giants' in game_names
        assert 'Yankees vs Red Sox' in game_names
        
        # Check data transformation for a specific game
        lakers_row = results_df[results_df['Game'] == 'Lakers vs Warriors'].iloc[0]
        assert lakers_row['Win %'] == 0.68  # Converted from 68
        assert lakers_row['Contract Price (¢)'] == 45
        
        # Verify betting decisions were made
        decisions = results_df['Decision'].unique()
        assert all(decision in ['BET', 'NO BET'] for decision in decisions)
        
        # Verify output file was created
        assert output_file.exists()
    
    def test_excel_workflow_with_profitable_bets(self, tmp_path: Path) -> None:
        """Test Excel workflow with data that should generate profitable bets."""
        # Arrange - Create data with high win percentages and low prices
        input_file = tmp_path / "profitable_games.xlsx"
        test_data = pd.DataFrame({
            'Game': ['High EV Game 1', 'High EV Game 2'],
            'Model Win Percentage': [75, 80],  # High win rates
            'Contract Price': [0.25, 0.30]     # Low prices = high EV
        })
        test_data.to_excel(input_file, sheet_name=sheet_name, index=False)
        
        weekly_bankroll = 2000.0
        
        with patch('src.excel_processor.OUTPUT_DIR', tmp_path):
            # Act
            results_df, output_file = process_betting_excel(input_file, weekly_bankroll)
        
        # Assert
        assert results_df is not None
        
        # Should have some BET decisions with high EV
        bet_decisions = results_df[results_df['Decision'] == 'BET']
        assert len(bet_decisions) > 0
        
        # Verify bet amounts are reasonable
        for _, row in bet_decisions.iterrows():
            assert row['Bet Amount'] > 0
            assert row['Bet Percentage'] > 0
            assert row['Contracts To Buy'] > 0
            assert row['EV Percentage'] >= 0.10  # Should meet Wharton threshold
    
    def test_excel_workflow_with_unprofitable_bets(self, tmp_path: Path) -> None:
        """Test Excel workflow with data that should generate NO BET decisions."""
        # Arrange - Create data with low win percentages or high prices
        input_file = tmp_path / "unprofitable_games.xlsx"
        test_data = pd.DataFrame({
            'Game': ['Low EV Game 1', 'Low EV Game 2'],
            'Model Win Percentage': [52, 48],  # Low win rates
            'Contract Price': [0.55, 0.60]     # High prices = low/negative EV
        })
        test_data.to_excel(input_file, sheet_name=sheet_name, index=False)
        
        weekly_bankroll = 1000.0
        
        with patch('src.excel_processor.OUTPUT_DIR', tmp_path):
            # Act
            results_df, output_file = process_betting_excel(input_file, weekly_bankroll)
        
        # Assert
        assert results_df is not None
        
        # Should have mostly NO BET decisions
        no_bet_decisions = results_df[results_df['Decision'] == 'NO BET']
        assert len(no_bet_decisions) > 0
        
        # Verify reasons are provided for NO BET decisions
        for _, row in no_bet_decisions.iterrows():
            assert row['Reason'] != ''
            assert row['Bet Amount'] == 0
            assert row['Contracts To Buy'] == 0
    
    def test_excel_workflow_bankroll_allocation(self, tmp_path):
        """Test Excel workflow bankroll allocation with limited funds."""
        # Arrange - Create multiple profitable bets that exceed bankroll
        input_file = tmp_path / "allocation_test.xlsx"
        test_data = pd.DataFrame({
            'Game': ['Game 1', 'Game 2', 'Game 3', 'Game 4'],
            'Model Win Percentage': [75, 72, 70, 68],  # All profitable
            'Contract Price': [0.25, 0.28, 0.30, 0.32]
        })
        test_data.to_excel(input_file, sheet_name=sheet_name, index=False)
        
        weekly_bankroll = 500.0  # Limited bankroll
        
        with patch('src.excel_processor.OUTPUT_DIR', tmp_path):
            # Act
            results_df, output_file = process_betting_excel(input_file, weekly_bankroll)
        
        # Assert
        assert results_df is not None
        
        # Verify bankroll allocation logic
        total_allocated = results_df['Cumulative Bet Amount'].sum()
        assert total_allocated <= weekly_bankroll
        
        # Should have some bets and some skipped due to insufficient funds
        final_recommendations = results_df['Final Recommendation'].unique()
        assert 'BET' in final_recommendations or any('PARTIAL' in rec for rec in final_recommendations)
        
        # Verify games are prioritized by EV (highest first)
        bet_rows = results_df[results_df['Cumulative Bet Amount'] > 0]
        if len(bet_rows) > 1:
            ev_values = bet_rows['EV Percentage'].tolist()
            assert ev_values == sorted(ev_values, reverse=True)
    
    def test_excel_workflow_with_commission_impact(self, tmp_path):
        """Test Excel workflow with commission impact on betting decisions."""
        # Arrange
        input_file = tmp_path / "commission_test.xlsx"
        test_data = pd.DataFrame({
            'Game': ['Marginal Game 1', 'Marginal Game 2'],
            'Model Win Percentage': [62, 58],  # Marginal win rates
            'Contract Price': [0.42, 0.48]     # Prices that might be affected by commission
        })
        test_data.to_excel(input_file, sheet_name=sheet_name, index=False)
        
        weekly_bankroll = 1000.0
        
        # Test with different commission rates
        with patch('src.excel_processor.OUTPUT_DIR', tmp_path):
            # Test with higher commission
            with patch.object(commission_manager, 'get_commission_rate', return_value=0.05):
                with patch.object(commission_manager, 'get_current_platform', return_value='High Commission Platform'):
                    results_high_comm, _ = process_betting_excel(input_file, weekly_bankroll)
            
            # Test with lower commission
            with patch.object(commission_manager, 'get_commission_rate', return_value=0.01):
                with patch.object(commission_manager, 'get_current_platform', return_value='Low Commission Platform'):
                    results_low_comm, _ = process_betting_excel(input_file, weekly_bankroll)
        
        # Assert
        assert results_high_comm is not None
        assert results_low_comm is not None
        
        # Verify commission data is included
        assert 'Commission Rate' in results_high_comm.columns
        assert 'Platform' in results_high_comm.columns
        assert 'Adjusted Price' in results_high_comm.columns
        
        # Commission should affect betting decisions
        high_comm_bets = len(results_high_comm[results_high_comm['Decision'] == 'BET'])
        low_comm_bets = len(results_low_comm[results_low_comm['Decision'] == 'BET'])
        
        # Lower commission should generally result in more or equal bets
        assert low_comm_bets >= high_comm_bets
    
    def test_excel_workflow_margin_data_handling(self, tmp_path):
        """Test Excel workflow with and without margin data."""
        # Test with margin data
        input_file_with_margin = tmp_path / "with_margin.xlsx"
        test_data_with_margin = pd.DataFrame({
            'Game': ['Game 1', 'Game 2'],
            'Model Win Percentage': [65, 70],
            'Model Margin': [3.5, 5.2],  # Include margin data
            'Contract Price': [0.35, 0.30]
        })
        test_data_with_margin.to_excel(input_file_with_margin, sheet_name=sheet_name, index=False)
        
        # Test without margin data
        input_file_without_margin = tmp_path / "without_margin.xlsx"
        test_data_without_margin = pd.DataFrame({
            'Game': ['Game 3', 'Game 4'],
            'Model Win Percentage': [65, 70],
            'Contract Price': [0.35, 0.30]
            # No margin column
        })
        test_data_without_margin.to_excel(input_file_without_margin, sheet_name=sheet_name, index=False)
        
        weekly_bankroll = 1000.0
        
        with patch('src.excel_processor.OUTPUT_DIR', tmp_path):
            # Act
            results_with_margin, _ = process_betting_excel(input_file_with_margin, weekly_bankroll)
            results_without_margin, _ = process_betting_excel(input_file_without_margin, weekly_bankroll)
        
        # Assert
        assert results_with_margin is not None
        assert results_without_margin is not None
        
        # Results with margin should include Margin column
        assert 'Margin' in results_with_margin.columns
        # Check that margin data is preserved (results are sorted by EV, so find the right row)
        game1_row = results_with_margin[results_with_margin['Game'] == 'Game 1'].iloc[0]
        assert game1_row['Margin'] == 3.5
        
        # Results without margin should not include Margin column or have null values
        if 'Margin' in results_without_margin.columns:
            assert pd.isna(results_without_margin.iloc[0]['Margin'])
    
    def test_excel_workflow_mixed_price_formats(self, tmp_path):
        """Test Excel workflow with mixed price formats (cents vs dollars)."""
        # Arrange
        input_file = tmp_path / "mixed_formats.xlsx"
        test_data = pd.DataFrame({
            'Game': ['Cents Format', 'Dollar Format', 'High Cents'],
            'Model Win Percentage': [65, 65, 65],
            'Contract Price': [27, 0.27, 85]  # Mixed: cents, dollars, high cents
        })
        test_data.to_excel(input_file, sheet_name=sheet_name, index=False)
        
        weekly_bankroll = 1000.0
        
        with patch('src.excel_processor.OUTPUT_DIR', tmp_path):
            # Act
            results_df, output_file = process_betting_excel(input_file, weekly_bankroll)
        
        # Assert
        assert results_df is not None
        
        # Verify price normalization occurred
        # All should be processed correctly regardless of input format
        for _, row in results_df.iterrows():
            # Contract prices should be preserved as entered
            assert row['Contract Price (¢)'] in [27, 0.27, 85]
            
            # But calculations should work correctly (check that we have valid decisions)
            assert row['Decision'] in ['BET', 'NO BET']
            assert isinstance(row['EV Percentage'], (int, float))
    
    def test_excel_workflow_error_handling(self, tmp_path):
        """Test Excel workflow error handling with invalid data."""
        # Test with missing required columns
        input_file_missing_cols = tmp_path / "missing_cols.xlsx"
        invalid_data = pd.DataFrame({
            'Game': ['Game 1'],
            'Model Win Percentage': [65]
            # Missing Contract Price
        })
        invalid_data.to_excel(input_file_missing_cols, sheet_name=sheet_name, index=False)
        
        weekly_bankroll = 1000.0
        
        with patch('src.excel_processor.OUTPUT_DIR', tmp_path):
            # Act
            results_df, output_file = process_betting_excel(input_file_missing_cols, weekly_bankroll)
        
        # Assert - Should handle error gracefully
        assert results_df is None
        assert output_file is None
    
    def test_excel_workflow_performance(self, tmp_path):
        """Test Excel workflow performance with larger dataset."""
        # Arrange - Create larger dataset to test performance
        input_file = tmp_path / "large_dataset.xlsx"
        
        # Create 50 games to test performance
        games = [f'Game {i}' for i in range(1, 51)]
        win_percentages = [60 + (i % 20) for i in range(50)]  # 60-79%
        contract_prices = [0.25 + (i % 50) * 0.01 for i in range(50)]  # 0.25-0.74
        
        test_data = pd.DataFrame({
            'Game': games,
            'Model Win Percentage': win_percentages,
            'Contract Price': contract_prices
        })
        test_data.to_excel(input_file, sheet_name=sheet_name, index=False)
        
        weekly_bankroll = 5000.0
        
        with patch('src.excel_processor.OUTPUT_DIR', tmp_path):
            # Act - Time the processing
            import time
            start_time = time.time()
            results_df, output_file = process_betting_excel(input_file, weekly_bankroll)
            end_time = time.time()
            processing_time = end_time - start_time
        
        # Assert
        assert results_df is not None
        assert len(results_df) == 50
        
        # Should complete within reasonable time (under 10 seconds for 50 games)
        assert processing_time < 10.0
        
        # Verify all games were processed
        assert len(results_df) == len(test_data)
        
        # Verify bankroll allocation worked correctly
        total_allocated = results_df['Cumulative Bet Amount'].sum()
        assert total_allocated <= weekly_bankroll


class TestExcelOutputGeneration:
    """Test Excel output file generation and formatting."""
    
    def test_excel_output_file_structure(self, tmp_path):
        """Test that output Excel file has correct structure and sheets."""
        # Arrange
        input_file = tmp_path / "test_output.xlsx"
        test_data = pd.DataFrame({
            'Game': ['Test Game'],
            'Model Win Percentage': [70],
            'Contract Price': [0.30]
        })
        test_data.to_excel(input_file, sheet_name=sheet_name, index=False)
        
        weekly_bankroll = 1000.0
        
        with patch('src.excel_processor.OUTPUT_DIR', tmp_path):
            # Act
            results_df, output_file = process_betting_excel(input_file, weekly_bankroll)
        
        # Assert
        assert output_file is not None
        assert output_file.exists()
        
        # Read the output file to verify structure
        with pd.ExcelFile(output_file) as excel_file:
            sheet_names = excel_file.sheet_names
            
            # Should have both Quick_View and Betting_Results sheets
            assert 'Quick_View' in sheet_names
            assert 'Betting_Results' in sheet_names
            
            # Read both sheets to verify they have data
            quick_view_df = pd.read_excel(excel_file, sheet_name='Quick_View')
            betting_results_df = pd.read_excel(excel_file, sheet_name='Betting_Results')
            
            assert len(quick_view_df) > 0
            assert len(betting_results_df) > 0
            
            # Quick view should have simplified columns
            assert 'Game' in quick_view_df.columns
            assert 'Win %' in quick_view_df.columns or 'Win %' in [col for col in quick_view_df.columns if 'Win' in col]
    
    def test_excel_output_column_ordering(self, tmp_path):
        """Test that output Excel has logical column ordering."""
        # Arrange
        input_file = tmp_path / "column_order_test.xlsx"
        test_data = pd.DataFrame({
            'Game': ['Test Game 1', 'Test Game 2'],
            'Model Win Percentage': [70, 65],
            'Model Margin': [4.5, 2.1],
            'Contract Price': [0.30, 0.35]
        })
        test_data.to_excel(input_file, sheet_name=sheet_name, index=False)
        
        weekly_bankroll = 1000.0
        
        with patch('src.excel_processor.OUTPUT_DIR', tmp_path):
            # Act
            results_df, output_file = process_betting_excel(input_file, weekly_bankroll)
        
        # Assert
        assert results_df is not None
        
        # Verify logical column grouping
        columns = list(results_df.columns)
        
        # Game identification should come first
        assert columns[0] == 'Game'
        
        # Input data should be early
        assert 'Win %' in columns[:5]
        assert 'Contract Price (¢)' in columns[:5]
        
        # Decision columns should be towards the end
        decision_related = ['Decision', 'Final Recommendation', 'Reason']
        for col in decision_related:
            if col in columns:
                assert columns.index(col) > len(columns) // 2  # In latter half


class TestExcelWorkflowEdgeCases:
    """Test Excel workflow edge cases and boundary conditions."""
    
    def test_excel_workflow_zero_bankroll(self, tmp_path):
        """Test Excel workflow with zero bankroll."""
        # Arrange
        input_file = tmp_path / "zero_bankroll.xlsx"
        test_data = pd.DataFrame({
            'Game': ['Game 1'],
            'Model Win Percentage': [75],
            'Contract Price': [0.25]
        })
        test_data.to_excel(input_file, sheet_name=sheet_name, index=False)
        
        weekly_bankroll = 0.0
        
        with patch('src.excel_processor.OUTPUT_DIR', tmp_path):
            # Act
            results_df, output_file = process_betting_excel(input_file, weekly_bankroll)
        
        # Assert
        assert results_df is not None
        
        # All final recommendations should be SKIP due to no bankroll
        for _, row in results_df.iterrows():
            if row['Decision'] == 'BET':
                assert 'SKIP' in row['Final Recommendation'] or 'Insufficient' in row['Final Recommendation']
            assert row['Cumulative Bet Amount'] == 0.0
    
    def test_excel_workflow_single_game(self, tmp_path):
        """Test Excel workflow with single game."""
        # Arrange
        input_file = tmp_path / "single_game.xlsx"
        test_data = pd.DataFrame({
            'Game': ['Single Game'],
            'Model Win Percentage': [68],
            'Contract Price': [0.32]
        })
        test_data.to_excel(input_file, sheet_name=sheet_name, index=False)
        
        weekly_bankroll = 1000.0
        
        with patch('src.excel_processor.OUTPUT_DIR', tmp_path):
            # Act
            results_df, output_file = process_betting_excel(input_file, weekly_bankroll)
        
        # Assert
        assert results_df is not None
        assert len(results_df) == 1
        assert results_df.iloc[0]['Game'] == 'Single Game'
        
        # Should process correctly
        assert results_df.iloc[0]['Decision'] in ['BET', 'NO BET']
    
    def test_excel_workflow_extreme_values(self, tmp_path):
        """Test Excel workflow with extreme input values."""
        # Arrange
        input_file = tmp_path / "extreme_values.xlsx"
        test_data = pd.DataFrame({
            'Game': ['Very High Win %', 'Very Low Win %', 'Very High Price', 'Very Low Price'],
            'Model Win Percentage': [95, 5, 60, 60],
            'Contract Price': [0.10, 0.10, 0.95, 0.05]
        })
        test_data.to_excel(input_file, sheet_name=sheet_name, index=False)
        
        weekly_bankroll = 1000.0
        
        with patch('src.excel_processor.OUTPUT_DIR', tmp_path):
            # Act
            results_df, output_file = process_betting_excel(input_file, weekly_bankroll)
        
        # Assert
        assert results_df is not None
        assert len(results_df) == 4
        
        # Should handle extreme values without crashing
        for _, row in results_df.iterrows():
            assert row['Decision'] in ['BET', 'NO BET']
            assert isinstance(row['EV Percentage'], (int, float))
            assert row['EV Percentage'] >= -1.0  # Should not be extremely negative
    
    def test_excel_workflow_empty_file(self, tmp_path):
        """Test Excel workflow with empty Excel file."""
        # Arrange
        input_file = tmp_path / "empty_file.xlsx"
        empty_data = pd.DataFrame()  # Empty DataFrame
        empty_data.to_excel(input_file, sheet_name=sheet_name, index=False)
        
        weekly_bankroll = 1000.0
        
        with patch('src.excel_processor.OUTPUT_DIR', tmp_path):
            # Act
            results_df, output_file = process_betting_excel(input_file, weekly_bankroll)
        
        # Assert - Should handle gracefully
        assert results_df is None or len(results_df) == 0
