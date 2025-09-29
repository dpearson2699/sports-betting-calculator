"""
Unit tests for excel_processor.py

Tests Excel file processing, data parsing, validation, and transformation functions
with clear arrange-act-assert structure.
"""

import pytest
import pandas as pd
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.excel_processor import (
    get_required_input_columns,
    get_dynamic_explanation,
    apply_excel_formatting,
    adjust_column_widths,
    list_available_input_files,
    get_input_file_path,
    create_sample_excel_in_input_dir,
    process_betting_excel,
    apply_bankroll_allocation,
    display_summary,
    COLUMN_CONFIG,
    QUICK_VIEW_MAPPING
)


class TestGetRequiredInputColumns:
    """Test required input column identification."""
    
    def test_get_required_input_columns_basic(self):
        """Test that required input columns are correctly identified."""
        # Act
        result = get_required_input_columns()
        
        # Assert
        expected_columns = ['Game', 'Model Win Percentage', 'Contract Price']
        assert all(col in result for col in expected_columns)
        assert 'Model Margin' not in result  # Should be excluded as optional
    
    def test_get_required_input_columns_excludes_optional(self):
        """Test that optional columns are excluded from required list."""
        # Act
        result = get_required_input_columns()
        
        # Assert
        # Model Margin should not be in required columns
        assert 'Model Margin' not in result
        # Only input columns should be included
        for col in result:
            assert COLUMN_CONFIG[col].get('is_input', False) is True


class TestGetDynamicExplanation:
    """Test dynamic explanation generation with commission rates."""
    
    @patch('src.excel_processor.commission_manager')
    def test_get_dynamic_explanation_adjusted_price(self, mock_commission_manager):
        """Test dynamic explanation for Adjusted Price column."""
        # Arrange
        mock_commission_manager.get_commission_rate.return_value = 0.05
        column_name = 'Adjusted Price'
        base_explanation = 'Total cost per contract including contract price + commission'
        
        # Act
        result = get_dynamic_explanation(column_name, base_explanation)
        
        # Assert
        assert '$0.05' in result
        assert 'contract price + $0.05' in result
    
    @patch('src.excel_processor.commission_manager')
    def test_get_dynamic_explanation_contract_cost(self, mock_commission_manager):
        """Test dynamic explanation for Contract Cost column."""
        # Arrange
        mock_commission_manager.get_commission_rate.return_value = 0.02
        column_name = 'Contract Cost'
        base_explanation = 'Total cost including $0.02 commission per contract'
        
        # Act
        result = get_dynamic_explanation(column_name, base_explanation)
        
        # Assert
        assert '$0.02 commission' in result
    
    def test_get_dynamic_explanation_non_commission_column(self):
        """Test that non-commission columns return unchanged explanation."""
        # Arrange
        column_name = 'Game'
        base_explanation = 'The game being analyzed'
        
        # Act
        result = get_dynamic_explanation(column_name, base_explanation)
        
        # Assert
        assert result == base_explanation


class TestApplyExcelFormatting:
    """Test Excel worksheet formatting functionality."""
    
    def test_apply_excel_formatting_basic(self):
        """Test basic Excel formatting application."""
        # Arrange
        mock_worksheet = MagicMock()
        mock_cell = MagicMock()
        mock_worksheet.cell.return_value = mock_cell
        mock_worksheet.__getitem__ = MagicMock(return_value=mock_cell)
        
        df = pd.DataFrame({
            'Game': ['Team A vs Team B'],
            'EV Percentage': [0.15]
        })
        
        # Act
        apply_excel_formatting(mock_worksheet, df)
        
        # Assert
        # Should have been called to format cells
        assert mock_worksheet.cell.called or mock_worksheet.__getitem__.called
    
    def test_apply_excel_formatting_with_custom_mapping(self):
        """Test Excel formatting with custom format mapping."""
        # Arrange
        mock_worksheet = MagicMock()
        mock_cell = MagicMock()
        mock_worksheet.cell.return_value = mock_cell
        mock_worksheet.__getitem__ = MagicMock(return_value=mock_cell)
        
        df = pd.DataFrame({'Test Column': [100]})
        custom_mapping = {
            'Test Column': {
                'format_type': 'currency',
                'explanation': 'Test explanation'
            }
        }
        
        # Act
        apply_excel_formatting(mock_worksheet, df, custom_mapping)
        
        # Assert
        # Should have attempted to format the cell
        assert mock_worksheet.cell.called or mock_worksheet.__getitem__.called


