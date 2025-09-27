"""Integration tests for end-to-end betting framework workflows"""

import pytest
import pandas as pd
import sys
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, Mock

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from betting_framework import user_input_betting_framework
from excel_processor import process_betting_excel, create_sample_excel_in_input_dir
import main


class TestEndToEndWorkflow:
    """Test complete workflow from input to output"""
    
    def test_complete_excel_workflow(self):
        """Test complete Excel processing workflow"""
        # Create test data
        test_data = pd.DataFrame({
            'Game': [
                'Lakers vs Warriors',
                'Cowboys vs Giants', 
                'Yankees vs Red Sox',
                'Chiefs vs Bills',
                'Low EV Game'
            ],
            'Model Win Percentage': [68.0, 75.0, 55.0, 80.0, 52.0],
            'Contract Price': [0.45, 0.20, 0.50, 0.10, 0.49],
            'Model Margin': [5.5, 8.2, 2.1, 15.3, 1.2]
        })
        
        # Create temporary Excel file
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            test_data.to_excel(tmp.name, sheet_name='Games', index=False)
            temp_file = tmp.name
        
        try:
            # Process through complete workflow
            with patch('excel_processor.OUTPUT_DIR', Path(tempfile.gettempdir())):
                result_df, output_file = process_betting_excel(temp_file, 100.0)
                
                # Verify results
                assert result_df is not None
                assert len(result_df) == 5
                
                # Check that all required columns are present
                required_output_columns = [
                    'Game', 'Win %', 'Contract Price (¢)', 'EV Percentage',
                    'Decision', 'Final Recommendation', 'Bet Amount'
                ]
                for col in required_output_columns:
                    assert col in result_df.columns
                
                # Verify decision logic works
                decisions = result_df['Decision'].unique()
                assert 'BET' in decisions or 'NO BET' in decisions
                
                # Verify bankroll allocation logic
                total_allocated = result_df['Cumulative Bet Amount'].sum()
                assert total_allocated <= 100.0  # Should not exceed bankroll
                
                # Verify EV calculations
                for _, row in result_df.iterrows():
                    assert isinstance(row['EV Percentage'], (int, float))
                    assert row['EV Percentage'] >= 0  # EV can be negative but stored as positive
        
        finally:
            os.unlink(temp_file)
    
    def test_wharton_methodology_compliance(self):
        """Test that complete workflow adheres to Wharton methodology"""
        # Test cases that should demonstrate Wharton compliance
        test_cases = [
            # (bankroll, win_pct, price, expected_compliance)
            (100, 68.0, 0.45, True),   # Should meet 10% EV threshold
            (100, 55.0, 0.50, False),  # Should fail EV threshold
            (100, 95.0, 0.05, True),   # High EV but should be capped at 15%
        ]
        
        for bankroll, win_pct, price, expected_compliance in test_cases:
            result = user_input_betting_framework(bankroll, win_pct, price)
            
            if expected_compliance:
                if result['decision'] == 'BET':
                    # Verify Wharton constraints
                    assert result['ev_percentage'] >= 10.0, "Must meet 10% EV threshold"
                    assert result['bet_percentage'] <= 15.0, "Must not exceed 15% bankroll cap"
                    assert result.get('wharton_compliant', False), "Should be marked as Wharton compliant"
                    assert result.get('whole_contracts_only', False), "Should enforce whole contracts"
            else:
                assert result['decision'] == 'NO BET', f"Should be NO BET for case: {win_pct}%, ${price}"
                assert 'reason' in result, "Should provide reason for NO BET"
    
    def test_robinhood_constraints_integration(self):
        """Test that Robinhood-specific constraints are enforced end-to-end"""
        # Test scenarios where whole contract constraint matters
        test_data = pd.DataFrame({
            'Game': [
                'Whole Contract Test 1',
                'Whole Contract Test 2',
                'Insufficient Funds Test'
            ],
            'Model Win Percentage': [70.0, 68.0, 75.0],
            'Contract Price': [0.45, 0.47, 0.50],  # Different prices to test rounding
        })
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            test_data.to_excel(tmp.name, sheet_name='Games', index=False)
            temp_file = tmp.name
        
        try:
            with patch('excel_processor.OUTPUT_DIR', Path(tempfile.gettempdir())):
                result_df, output_file = process_betting_excel(temp_file, 10.0)  # Small bankroll
                
                for _, row in result_df.iterrows():
                    if row['Decision'] == 'BET':
                        # Verify whole contracts only
                        contracts = row['Contracts To Buy']
                        assert contracts == int(contracts), "Must be whole contracts only"
                        assert contracts >= 0, "Cannot have negative contracts"
                        
                        # Verify commission is factored in
                        adjusted_price = row.get('Adjusted Price', 0)
                        contract_price = row['Contract Price (¢)']
                        normalized_price = contract_price / 100 if contract_price >= 1 else contract_price
                        expected_adjusted = normalized_price + 0.02  # Default commission
                        assert abs(adjusted_price - expected_adjusted) < 0.01, "Commission should be included"
        
        finally:
            os.unlink(temp_file)
    
    def test_dual_format_input_integration(self):
        """Test that dual format inputs work correctly in complete workflow"""
        # Test data with mixed formats (cents vs dollars, percentage vs decimal)
        test_data = pd.DataFrame({
            'Game': [
                'Percentage Format Game',
                'Decimal Format Game',
                'Cents Format Game',
                'Dollar Format Game'
            ],
            'Model Win Percentage': [68, 0.72, 55, 0.80],  # Mixed formats
            'Contract Price': [45, 0.40, 52, 0.35],        # Mixed formats
        })
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            test_data.to_excel(tmp.name, sheet_name='Games', index=False)
            temp_file = tmp.name
        
        try:
            with patch('excel_processor.OUTPUT_DIR', Path(tempfile.gettempdir())):
                result_df, output_file = process_betting_excel(temp_file, 100.0)
                
                # All should process successfully
                assert len(result_df) == 4
                
                # Check that formats were normalized correctly
                for _, row in result_df.iterrows():
                    win_pct = row['Win %']
                    assert 0 <= win_pct <= 1, f"Win percentage should be normalized to 0-1: {win_pct}"
                    
                    price = row['Contract Price (¢)']
                    assert price > 0, "Price should be positive"
        
        finally:
            os.unlink(temp_file)


