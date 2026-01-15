"""Configuration management for LN-NFC application."""

import os
import logging
from typing import Literal, Optional
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Config(BaseSettings):
    """
    Application configuration loaded from environment variables.
    
    Uses pydantic-settings for validation and .env file support.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # LNbits Configuration
    lnbits_url: str = Field(
        ...,
        description="LNbits instance URL",
    )
    lnbits_api_key: str = Field(
        ...,
        description="LNbits API key (admin or invoice key)",
    )
    lnbits_wallet_id: Optional[str] = Field(
        None,
        description="LNbits wallet ID (optional)",
    )
    
    # NFC Configuration
    nfc_interface: Literal["i2c", "spi"] = Field(
        default="i2c",
        description="NFC interface type",
    )
    nfc_i2c_bus: int = Field(
        default=1,
        description="I2C bus number",
    )
    nfc_spi_bus: int = Field(
        default=0,
        description="SPI bus number",
    )
    nfc_spi_device: int = Field(
        default=0,
        description="SPI device number",
    )
    
    # Application Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level",
    )
    log_file: Optional[str] = Field(
        default="/app/logs/ln-nfc.log",
        description="Log file path",
    )
    
    # Security
    admin_pin: Optional[str] = Field(
        None,
        description="Optional PIN for admin operations",
    )
    
    # Tag Configuration
    default_tag_uses: int = Field(
        default=1,
        description="Default number of uses for withdraw links",
    )
    default_tag_title: str = Field(
        default="Lightning Gift Card",
        description="Default title for withdraw links",
    )
    lnurl_use_bech32: bool = Field(
        default=True,
        description="Use bech32 encoding for LNURL",
    )
    
    # Payment Processor
    rate_limit_seconds: float = Field(
        default=2.0,
        description="Minimum seconds between processing same tag",
    )
    poll_interval: float = Field(
        default=0.5,
        description="Polling interval for daemon mode",
    )
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v_upper
    
    @field_validator("lnbits_url")
    @classmethod
    def validate_lnbits_url(cls, v: str) -> str:
        """Validate and normalize LNbits URL."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("LNbits URL must start with http:// or https://")
        return v.rstrip("/")
    
    @field_validator("default_tag_uses")
    @classmethod
    def validate_tag_uses(cls, v: int) -> int:
        """Validate tag uses."""
        if v < 1:
            raise ValueError("Tag uses must be at least 1")
        return v
    
    def setup_logging(self) -> None:
        """Configure logging based on settings."""
        # Create logs directory if needed
        if self.log_file:
            log_path = Path(self.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Configure root logger
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        handlers = []
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(log_format))
        handlers.append(console_handler)
        
        # File handler
        if self.log_file:
            try:
                file_handler = logging.FileHandler(self.log_file)
                file_handler.setFormatter(logging.Formatter(log_format))
                handlers.append(file_handler)
            except Exception as e:
                print(f"Warning: Could not create log file: {e}")
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, self.log_level),
            format=log_format,
            handlers=handlers,
        )
        
        logger.info(f"Logging configured: level={self.log_level}")
        if self.log_file:
            logger.info(f"Log file: {self.log_file}")
    
    def validate_admin_pin(self, pin: str) -> bool:
        """
        Validate admin PIN.
        
        Args:
            pin: PIN to validate
        
        Returns:
            True if PIN is correct or no PIN is set
        """
        if self.admin_pin is None:
            return True
        
        return pin == self.admin_pin
    
    def get_nfc_config(self) -> dict:
        """Get NFC configuration as dictionary."""
        return {
            "interface": self.nfc_interface,
            "i2c_bus": self.nfc_i2c_bus,
            "spi_bus": self.nfc_spi_bus,
            "spi_device": self.nfc_spi_device,
        }
    
    def get_lnbits_config(self) -> dict:
        """Get LNbits configuration as dictionary."""
        return {
            "base_url": self.lnbits_url,
            "api_key": self.lnbits_api_key,
            "wallet_id": self.lnbits_wallet_id,
        }
    
    def __repr__(self) -> str:
        """String representation (hides sensitive data)."""
        return (
            f"Config(lnbits_url={self.lnbits_url}, "
            f"nfc_interface={self.nfc_interface}, "
            f"log_level={self.log_level})"
        )


def load_config(env_file: Optional[str] = None) -> Config:
    """
    Load configuration from environment variables and .env file.
    
    Args:
        env_file: Optional path to .env file (default: .env)
    
    Returns:
        Config instance
    
    Raises:
        ValueError: If configuration is invalid
    """
    if env_file:
        os.environ["ENV_FILE"] = env_file
    
    try:
        config = Config()
        logger.debug("Configuration loaded successfully")
        return config
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        raise


def get_config() -> Config:
    """
    Get or create global configuration instance.
    
    Returns:
        Config instance
    """
    return load_config()
