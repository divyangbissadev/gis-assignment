"""
Configuration management for the ArcGIS client application.

This module provides centralized configuration handling with environment variable
support, validation, and sensible defaults for production deployments.
"""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class NetworkConfig:
    """Network and HTTP client configuration."""

    connect_timeout: int = field(default=10)
    read_timeout: int = field(default=30)
    max_retries: int = field(default=3)
    retry_backoff_factor: float = field(default=0.5)
    max_connections: int = field(default=10)
    max_keepalive_connections: int = field(default=5)
    keepalive_expiry: int = field(default=30)
    rate_limit_calls: int = field(default=100)
    rate_limit_period: int = field(default=60)

    @classmethod
    def from_env(cls) -> "NetworkConfig":
        """Load network configuration from environment variables."""
        return cls(
            connect_timeout=int(os.getenv("ARCGIS_CONNECT_TIMEOUT", "10")),
            read_timeout=int(os.getenv("ARCGIS_READ_TIMEOUT", "30")),
            max_retries=int(os.getenv("ARCGIS_MAX_RETRIES", "3")),
            retry_backoff_factor=float(os.getenv("ARCGIS_RETRY_BACKOFF", "0.5")),
            max_connections=int(os.getenv("ARCGIS_MAX_CONNECTIONS", "10")),
            max_keepalive_connections=int(os.getenv("ARCGIS_MAX_KEEPALIVE", "5")),
            keepalive_expiry=int(os.getenv("ARCGIS_KEEPALIVE_EXPIRY", "30")),
            rate_limit_calls=int(os.getenv("ARCGIS_RATE_LIMIT_CALLS", "100")),
            rate_limit_period=int(os.getenv("ARCGIS_RATE_LIMIT_PERIOD", "60")),
        )


@dataclass
class CacheConfig:
    """Caching configuration."""

    enabled: bool = field(default=True)
    ttl_seconds: int = field(default=300)
    max_size: int = field(default=1000)
    cache_dir: Optional[str] = field(default=None)

    @classmethod
    def from_env(cls) -> "CacheConfig":
        """Load cache configuration from environment variables."""
        return cls(
            enabled=os.getenv("ARCGIS_CACHE_ENABLED", "true").lower() == "true",
            ttl_seconds=int(os.getenv("ARCGIS_CACHE_TTL", "300")),
            max_size=int(os.getenv("ARCGIS_CACHE_MAX_SIZE", "1000")),
            cache_dir=os.getenv("ARCGIS_CACHE_DIR"),
        )


@dataclass
class LoggingConfig:
    """Logging configuration."""

    level: str = field(default="INFO")
    format: str = field(default="json")
    file_path: Optional[str] = field(default=None)
    max_bytes: int = field(default=10485760)  # 10MB
    backup_count: int = field(default=5)

    @classmethod
    def from_env(cls) -> "LoggingConfig":
        """Load logging configuration from environment variables."""
        return cls(
            level=os.getenv("LOG_LEVEL", "INFO").upper(),
            format=os.getenv("LOG_FORMAT", "json"),
            file_path=os.getenv("LOG_FILE_PATH"),
            max_bytes=int(os.getenv("LOG_MAX_BYTES", "10485760")),
            backup_count=int(os.getenv("LOG_BACKUP_COUNT", "5")),
        )


@dataclass
class QueryConfig:
    """Default query configuration."""

    default_page_size: int = field(default=1000)
    max_page_size: int = field(default=2000)
    default_out_fields: str = field(default="*")
    enable_pagination: bool = field(default=True)
    spatial_reference_wkid: int = field(default=4326)

    @classmethod
    def from_env(cls) -> "QueryConfig":
        """Load query configuration from environment variables."""
        return cls(
            default_page_size=int(os.getenv("ARCGIS_DEFAULT_PAGE_SIZE", "1000")),
            max_page_size=int(os.getenv("ARCGIS_MAX_PAGE_SIZE", "2000")),
            default_out_fields=os.getenv("ARCGIS_DEFAULT_OUT_FIELDS", "*"),
            enable_pagination=os.getenv("ARCGIS_ENABLE_PAGINATION", "true").lower() == "true",
            spatial_reference_wkid=int(os.getenv("ARCGIS_SPATIAL_REF_WKID", "4326")),
        )