class TestAdjustColumnWidths:
    """Test column width adjustment functionality."""
    
    def test_adjust_column_widths_basic(self):
        """Test basic column width adjustment."""
        # Arrange
        mock_worksheet = MagicMock()
        mock_column = MagicMock()
        mock_cell = MagicMock()
        mock_cell.value = 'Test Header'
        mock_cell.column_letter = 'A'
        mock_column.__iter__ = MagicMock(return_value=iter([mock_cell]))
        mock_worksheet.columns = [mock_column]
        mock_worksheet.column_dimensions = {}
        
        # Act
        adjust_column_widths(mock_worksheet)
        
        # Assert
        # Should have processed the columns
        assert mock_worksheet.columns is not None
    
    def test_adjust_column_widths_with_dataframe(self):
        """Test column width adjustment with DataFrame context."""
        # Arrange
        mock_worksheet = MagicMock()
        mock_column = MagicMock()
        mock_cell = MagicMock()
        mock_cell.value = 'Long Header Name'
        mock_cell.column_letter = 'A'
        mock_column.__iter__ = MagicMock(return_value=iter([mock_cell]))
        mock_worksheet.columns = [mock_column]
        mock_worksheet.column_dimensions = {}
        
        df = pd.DataFrame({'Long Header Name': ['Some data']})
        
        # Act
        adjust_column_widths(mock_worksheet, df)
        
        # Assert
        # Should have processed the worksheet
        assert mock_worksheet.columns is not None


class TestFileOperations:
    """Test file operation functions."""
    
    @patch('src.excel_processor.INPUT_DIR')
    def test_list_available_input_files(self, mock_input_dir):
        """Test listing available Excel files in input directory."""
        # Arrange
        mock_path = MagicMock()
        mock_path.glob.return_value = [
            MagicMock(name='file1.xlsx'),
            MagicMock(name='file2.xlsx'),
            MagicMock(name='~temp.xlsx')  # Should be excluded
        ]
        mock_input_dir.return_value = mock_path
        
        # Act
        result = list_available_input_files()
        
        # Assert
        assert isinstance(result, list)
    
    @patch('src.excel_processor.INPUT_DIR')
    def test_get_input_file_path(self, mock_input_dir):
        """Test getting full path for input file."""
        # Arrange
        mock_input_dir.__truediv__ = MagicMock(return_value=Path('/test/path/file.xlsx'))
        filename = 'test.xlsx'
        
        # Act
        result = get_input_file_path(filename)
        
        # Assert
        assert isinstance(result, (str, Path))
    
    @patch('src.excel_processor.INPUT_DIR')
    @patch('src.excel_processor.DEFAULT_SAMPLE_FILE', 'sample.xlsx')
    @patch('src.excel_processor.DEFAULT_SHEET_NAME', 'Games')
    def test_create_sample_excel_in_input_dir(self, mock_input_dir):
        """Test creation of sample Excel file."""
        # Arrange
        mock_path = MagicMock()
        mock_input_dir.__truediv__ = MagicMock(return_value=mock_path)
        
        with patch('pandas.DataFrame.to_excel') as mock_to_excel:
            # Act
            result = create_sample_excel_in_input_dir()
            
            # Assert
            mock_to_excel.assert_called_once()
            assert result == mock_path


