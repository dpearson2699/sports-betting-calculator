"""Unit tests for CommissionManager class"""

import pytest
from unittest.mock import patch, MagicMock
import logging

from src.commission_manager import CommissionManager, commission_manager


class TestCommissionManagerInitialization:
    """Test CommissionManager initialization and default settings"""
    
    def test_fresh_initialization_with_no_config(self):
        """Test that CommissionManager initializes with defaults when no config exists"""
        manager = CommissionManager()
        # Clear config to test fresh initialization
        manager._clear_config_file()
        
        # Create new instance to test fresh initialization
        fresh_manager = CommissionManager()
        assert fresh_manager.get_commission_rate() == 0.02
        assert fresh_manager.get_current_platform() == "Robinhood"
    
    def test_initialization_loads_saved_settings(self):
        """Test that CommissionManager loads previously saved settings"""
        # Set up a known state
        manager = CommissionManager()
        manager.set_platform("Kalshi")
        
        # Create new instance - should load saved settings
        new_manager = CommissionManager()
        assert new_manager.get_commission_rate() == 0.00
        assert new_manager.get_current_platform() == "Kalshi"
        
        # Clean up for other tests
        new_manager.reset_to_default()
    
    def test_global_instance_exists(self):
        """Test that global commission_manager instance is available"""
        assert commission_manager is not None
        assert isinstance(commission_manager, CommissionManager)
        # Don't assert specific values since they depend on saved state


class TestCommissionRateGetterSetter:
    """Test commission rate getting and setting functionality"""
    
    def setup_method(self):
        """Set up CommissionManager for each test"""
        self.manager = CommissionManager()
        # Store initial state to restore later
        self.initial_rate = self.manager.get_commission_rate()
        self.initial_platform = self.manager.get_current_platform()
    
    def teardown_method(self):
        """Restore initial state after each test"""
        self.manager.set_commission_rate(self.initial_rate, self.initial_platform)
    
    def test_get_commission_rate_current(self):
        """Test getting current commission rate (whatever it is)"""
        rate = self.manager.get_commission_rate()
        assert isinstance(rate, float)
        assert 0.0 <= rate <= 1.0
    
    def test_set_commission_rate_valid(self):
        """Test setting valid commission rates"""
        # Test various valid rates
        test_rates = [0.00, 0.01, 0.05, 0.10, 0.50, 1.00]
        
        for rate in test_rates:
            self.manager.set_commission_rate(rate)
            assert self.manager.get_commission_rate() == rate
            assert self.manager.get_current_platform() == "Custom"
            
            # Verify persistence by creating new instance
            new_manager = CommissionManager()
            assert new_manager.get_commission_rate() == rate
            assert new_manager.get_current_platform() == "Custom"
    
    def test_set_commission_rate_with_platform_name(self):
        """Test setting commission rate with custom platform name"""
        self.manager.set_commission_rate(0.05, "TestPlatform")
        
        assert self.manager.get_commission_rate() == 0.05
        assert self.manager.get_current_platform() == "TestPlatform"
    
    def test_set_commission_rate_type_conversion(self):
        """Test that integer rates are converted to float"""
        self.manager.set_commission_rate(1, "IntegerTest")
        
        assert self.manager.get_commission_rate() == 1.0
        assert isinstance(self.manager.get_commission_rate(), float)
    
    @patch('src.commission_manager.logger')
    def test_set_commission_rate_logging(self, mock_logger):
        """Test that commission rate changes are logged"""
        old_rate = self.manager.get_commission_rate()
        self.manager.set_commission_rate(0.05, "TestPlatform")
        
        mock_logger.info.assert_called()
        log_call = mock_logger.info.call_args[0][0]
        assert "Commission rate updated" in log_call
        assert f"{old_rate:.2f}" in log_call  # old rate (whatever it was)
        assert "0.05" in log_call  # new rate
    
    def test_commission_persistence_across_instances(self):
        """Test that commission settings persist across CommissionManager instances"""
        # Set a distinctive rate
        test_rate = 0.07
        test_platform = "PersistenceTest"
        
        self.manager.set_commission_rate(test_rate, test_platform)
        
        # Create new instance - should load saved settings
        new_manager = CommissionManager()
        assert new_manager.get_commission_rate() == test_rate
        assert new_manager.get_current_platform() == test_platform
        
        # Change settings in new instance
        new_manager.set_platform("Kalshi")
        
        # Create another instance - should load the updated settings
        third_manager = CommissionManager()
        assert third_manager.get_commission_rate() == 0.00  # Kalshi rate
        assert third_manager.get_current_platform() == "Kalshi"


