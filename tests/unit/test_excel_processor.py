"""Unit tests for src.excel_processor.py"""

import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.excel_processor import (
    get_required_input_columns,
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


class TestColumnConfiguration:
    """Test column configuration and validation"""
    
    def test_column_config_structure(self):
        """Test that COLUMN_CONFIG has proper structure"""
        for col_name, config in COLUMN_CONFIG.items():
            assert isinstance(config, dict)
            assert 'explanation' in config
            assert 'format_type' in config
            assert 'is_input' in config
    
    def test_get_required_input_columns(self):
        """Test that required input columns are correctly identified"""
        required = get_required_input_columns()
        
        assert 'Game' in required
        assert 'Model Win Percentage' in required
        assert 'Contract Price' in required
        assert 'Model Margin' not in required  # Optional column
        
        # Should only return input columns
        for col in required:
            assert COLUMN_CONFIG[col]['is_input'] == True
    
    def test_quick_view_mapping_completeness(self):
        """Test that quick view mapping covers expected columns"""
        assert 'Game' in QUICK_VIEW_MAPPING
        assert 'EV Percentage' in QUICK_VIEW_MAPPING
        assert 'Cumulative Bet Amount' in QUICK_VIEW_MAPPING
        assert 'Final Recommendation' in QUICK_VIEW_MAPPING


class TestExcelFormatting:
    """Test Excel formatting functionality"""
    
    @patch('openpyxl.comments.Comment')
    def test_apply_excel_formatting(self, mock_comment):
        """Test Excel formatting application"""
        # Create mock worksheet
        mock_worksheet = Mock()
        mock_cell = Mock()
        mock_cell.column_letter = 'A'
        mock_worksheet.cell.return_value = mock_cell
        mock_worksheet.__getitem__ = Mock(return_value=mock_cell)
        
        # Create test DataFrame
        df = pd.DataFrame({
            'EV Percentage': [0.15, 0.12],
            'Bet Amount': [100.50, 75.25]
        })
        
        # Apply formatting
        apply_excel_formatting(mock_worksheet, df)
        
        # Verify calls were made
        assert mock_worksheet.cell.called
    
    def test_adjust_column_widths(self):
        """Test column width adjustment"""
        mock_worksheet = Mock()
        mock_column = [Mock(value='Test Value', column_letter='A')]
        mock_worksheet.columns = [mock_column]
        mock_worksheet.column_dimensions = {'A': Mock()}
        
        adjust_column_widths(mock_worksheet)
        
        # Should have set width
        assert hasattr(mock_worksheet.column_dimensions['A'], 'width')


class TestFileOperations:
    """Test file operation utilities"""
    
    @patch('src.excel_processor.INPUT_DIR')
    def test_list_available_input_files(self, mock_input_dir):
        """Test listing available Excel files"""
        # Create mock file objects with name attribute
        mock_file1 = Mock()
        mock_file1.name = 'test1.xlsx'
        mock_file2 = Mock()
        mock_file2.name = 'test2.xlsx'
        mock_file3 = Mock()
        mock_file3.name = '~temp.xlsx'
        
        mock_input_dir.glob.return_value = [mock_file1, mock_file2, mock_file3]
        
        files = list_available_input_files()
        
        assert len(files) == 2
        assert 'test1.xlsx' in files
        assert 'test2.xlsx' in files
        assert '~temp.xlsx' not in files
    
    @patch('src.excel_processor.INPUT_DIR')
    def test_get_input_file_path(self, mock_input_dir):
        """Test getting input file path"""
        filename = 'test.xlsx'
        path = get_input_file_path(filename)
        
        mock_input_dir.__truediv__.assert_called_once_with(filename)
    
    @patch('src.excel_processor.INPUT_DIR')
    @patch('src.excel_processor.pd.DataFrame.to_excel')
    def test_create_sample_excel_in_input_dir(self, mock_to_excel, mock_input_dir):
        """Test sample Excel file creation"""
        mock_input_dir.__truediv__.return_value = Path('test_path.xlsx')
        
        result_path = create_sample_excel_in_input_dir()
        
        mock_to_excel.assert_called_once()
        assert result_path == mock_input_dir.__truediv__.return_value


class TestBankrollAllocation:
    """Test bankroll allocation logic"""
    
    def test_apply_bankroll_allocation_sufficient_funds(self):
        """Test allocation when bankroll is sufficient"""
        df = pd.DataFrame({
            'Decision': ['BET', 'BET', 'NO BET'],
            'Bet Amount': [50.0, 30.0, 0.0],
            'EV Percentage': [0.15, 0.12, 0.08],
            'Expected Value EV': [5.0, 3.0, 0.0]
        })
        
        result_df = apply_bankroll_allocation(df, 100.0)
        
        assert result_df.loc[0, 'Final Recommendation'] == 'BET'
        assert result_df.loc[1, 'Final Recommendation'] == 'BET'
        assert result_df.loc[2, 'Final Recommendation'] == 'NO BET'
        assert result_df.loc[0, 'Cumulative Bet Amount'] == 50.0
        assert result_df.loc[1, 'Cumulative Bet Amount'] == 30.0
    
    def test_apply_bankroll_allocation_insufficient_funds(self):
        """Test allocation when bankroll is insufficient"""
        df = pd.DataFrame({
            'Decision': ['BET', 'BET', 'BET'],
            'Bet Amount': [60.0, 50.0, 40.0],
            'EV Percentage': [0.20, 0.15, 0.12],
            'Expected Value EV': [10.0, 7.5, 5.0]
        })
        
        result_df = apply_bankroll_allocation(df, 100.0)
        
        # First bet should get full allocation
        assert result_df.loc[0, 'Final Recommendation'] == 'BET'
        assert result_df.loc[0, 'Cumulative Bet Amount'] == 60.0
        
        # Second bet should get partial allocation
        assert 'PARTIAL BET' in result_df.loc[1, 'Final Recommendation']
        assert result_df.loc[1, 'Cumulative Bet Amount'] == 40.0
        
        # Third bet should be skipped
        assert result_df.loc[2, 'Final Recommendation'] == 'SKIP - Insufficient Bankroll'
        assert result_df.loc[2, 'Cumulative Bet Amount'] == 0.0
    
    def test_apply_bankroll_allocation_no_bet_decisions(self):
        """Test allocation preserves NO BET decisions"""
        df = pd.DataFrame({
            'Decision': ['NO BET', 'BET', 'NO BET'],
            'Bet Amount': [0.0, 50.0, 0.0],
            'EV Percentage': [0.08, 0.15, 0.05],
            'Expected Value EV': [0.0, 5.0, 0.0]
        })
        
        result_df = apply_bankroll_allocation(df, 100.0)
        
        assert result_df.loc[0, 'Final Recommendation'] == 'NO BET'
        assert result_df.loc[1, 'Final Recommendation'] == 'BET'
        assert result_df.loc[2, 'Final Recommendation'] == 'NO BET'
    
    def test_apply_bankroll_allocation_minimal_remaining_bankroll(self):
        """Test allocation when remaining bankroll is exactly 1%"""
        df = pd.DataFrame({
            'Decision': ['BET', 'BET'],
            'Bet Amount': [99.0, 50.0],
            'EV Percentage': [0.20, 0.15],
            'Expected Value EV': [15.0, 7.5]
        })
        
        result_df = apply_bankroll_allocation(df, 100.0)
        
        assert result_df.loc[0, 'Final Recommendation'] == 'BET'
        assert result_df.loc[0, 'Cumulative Bet Amount'] == 99.0
        
        # $1 left, which is exactly 1% of $100 bankroll, so should get partial bet
        # Logic: remaining >= (weekly_bankroll * 0.01) means >= 1% gets partial bet
        assert result_df.loc[1, 'Final Recommendation'] == 'PARTIAL BET ($1.00)'
        assert result_df.loc[1, 'Cumulative Bet Amount'] == 1.0
    
    def test_apply_bankroll_allocation_below_one_percent(self):
        """Test allocation when remaining bankroll is less than 1%"""
        df = pd.DataFrame({
            'Decision': ['BET', 'BET'],
            'Bet Amount': [99.5, 50.0],  # Leaves only $0.50
            'EV Percentage': [0.20, 0.15],
            'Expected Value EV': [15.0, 7.5]
        })
        
        result_df = apply_bankroll_allocation(df, 100.0)
        
        assert result_df.loc[0, 'Final Recommendation'] == 'BET'
        assert result_df.loc[0, 'Cumulative Bet Amount'] == 99.5
        
        # Only $0.50 left, which is 0.5% of $100 bankroll, so should be skipped
        assert result_df.loc[1, 'Final Recommendation'] == 'SKIP - Insufficient Bankroll'
        assert result_df.loc[1, 'Cumulative Bet Amount'] == 0.0


class TestProcessBettingExcel:
    """Test main Excel processing functionality"""
    
    def test_process_betting_excel_with_valid_data(self, temp_excel_file, sample_bankroll):
        """Test processing valid Excel file"""
        with patch('src.excel_processor.user_input_betting_framework') as mock_framework:
            # Mock framework responses with proper data types
            mock_framework.return_value = {
                'decision': 'BET',
                'ev_percentage': 15.0,
                'bet_amount': 50.0,
                'bet_percentage': 5.0,
                'expected_profit': 7.5,
                'contracts_to_buy': 100,
                'adjusted_price': 0.47,
                'target_bet_amount': 50.0,
                'unused_amount': 3.0
            }
            
            # Don't mock the Excel writer, let it fail gracefully or use real temp file
            with patch('src.excel_processor.OUTPUT_DIR') as mock_output_dir:
                mock_output_dir.__truediv__ = Mock(return_value=Path('/tmp/test_output.xlsx'))
                
                # Mock only the actual file writing operations that would fail
                with patch('pandas.ExcelWriter') as mock_writer:
                    mock_writer.return_value.__enter__ = Mock()
                    mock_writer.return_value.__exit__ = Mock()
                    mock_writer.return_value.sheets = {}
                    
                    result_df, output_file = process_betting_excel(temp_excel_file, sample_bankroll)
                    
                    assert result_df is not None
                    assert len(result_df) > 0
                    assert 'Decision' in result_df.columns
                    assert 'EV Percentage' in result_df.columns
                    assert 'Final Recommendation' in result_df.columns
    
    def test_process_betting_excel_missing_columns(self, temp_invalid_excel_file, sample_bankroll):
        """Test processing Excel file with missing required columns"""
        result_df, output_file = process_betting_excel(temp_invalid_excel_file, sample_bankroll)
        
        assert result_df is None
        assert output_file is None
    
    def test_process_betting_excel_with_margin_data(self, sample_bankroll):
        """Test processing Excel file that includes margin data"""
        # Create test file with margin data
        test_data = pd.DataFrame({
            'Game': ['Test Game'],
            'Model Win Percentage': [68.0],
            'Contract Price': [0.45],
            'Model Margin': [5.5]
        })
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            test_data.to_excel(tmp.name, sheet_name='Games', index=False)
            temp_file = tmp.name
        
        try:
            with patch('src.excel_processor.user_input_betting_framework') as mock_framework:
                mock_framework.return_value = {
                    'decision': 'BET',
                    'ev_percentage': 15.0,
                    'bet_amount': 50.0,
                    'bet_percentage': 5.0,
                    'expected_profit': 7.5,
                    'contracts_to_buy': 100,
                    'adjusted_price': 0.47,
                    'target_bet_amount': 50.0,
                    'unused_amount': 3.0
                }
                
                with patch('src.excel_processor.pd.ExcelWriter') as mock_writer:
                    mock_writer_instance = Mock()
                    mock_writer_instance.__enter__ = Mock(return_value=mock_writer_instance)
                    mock_writer_instance.__exit__ = Mock(return_value=None)
                    mock_writer_instance.sheets = {'Quick_View': Mock(), 'Betting_Results': Mock()}
                    mock_writer.return_value = mock_writer_instance
                    
                    result_df, output_file = process_betting_excel(temp_file, sample_bankroll)
                    
                    # Should call framework with margin data
                    mock_framework.assert_called_with(
                        weekly_bankroll=sample_bankroll,
                        model_win_percentage=68.0,
                        contract_price=0.45,
                        model_win_margin=5.5,
                        commission_per_contract=0.02
                    )
        finally:
            os.unlink(temp_file)
    
    def test_process_betting_excel_without_margin_data(self, sample_bankroll):
        """Test processing Excel file without margin data"""
        # Create test file without margin data
        test_data = pd.DataFrame({
            'Game': ['Test Game'],
            'Model Win Percentage': [68.0],
            'Contract Price': [0.45]
        })
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            test_data.to_excel(tmp.name, sheet_name='Games', index=False)
            temp_file = tmp.name
        
        try:
            with patch('src.excel_processor.user_input_betting_framework') as mock_framework:
                mock_framework.return_value = {
                    'decision': 'BET',
                    'ev_percentage': 15.0,
                    'bet_amount': 50.0,
                    'bet_percentage': 5.0,
                    'expected_profit': 7.5,
                    'contracts_to_buy': 100,
                    'adjusted_price': 0.47,
                    'target_bet_amount': 50.0,
                    'unused_amount': 3.0
                }
                
                with patch('src.excel_processor.pd.ExcelWriter') as mock_writer:
                    mock_writer_instance = Mock()
                    mock_writer_instance.__enter__ = Mock(return_value=mock_writer_instance)
                    mock_writer_instance.__exit__ = Mock(return_value=None)
                    mock_writer_instance.sheets = {'Quick_View': Mock(), 'Betting_Results': Mock()}
                    mock_writer.return_value = mock_writer_instance
                    
                    result_df, output_file = process_betting_excel(temp_file, sample_bankroll)
                    
                    # Should call framework with margin as None
                    mock_framework.assert_called_with(
                        weekly_bankroll=sample_bankroll,
                        model_win_percentage=68.0,
                        contract_price=0.45,
                        model_win_margin=None,
                        commission_per_contract=0.02
                    )
        finally:
            os.unlink(temp_file)


class TestDisplaySummary:
    """Test summary display functionality"""
    
    def test_display_summary(self, capsys):
        """Test that summary displays correctly"""
        df = pd.DataFrame({
            'Decision': ['BET', 'BET', 'NO BET'],
            'Final Recommendation': ['BET', 'BET', 'NO BET'],
            'Game': ['Game 1', 'Game 2', 'Game 3'],
            'Cumulative Bet Amount': [50.0, 30.0, 0.0],
            'Expected Value EV': [7.5, 4.5, 0.0],
            'EV Percentage': [0.15, 0.12, 0.08]
        })
        
        display_summary(df, 100.0)
        
        captured = capsys.readouterr()
        assert 'BETTING ANALYSIS SUMMARY' in captured.out
        assert 'Total Games Analyzed: 3' in captured.out
        assert 'Initial BET Opportunities: 2' in captured.out
        assert 'NO BET Games: 1' in captured.out
        assert 'Final Recommended Bets: 2' in captured.out
        assert 'Weekly Bankroll: $100.00' in captured.out
        assert 'Total Allocated: $80.00' in captured.out


class TestIntegrationScenarios:
    """Integration tests for complete Excel processing scenarios"""
    
    def test_high_ev_scenario(self, sample_bankroll):
        """Test scenario with high EV games"""
        test_data = pd.DataFrame({
            'Game': ['High EV Game 1', 'High EV Game 2'],
            'Model Win Percentage': [75.0, 80.0],
            'Contract Price': [0.20, 0.15]
        })
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            test_data.to_excel(tmp.name, sheet_name='Games', index=False)
            temp_file = tmp.name
        
        try:
            # Mock only the file output operations
            with patch('src.excel_processor.OUTPUT_DIR') as mock_output_dir:
                mock_output_dir.__truediv__ = Mock(return_value=Path('/tmp/test_output.xlsx'))
                
                with patch('pandas.ExcelWriter') as mock_writer:
                    mock_writer.return_value.__enter__ = Mock()
                    mock_writer.return_value.__exit__ = Mock()
                    mock_writer.return_value.sheets = {}
                    
                    result_df, output_file = process_betting_excel(temp_file, sample_bankroll)
                    
                    assert result_df is not None
                    # Both games should likely be BET decisions due to high EV
                    bet_decisions = result_df[result_df['Decision'] == 'BET']
                    assert len(bet_decisions) >= 1  # At least one should be a bet
        finally:
            os.unlink(temp_file)
    
    def test_low_ev_scenario(self, sample_bankroll):
        """Test scenario with low EV games"""
        test_data = pd.DataFrame({
            'Game': ['Low EV Game 1', 'Low EV Game 2'],
            'Model Win Percentage': [52.0, 55.0],
            'Contract Price': [0.50, 0.48]
        })
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            test_data.to_excel(tmp.name, sheet_name='Games', index=False)
            temp_file = tmp.name
        
        try:
            # Mock only the file output operations
            with patch('src.excel_processor.OUTPUT_DIR') as mock_output_dir:
                mock_output_dir.__truediv__ = Mock(return_value=Path('/tmp/test_output.xlsx'))
                
                with patch('pandas.ExcelWriter') as mock_writer:
                    mock_writer.return_value.__enter__ = Mock()
                    mock_writer.return_value.__exit__ = Mock()
                    mock_writer.return_value.sheets = {}
                    
                    result_df, output_file = process_betting_excel(temp_file, sample_bankroll)
                    
                    assert result_df is not None
                    # Games should likely be NO BET decisions due to low EV
                    no_bet_decisions = result_df[result_df['Decision'] == 'NO BET']
                    assert len(no_bet_decisions) >= 1  # At least one should be no bet
        finally:
            os.unlink(temp_file)