@dataclass
class ComplianceConfig:
    """Compliance checking configuration."""

    default_min_area_sq_miles: float = field(default=1000.0)
    strict_validation: bool = field(default=True)

    @classmethod
    def from_env(cls) -> "ComplianceConfig":
        """Load compliance configuration from environment variables."""
        return cls(
            default_min_area_sq_miles=float(os.getenv("COMPLIANCE_MIN_AREA", "1000.0")),
            strict_validation=os.getenv("COMPLIANCE_STRICT", "true").lower() == "true",
        )


@dataclass
class SessionConfig:
    """Session management configuration."""

    default_session_dir: str = field(default="sessions")
    auto_backup: bool = field(default=True)
    backup_count: int = field(default=3)
    compress_backup: bool = field(default=True)

    @classmethod
    def from_env(cls) -> "SessionConfig":
        """Load session configuration from environment variables."""
        return cls(
            default_session_dir=os.getenv("SESSION_DIR", "sessions"),
            auto_backup=os.getenv("SESSION_AUTO_BACKUP", "true").lower() == "true",
            backup_count=int(os.getenv("SESSION_BACKUP_COUNT", "3")),
            compress_backup=os.getenv("SESSION_COMPRESS", "true").lower() == "true",
        )


@dataclass
class ApplicationConfig:
    """Main application configuration container."""

    network: NetworkConfig = field(default_factory=NetworkConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    query: QueryConfig = field(default_factory=QueryConfig)
    compliance: ComplianceConfig = field(default_factory=ComplianceConfig)
    session: SessionConfig = field(default_factory=SessionConfig)

    environment: str = field(default="production")
    debug: bool = field(default=False)

    @classmethod
    def from_env(cls) -> "ApplicationConfig":
        """
        Load complete application configuration from environment variables.

        Returns:
            ApplicationConfig: Fully configured application settings.
        """
        env = os.getenv("ENVIRONMENT", "production")
        debug = os.getenv("DEBUG", "false").lower() == "true"

        return cls(
            network=NetworkConfig.from_env(),
            cache=CacheConfig.from_env(),
            logging=LoggingConfig.from_env(),
            query=QueryConfig.from_env(),
            compliance=ComplianceConfig.from_env(),
            session=SessionConfig.from_env(),
            environment=env,
            debug=debug,
        )

    def validate(self) -> None:
        """
        Validate configuration values.

        Raises:
            ValueError: If any configuration value is invalid.
        """
        if self.network.connect_timeout <= 0:
            raise ValueError("connect_timeout must be positive")

        if self.network.read_timeout <= 0:
            raise ValueError("read_timeout must be positive")

        if self.network.max_retries < 0:
            raise ValueError("max_retries cannot be negative")

        if self.query.default_page_size <= 0:
            raise ValueError("default_page_size must be positive")

        if self.query.max_page_size < self.query.default_page_size:
            raise ValueError("max_page_size must be >= default_page_size")

        if self.compliance.default_min_area_sq_miles <= 0:
            raise ValueError("default_min_area_sq_miles must be positive")

        if self.logging.level not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
            raise ValueError(f"Invalid log level: {self.logging.level}")


# Global configuration instance
_config: Optional[ApplicationConfig] = None


def get_config() -> ApplicationConfig:
    """
    Get the global application configuration instance.

    The configuration is loaded once and cached. Call reload_config() to reload.

    Returns:
        ApplicationConfig: The global configuration instance.
    """
    global _config
    if _config is None:
        _config = ApplicationConfig.from_env()
        _config.validate()
    return _config


def reload_config() -> ApplicationConfig:
    """
    Reload configuration from environment variables.

    Returns:
        ApplicationConfig: The newly loaded configuration instance.
    """
    global _config
    _config = ApplicationConfig.from_env()
    _config.validate()
    return _config


def set_config(config: ApplicationConfig) -> None:
    """
    Set a custom configuration instance (useful for testing).

    Args:
        config: The configuration instance to use.
    """
    global _config
    config.validate()
    _config = config
