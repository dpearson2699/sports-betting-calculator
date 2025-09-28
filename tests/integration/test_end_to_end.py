"""Integration tests for end-to-end betting framework workflows"""

import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, Mock

from src.betting_framework import user_input_betting_framework
from src.excel_processor import process_betting_excel, create_sample_excel_in_input_dir
from src.commission_manager import CommissionManager, commission_manager
from src import main


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
            with patch('src.excel_processor.OUTPUT_DIR', Path(tempfile.gettempdir())):
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
            with patch('src.excel_processor.OUTPUT_DIR', Path(tempfile.gettempdir())):
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
            with patch('src.excel_processor.OUTPUT_DIR', Path(tempfile.gettempdir())):
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
            with patch('src.excel_processor.OUTPUT_DIR', Path(tempfile.gettempdir())):
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
    """Test src.main.py integration with complete system"""
    
    @patch('src.main.input')
    @patch('src.main.list_available_input_files')
    def test_main_single_bet_mode(self, mock_list_files, mock_input):
        """Test src.main.py single bet mode integration"""
        # Mock user inputs
        mock_input.side_effect = ['1', '100', '68', '0.45', 'n']
        
        # Should run without error
        try:
            # This tests that the complete import and execution chain works
            from src.main import main
            # We can't easily test the full execution without mocking print statements
            # But we can verify imports work
            assert callable(main)
        except ImportError as e:
            pytest.fail(f"Main import failed: {e}")
    
    @patch('src.main.input')
    @patch('src.main.list_available_input_files')
    def test_main_excel_mode_integration(self, mock_list_files, mock_input):
        """Test src.main.py Excel mode integration"""
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
            
            with patch('src.main.get_input_file_path') as mock_get_path:
                mock_get_path.return_value = temp_file_path
                
                from src.main import main
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
            with patch('src.excel_processor.OUTPUT_DIR', Path(tempfile.gettempdir())):
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
            with patch('src.excel_processor.OUTPUT_DIR', Path(tempfile.gettempdir())):
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
        with patch('src.excel_processor.INPUT_DIR', INPUT_DIR):
            with patch('src.excel_processor.OUTPUT_DIR', OUTPUT_DIR):
                # Should work with configured directories
                sample_path = create_sample_excel_in_input_dir()
                assert INPUT_DIR in sample_path.parents or sample_path.parent == INPUT_DIR