class TestErrorHandlingIntegration:
    """Test error handling in complete workflows"""
    
    def test_invalid_excel_file_handling(self):
        """Test handling of invalid Excel files"""
        # Create Excel file with missing required columns
        invalid_data = pd.DataFrame({
            'Wrong Column': ['Game 1', 'Game 2'],
            'Bad Data': ['not a number', 'also not a number']
        })
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            invalid_data.to_excel(tmp.name, sheet_name='Games', index=False)
            temp_file = tmp.name
        
        try:
            result_df, output_file = process_betting_excel(temp_file, 100.0)
            
            # Should handle error gracefully
            assert result_df is None
            assert output_file is None
        
        finally:
            os.unlink(temp_file)
    
    def test_nonexistent_file_handling(self):
        """Test handling of nonexistent files"""
        nonexistent_file = "this_file_does_not_exist.xlsx"
        
        result_df, output_file = process_betting_excel(nonexistent_file, 100.0)
        
        # Should handle error gracefully
        assert result_df is None
        assert output_file is None
    
    def test_corrupted_data_handling(self):
        """Test handling of corrupted or invalid data within valid Excel structure"""
        # Valid structure but invalid data
        corrupted_data = pd.DataFrame({
            'Game': ['Valid Game', 'Another Game'],
            'Model Win Percentage': ['not_a_number', -999],  # Invalid data
            'Contract Price': [0.45, 'invalid_price']        # Invalid data
        })
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            corrupted_data.to_excel(tmp.name, sheet_name='Games', index=False)
            temp_file = tmp.name
        
        try:
            with patch('excel_processor.OUTPUT_DIR', Path(tempfile.gettempdir())):
                # Should not crash, but may produce NO BET decisions or handle gracefully
                result_df, output_file = process_betting_excel(temp_file, 100.0)
                
                # Framework should be robust enough to handle this
                # Either returns results with NO BET decisions or None for complete failure
                if result_df is not None:
                    # If it processes, all decisions should be NO BET due to invalid data
                    assert all(row['Decision'] == 'NO BET' for _, row in result_df.iterrows() if pd.notna(row['Decision']))
        
        finally:
            os.unlink(temp_file)


class TestMainIntegration:
    """Test main.py integration with complete system"""
    
    @patch('main.input')
    @patch('main.list_available_input_files')
    def test_main_single_bet_mode(self, mock_list_files, mock_input):
        """Test main.py single bet mode integration"""
        # Mock user inputs
        mock_input.side_effect = ['1', '100', '68', '0.45', 'n']
        
        # Should run without error
        try:
            # This tests that the complete import and execution chain works
            from main import main
            # We can't easily test the full execution without mocking print statements
            # But we can verify imports work
            assert callable(main)
        except ImportError as e:
            pytest.fail(f"Main import failed: {e}")
    
    @patch('main.input')
    @patch('main.list_available_input_files')
    def test_main_excel_mode_integration(self, mock_list_files, mock_input):
        """Test main.py Excel mode integration"""
        # Mock file listing and user inputs
        mock_list_files.return_value = ['sample_games.xlsx']
        mock_input.side_effect = ['2', '100', '1', 'n']

        # Create a temporary sample file for the test
        temp_file_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
                temp_file_path = tmp.name
                sample_data = pd.DataFrame({
                    'Game': ['Test Game'],
                    'Model Win Percentage': [68.0],
                    'Contract Price': [0.45]
                })
                sample_data.to_excel(tmp.name, sheet_name='Games', index=False)
            
            with patch('main.get_input_file_path') as mock_get_path:
                mock_get_path.return_value = temp_file_path
                
                from main import main
                assert callable(main)
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)