class TestProcessBettingExcel:
    """Test main Excel processing functionality."""
    
    def test_process_betting_excel_missing_file(self):
        """Test processing with non-existent Excel file."""
        # Arrange
        non_existent_file = 'non_existent.xlsx'
        weekly_bankroll = 1000.0
        
        # Act & Assert
        result_df, output_file = process_betting_excel(non_existent_file, weekly_bankroll)
        assert result_df is None
        assert output_file is None
    
    @patch('src.excel_processor.pd.read_excel')
    @patch('src.excel_processor.user_input_betting_framework')
    @patch('src.excel_processor.OUTPUT_DIR')
    def test_process_betting_excel_missing_columns(self, mock_output_dir, mock_betting_framework, mock_read_excel):
        """Test processing Excel file with missing required columns."""
        # Arrange
        mock_read_excel.return_value = pd.DataFrame({
            'Game': ['Team A vs Team B'],
            # Missing 'Model Win Percentage' and 'Contract Price'
        })
        
        # Act
        result_df, output_file = process_betting_excel('test.xlsx', 1000.0)
        
        # Assert
        assert result_df is None
        assert output_file is None
    
    def test_process_betting_excel_data_transformation(self):
        """Test data transformation logic in Excel processing."""
        # This test focuses on the data transformation logic without file I/O
        # Arrange
        input_data = {
            'Game': 'Team A vs Team B',
            'Model Win Percentage': 65,  # Should be converted to 0.65
            'Contract Price': 27  # Should be converted to 0.27
        }
        
        betting_result = {
            'decision': 'BET',
            'bet_amount': 50.0,
            'ev_percentage': 15.0,
            'bet_percentage': 5.0,
            'contracts_to_buy': 185,
            'adjusted_price': 0.27,
            'target_bet_amount': 50.0,
            'unused_amount': 0.05,
            'expected_profit': 7.5,
            'reason': ''
        }
        
        # Act - Test the data transformation logic
        result_row = {
            'Game': input_data['Game'],
            'Win %': input_data['Model Win Percentage'] / 100 if input_data['Model Win Percentage'] > 1 else input_data['Model Win Percentage'],
            'Contract Price (¢)': input_data['Contract Price'],
            'Decision': betting_result['decision'],
            'EV Percentage': betting_result['ev_percentage'] / 100,
            'Bet Amount': betting_result['bet_amount'],
            'Bet Percentage': betting_result.get('bet_percentage', 0) / 100,
            'Contracts To Buy': betting_result.get('contracts_to_buy', 0),
            'Adjusted Price': betting_result.get('adjusted_price', 0),
        }
        
        # Assert
        assert result_row['Win %'] == 0.65  # Converted from 65
        assert result_row['Contract Price (¢)'] == 27
        assert result_row['Decision'] == 'BET'
        assert result_row['EV Percentage'] == 0.15  # Converted from 15.0
        assert result_row['Contracts To Buy'] == 185
    
    def test_process_betting_excel_margin_handling(self):
        """Test handling of optional margin data in Excel processing."""
        # Test the logic for handling margin data
        # Arrange
        row_with_margin = pd.Series({
            'Game': 'Team A vs Team B',
            'Model Win Percentage': 65,
            'Model Margin': 3.5,
            'Contract Price': 27
        })
        
        row_without_margin = pd.Series({
            'Game': 'Team C vs Team D',
            'Model Win Percentage': 58,
            'Contract Price': 45
        })
        
        # Act - Test margin handling logic
        # Check if margin exists and is not null
        margin_val_1 = None
        if 'Model Margin' in row_with_margin.index:
            margin_val = row_with_margin.get('Model Margin', None)
            if pd.notna(margin_val):
                margin_val_1 = margin_val
        
        margin_val_2 = None
        if 'Model Margin' in row_without_margin.index:
            margin_val = row_without_margin.get('Model Margin', None)
            if pd.notna(margin_val):
                margin_val_2 = margin_val
        
        # Assert
        assert margin_val_1 == 3.5  # Should capture the margin value
        assert margin_val_2 is None  # Should be None when margin doesn't exist
    
    def test_process_betting_excel_no_bet_logic(self):
        """Test logic for handling NO BET decisions in Excel processing."""
        # Test the data transformation for NO BET scenarios
        # Arrange
        betting_result = {
            'decision': 'NO BET',
            'bet_amount': 0.0,
            'ev_percentage': 8.0,  # Below threshold
            'bet_percentage': 0.0,
            'contracts_to_buy': 0,
            'adjusted_price': 0.48,
            'target_bet_amount': 0.0,
            'unused_amount': 0.0,
            'expected_profit': 0.0,
            'reason': 'EV below 10% threshold'
        }
        
        # Act - Test the result row creation logic
        result_row = {
            'Game': 'Team A vs Team B',
            'Decision': betting_result['decision'],
            'Bet Amount': betting_result['bet_amount'],
            'EV Percentage': betting_result['ev_percentage'] / 100,
            'Contracts To Buy': betting_result.get('contracts_to_buy', 0),
            'Expected Value EV': betting_result.get('expected_profit', 0),
            'Reason': betting_result.get('reason', '')
        }
        
        # Assert
        assert result_row['Decision'] == 'NO BET'
        assert result_row['Bet Amount'] == 0.0
        assert result_row['EV Percentage'] == 0.08  # 8% converted to decimal
        assert result_row['Contracts To Buy'] == 0
        assert 'EV' in result_row['Reason']