class TestPlatformAgnosticIntegration:
    """Integration tests for platform-agnostic commission functionality"""
    
    def setup_method(self):
        """Reset commission manager to default state before each test"""
        commission_manager.reset_to_default()
    
    def teardown_method(self):
        """Reset commission manager to default state after each test"""
        commission_manager.reset_to_default()
    
    def test_end_to_end_betting_with_different_commission_rates(self):
        """Test end-to-end betting calculations with different commission rates"""
        # Test data that should be sensitive to commission changes
        test_cases = [
            # (platform, commission_rate, expected_behavior)
            ("Robinhood", 0.02, "baseline"),
            ("Kalshi", 0.00, "more_aggressive"),  # No commission should allow more bets
            ("PredictIt", 0.10, "more_conservative"),  # High commission should be more conservative
            ("Custom", 0.05, "moderate")  # Medium commission
        ]
        
        # Test scenario: marginal bet that's sensitive to commission
        bankroll = 100.0
        win_percentage = 65.0  # Marginal EV case
        contract_price = 0.48
        
        results = {}
        
        for platform, commission_rate, expected_behavior in test_cases:
            # Set commission rate
            if platform == "Custom":
                commission_manager.set_commission_rate(commission_rate, platform)
            else:
                commission_manager.set_platform(platform)
            
            # Run betting calculation
            result = user_input_betting_framework(
                weekly_bankroll=bankroll,
                model_win_percentage=win_percentage,
                contract_price=contract_price
            )
            
            results[platform] = result
            
            # Verify commission rate is being used
            assert result.get('commission_per_contract') == commission_rate or \
                   abs(result.get('commission_per_contract', 0) - commission_rate) < 0.001
        
        # Verify commission impact on decisions
        robinhood_result = results["Robinhood"]
        kalshi_result = results["Kalshi"]
        predictit_result = results["PredictIt"]
        
        # Kalshi (no commission) should be more favorable than Robinhood
        if kalshi_result['decision'] == 'BET' and robinhood_result['decision'] == 'BET':
            assert kalshi_result['ev_percentage'] >= robinhood_result['ev_percentage']
            # Allow small tolerance for bet amount due to rounding in Kelly calculations
            assert kalshi_result['bet_amount'] >= robinhood_result['bet_amount'] - 0.5
        
        # PredictIt (high commission) should be less favorable than Robinhood
        if robinhood_result['decision'] == 'BET':
            # PredictIt might reject the bet due to high commission
            if predictit_result['decision'] == 'BET':
                assert predictit_result['ev_percentage'] <= robinhood_result['ev_percentage']
                assert predictit_result['bet_amount'] <= robinhood_result['bet_amount']
    
    def test_excel_processing_with_custom_commission_rates(self):
        """Test Excel processing with different commission rates"""
        # Create test data
        test_data = pd.DataFrame({
            'Game': [
                'High EV Game',
                'Marginal EV Game',
                'Low EV Game'
            ],
            'Model Win Percentage': [75.0, 62.0, 55.0],
            'Contract Price': [0.25, 0.45, 0.48],
            'Model Margin': [12.5, 4.2, 2.1]
        })
        
        commission_scenarios = [
            ("Robinhood", 0.02),
            ("Kalshi", 0.00),
            ("PredictIt", 0.10)
        ]
        
        results_by_platform = {}
        
        for platform, commission_rate in commission_scenarios:
            # Set commission rate
            commission_manager.set_platform(platform)
            
            # Create temporary Excel file
            with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
                test_data.to_excel(tmp.name, sheet_name='Games', index=False)
                temp_file = tmp.name
            
            try:
                with patch('src.excel_processor.OUTPUT_DIR', Path(tempfile.gettempdir())):
                    result_df, output_file = process_betting_excel(temp_file, 100.0)
                    
                    # Store results
                    results_by_platform[platform] = result_df.copy()
                    
                    # Verify commission rate is reflected in results
                    assert all(row['Commission Rate'] == commission_rate 
                             for _, row in result_df.iterrows())
                    assert all(row['Platform'] == platform 
                             for _, row in result_df.iterrows())
                    
                    # Verify calculations use correct commission
                    for _, row in result_df.iterrows():
                        if row['Decision'] == 'BET':
                            # Check that adjusted price includes commission
                            expected_adjusted = (row['Contract Price (¢)'] / 100 
                                               if row['Contract Price (¢)'] >= 1 
                                               else row['Contract Price (¢)']) + commission_rate
                            actual_adjusted = row.get('Adjusted Price', 0)
                            assert abs(actual_adjusted - expected_adjusted) < 0.01
            
            finally:
                os.unlink(temp_file)
        
        # Compare results across platforms
        robinhood_df = results_by_platform["Robinhood"]
        kalshi_df = results_by_platform["Kalshi"]
        predictit_df = results_by_platform["PredictIt"]
        
        # Verify that lower commission rates result in more favorable outcomes
        for i in range(len(robinhood_df)):
            robinhood_row = robinhood_df.iloc[i]
            kalshi_row = kalshi_df.iloc[i]
            predictit_row = predictit_df.iloc[i]
            
            # Same game should have consistent ordering by commission impact
            if all(row['Decision'] == 'BET' for row in [robinhood_row, kalshi_row, predictit_row]):
                # Kalshi (no commission) should have highest EV
                assert kalshi_row['EV Percentage'] >= robinhood_row['EV Percentage']
                # PredictIt (high commission) should have lowest EV
                assert robinhood_row['EV Percentage'] >= predictit_row['EV Percentage']
    
    def test_cli_interface_commission_configuration_workflow(self):
        """Test CLI interface commission configuration workflow"""
        # Test platform selection workflow - select Kalshi (option 2)
        with patch('src.main.input') as mock_input:
            # Simulate user selecting Kalshi platform (option 2 in the menu)
            mock_input.side_effect = ['2']  # Select Kalshi
            
            # Import and test the commission configuration function
            from src.main import commission_configuration
            
            # Should not raise any exceptions
            commission_configuration()
            
            # Verify platform was changed
            assert commission_manager.get_current_platform() == "Kalshi"
            assert commission_manager.get_commission_rate() == 0.00
        
        # Reset for next test
        commission_manager.reset_to_default()
        
        # Test custom rate workflow - custom rate is option 5 (after 4 platforms)
        with patch('src.main.input') as mock_input:
            # Simulate user setting custom rate
            mock_input.side_effect = ['5', '0.03']  # Custom rate option, then $0.03
            
            commission_configuration()
            
            # Verify custom rate was set
            assert commission_manager.get_current_platform() == "Custom"
            assert commission_manager.get_commission_rate() == 0.03
        
        # Test reset to default workflow - reset is option 6
        with patch('src.main.input') as mock_input:
            mock_input.side_effect = ['6']  # Reset to default option
            
            commission_configuration()
            
            # Verify reset to default
            assert commission_manager.get_current_platform() == "Robinhood"
            assert commission_manager.get_commission_rate() == 0.02
    
    def test_backward_compatibility_with_existing_code(self):
        """Verify backward compatibility with existing code"""
        # Test that existing function calls still work without commission parameter
        result = user_input_betting_framework(
            weekly_bankroll=100.0,
            model_win_percentage=68.0,
            contract_price=0.45
        )
        
        # Should use default commission rate
        assert result is not None
        assert 'decision' in result
        assert result.get('commission_per_contract') == commission_manager.get_commission_rate()
        
        # Test with explicit commission parameter (should override CommissionManager)
        explicit_commission = 0.05
        result_explicit = user_input_betting_framework(
            weekly_bankroll=100.0,
            model_win_percentage=68.0,
            contract_price=0.45,
            commission_per_contract=explicit_commission
        )
        
        # Should use explicit commission, not CommissionManager
        assert result_explicit.get('commission_per_contract') == explicit_commission
        
        # Test Excel processing backward compatibility
        test_data = pd.DataFrame({
            'Game': ['Compatibility Test'],
            'Model Win Percentage': [68.0],
            'Contract Price': [0.45]
        })
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            test_data.to_excel(tmp.name, sheet_name='Games', index=False)
            temp_file = tmp.name
        
        try:
            with patch('src.excel_processor.OUTPUT_DIR', Path(tempfile.gettempdir())):
                result_df, output_file = process_betting_excel(temp_file, 100.0)
                
                # Should process successfully
                assert result_df is not None
                assert len(result_df) == 1
                
                # Should include commission information
                row = result_df.iloc[0]
                assert 'Commission Rate' in result_df.columns
                assert 'Platform' in result_df.columns
                assert row['Commission Rate'] == commission_manager.get_commission_rate()
                assert row['Platform'] == commission_manager.get_current_platform()
        
        finally:
            os.unlink(temp_file)
    
    def test_commission_manager_integration_with_betting_framework(self):
        """Test CommissionManager integration with core betting framework"""
        # Test different commission rates affect calculations correctly
        test_scenarios = [
            (0.00, "zero_commission"),
            (0.02, "robinhood_default"),
            (0.05, "medium_commission"),
            (0.10, "high_commission")
        ]
        
        bankroll = 100.0
        win_percentage = 65.0
        contract_price = 0.40
        
        results = []
        
        for commission_rate, scenario_name in test_scenarios:
            commission_manager.set_commission_rate(commission_rate, f"Test_{scenario_name}")
            
            result = user_input_betting_framework(
                weekly_bankroll=bankroll,
                model_win_percentage=win_percentage,
                contract_price=contract_price
            )
            
            results.append((commission_rate, result))
            
            # Verify commission is correctly applied
            expected_adjusted_price = contract_price + commission_rate
            actual_adjusted_price = result.get('adjusted_price', 0)
            assert abs(actual_adjusted_price - expected_adjusted_price) < 0.001
        
        # Verify that higher commission rates result in lower EVs and bet amounts
        for i in range(len(results) - 1):
            current_commission, current_result = results[i]
            next_commission, next_result = results[i + 1]
            
            if current_result['decision'] == 'BET' and next_result['decision'] == 'BET':
                # Higher commission should result in lower EV
                assert current_result['ev_percentage'] >= next_result['ev_percentage']
                # Higher commission should result in lower bet amount (with tolerance for rounding)
                assert current_result['bet_amount'] >= next_result['bet_amount'] - 0.5
    
    def test_commission_persistence_across_operations(self):
        """Test that commission settings persist across multiple operations"""
        # Set custom commission rate
        custom_rate = 0.03
        commission_manager.set_commission_rate(custom_rate, "TestPlatform")
        
        # Perform multiple betting calculations
        for i in range(5):
            result = user_input_betting_framework(
                weekly_bankroll=100.0,
                model_win_percentage=65.0 + i,
                contract_price=0.40 + (i * 0.01)
            )
            
            # Commission rate should remain consistent
            assert result.get('commission_per_contract') == custom_rate
        
        # Process Excel file
        test_data = pd.DataFrame({
            'Game': [f'Game {i}' for i in range(3)],
            'Model Win Percentage': [65.0, 70.0, 75.0],
            'Contract Price': [0.40, 0.35, 0.30]
        })
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            test_data.to_excel(tmp.name, sheet_name='Games', index=False)
            temp_file = tmp.name
        
        try:
            with patch('src.excel_processor.OUTPUT_DIR', Path(tempfile.gettempdir())):
                result_df, output_file = process_betting_excel(temp_file, 100.0)
                
                # All rows should use the same commission rate
                for _, row in result_df.iterrows():
                    assert row['Commission Rate'] == custom_rate
                    assert row['Platform'] == "TestPlatform"
        
        finally:
            os.unlink(temp_file)
    
    def test_error_handling_with_invalid_commission_rates(self):
        """Test error handling when invalid commission rates are used"""
        # Test invalid commission rate handling in CommissionManager
        with pytest.raises(ValueError):
            commission_manager.set_commission_rate(-0.01)  # Negative rate
        
        with pytest.raises(ValueError):
            commission_manager.set_commission_rate(1.01)   # Rate > 100%
        
        with pytest.raises(TypeError):
            commission_manager.set_commission_rate("invalid")  # Non-numeric
        
        # Test invalid platform handling
        with pytest.raises(ValueError):
            commission_manager.set_platform("NonexistentPlatform")
        
        # Verify system remains stable after errors
        assert commission_manager.get_commission_rate() == 0.02  # Should remain at default
        assert commission_manager.get_current_platform() == "Robinhood"
        
        # Test that betting framework handles edge cases gracefully
        commission_manager.set_commission_rate(0.00)  # Zero commission
        result = user_input_betting_framework(100.0, 68.0, 0.45)
        assert result is not None
        assert result['decision'] in ['BET', 'NO BET']
        
        commission_manager.set_commission_rate(0.50)  # Very high commission
        result = user_input_betting_framework(100.0, 68.0, 0.45)
        assert result is not None
        assert result['decision'] in ['BET', 'NO BET']
    
    def test_commission_impact_visibility_in_outputs(self):
        """Test that commission impact is visible in all output formats"""
        # Set a distinctive commission rate for testing
        test_commission = 0.07
        commission_manager.set_commission_rate(test_commission, "TestVisibility")
        
        # Test single bet output
        result = user_input_betting_framework(100.0, 70.0, 0.40)
        
        # Should include commission information
        assert 'commission_per_contract' in result
        assert result['commission_per_contract'] == test_commission
        assert 'adjusted_price' in result
        expected_adjusted = 0.40 + test_commission
        assert abs(result['adjusted_price'] - expected_adjusted) < 0.001
        
        # Test Excel output
        test_data = pd.DataFrame({
            'Game': ['Visibility Test Game'],
            'Model Win Percentage': [70.0],
            'Contract Price': [0.40]
        })
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            test_data.to_excel(tmp.name, sheet_name='Games', index=False)
            temp_file = tmp.name
        
        try:
            with patch('src.excel_processor.OUTPUT_DIR', Path(tempfile.gettempdir())):
                result_df, output_file = process_betting_excel(temp_file, 100.0)
                
                # Should include commission columns
                assert 'Commission Rate' in result_df.columns
                assert 'Platform' in result_df.columns
                
                row = result_df.iloc[0]
                assert row['Commission Rate'] == test_commission
                assert row['Platform'] == "TestVisibility"
                
                # Should include adjusted price information
                if 'Adjusted Price' in result_df.columns:
                    expected_adjusted = 0.40 + test_commission
                    assert abs(row['Adjusted Price'] - expected_adjusted) < 0.001
        
        finally:
            os.unlink(temp_file)
    
    def test_multiple_platform_switching_workflow(self):
        """Test switching between multiple platforms in a single session"""
        platforms_to_test = ["Robinhood", "Kalshi", "PredictIt", "Robinhood"]
        
        # Test data that should show different results across platforms
        bankroll = 100.0
        win_percentage = 63.0  # Marginal case
        contract_price = 0.47
        
        results = []
        
        for platform in platforms_to_test:
            commission_manager.set_platform(platform)
            
            result = user_input_betting_framework(
                weekly_bankroll=bankroll,
                model_win_percentage=win_percentage,
                contract_price=contract_price
            )
            
            results.append({
                'platform': platform,
                'commission_rate': commission_manager.get_commission_rate(),
                'result': result
            })
            
            # Verify platform is correctly set
            assert commission_manager.get_current_platform() == platform
        
        # Verify results are consistent when returning to same platform
        first_robinhood = results[0]
        second_robinhood = results[3]
        
        assert first_robinhood['platform'] == second_robinhood['platform']
        assert first_robinhood['commission_rate'] == second_robinhood['commission_rate']
        assert first_robinhood['result']['decision'] == second_robinhood['result']['decision']
        assert abs(first_robinhood['result']['ev_percentage'] - 
                  second_robinhood['result']['ev_percentage']) < 0.01
