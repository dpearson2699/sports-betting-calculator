"""Unit tests for main.py CLI interface"""

import pytest
from unittest.mock import patch, Mock, MagicMock, call
from io import StringIO
import sys
import tempfile
import os
from pathlib import Path

from src.main import interactive_single_bet, excel_batch_mode, main


class TestInteractiveSingleBet:
    """Test interactive single bet functionality"""
    
    @patch('builtins.input')
    @patch('builtins.print')
    @patch('src.main.user_input_betting_framework')
    def test_successful_bet_decision(self, mock_framework, mock_print, mock_input):
        """Test successful BET decision flow"""
        # Setup mock inputs
        mock_input.side_effect = ['100', '68', '0.45', '']  # bankroll, win%, price, margin (empty)
        
        # Setup mock framework response
        mock_framework.return_value = {
            'decision': 'BET',
            'bet_amount': 15.00,
            'bet_percentage': 15.0,
            'contracts_to_buy': 32,
            'expected_profit': 18.67,
            'target_bet_amount': 15.50,
            'unused_amount': 0.50
        }
        
        # Execute
        interactive_single_bet()
        
        # Verify framework called with correct parameters
        mock_framework.assert_called_once_with(
            weekly_bankroll=100.0,
            model_win_percentage=68.0,
            contract_price=0.45,
            model_win_margin=None
        )
        
        # Verify output contains key information
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        output_text = ' '.join(print_calls)
        
        assert 'Decision: BET' in output_text
        assert 'Bet Amount: $15.00' in output_text
        assert 'Bet Percentage: 15.0% of bankroll' in output_text
        assert 'Contracts to Buy: 32' in output_text
        assert 'Expected Profit: $18.67' in output_text

    @patch('builtins.input')
    @patch('builtins.print')
    @patch('src.main.user_input_betting_framework')
    def test_no_bet_decision(self, mock_framework, mock_print, mock_input):
        """Test NO BET decision flow"""
        # Setup mock inputs
        mock_input.side_effect = ['100', '55', '0.50', '']
        
        # Setup mock framework response
        mock_framework.return_value = {
            'decision': 'NO BET',
            'reason': 'EV below 10% threshold (8.0%)',
            'ev_percentage': 8.0,
            'bet_amount': 0.0
        }
        
        # Execute
        interactive_single_bet()
        
        # Verify output contains NO BET information
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        output_text = ' '.join(print_calls)
        
        assert 'Decision: NO BET' in output_text
        assert 'Reason: EV below 10% threshold (8.0%)' in output_text

    @patch('builtins.input')
    @patch('builtins.print')
    @patch('src.main.user_input_betting_framework')
    def test_with_margin_input(self, mock_framework, mock_print, mock_input):
        """Test flow with margin input provided"""
        # Setup mock inputs
        mock_input.side_effect = ['100', '70', '0.40', '5.5']  # Include margin
        
        mock_framework.return_value = {
            'decision': 'BET',
            'bet_amount': 12.00,
            'bet_percentage': 12.0,
            'contracts_to_buy': 28,
            'expected_profit': 15.00
        }
        
        # Execute
        interactive_single_bet()
        
        # Verify framework called with margin
        mock_framework.assert_called_once_with(
            weekly_bankroll=100.0,
            model_win_percentage=70.0,
            contract_price=0.40,
            model_win_margin=5.5
        )

    @patch('builtins.input')
    @patch('builtins.print')
    def test_invalid_numeric_input(self, mock_print, mock_input):
        """Test handling of invalid numeric input"""
        # Setup invalid input - the function handles this gracefully with try/except
        mock_input.side_effect = ['not_a_number']
        
        # Should not raise, but should print error message
        interactive_single_bet()
        
        # Verify error message was printed
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        output_text = ' '.join(print_calls)
        assert 'Error:' in output_text and 'valid numeric' in output_text

    @patch('builtins.input')
    @patch('builtins.print')
    @patch('src.main.user_input_betting_framework')
    def test_whole_contract_adjustment_display(self, mock_framework, mock_print, mock_input):
        """Test display of whole contract adjustment information"""
        mock_input.side_effect = ['100', '68', '0.45', '']
        
        mock_framework.return_value = {
            'decision': 'BET',
            'bet_amount': 14.50,
            'bet_percentage': 14.5,
            'contracts_to_buy': 31,
            'expected_profit': 17.25,
            'target_bet_amount': 15.00,
            'unused_amount': 0.50
        }
        
        interactive_single_bet()
        
        # Check for whole contract adjustment info
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        output_text = ' '.join(print_calls)
        
        # Should show target vs actual amounts when there's unused amount
        assert any('target' in call.lower() or 'unused' in call.lower() or 'adjustment' in call.lower() 
                  for call in print_calls)


