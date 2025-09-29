"""Commission management system for platform-agnostic betting framework."""

from typing import Dict, Any, Union
import logging
from pathlib import Path

# Set up logging
logger = logging.getLogger(__name__)


class CommissionManager:
    """
    Centralized commission rate management for different trading platforms.
    
    This class provides a unified interface for managing commission rates across
    different trading platforms, with built-in validation and platform presets.
    """
    
    # Platform presets for popular trading platforms
    PLATFORM_PRESETS: Dict[str, Union[float, None]] = {
        "Robinhood": 0.02,      # $0.02 per contract
        "Kalshi": 0.00,         # No commission (built into spread)
        "PredictIt": 0.10,      # 10% of winnings
        "Polymarket": 0.00,     # Gas fees only (variable)
        "Custom": None          # User-defined rate
    }
    
    # Default configuration
    DEFAULT_PLATFORM = "Robinhood"
    DEFAULT_COMMISSION_RATE = 0.02
    
    # Validation constraints
    MIN_COMMISSION_RATE = 0.00
    MAX_COMMISSION_RATE = 1.00
    
    # Class-level shared state for persistence across instances
    _shared_commission_rate: Union[float, None] = None
    _shared_platform: Union[str, None] = None
    
    def __init__(self) -> None:
        """Initialize CommissionManager with saved settings or defaults."""
        # Set up config file path
        self._settings_file = Path("config") / "settings.py"
        
        # Initialize instance attributes
        self._current_commission_rate: Union[float, None] = None
        self._current_platform: Union[str, None] = None
        
        # Use shared state if available, otherwise load from settings
        if CommissionManager._shared_commission_rate is not None:
            self._current_commission_rate = CommissionManager._shared_commission_rate
            self._current_platform = CommissionManager._shared_platform
        else:
            # Load saved settings or use defaults
            self._load_settings()
            # Update shared state
            CommissionManager._shared_commission_rate = self._current_commission_rate
            CommissionManager._shared_platform = self._current_platform
        
        try:
            logger.info(f"CommissionManager initialized with {self._current_platform} "
                       f"platform (${self._current_commission_rate:.2f} per contract)")
        except Exception:
            # Logging failures should not break functionality
            pass
    
    def get_commission_rate(self) -> float:
        """
        Get the current commission rate per contract.
        
        Returns:
            float: Current commission rate per contract in dollars
        """
        return self._current_commission_rate if self._current_commission_rate is not None else self.DEFAULT_COMMISSION_RATE
    
    def set_commission_rate(self, rate: float, platform_name: str = "Custom") -> None:
        """
        Set a custom commission rate.
        
        Args:
            rate: Commission rate per contract in dollars
            platform_name: Name of the platform (defaults to "Custom")
            
        Raises:
            ValueError: If commission rate is outside valid range
            TypeError: If rate is not a number
        """
        self._validate_commission_rate(rate)
        
        old_rate = self._current_commission_rate
        old_platform = self._current_platform
        
        self._current_commission_rate = float(rate)
        self._current_platform = platform_name
        
        # Update shared state for all instances
        CommissionManager._shared_commission_rate = self._current_commission_rate
        CommissionManager._shared_platform = self._current_platform
        
        # Save settings to persist across runs
        self._save_settings()
        
        try:
            logger.info(f"Commission rate updated from ${old_rate:.2f} ({old_platform}) "
                       f"to ${rate:.2f} ({platform_name})")
        except Exception:
            # Logging failures should not break functionality
            pass
    
    def get_platform_presets(self) -> Dict[str, float]:
        """
        Get dictionary of predefined commission rates for popular platforms.
        
        Returns:
            Dict[str, float]: Platform names mapped to commission rates
        """
        # Return a copy to prevent external modification
        return {k: v for k, v in self.PLATFORM_PRESETS.items() if v is not None}
    
    def set_platform(self, platform_name: str) -> None:
        """
        Set commission rate using a platform preset.
        
        Args:
            platform_name: Name of the platform from available presets
            
        Raises:
            ValueError: If platform is not in presets or is "Custom"
        """
        if platform_name not in self.PLATFORM_PRESETS:
            available_platforms = list(self.PLATFORM_PRESETS.keys())
            raise ValueError(f"Platform '{platform_name}' not found. "
                           f"Available platforms: {available_platforms}")
        
        if platform_name == "Custom":
            raise ValueError("Cannot set platform to 'Custom'. Use set_commission_rate() instead.")
        
        preset_rate = self.PLATFORM_PRESETS[platform_name]
        old_rate = self._current_commission_rate
        old_platform = self._current_platform
        
        self._current_commission_rate = preset_rate
        self._current_platform = platform_name
        
        # Update shared state for all instances
        CommissionManager._shared_commission_rate = self._current_commission_rate
        CommissionManager._shared_platform = self._current_platform
        
        # Save settings to persist across runs
        self._save_settings()
        
        try:
            logger.info(f"Platform changed from {old_platform} (${old_rate:.2f}) "
                       f"to {platform_name} (${preset_rate:.2f})")
        except Exception:
            # Logging failures should not break functionality
            pass
    
    def get_current_platform(self) -> str:
        """
        Get the name of the currently selected platform.
        
        Returns:
            str: Current platform name
        """
        return self._current_platform or self.DEFAULT_PLATFORM
    
    def reset_to_default(self) -> None:
        """Reset commission rate to default Robinhood settings."""
        old_rate = self._current_commission_rate
        old_platform = self._current_platform
        
        self._current_commission_rate = self.DEFAULT_COMMISSION_RATE
        self._current_platform = self.DEFAULT_PLATFORM
        
        # Update shared state for all instances
        CommissionManager._shared_commission_rate = self._current_commission_rate
        CommissionManager._shared_platform = self._current_platform
        
        # Save settings to persist across runs
        self._save_settings()
        
        try:
            logger.info(f"Commission settings reset from {old_platform} (${old_rate:.2f}) "
                       f"to default {self.DEFAULT_PLATFORM} (${self.DEFAULT_COMMISSION_RATE:.2f})")
        except Exception:
            # Logging failures should not break functionality
            pass
    
    def _clear_config_file(self) -> None:
        """Reset settings.py to default values (for testing purposes)."""
        try:
            if self._settings_file.exists():
                # Read current settings.py content
                with open(self._settings_file, 'r') as f:
                    content = f.read()
                
                # Reset to default values
                import re
                
                # Reset CURRENT_COMMISSION_RATE to None
                rate_pattern = r'(CURRENT_COMMISSION_RATE\s*=\s*)([0-9.]+|None)'
                content = re.sub(rate_pattern, r'\g<1>None', content)
                
                # Reset CURRENT_PLATFORM to default
                platform_pattern = r'(CURRENT_PLATFORM\s*=\s*["\'])([^"\']+)(["\'])'
                content = re.sub(platform_pattern, f'\\g<1>{self.DEFAULT_PLATFORM}\\g<3>', content)
                
                # Write back to file
                with open(self._settings_file, 'w') as f:
                    f.write(content)
        except Exception:
            pass
    
    @classmethod
    def _clear_shared_state(cls) -> None:
        """Clear shared state (for testing purposes)."""
        cls._shared_commission_rate = None
        cls._shared_platform = None
    
    def _validate_commission_rate(self, rate: Any) -> None:
        """
        Validate commission rate input.
        
        Args:
            rate: Commission rate to validate
            
        Raises:
            TypeError: If rate is not a number
            ValueError: If rate is outside valid range
        """
        # Type validation
        if not isinstance(rate, (int, float)):
            raise TypeError(f"Commission rate must be a number, got {type(rate).__name__}")
        
        # Range validation
        if rate < self.MIN_COMMISSION_RATE or rate > self.MAX_COMMISSION_RATE:
            raise ValueError(f"Commission rate must be between ${self.MIN_COMMISSION_RATE:.2f} "
                           f"and ${self.MAX_COMMISSION_RATE:.2f}, got ${rate:.2f}")
    
    def get_commission_info(self) -> Dict[str, Any]:
        """
        Get comprehensive information about current commission settings.
        
        Returns:
            Dict containing current platform, rate, and available presets
        """
        return {
            "current_platform": self._current_platform,
            "current_rate": self._current_commission_rate,
            "available_platforms": list(self.PLATFORM_PRESETS.keys()),
            "platform_presets": self.get_platform_presets()
        }
    
    def __str__(self) -> str:
        """String representation of current commission settings."""
        return f"CommissionManager({self._current_platform}: ${self._current_commission_rate:.2f})"
    
    def __repr__(self) -> str:
        """Detailed string representation for debugging."""
        return (f"CommissionManager(platform='{self._current_platform}', "
                f"rate={self._current_commission_rate})")
    
    def _load_settings(self) -> None:
        """Load commission settings from settings.py file or use defaults."""
        try:
            if self._settings_file.exists():
                # Read the current settings.py file
                with open(self._settings_file, 'r') as f:
                    content = f.read()
                
                # Extract current values using regex
                import re
                
                # Look for CURRENT_COMMISSION_RATE = value
                rate_match = re.search(r'CURRENT_COMMISSION_RATE\s*=\s*([0-9.]+|None)', content)
                platform_match = re.search(r'CURRENT_PLATFORM\s*=\s*["\']([^"\']+)["\']', content)
                
                if rate_match and platform_match:
                    rate_str = rate_match.group(1)
                    platform = platform_match.group(1)
                    
                    if rate_str == "None":
                        # Use defaults when None
                        self._current_commission_rate = self.DEFAULT_COMMISSION_RATE
                        self._current_platform = self.DEFAULT_PLATFORM
                    else:
                        rate = float(rate_str)
                        
                        # Validate settings
                        try:
                            self._validate_commission_rate(rate)
                            self._current_commission_rate = rate
                            self._current_platform = platform
                        except (ValueError, TypeError):
                            # Invalid rate, use defaults
                            self._current_commission_rate = self.DEFAULT_COMMISSION_RATE
                            self._current_platform = self.DEFAULT_PLATFORM
                else:
                    # Couldn't parse, use defaults
                    self._current_commission_rate = self.DEFAULT_COMMISSION_RATE
                    self._current_platform = self.DEFAULT_PLATFORM
                    
                try:
                    logger.info(f"Loaded commission settings: {self._current_platform} (${self._current_commission_rate:.2f})")
                except Exception:
                    pass
            else:
                # No settings file, use defaults
                self._current_commission_rate = self.DEFAULT_COMMISSION_RATE
                self._current_platform = self.DEFAULT_PLATFORM
                
        except (FileNotFoundError, PermissionError) as e:
            # Settings file inaccessible, use defaults
            self._current_commission_rate = self.DEFAULT_COMMISSION_RATE
            self._current_platform = self.DEFAULT_PLATFORM
            try:
                logger.warning(f"Could not load commission settings: {e}. Using defaults.")
            except Exception:
                pass
    
    def _save_settings(self) -> None:
        """Save current commission settings to settings.py file."""
        try:
            if not self._settings_file.exists():
                # Settings file doesn't exist, can't save
                try:
                    logger.warning("Settings file not found, cannot save commission settings")
                except Exception:
                    pass
                return
            
            # Read current settings.py content
            with open(self._settings_file, 'r') as f:
                content = f.read()
            
            # Update the CURRENT_COMMISSION_RATE and CURRENT_PLATFORM lines
            import re
            
            # Replace CURRENT_COMMISSION_RATE line
            rate_pattern = r'CURRENT_COMMISSION_RATE\s*=\s*([0-9.]+|None)(\s*#.*)?'
            if self._current_commission_rate is not None:
                new_rate_line = f'CURRENT_COMMISSION_RATE = {self._current_commission_rate}  # Will be set by CommissionManager'
            else:
                new_rate_line = f'CURRENT_COMMISSION_RATE = None  # Will be set by CommissionManager'
            content = re.sub(rate_pattern, new_rate_line, content)
            
            # Replace CURRENT_PLATFORM line
            platform_pattern = r'CURRENT_PLATFORM\s*=\s*["\'][^"\']*["\'](\s*#.*)?'
            new_platform_line = f'CURRENT_PLATFORM = "{self._current_platform}"  # Current platform name'
            content = re.sub(platform_pattern, new_platform_line, content)
            
            # Write back to file
            with open(self._settings_file, 'w') as f:
                f.write(content)
                
            try:
                logger.info(f"Saved commission settings: {self._current_platform} (${self._current_commission_rate:.2f})")
            except Exception:
                pass
                
        except (PermissionError, OSError) as e:
            # Could not save settings, but don't break functionality
            try:
                logger.warning(f"Could not save commission settings: {e}")
            except Exception:
                pass


# Global instance for application-wide use
commission_manager = CommissionManager()