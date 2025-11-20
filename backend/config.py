"""
CRYPTO VIZ - Backend Configuration
Centralized configuration with environment variables and CORS settings
"""

import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings from environment variables"""

    # Application
    app_name: str = Field(default="CRYPTO VIZ API", description="Application name")
    app_version: str = Field(default="2.0.0", description="Application version")
    app_description: str = Field(
        default="Backend API pour la plateforme d'analyse crypto en temps réel avec PostgreSQL",
        description="Application description"
    )

    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    log_level: str = Field(default="INFO", description="Logging level")
    debug: bool = Field(default=False, description="Debug mode")

    # CORS
    cors_origins: str = Field(
        default="http://localhost:3000,http://frontend:3000",
        description="Comma-separated list of allowed origins"
    )
    cors_credentials: bool = Field(default=True, description="Allow credentials")
    cors_methods: List[str] = Field(default=["*"], description="Allowed HTTP methods")
    cors_headers: List[str] = Field(default=["*"], description="Allowed HTTP headers")

    # PostgreSQL Database
    postgres_host: str = Field(default="postgres", description="PostgreSQL host")
    postgres_port: int = Field(default=5432, description="PostgreSQL port")
    postgres_db: str = Field(default="crypto_viz", description="PostgreSQL database name")
    postgres_user: str = Field(default="crypto_user", description="PostgreSQL user")
    postgres_password: str = Field(default="crypto_password", description="PostgreSQL password")
    postgres_min_conn: int = Field(default=2, description="Minimum database connections")
    postgres_max_conn: int = Field(default=10, description="Maximum database connections")

    # Kafka (for future WebSocket integration)
    kafka_bootstrap_servers: str = Field(default="kafka:29092", description="Kafka bootstrap servers")
    kafka_consumer_group: str = Field(default="backend-api", description="Kafka consumer group")

    # DuckDB (for analytics queries)
    duckdb_path: str = Field(default="/app/data/crypto_analytics.db", description="DuckDB database path")
    duckdb_readonly: bool = Field(default=True, description="DuckDB read-only mode")

    # API Rate Limiting
    rate_limit_enabled: bool = Field(default=False, description="Enable rate limiting")
    rate_limit_per_minute: int = Field(default=60, description="Requests per minute")

    # Security
    secret_key: str = Field(default="your-secret-key-change-in-production", description="Secret key for JWT")
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(default=30, description="Access token expiration")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def postgres_dsn(self) -> str:
        """Build PostgreSQL DSN"""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def database_url(self) -> str:
        """Alias for postgres_dsn"""
        return self.postgres_dsn


# Global settings instance
settings = Settings()


# Logging configuration
def get_logging_config():
    """Get logging configuration dictionary"""
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.log_level,
                "formatter": "default",
                "stream": "ext://sys.stdout"
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": settings.log_level,
                "formatter": "detailed",
                "filename": "/app/logs/backend.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5
            }
        },
        "loggers": {
            "": {  # Root logger
                "level": settings.log_level,
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn": {
                "level": settings.log_level,
                "handlers": ["console"],
                "propagate": False
            },
            "fastapi": {
                "level": settings.log_level,
                "handlers": ["console"],
                "propagate": False
            }
        }
    }