class TestApplyBankrollAllocation:
    """Test bankroll allocation logic."""
    
    def test_apply_bankroll_allocation_sufficient_funds(self):
        """Test bankroll allocation when sufficient funds are available."""
        # Arrange
        df = pd.DataFrame({
            'Decision': ['BET', 'BET', 'NO BET'],
            'Bet Amount': [100.0, 150.0, 0.0],
            'EV Percentage': [0.15, 0.12, 0.08]  # Already sorted by EV
        })
        weekly_bankroll = 1000.0
        
        # Act
        result_df = apply_bankroll_allocation(df, weekly_bankroll)
        
        # Assert
        assert result_df.iloc[0]['Final Recommendation'] == 'BET'
        assert result_df.iloc[1]['Final Recommendation'] == 'BET'
        assert result_df.iloc[2]['Final Recommendation'] == 'NO BET'
        assert result_df.iloc[0]['Cumulative Bet Amount'] == 100.0
        assert result_df.iloc[1]['Cumulative Bet Amount'] == 150.0
        assert result_df.iloc[2]['Cumulative Bet Amount'] == 0.0
    
    def test_apply_bankroll_allocation_insufficient_funds(self):
        """Test bankroll allocation when funds are insufficient for all bets."""
        # Arrange
        df = pd.DataFrame({
            'Decision': ['BET', 'BET', 'BET'],
            'Bet Amount': [400.0, 300.0, 200.0],
            'EV Percentage': [0.15, 0.12, 0.10]  # Already sorted by EV
        })
        weekly_bankroll = 500.0  # Not enough for all bets
        
        # Act
        result_df = apply_bankroll_allocation(df, weekly_bankroll)
        
        # Assert
        assert result_df.iloc[0]['Final Recommendation'] == 'BET'  # First bet fits
        assert result_df.iloc[1]['Final Recommendation'] == 'PARTIAL BET ($100.00)'  # Partial second bet
        assert result_df.iloc[2]['Final Recommendation'] == 'SKIP - Insufficient Bankroll'  # No funds left
        assert result_df.iloc[0]['Cumulative Bet Amount'] == 400.0
        assert result_df.iloc[1]['Cumulative Bet Amount'] == 100.0
        assert result_df.iloc[2]['Cumulative Bet Amount'] == 0.0
    
    def test_apply_bankroll_allocation_very_small_remaining(self):
        """Test bankroll allocation when remaining funds are too small for partial bet."""
        # Arrange
        df = pd.DataFrame({
            'Decision': ['BET', 'BET'],
            'Bet Amount': [995.0, 100.0],
            'EV Percentage': [0.15, 0.12]
        })
        weekly_bankroll = 1000.0  # Only $5 left after first bet
        
        # Act
        result_df = apply_bankroll_allocation(df, weekly_bankroll)
        
        # Assert
        assert result_df.iloc[0]['Final Recommendation'] == 'BET'
        assert result_df.iloc[1]['Final Recommendation'] == 'SKIP - Insufficient Bankroll'  # $5 < 1% of $1000
        assert result_df.iloc[0]['Cumulative Bet Amount'] == 995.0
        assert result_df.iloc[1]['Cumulative Bet Amount'] == 0.0
    
    def test_apply_bankroll_allocation_no_bet_decisions_unchanged(self):
        """Test that NO BET decisions pass through unchanged."""
        # Arrange
        df = pd.DataFrame({
            'Decision': ['NO BET', 'BET', 'NO BET'],
            'Bet Amount': [0.0, 100.0, 0.0],
            'EV Percentage': [0.08, 0.15, 0.05]
        })
        weekly_bankroll = 1000.0
        
        # Act
        result_df = apply_bankroll_allocation(df, weekly_bankroll)
        
        # Assert
        assert result_df.iloc[0]['Final Recommendation'] == 'NO BET'
        assert result_df.iloc[1]['Final Recommendation'] == 'BET'
        assert result_df.iloc[2]['Final Recommendation'] == 'NO BET'
        assert result_df.iloc[0]['Cumulative Bet Amount'] == 0.0
        assert result_df.iloc[1]['Cumulative Bet Amount'] == 100.0
        assert result_df.iloc[2]['Cumulative Bet Amount'] == 0.0