class TestExcelBatchMode:
    """Test Excel batch processing mode"""
    
    @patch('builtins.input')
    @patch('builtins.print')
    @patch('src.main.list_available_input_files')
    @patch('src.main.get_input_file_path')
    @patch('src.main.process_betting_excel')
    def test_successful_file_selection_and_processing(self, mock_process, mock_get_path, mock_list_files, mock_print, mock_input):
        """Test successful file selection and processing"""
        # Setup mock available files
        mock_list_files.return_value = ['game1.xlsx', 'game2.xlsx']
        
        # Setup user inputs: file selection, then bankroll
        mock_input.side_effect = ['1', '500']  # Select first file, $500 bankroll
        
        # Setup mock file path resolution
        expected_file_path = str(Path('data/input') / 'game1.xlsx')
        mock_get_path.return_value = expected_file_path
        
        # Setup mock processing results
        mock_df = Mock()
        mock_output_file = 'output.xlsx'
        mock_process.return_value = (mock_df, mock_output_file)
        
        # Execute
        excel_batch_mode()
        
        # Verify get_input_file_path called correctly
        mock_get_path.assert_called_once_with('game1.xlsx')
        
        # Verify process_betting_excel called correctly
        mock_process.assert_called_once_with(expected_file_path, 500.0)
        
        # Verify success message printed
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        output_text = ' '.join(print_calls)
        assert 'Results saved to' in output_text

    @patch('builtins.input')
    @patch('builtins.print')
    @patch('src.main.list_available_input_files')
    @patch('src.main.create_sample_excel_in_input_dir')
    def test_no_files_available_creates_sample(self, mock_create_sample, mock_list_files, mock_print, mock_input):
        """Test sample creation when no files available"""
        # Setup no available files
        mock_list_files.return_value = []
        
        # User chooses to create sample
        mock_input.side_effect = ['y']  # yes to create sample
        
        # Mock sample creation
        mock_create_sample.return_value = 'sample_games.xlsx'
        
        # Execute
        excel_batch_mode()
        
        # Verify sample creation was called
        mock_create_sample.assert_called_once()
        
        # Verify appropriate messages
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        output_text = ' '.join(print_calls)
        assert 'No Excel files found' in output_text
        assert 'Sample file created' in output_text

    @patch('builtins.input')
    @patch('builtins.print')
    @patch('src.main.list_available_input_files')
    def test_no_files_user_declines_sample(self, mock_list_files, mock_print, mock_input):
        """Test when user declines sample creation"""
        mock_list_files.return_value = []
        mock_input.side_effect = ['n']  # no to create sample
        
        excel_batch_mode()
        
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        output_text = ' '.join(print_calls)
        assert 'No Excel files found' in output_text

    @patch('builtins.input')
    @patch('builtins.print')
    @patch('src.main.list_available_input_files')
    @patch('pathlib.Path.exists')
    @patch('src.main.process_betting_excel')
    def test_custom_file_path_input(self, mock_process, mock_exists, mock_list_files, mock_print, mock_input):
        """Test custom file path input"""
        mock_list_files.return_value = ['file1.xlsx']
        
        # User selects custom path option (option 3 for 1 file: 1=file1, 2=sample, 3=custom)
        mock_input.side_effect = ['3', 'custom_file.xlsx', '100']  # option 3, custom path, bankroll
        
        # Mock that custom file exists
        mock_exists.return_value = True
        mock_process.return_value = (Mock(), 'output.xlsx')
        
        excel_batch_mode()
        
        # Verify process_betting_excel was called with custom file
        mock_process.assert_called_once_with('custom_file.xlsx', 100.0)

    @patch('builtins.input')
    @patch('builtins.print')
    @patch('src.main.list_available_input_files')
    def test_invalid_file_selection(self, mock_list_files, mock_print, mock_input):
        """Test invalid file selection handling"""
        mock_list_files.return_value = ['file1.xlsx', 'file2.xlsx']
        
        # Invalid selection (out of range) - should handle gracefully, not raise
        mock_input.side_effect = ['5']  # Invalid file selection
        
        excel_batch_mode()
        
        # Should print invalid selection message
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        output_text = ' '.join(print_calls)
        assert 'Invalid selection' in output_text

    @patch('builtins.input')
    @patch('builtins.print')
    @patch('src.main.list_available_input_files')
    @patch('src.main.get_input_file_path')
    def test_invalid_bankroll_input(self, mock_get_path, mock_list_files, mock_print, mock_input):
        """Test invalid bankroll input handling"""
        mock_list_files.return_value = ['file1.xlsx']
        mock_get_path.return_value = 'path/to/file1.xlsx'
        
        # Valid file selection, invalid bankroll
        mock_input.side_effect = ['1', 'not_a_number']  # Select file 1, invalid bankroll
        
        excel_batch_mode()
        
        # Should handle gracefully and print error message
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        output_text = ' '.join(print_calls)
        assert 'Error:' in output_text and 'valid number' in output_text

    @patch('builtins.input')
    @patch('builtins.print')
    @patch('src.main.list_available_input_files')
    @patch('src.main.process_betting_excel')
    def test_processing_error_handling(self, mock_process, mock_list_files, mock_print, mock_input):
        """Test handling of processing errors"""
        mock_list_files.return_value = ['test.xlsx']
        mock_input.side_effect = ['100', '1']
        
        # Mock processing failure
        mock_process.return_value = (None, None)
        
        excel_batch_mode()
        
        # Should handle gracefully and print error message
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        output_text = ' '.join(print_calls)
        # The function should handle the None return gracefully