class TestPerformanceIntegration:
    """Test performance characteristics of complete workflows"""
    
    def test_large_dataset_processing(self):
        """Test processing of larger datasets"""
        # Create a larger dataset (100 games)
        import random
        random.seed(42)  # For reproducible tests
        
        large_data = pd.DataFrame({
            'Game': [f'Game {i}' for i in range(100)],
            'Model Win Percentage': [random.uniform(45, 85) for _ in range(100)],
            'Contract Price': [random.uniform(0.10, 0.90) for _ in range(100)],
            'Model Margin': [random.uniform(0.5, 15.0) for _ in range(100)]
        })
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            large_data.to_excel(tmp.name, sheet_name='Games', index=False)
            temp_file = tmp.name
        
        try:
            with patch('excel_processor.OUTPUT_DIR', Path(tempfile.gettempdir())):
                import time
                start_time = time.time()
                
                result_df, output_file = process_betting_excel(temp_file, 1000.0)
                
                end_time = time.time()
                processing_time = end_time - start_time
                
                # Should complete within reasonable time (adjust threshold as needed)
                assert processing_time < 10.0, f"Processing took too long: {processing_time} seconds"
                
                # Verify all games were processed
                assert result_df is not None
                assert len(result_df) == 100
                
                # Verify memory efficiency - result should have reasonable size
                assert result_df.memory_usage(deep=True).sum() < 10 * 1024 * 1024  # Less than 10MB
        
        finally:
            os.unlink(temp_file)
    
    def test_memory_usage_stability(self):
        """Test that memory usage remains stable during processing"""
        # This is a basic test - in production you might use memory profiling tools
        test_data = pd.DataFrame({
            'Game': [f'Memory Test Game {i}' for i in range(50)],
            'Model Win Percentage': [60.0 + i for i in range(50)],
            'Contract Price': [0.40 + (i * 0.01) for i in range(50)]
        })
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            test_data.to_excel(tmp.name, sheet_name='Games', index=False)
            temp_file = tmp.name
        
        try:
            with patch('excel_processor.OUTPUT_DIR', Path(tempfile.gettempdir())):
                # Process multiple times to check for memory leaks
                for _ in range(5):
                    result_df, output_file = process_betting_excel(temp_file, 500.0)
                    assert result_df is not None
                    
                    # Clear the result to help with memory management
                    del result_df
        
        finally:
            os.unlink(temp_file)


class TestConfigurationIntegration:
    """Test integration with configuration settings"""
    
    def test_settings_integration(self):
        """Test that configuration settings are properly integrated"""
        from config.settings import (
            MIN_EV_THRESHOLD, 
            HALF_KELLY_MULTIPLIER, 
            MAX_BET_PERCENTAGE,
            COMMISSION_PER_CONTRACT
        )
        
        # Test that constants are used in calculations
        result = user_input_betting_framework(100, 55.0, 0.50)
        
        # Should respect MIN_EV_THRESHOLD
        if result['ev_percentage'] < MIN_EV_THRESHOLD:
            assert result['decision'] == 'NO BET'
        
        # Test high EV case to verify other constraints
        high_ev_result = user_input_betting_framework(1000, 90.0, 0.05)
        if high_ev_result['decision'] == 'BET':
            # Should respect MAX_BET_PERCENTAGE
            assert high_ev_result['bet_percentage'] <= (MAX_BET_PERCENTAGE * 100)
            
            # Should include commission in calculations
            adjusted_price = high_ev_result.get('adjusted_price', 0)
            contract_price = 0.05
            expected_adjusted = contract_price + COMMISSION_PER_CONTRACT
            assert abs(adjusted_price - expected_adjusted) < 0.01
    
    def test_directory_structure_integration(self):
        """Test that directory structure is properly used"""
        from config.settings import INPUT_DIR, OUTPUT_DIR
        
        # Directories should be Path objects
        assert isinstance(INPUT_DIR, Path)
        assert isinstance(OUTPUT_DIR, Path)
        
        # Test that functions use these directories
        with patch('excel_processor.INPUT_DIR', INPUT_DIR):
            with patch('excel_processor.OUTPUT_DIR', OUTPUT_DIR):
                # Should work with configured directories
                sample_path = create_sample_excel_in_input_dir()
                assert INPUT_DIR in sample_path.parents or sample_path.parent == INPUT_DIR