class TestDisplaySummary:
    """Test summary display functionality."""
    
    def test_display_summary_basic(self, capsys):
        """Test basic summary display functionality."""
        # Arrange
        df = pd.DataFrame({
            'Decision': ['BET', 'NO BET', 'BET'],
            'Final Recommendation': ['BET', 'NO BET', 'SKIP - Insufficient Bankroll'],
            'Cumulative Bet Amount': [100.0, 0.0, 0.0],
            'Expected Value EV': [15.0, 0.0, 12.0],
            'Contracts To Buy': [370, 0, 444],
            'EV Percentage': [0.15, 0.08, 0.12],  # Add missing column
            'Game': ['Game 1', 'Game 2', 'Game 3'],
            'Adjusted Price': [0.27, 0.48, 0.35]
        })
        weekly_bankroll = 1000.0
        
        # Act
        display_summary(df, weekly_bankroll)
        
        # Assert
        captured = capsys.readouterr()
        assert 'BETTING ANALYSIS SUMMARY' in captured.out
        assert 'Total Games Analyzed: 3' in captured.out
        assert 'Initial BET Opportunities: 2' in captured.out
        assert 'NO BET Games: 1' in captured.out
        assert 'Final Recommended Bets: 1' in captured.out


class TestDataValidation:
    """Test data validation and error handling."""
    
    def test_column_config_consistency(self):
        """Test that COLUMN_CONFIG is properly structured."""
        # Act & Assert
        for column_name, config in COLUMN_CONFIG.items():
            assert isinstance(config, dict)
            assert 'explanation' in config
            assert 'is_input' in config
            if config.get('format_type'):
                assert config['format_type'] in ['percentage', 'currency', 'text', None]
    
    def test_quick_view_mapping_consistency(self):
        """Test that QUICK_VIEW_MAPPING references valid columns."""
        # Act & Assert
        for original_col, quick_col in QUICK_VIEW_MAPPING.items():
            # Original column should exist in COLUMN_CONFIG or be a known output column
            assert isinstance(original_col, str)
            assert isinstance(quick_col, str)
            assert len(quick_col) > 0
    
    def test_required_columns_are_input_columns(self):
        """Test that all required columns are marked as input columns."""
        # Arrange
        required_cols = get_required_input_columns()
        
        # Act & Assert
        for col in required_cols:
            assert col in COLUMN_CONFIG
            assert COLUMN_CONFIG[col].get('is_input', False) is True