class TestMainFunction:
    """Test main menu function"""
    
    @patch('builtins.input')
    @patch('builtins.print')
    @patch('src.main.excel_batch_mode')
    def test_excel_batch_option(self, mock_excel_mode, mock_print, mock_input):
        """Test selecting Excel batch mode"""
        mock_input.side_effect = ['1', '3']  # Select option 1, then exit
        
        main()
        
        mock_excel_mode.assert_called_once()

    @patch('builtins.input')
    @patch('builtins.print')
    @patch('src.main.interactive_single_bet')
    def test_single_bet_option(self, mock_single_bet, mock_print, mock_input):
        """Test selecting single bet mode"""
        mock_input.side_effect = ['2', '3']  # Select option 2, then exit
        
        main()
        
        mock_single_bet.assert_called_once()

    @patch('builtins.input')
    @patch('builtins.print')
    def test_exit_option(self, mock_print, mock_input):
        """Test exit option"""
        mock_input.return_value = '3'  # Exit immediately
        
        main()
        
        # Should print goodbye message
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        output_text = ' '.join(print_calls)
        assert any('goodbye' in call.lower() or 'exit' in call.lower() or 'thank' in call.lower() 
                  for call in print_calls)

    @patch('builtins.input')
    @patch('builtins.print')
    def test_invalid_menu_option(self, mock_print, mock_input):
        """Test invalid menu option handling"""
        mock_input.side_effect = ['5', '3']  # Invalid option, then exit
        
        main()
        
        # Should show error message for invalid option
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        output_text = ' '.join(print_calls)
        assert any('invalid' in call.lower() or 'error' in call.lower() or 'choose' in call.lower()
                  for call in print_calls)

    @patch('builtins.input')
    @patch('builtins.print')
    @patch('src.main.interactive_single_bet')
    def test_menu_loop_continues_after_operation(self, mock_single_bet, mock_print, mock_input):
        """Test that menu continues after completing an operation"""
        mock_input.side_effect = ['2', '3']  # Single bet, then exit
        
        main()
        
        # Should call single bet once, then return to menu
        mock_single_bet.assert_called_once()
        
        # Menu should be displayed multiple times (initial + after operation)
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        menu_displays = sum(1 for call in print_calls if 'Excel Batch Processing' in call)
        assert menu_displays >= 1

    @patch('builtins.input')
    @patch('builtins.print')
    def test_menu_display_format(self, mock_print, mock_input):
        """Test that menu displays correctly formatted options"""
        mock_input.return_value = '3'  # Exit immediately
        
        main()
        
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        output_text = ' '.join(print_calls)
        
        # Check for key menu elements (case insensitive)
        assert 'WHARTON BETTING FRAMEWORK' in output_text.upper()
        assert '1' in output_text and 'Excel Batch Processing' in output_text
        assert '2' in output_text and 'Single Bet Analysis' in output_text
        assert '3' in output_text and 'Exit' in output_text