class TestCommissionRateValidation:
    """Test commission rate validation and error handling"""
    
    def setup_method(self):
        """Set up CommissionManager for each test"""
        self.manager = CommissionManager()
        # Store initial state to restore later
        self.initial_rate = self.manager.get_commission_rate()
        self.initial_platform = self.manager.get_current_platform()
    
    def teardown_method(self):
        """Restore initial state after each test"""
        self.manager.set_commission_rate(self.initial_rate, self.initial_platform)
    
    def test_invalid_rate_too_low(self):
        """Test that negative commission rates raise ValueError"""
        with pytest.raises(ValueError, match="Commission rate must be between"):
            self.manager.set_commission_rate(-0.01)
    
    def test_invalid_rate_too_high(self):
        """Test that commission rates above 1.00 raise ValueError"""
        with pytest.raises(ValueError, match="Commission rate must be between"):
            self.manager.set_commission_rate(1.01)
    
    def test_invalid_rate_type_string(self):
        """Test that string commission rates raise TypeError"""
        with pytest.raises(TypeError, match="Commission rate must be a number"):
            self.manager.set_commission_rate("0.05")
    
    def test_invalid_rate_type_none(self):
        """Test that None commission rates raise TypeError"""
        with pytest.raises(TypeError, match="Commission rate must be a number"):
            self.manager.set_commission_rate(None)
    
    def test_invalid_rate_type_list(self):
        """Test that list commission rates raise TypeError"""
        with pytest.raises(TypeError, match="Commission rate must be a number"):
            self.manager.set_commission_rate([0.05])
    
    def test_boundary_values_valid(self):
        """Test that boundary values (0.00 and 1.00) are valid"""
        # Test minimum boundary
        self.manager.set_commission_rate(0.00)
        assert self.manager.get_commission_rate() == 0.00
        
        # Test maximum boundary
        self.manager.set_commission_rate(1.00)
        assert self.manager.get_commission_rate() == 1.00


class TestPlatformPresets:
    """Test platform preset functionality"""
    
    def setup_method(self):
        """Set up CommissionManager for each test"""
        self.manager = CommissionManager()
        # Store initial state to restore later
        self.initial_rate = self.manager.get_commission_rate()
        self.initial_platform = self.manager.get_current_platform()
    
    def teardown_method(self):
        """Restore initial state after each test"""
        self.manager.set_commission_rate(self.initial_rate, self.initial_platform)
    
    def test_get_platform_presets(self):
        """Test getting platform presets dictionary"""
        presets = self.manager.get_platform_presets()
        
        # Check expected platforms are present
        expected_platforms = ["Robinhood", "Kalshi", "PredictIt", "Polymarket"]
        for platform in expected_platforms:
            assert platform in presets
        
        # Check specific rates
        assert presets["Robinhood"] == 0.02
        assert presets["Kalshi"] == 0.00
        assert presets["PredictIt"] == 0.10
        assert presets["Polymarket"] == 0.00
        
        # Check that Custom is not included (it's None)
        assert "Custom" not in presets
    
    def test_platform_presets_immutable(self):
        """Test that returned presets dictionary cannot modify internal state"""
        presets = self.manager.get_platform_presets()
        presets["Robinhood"] = 999.99  # Try to modify
        
        # Original should be unchanged
        fresh_presets = self.manager.get_platform_presets()
        assert fresh_presets["Robinhood"] == 0.02
    
    def test_set_platform_valid(self):
        """Test setting platform using valid presets"""
        test_platforms = {
            "Robinhood": 0.02,
            "Kalshi": 0.00,
            "PredictIt": 0.10,
            "Polymarket": 0.00
        }
        
        for platform, expected_rate in test_platforms.items():
            self.manager.set_platform(platform)
            assert self.manager.get_commission_rate() == expected_rate
            assert self.manager.get_current_platform() == platform
    
    def test_set_platform_invalid(self):
        """Test setting platform with invalid platform name"""
        with pytest.raises(ValueError, match="Platform 'InvalidPlatform' not found"):
            self.manager.set_platform("InvalidPlatform")
    
    def test_set_platform_custom_rejected(self):
        """Test that setting platform to 'Custom' is rejected"""
        with pytest.raises(ValueError, match="Cannot set platform to 'Custom'"):
            self.manager.set_platform("Custom")
    
    @patch('src.commission_manager.logger')
    def test_set_platform_logging(self, mock_logger):
        """Test that platform changes are logged"""
        old_platform = self.manager.get_current_platform()
        self.manager.set_platform("Kalshi")
        
        mock_logger.info.assert_called()
        log_call = mock_logger.info.call_args[0][0]
        assert "Platform changed" in log_call
        assert old_platform in log_call  # old platform (whatever it was)
        assert "Kalshi" in log_call  # new platform