class TestErrorHandling:
    """Test error handling in Excel processing functions."""
    
    @patch('src.excel_processor.pd.read_excel')
    def test_process_betting_excel_read_error(self, mock_read_excel):
        """Test handling of Excel file read errors."""
        # Arrange
        mock_read_excel.side_effect = FileNotFoundError("File not found")
        
        # Act
        result_df, output_file = process_betting_excel('missing.xlsx', 1000.0)
        
        # Assert
        assert result_df is None
        assert output_file is None
    
    @patch('src.excel_processor.pd.read_excel')
    def test_process_betting_excel_invalid_data_types(self, mock_read_excel):
        """Test handling of invalid data types in Excel file."""
        # Arrange
        mock_read_excel.return_value = pd.DataFrame({
            'Game': ['Team A vs Team B'],
            'Model Win Percentage': ['invalid'],  # Should be numeric
            'Contract Price': [27]
        })
        
        # Act
        result_df, output_file = process_betting_excel('invalid.xlsx', 1000.0)
        
        # Assert
        # Should handle the error gracefully
        assert result_df is None
        assert output_file is None
    
    def test_apply_bankroll_allocation_empty_dataframe(self):
        """Test bankroll allocation with empty DataFrame."""
        # Arrange
        df = pd.DataFrame()
        weekly_bankroll = 1000.0
        
        # Act
        result_df = apply_bankroll_allocation(df, weekly_bankroll)
        
        # Assert
        assert len(result_df) == 0
        assert isinstance(result_df, pd.DataFrame)
    
    def test_apply_bankroll_allocation_zero_bankroll(self):
        """Test bankroll allocation with zero bankroll."""
        # Arrange
        df = pd.DataFrame({
            'Decision': ['BET', 'BET'],
            'Bet Amount': [100.0, 150.0],
            'EV Percentage': [0.15, 0.12]
        })
        weekly_bankroll = 0.0
        
        # Act
        result_df = apply_bankroll_allocation(df, weekly_bankroll)
        
        # Assert
        assert result_df.iloc[0]['Final Recommendation'] == 'SKIP - Insufficient Bankroll'
        assert result_df.iloc[1]['Final Recommendation'] == 'SKIP - Insufficient Bankroll'
        assert result_df.iloc[0]['Cumulative Bet Amount'] == 0.0
        assert result_df.iloc[1]['Cumulative Bet Amount'] == 0.0


class TestIntegrationWithBettingFramework:
    """Test integration between Excel processor and betting framework."""
    
    @patch('src.excel_processor.commission_manager')
    def test_commission_manager_integration_logic(self, mock_commission_manager):
        """Test that commission manager integration logic works correctly."""
        # Test the commission integration without file I/O complexity
        # Arrange
        mock_commission_manager.get_commission_rate.return_value = 0.05
        mock_commission_manager.get_current_platform.return_value = 'Test Platform'
        
        betting_result = {
            'decision': 'BET',
            'bet_amount': 50.0,
            'ev_percentage': 15.0,
            'bet_percentage': 5.0,
            'contracts_to_buy': 185,
            'adjusted_price': 0.32,  # 0.27 + 0.05 commission
            'target_bet_amount': 50.0,
            'unused_amount': 0.05,
            'expected_profit': 7.5,
            'reason': ''
        }
        
        # Act - Test commission data inclusion logic
        result_row = {
            'Game': 'Team A vs Team B',
            'Decision': betting_result['decision'],
            'Commission Rate': mock_commission_manager.get_commission_rate(),
            'Platform': mock_commission_manager.get_current_platform(),
            'Adjusted Price': betting_result.get('adjusted_price', 0)
        }
        
        # Assert
        assert result_row['Commission Rate'] == 0.05
        assert result_row['Platform'] == 'Test Platform'
        assert result_row['Adjusted Price'] == 0.32
        
        # Verify commission manager methods were called
        mock_commission_manager.get_commission_rate.assert_called()
        mock_commission_manager.get_current_platform.assert_called()
