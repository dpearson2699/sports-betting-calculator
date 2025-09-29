"""
Unit tests for commission_manager.py

Tests commission calculation, different commission structures, validation,
and edge case handling with clear arrange-act-assert structure.
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

from src.commission_manager import CommissionManager, commission_manager


class TestCommissionManagerInitialization:
    """Test CommissionManager initialization and default settings."""
    
    def setup_method(self):
        """Clear shared state before each test."""
        CommissionManager._clear_shared_state()
    
    def test_initialization_with_defaults(self):
        """Test initialization with default settings when no saved settings exist."""
        # Arrange & Act
        with patch.object(Path, 'exists', return_value=False):
            manager = CommissionManager()
        
        # Assert
        assert manager.get_commission_rate() == CommissionManager.DEFAULT_COMMISSION_RATE
        assert manager.get_current_platform() == CommissionManager.DEFAULT_PLATFORM
        assert manager.get_commission_rate() == 0.02
        assert manager.get_current_platform() == "Robinhood"
    
    def test_initialization_with_shared_state(self):
        """Test initialization using existing shared state."""
        # Arrange
        CommissionManager._shared_commission_rate = 0.05
        CommissionManager._shared_platform = "Kalshi"
        
        # Act
        manager = CommissionManager()
        
        # Assert
        assert manager.get_commission_rate() == 0.05
        assert manager.get_current_platform() == "Kalshi"
    
    @patch('commission_manager.Path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='CURRENT_COMMISSION_RATE = 0.10\nCURRENT_PLATFORM = "PredictIt"')
    def test_initialization_loads_saved_settings(self, mock_file, mock_exists):
        """Test initialization loads settings from config file."""
        # Arrange
        mock_exists.return_value = True
        
        # Act
        manager = CommissionManager()
        
        # Assert
        assert manager.get_commission_rate() == 0.10
        assert manager.get_current_platform() == "PredictIt"
    
    @patch('commission_manager.Path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='CURRENT_COMMISSION_RATE = None\nCURRENT_PLATFORM = "Robinhood"')
    def test_initialization_handles_none_rate(self, mock_file, mock_exists):
        """Test initialization handles None rate in config file."""
        # Arrange
        mock_exists.return_value = True
        
        # Act
        manager = CommissionManager()
        
        # Assert
        assert manager.get_commission_rate() == CommissionManager.DEFAULT_COMMISSION_RATE
        assert manager.get_current_platform() == CommissionManager.DEFAULT_PLATFORM


class TestCommissionRateManagement:
    """Test commission rate getting and setting functionality."""
    
    def setup_method(self):
        """Clear shared state before each test."""
        CommissionManager._clear_shared_state()
    
    def test_get_commission_rate_default(self):
        """Test getting default commission rate."""
        # Arrange & Act
        with patch.object(Path, 'exists', return_value=False):
            manager = CommissionManager()
            rate = manager.get_commission_rate()
        
        # Assert
        assert rate == 0.02
        assert isinstance(rate, float)
    
    def test_set_commission_rate_valid(self):
        """Test setting a valid commission rate."""
        # Arrange
        with patch.object(Path, 'exists', return_value=False):
            manager = CommissionManager()
        
        with patch.object(manager, '_save_settings'):
            # Act
            manager.set_commission_rate(0.05, "Custom Platform")
        
        # Assert
        assert manager.get_commission_rate() == 0.05
        assert manager.get_current_platform() == "Custom Platform"
    
    def test_set_commission_rate_updates_shared_state(self):
        """Test that setting commission rate updates shared state for new instances."""
        # Arrange
        with patch.object(Path, 'exists', return_value=False):
            manager1 = CommissionManager()
        
        with patch.object(manager1, '_save_settings'):
            # Act
            manager1.set_commission_rate(0.08)
            
            # Create new instance after shared state is updated
            manager2 = CommissionManager()
        
        # Assert
        assert manager2.get_commission_rate() == 0.08
        assert CommissionManager._shared_commission_rate == 0.08
    
    def test_set_commission_rate_invalid_type(self):
        """Test setting commission rate with invalid type raises TypeError."""
        # Arrange
        with patch.object(Path, 'exists', return_value=False):
            manager = CommissionManager()
        
        # Act & Assert
        with pytest.raises(TypeError, match="Commission rate must be a number"):
            manager.set_commission_rate("invalid")  # type: ignore[arg-type]
    
    def test_set_commission_rate_negative_value(self):
        """Test setting negative commission rate raises ValueError."""
        # Arrange
        with patch.object(Path, 'exists', return_value=False):
            manager = CommissionManager()
        
        # Act & Assert
        with pytest.raises(ValueError, match="Commission rate must be between"):
            manager.set_commission_rate(-0.01)
    
    def test_set_commission_rate_too_high(self):
        """Test setting commission rate above maximum raises ValueError."""
        # Arrange
        with patch.object(Path, 'exists', return_value=False):
            manager = CommissionManager()
        
        # Act & Assert
        with pytest.raises(ValueError, match="Commission rate must be between"):
            manager.set_commission_rate(1.01)
    
    def test_set_commission_rate_boundary_values(self):
        """Test setting commission rate at boundary values."""
        # Arrange
        with patch.object(Path, 'exists', return_value=False):
            manager = CommissionManager()
        
        with patch.object(manager, '_save_settings'):
            # Act & Assert - Minimum boundary
            manager.set_commission_rate(0.00)
            assert manager.get_commission_rate() == 0.00
            
            # Act & Assert - Maximum boundary
            manager.set_commission_rate(1.00)
            assert manager.get_commission_rate() == 1.00


class TestPlatformPresets:
    """Test platform preset functionality."""
    
    def setup_method(self):
        """Clear shared state before each test."""
        CommissionManager._clear_shared_state()
    
    def test_get_platform_presets(self):
        """Test getting platform presets returns correct structure."""
        # Arrange & Act
        with patch.object(Path, 'exists', return_value=False):
            manager = CommissionManager()
            presets = manager.get_platform_presets()
        
        # Assert
        assert isinstance(presets, dict)
        assert "Robinhood" in presets
        assert "Kalshi" in presets
        assert "PredictIt" in presets
        assert "Polymarket" in presets
        assert "Custom" not in presets  # Should be excluded (value is None)
        assert presets["Robinhood"] == 0.02
        assert presets["Kalshi"] == 0.00
        assert presets["PredictIt"] == 0.10
    
    def test_get_platform_presets_returns_copy(self):
        """Test that platform presets returns a copy to prevent external modification."""
        # Arrange & Act
        with patch.object(Path, 'exists', return_value=False):
            manager = CommissionManager()
            presets1 = manager.get_platform_presets()
            presets2 = manager.get_platform_presets()
        
        # Modify one copy
        presets1["Robinhood"] = 999.99
        
        # Assert
        assert presets2["Robinhood"] == 0.02  # Should be unchanged
        assert presets1 is not presets2  # Should be different objects
    
    def test_set_platform_valid(self):
        """Test setting a valid platform preset."""
        # Arrange
        with patch.object(Path, 'exists', return_value=False):
            manager = CommissionManager()
        
        with patch.object(manager, '_save_settings'):
            # Act
            manager.set_platform("PredictIt")
        
        # Assert
        assert manager.get_commission_rate() == 0.10
        assert manager.get_current_platform() == "PredictIt"
    
    def test_set_platform_kalshi_zero_commission(self):
        """Test setting Kalshi platform with zero commission."""
        # Arrange
        with patch.object(Path, 'exists', return_value=False):
            manager = CommissionManager()
        
        with patch.object(manager, '_save_settings'):
            # Act
            manager.set_platform("Kalshi")
        
        # Assert
        assert manager.get_commission_rate() == 0.00
        assert manager.get_current_platform() == "Kalshi"
    
    def test_set_platform_invalid(self):
        """Test setting invalid platform raises ValueError."""
        # Arrange
        with patch.object(Path, 'exists', return_value=False):
            manager = CommissionManager()
        
        # Act & Assert
        with pytest.raises(ValueError, match="Platform 'InvalidPlatform' not found"):
            manager.set_platform("InvalidPlatform")
    
    def test_set_platform_custom_raises_error(self):
        """Test setting platform to 'Custom' raises ValueError."""
        # Arrange
        with patch.object(Path, 'exists', return_value=False):
            manager = CommissionManager()
        
        # Act & Assert
        with pytest.raises(ValueError, match="Cannot set platform to 'Custom'"):
            manager.set_platform("Custom")
    
    def test_set_platform_updates_shared_state(self):
        """Test that setting platform updates shared state for new instances."""
        # Arrange
        with patch.object(Path, 'exists', return_value=False):
            manager1 = CommissionManager()
        
        with patch.object(manager1, '_save_settings'):
            # Act
            manager1.set_platform("PredictIt")
            
            # Create new instance after shared state is updated
            manager2 = CommissionManager()
        
        # Assert
        assert manager2.get_commission_rate() == 0.10
        assert manager2.get_current_platform() == "PredictIt"


class TestValidation:
    """Test commission rate validation functionality."""
    
    def setup_method(self):
        """Clear shared state before each test."""
        CommissionManager._clear_shared_state()
    
    def test_validate_commission_rate_valid_float(self):
        """Test validation accepts valid float values."""
        # Arrange
        with patch.object(Path, 'exists', return_value=False):
            manager = CommissionManager()
        
        # Act & Assert - Should not raise exception
        manager._validate_commission_rate(0.05)
        manager._validate_commission_rate(0.00)
        manager._validate_commission_rate(1.00)
    
    def test_validate_commission_rate_valid_int(self):
        """Test validation accepts valid integer values."""
        # Arrange
        with patch.object(Path, 'exists', return_value=False):
            manager = CommissionManager()
        
        # Act & Assert - Should not raise exception
        manager._validate_commission_rate(0)
        manager._validate_commission_rate(1)
    
    def test_validate_commission_rate_invalid_string(self):
        """Test validation rejects string values."""
        # Arrange
        with patch.object(Path, 'exists', return_value=False):
            manager = CommissionManager()
        
        # Act & Assert
        with pytest.raises(TypeError, match="Commission rate must be a number, got str"):
            manager._validate_commission_rate("0.05")
    
    def test_validate_commission_rate_invalid_none(self):
        """Test validation rejects None values."""
        # Arrange
        with patch.object(Path, 'exists', return_value=False):
            manager = CommissionManager()
        
        # Act & Assert
        with pytest.raises(TypeError, match="Commission rate must be a number, got NoneType"):
            manager._validate_commission_rate(None)
    
    def test_validate_commission_rate_below_minimum(self):
        """Test validation rejects values below minimum."""
        # Arrange
        with patch.object(Path, 'exists', return_value=False):
            manager = CommissionManager()
        
        # Act & Assert
        with pytest.raises(ValueError, match="Commission rate must be between \\$0.00 and \\$1.00, got \\$-0.01"):
            manager._validate_commission_rate(-0.01)
    
    def test_validate_commission_rate_above_maximum(self):
        """Test validation rejects values above maximum."""
        # Arrange
        with patch.object(Path, 'exists', return_value=False):
            manager = CommissionManager()
        
        # Act & Assert
        with pytest.raises(ValueError, match="Commission rate must be between \\$0.00 and \\$1.00, got \\$1.01"):
            manager._validate_commission_rate(1.01)


class TestResetFunctionality:
    """Test reset to default functionality."""
    
    def setup_method(self):
        """Clear shared state before each test."""
        CommissionManager._clear_shared_state()
    
    def test_reset_to_default(self):
        """Test resetting to default settings."""
        # Arrange
        with patch.object(Path, 'exists', return_value=False):
            manager = CommissionManager()
        
        with patch.object(manager, '_save_settings'):
            # Set custom values first
            manager.set_commission_rate(0.15, "Custom")
            
            # Act
            manager.reset_to_default()
        
        # Assert
        assert manager.get_commission_rate() == CommissionManager.DEFAULT_COMMISSION_RATE
        assert manager.get_current_platform() == CommissionManager.DEFAULT_PLATFORM
        assert manager.get_commission_rate() == 0.02
        assert manager.get_current_platform() == "Robinhood"
    
    def test_reset_to_default_updates_shared_state(self):
        """Test that reset updates shared state for all instances."""
        # Arrange
        with patch.object(Path, 'exists', return_value=False):
            manager1 = CommissionManager()
            manager2 = CommissionManager()
        
        with patch.object(manager1, '_save_settings'):
            # Set custom values first
            manager1.set_commission_rate(0.15, "Custom")
            
            # Act
            manager1.reset_to_default()
        
        # Assert
        assert manager2.get_commission_rate() == 0.02
        assert manager2.get_current_platform() == "Robinhood"


class TestCommissionInfo:
    """Test commission information retrieval."""
    
    def setup_method(self):
        """Clear shared state before each test."""
        CommissionManager._clear_shared_state()
    
    def test_get_commission_info_structure(self):
        """Test commission info returns correct structure."""
        # Arrange & Act
        with patch.object(Path, 'exists', return_value=False):
            manager = CommissionManager()
            info = manager.get_commission_info()
        
        # Assert
        assert isinstance(info, dict)
        assert "current_platform" in info
        assert "current_rate" in info
        assert "available_platforms" in info
        assert "platform_presets" in info
    
    def test_get_commission_info_content(self):
        """Test commission info contains correct content."""
        # Arrange
        with patch.object(Path, 'exists', return_value=False):
            manager = CommissionManager()
        
        with patch.object(manager, '_save_settings'):
            manager.set_platform("PredictIt")
            
            # Act
            info = manager.get_commission_info()
        
        # Assert
        assert info["current_platform"] == "PredictIt"
        assert info["current_rate"] == 0.10
        assert "Robinhood" in info["available_platforms"]
        assert "Custom" in info["available_platforms"]
        assert info["platform_presets"]["Robinhood"] == 0.02
        assert "Custom" not in info["platform_presets"]  # Should be excluded


class TestStringRepresentation:
    """Test string representation methods."""
    
    def setup_method(self):
        """Clear shared state before each test."""
        CommissionManager._clear_shared_state()
    
    def test_str_representation(self):
        """Test __str__ method returns readable format."""
        # Arrange & Act
        with patch.object(Path, 'exists', return_value=False):
            manager = CommissionManager()
            str_repr = str(manager)
        
        # Assert
        assert "CommissionManager" in str_repr
        assert "Robinhood" in str_repr
        assert "$0.02" in str_repr
    
    def test_repr_representation(self):
        """Test __repr__ method returns detailed format."""
        # Arrange & Act
        with patch.object(Path, 'exists', return_value=False):
            manager = CommissionManager()
            repr_str = repr(manager)
        
        # Assert
        assert "CommissionManager" in repr_str
        assert "platform='Robinhood'" in repr_str
        assert "rate=0.02" in repr_str
    
    def test_str_with_custom_settings(self):
        """Test string representation with custom settings."""
        # Arrange
        with patch.object(Path, 'exists', return_value=False):
            manager = CommissionManager()
        
        with patch.object(manager, '_save_settings'):
            manager.set_commission_rate(0.08, "Custom Platform")
            
            # Act
            str_repr = str(manager)
        
        # Assert
        assert "Custom Platform" in str_repr
        assert "$0.08" in str_repr


class TestPersistence:
    """Test settings persistence functionality."""
    
    def setup_method(self):
        """Clear shared state before each test."""
        CommissionManager._clear_shared_state()
    
    @patch('commission_manager.Path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='CURRENT_COMMISSION_RATE = 0.05\nCURRENT_PLATFORM = "Test"')
    def test_load_settings_success(self, mock_file, mock_exists):
        """Test successful loading of settings from file."""
        # Arrange
        mock_exists.return_value = True
        
        # Act
        manager = CommissionManager()
        
        # Assert
        assert manager.get_commission_rate() == 0.05
        assert manager.get_current_platform() == "Test"
    
    @patch('commission_manager.Path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='INVALID_FORMAT')
    def test_load_settings_invalid_format(self, mock_file, mock_exists):
        """Test loading settings with invalid file format falls back to defaults."""
        # Arrange
        mock_exists.return_value = True
        
        # Act
        manager = CommissionManager()
        
        # Assert
        assert manager.get_commission_rate() == CommissionManager.DEFAULT_COMMISSION_RATE
        assert manager.get_current_platform() == CommissionManager.DEFAULT_PLATFORM
    
    @patch('commission_manager.Path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='CURRENT_COMMISSION_RATE = 999.99\nCURRENT_PLATFORM = "Test"')
    def test_load_settings_invalid_rate(self, mock_file, mock_exists):
        """Test loading settings with invalid rate falls back to defaults."""
        # Arrange
        mock_exists.return_value = True
        
        # Act
        manager = CommissionManager()
        
        # Assert
        assert manager.get_commission_rate() == CommissionManager.DEFAULT_COMMISSION_RATE
        assert manager.get_current_platform() == CommissionManager.DEFAULT_PLATFORM
    
    @patch('commission_manager.Path.exists')
    @patch('builtins.open', side_effect=FileNotFoundError())
    def test_load_settings_file_not_found(self, mock_file, mock_exists):
        """Test loading settings when file cannot be read falls back to defaults."""
        # Arrange
        mock_exists.return_value = True
        
        # Act
        manager = CommissionManager()
        
        # Assert
        assert manager.get_commission_rate() == CommissionManager.DEFAULT_COMMISSION_RATE
        assert manager.get_current_platform() == CommissionManager.DEFAULT_PLATFORM
    
    @patch('commission_manager.Path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='CURRENT_COMMISSION_RATE = 0.05\nCURRENT_PLATFORM = "Test"')
    def test_save_settings_success(self, mock_file, mock_exists):
        """Test successful saving of settings to file."""
        # Arrange
        mock_exists.return_value = True
        manager = CommissionManager()
        
        # Act
        manager.set_commission_rate(0.08, "New Platform")
        
        # Assert
        # Verify file was written to
        mock_file.assert_called()
        handle = mock_file()
        handle.write.assert_called()
    
    @patch('commission_manager.Path.exists')
    def test_save_settings_no_file(self, mock_exists):
        """Test saving settings when config file doesn't exist."""
        # Arrange
        mock_exists.return_value = False
        
        with patch.object(Path, 'exists', return_value=False):
            manager = CommissionManager()
        
        # Act - Should not raise exception
        manager.set_commission_rate(0.08)
        
        # Assert - Should complete without error
        assert manager.get_commission_rate() == 0.08
    
    @patch('commission_manager.Path.exists')
    @patch('builtins.open', side_effect=PermissionError())
    def test_save_settings_permission_error(self, mock_file, mock_exists):
        """Test saving settings handles permission errors gracefully."""
        # Arrange
        mock_exists.return_value = True
        
        with patch.object(Path, 'exists', return_value=False):
            manager = CommissionManager()
        
        # Act - Should not raise exception
        manager.set_commission_rate(0.08)
        
        # Assert - Should complete without error
        assert manager.get_commission_rate() == 0.08


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def setup_method(self):
        """Clear shared state before each test."""
        CommissionManager._clear_shared_state()
    
    def test_multiple_instances_share_state(self):
        """Test that new instances use shared state from previous instances."""
        # Arrange & Act
        with patch.object(Path, 'exists', return_value=False):
            manager1 = CommissionManager()
        
        with patch.object(manager1, '_save_settings'):
            manager1.set_commission_rate(0.07, "Shared")
            
            # Create new instances after shared state is updated
            manager2 = CommissionManager()
            manager3 = CommissionManager()
        
        # Assert
        assert manager2.get_commission_rate() == 0.07
        assert manager3.get_commission_rate() == 0.07
        assert manager2.get_current_platform() == "Shared"
        assert manager3.get_current_platform() == "Shared"
    
    def test_commission_rate_precision(self):
        """Test commission rate handles floating point precision correctly."""
        # Arrange
        with patch.object(Path, 'exists', return_value=False):
            manager = CommissionManager()
        
        with patch.object(manager, '_save_settings'):
            # Act
            manager.set_commission_rate(0.123456789)
        
        # Assert
        assert manager.get_commission_rate() == 0.123456789
    
    def test_platform_name_with_special_characters(self):
        """Test platform names with special characters."""
        # Arrange
        with patch.object(Path, 'exists', return_value=False):
            manager = CommissionManager()
        
        with patch.object(manager, '_save_settings'):
            # Act
            manager.set_commission_rate(0.05, "Platform-Name_123 (Test)")
        
        # Assert
        assert manager.get_current_platform() == "Platform-Name_123 (Test)"
    
    def test_clear_shared_state_functionality(self):
        """Test clearing shared state works correctly."""
        # Arrange
        CommissionManager._shared_commission_rate = 0.99
        CommissionManager._shared_platform = "Test"
        
        # Act
        CommissionManager._clear_shared_state()
        
        # Assert
        assert CommissionManager._shared_commission_rate is None
        assert CommissionManager._shared_platform is None
    
    def test_logging_failures_dont_break_functionality(self):
        """Test that logging failures don't break core functionality."""
        # Arrange
        with patch.object(Path, 'exists', return_value=False):
            manager = CommissionManager()
        
        # Mock logger to raise exception
        with patch('commission_manager.logger') as mock_logger:
            mock_logger.info.side_effect = Exception("Logging failed")
            
            with patch.object(manager, '_save_settings'):
                # Act - Should not raise exception despite logging failure
                manager.set_commission_rate(0.06, "Test Platform")
        
        # Assert - Core functionality should still work
        assert manager.get_commission_rate() == 0.06
        assert manager.get_current_platform() == "Test Platform"