class TestResetFunctionality:
    """Test reset to default functionality"""
    
    def setup_method(self):
        """Set up CommissionManager for each test"""
        self.manager = CommissionManager()
        # Store initial state to restore later
        self.initial_rate = self.manager.get_commission_rate()
        self.initial_platform = self.manager.get_current_platform()
    
    def teardown_method(self):
        """Restore initial state after each test"""
        self.manager.set_commission_rate(self.initial_rate, self.initial_platform)
    
    def test_reset_to_default(self):
        """Test resetting to default settings"""
        # Change settings
        self.manager.set_commission_rate(0.10, "TestPlatform")
        assert self.manager.get_commission_rate() == 0.10
        assert self.manager.get_current_platform() == "TestPlatform"
        
        # Reset to default
        self.manager.reset_to_default()
        assert self.manager.get_commission_rate() == 0.02
        assert self.manager.get_current_platform() == "Robinhood"
    
    @patch('src.commission_manager.logger')
    def test_reset_to_default_logging(self, mock_logger):
        """Test that reset operations are logged"""
        # Change settings first
        self.manager.set_commission_rate(0.10, "TestPlatform")
        
        # Reset and check logging
        self.manager.reset_to_default()
        
        mock_logger.info.assert_called()
        log_call = mock_logger.info.call_args[0][0]
        assert "Commission settings reset" in log_call
        assert "TestPlatform" in log_call
        assert "Robinhood" in log_call


class TestCommissionInfo:
    """Test commission information retrieval"""
    
    def setup_method(self):
        """Set up CommissionManager for each test"""
        self.manager = CommissionManager()
        # Store initial state to restore later
        self.initial_rate = self.manager.get_commission_rate()
        self.initial_platform = self.manager.get_current_platform()
    
    def teardown_method(self):
        """Restore initial state after each test"""
        self.manager.set_commission_rate(self.initial_rate, self.initial_platform)
    
    def test_get_commission_info_default(self):
        """Test getting commission info with default settings"""
        info = self.manager.get_commission_info()
        
        assert info["current_platform"] == "Robinhood"
        assert info["current_rate"] == 0.02
        assert "available_platforms" in info
        assert "platform_presets" in info
        
        # Check available platforms includes all expected platforms
        expected_platforms = ["Robinhood", "Kalshi", "PredictIt", "Polymarket", "Custom"]
        for platform in expected_platforms:
            assert platform in info["available_platforms"]
    
    def test_get_commission_info_after_changes(self):
        """Test getting commission info after making changes"""
        self.manager.set_commission_rate(0.05, "TestPlatform")
        info = self.manager.get_commission_info()
        
        assert info["current_platform"] == "TestPlatform"
        assert info["current_rate"] == 0.05


class TestStringRepresentations:
    """Test string representation methods"""
    
    def setup_method(self):
        """Set up CommissionManager for each test"""
        self.manager = CommissionManager()
        # Store initial state to restore later
        self.initial_rate = self.manager.get_commission_rate()
        self.initial_platform = self.manager.get_current_platform()
    
    def teardown_method(self):
        """Restore initial state after each test"""
        self.manager.set_commission_rate(self.initial_rate, self.initial_platform)
    
    def test_str_representation(self):
        """Test __str__ method"""
        # Set known state for testing
        self.manager.set_commission_rate(0.02, "Robinhood")
        
        str_repr = str(self.manager)
        assert "CommissionManager" in str_repr
        assert "Robinhood" in str_repr
        assert "$0.02" in str_repr
    
    def test_repr_representation(self):
        """Test __repr__ method"""
        # Set known state for testing
        self.manager.set_commission_rate(0.02, "Robinhood")
        
        repr_str = repr(self.manager)
        assert "CommissionManager" in repr_str
        assert "platform='Robinhood'" in repr_str
        assert "rate=0.02" in repr_str
    
    def test_str_after_changes(self):
        """Test string representation after making changes"""
        self.manager.set_commission_rate(0.10, "TestPlatform")
        str_repr = str(self.manager)
        assert "TestPlatform" in str_repr
        assert "$0.10" in str_repr