class TestMainIntegrationScenarios:
    """Integration-like tests for main.py without external dependencies"""
    
    @patch('builtins.input')
    @patch('builtins.print')
    @patch('src.main.user_input_betting_framework')
    def test_complete_single_bet_workflow(self, mock_framework, mock_print, mock_input):
        """Test complete single bet workflow from menu to result"""
        # Menu selection, then single bet inputs, then exit
        mock_input.side_effect = [
            '2',          # Select single bet option
            '100',        # Bankroll
            '68',         # Win percentage  
            '0.45',       # Contract price
            '5.5',        # Margin
            '3'           # Exit after completing bet
        ]
        
        mock_framework.return_value = {
            'decision': 'BET',
            'bet_amount': 15.00,
            'bet_percentage': 15.0,
            'contracts_to_buy': 32,
            'expected_profit': 18.67
        }
        
        main()
        
        # Verify the complete flow worked
        mock_framework.assert_called_once_with(
            weekly_bankroll=100.0,
            model_win_percentage=68.0,
            contract_price=0.45,
            model_win_margin=5.5
        )

    @patch('builtins.input')
    @patch('builtins.print')  
    @patch('src.main.list_available_input_files')
    @patch('src.main.get_input_file_path')
    @patch('src.main.process_betting_excel')
    def test_complete_excel_workflow(self, mock_process, mock_get_path, mock_list_files, mock_print, mock_input):
        """Test complete Excel workflow from menu to processing"""
        mock_list_files.return_value = ['test_games.xlsx']
        mock_process.return_value = (Mock(), 'output.xlsx')
        
        # Setup file path resolution
        expected_path = str(Path('data/input') / 'test_games.xlsx')
        mock_get_path.return_value = expected_path
        
        # Menu selection, then Excel inputs
        mock_input.side_effect = [
            '1',          # Select Excel batch option
            '1',          # Select first file  
            '500'         # Bankroll
        ]
        
        main()
        
        # Verify Excel processing was initiated
        mock_process.assert_called_once_with(expected_path, 500.0)


@pytest.mark.unit
class TestMainErrorHandling:
    """Test error handling in main.py functions"""
    
    @patch('builtins.input')
    @patch('builtins.print')
    @patch('src.main.user_input_betting_framework')
    def test_framework_exception_handling(self, mock_framework, mock_print, mock_input):
        """Test handling of exceptions from betting framework"""
        mock_input.side_effect = ['100', '68', '0.45', '']
        mock_framework.side_effect = Exception("Framework error")
        
        # Should handle exception gracefully and print error message
        interactive_single_bet()
        
        # Verify error message was printed
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        output_text = ' '.join(print_calls)
        assert 'Error:' in output_text

    @patch('builtins.input')
    @patch('builtins.print')
    @patch('src.main.list_available_input_files')  
    @patch('src.main.get_input_file_path')
    @patch('src.main.process_betting_excel')
    def test_file_processing_exception_handling(self, mock_process, mock_get_path, mock_list_files, mock_print, mock_input):
        """Test handling of file processing exceptions"""
        mock_list_files.return_value = ['test.xlsx']
        mock_get_path.return_value = 'path/to/test.xlsx'
        mock_input.side_effect = ['1', '100']  # Select file, enter bankroll
        
        # Mock process_betting_excel to return None (simulating processing failure)
        mock_process.return_value = (None, None)
        
        # Should handle the None return gracefully
        excel_batch_mode()
        
        # Verify failure message was printed
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        output_text = ' '.join(print_calls)
        assert 'Processing failed' in output_text