class TestGlobalInstance:
    """Test the global commission_manager instance."""
    
    def test_global_instance_exists(self):
        """Test that global commission_manager instance exists and is functional."""
        # Act & Assert
        assert commission_manager is not None
        assert isinstance(commission_manager, CommissionManager)
        assert hasattr(commission_manager, 'get_commission_rate')
        assert hasattr(commission_manager, 'set_commission_rate')
        assert hasattr(commission_manager, 'get_current_platform')
    
    def test_global_instance_functionality(self):
        """Test that global instance has working functionality."""
        # Act
        rate = commission_manager.get_commission_rate()
        platform = commission_manager.get_current_platform()
        presets = commission_manager.get_platform_presets()
        
        # Assert
        assert isinstance(rate, (int, float))
        assert isinstance(platform, str)
        assert isinstance(presets, dict)
        assert rate >= 0.0
        assert len(platform) > 0
        assert len(presets) > 0


class TestCommissionStructures:
    """Test different commission structure scenarios."""
    
    def setup_method(self):
        """Clear shared state before each test."""
        CommissionManager._clear_shared_state()
    
    def test_zero_commission_structure(self):
        """Test zero commission structure (like Kalshi)."""
        # Arrange
        with patch.object(Path, 'exists', return_value=False):
            manager = CommissionManager()
        
        with patch.object(manager, '_save_settings'):
            # Act
            manager.set_platform("Kalshi")
        
        # Assert
        assert manager.get_commission_rate() == 0.00
        assert manager.get_current_platform() == "Kalshi"
    
    def test_percentage_based_commission_structure(self):
        """Test percentage-based commission structure (like PredictIt)."""
        # Arrange
        with patch.object(Path, 'exists', return_value=False):
            manager = CommissionManager()
        
        with patch.object(manager, '_save_settings'):
            # Act
            manager.set_platform("PredictIt")
        
        # Assert
        assert manager.get_commission_rate() == 0.10  # 10% represented as 0.10
        assert manager.get_current_platform() == "PredictIt"
    
    def test_fixed_per_contract_commission_structure(self):
        """Test fixed per-contract commission structure (like Robinhood)."""
        # Arrange
        with patch.object(Path, 'exists', return_value=False):
            manager = CommissionManager()
        
        with patch.object(manager, '_save_settings'):
            # Act
            manager.set_platform("Robinhood")
        
        # Assert
        assert manager.get_commission_rate() == 0.02  # $0.02 per contract
        assert manager.get_current_platform() == "Robinhood"
    
    def test_custom_commission_structure(self):
        """Test custom commission structure for unlisted platforms."""
        # Arrange
        with patch.object(Path, 'exists', return_value=False):
            manager = CommissionManager()
        
        with patch.object(manager, '_save_settings'):
            # Act
            manager.set_commission_rate(0.075, "Custom Broker")
        
        # Assert
        assert manager.get_commission_rate() == 0.075
        assert manager.get_current_platform() == "Custom Broker"
    
    def test_high_commission_structure(self):
        """Test high commission structure at upper boundary."""
        # Arrange
        with patch.object(Path, 'exists', return_value=False):
            manager = CommissionManager()
        
        with patch.object(manager, '_save_settings'):
            # Act
            manager.set_commission_rate(0.50, "High Commission Platform")
        
        # Assert
        assert manager.get_commission_rate() == 0.50
        assert manager.get_current_platform() == "High Commission Platform"
    
    def test_commission_structure_switching(self):
        """Test switching between different commission structures."""
        # Arrange
        with patch.object(Path, 'exists', return_value=False):
            manager = CommissionManager()
        
        with patch.object(manager, '_save_settings'):
            # Act - Switch through different structures
            manager.set_platform("Robinhood")  # Fixed per contract
            robinhood_rate = manager.get_commission_rate()
            
            manager.set_platform("PredictIt")  # Percentage based
            predictit_rate = manager.get_commission_rate()
            
            manager.set_platform("Kalshi")  # Zero commission
            kalshi_rate = manager.get_commission_rate()
            
            manager.set_commission_rate(0.15, "Custom")  # Custom rate
            custom_rate = manager.get_commission_rate()
        
        # Assert
        assert robinhood_rate == 0.02
        assert predictit_rate == 0.10
        assert kalshi_rate == 0.00
        assert custom_rate == 0.15
        assert manager.get_current_platform() == "Custom"