class TestIntegrationWithBettingFramework:
    """Test integration with existing betting framework functions"""
    
    def setup_method(self):
        """Set up CommissionManager for each test"""
        self.manager = CommissionManager()
        # Store initial state to restore later
        self.initial_rate = self.manager.get_commission_rate()
        self.initial_platform = self.manager.get_current_platform()
    
    def teardown_method(self):
        """Restore initial state after each test"""
        self.manager.set_commission_rate(self.initial_rate, self.initial_platform)
    
    def test_integration_calculate_whole_contracts(self):
        """Test integration with calculate_whole_contracts function"""
        from src.betting_framework import calculate_whole_contracts
        from src.commission_manager import commission_manager as global_manager
        
        # Reset global manager to ensure clean state
        global_manager.reset_to_default()
        
        # Test with default commission rate (should use CommissionManager)
        result_default = calculate_whole_contracts(100, 0.45, None)
        expected_price = 0.45 + 0.02  # Default Robinhood rate
        assert abs(result_default['adjusted_price'] - expected_price) < 1e-10
        
        # Change global commission rate and test again
        global_manager.set_commission_rate(0.05)
        result_custom = calculate_whole_contracts(100, 0.45, None)
        expected_price_custom = 0.45 + 0.05
        assert abs(result_custom['adjusted_price'] - expected_price_custom) < 1e-10
        
        # Test that explicit commission rate still overrides
        result_explicit = calculate_whole_contracts(100, 0.45, 0.01)
        expected_price_explicit = 0.45 + 0.01
        assert abs(result_explicit['adjusted_price'] - expected_price_explicit) < 1e-10
        
        # Reset global manager for other tests
        global_manager.reset_to_default()
    
    def test_integration_user_input_betting_framework(self):
        """Test integration with user_input_betting_framework function"""
        from src.betting_framework import user_input_betting_framework
        from src.commission_manager import commission_manager as global_manager
        
        # Reset global manager to ensure clean state
        global_manager.reset_to_default()
        
        # Test with default commission rate
        result_default = user_input_betting_framework(
            weekly_bankroll=1000,
            contract_price=45,  # Will be normalized to 0.45
            model_win_percentage=60,  # 60%
            commission_per_contract=None  # Should use CommissionManager
        )
        
        # Verify commission rate was used in calculation
        assert result_default is not None
        
        # Change commission rate and verify different result
        global_manager.set_commission_rate(0.10)
        result_high_commission = user_input_betting_framework(
            weekly_bankroll=1000,
            contract_price=45,
            model_win_percentage=60,
            commission_per_contract=None
        )
        
        # With higher commission, bet amount should be lower or NO BET
        if result_default['decision'] != 'NO BET' and result_high_commission['decision'] != 'NO BET':
            assert result_high_commission['bet_amount'] <= result_default['bet_amount']
        
        # Reset global manager for other tests
        global_manager.reset_to_default()
    
    def test_global_instance_consistency(self):
        """Test that global commission_manager instance maintains consistency"""
        from src.commission_manager import commission_manager as global_manager
        from src.betting_framework import calculate_whole_contracts
        
        # Change global instance
        global_manager.set_commission_rate(0.08, "TestGlobal")
        
        # Test that betting framework uses the global instance
        result = calculate_whole_contracts(100, 0.45, None)
        expected_price = 0.45 + 0.08
        assert abs(result['adjusted_price'] - expected_price) < 1e-10
        
        # Reset for other tests
        global_manager.reset_to_default()


class TestEdgeCasesAndRobustness:
    """Test edge cases and robustness of CommissionManager"""
    
    def setup_method(self):
        """Set up CommissionManager for each test"""
        self.manager = CommissionManager()
        # Store initial state to restore later
        self.initial_rate = self.manager.get_commission_rate()
        self.initial_platform = self.manager.get_current_platform()
    
    def teardown_method(self):
        """Restore initial state after each test"""
        self.manager.set_commission_rate(self.initial_rate, self.initial_platform)
    
    def test_very_small_commission_rates(self):
        """Test handling of very small commission rates"""
        small_rates = [0.0001, 0.00001, 1e-10]
        
        for rate in small_rates:
            self.manager.set_commission_rate(rate)
            assert self.manager.get_commission_rate() == rate
    
    def test_precision_handling(self):
        """Test precision handling for commission rates"""
        # Test that precision is maintained
        precise_rate = 0.123456789
        self.manager.set_commission_rate(precise_rate)
        assert abs(self.manager.get_commission_rate() - precise_rate) < 1e-10
    
    def test_multiple_rapid_changes(self):
        """Test rapid succession of commission rate changes"""
        rates = [0.01, 0.02, 0.03, 0.04, 0.05]
        
        for rate in rates:
            self.manager.set_commission_rate(rate)
            assert self.manager.get_commission_rate() == rate
    
    def test_platform_name_edge_cases(self):
        """Test edge cases for platform names"""
        edge_case_names = ["", "   ", "Very Long Platform Name With Spaces", "123", "Special!@#$%"]
        
        for name in edge_case_names:
            self.manager.set_commission_rate(0.05, name)
            assert self.manager.get_current_platform() == name
    
    @patch('src.commission_manager.logger')
    def test_logging_disabled_gracefully(self, mock_logger):
        """Test that logging errors don't break functionality"""
        # Make logger.info raise an exception
        mock_logger.info.side_effect = Exception("Logging failed")
        
        # Operations should still work despite logging failures
        self.manager.set_commission_rate(0.05)
        assert self.manager.get_commission_rate() == 0.05
        
        self.manager.set_platform("Kalshi")
        assert self.manager.get_current_platform() == "Kalshi"
        
        self.manager.reset_to_default()
        assert self.manager.get_commission_rate() == 0.02