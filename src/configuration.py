"""This file represents configurations from files and environment."""

import logging
from dataclasses import dataclass
from os import getenv
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import URL

from src.language.enums import LocaleIdentificationMode, Locales

load_dotenv(override=True)


@dataclass
class DatabaseConfig:
    """Database connection variables."""

    name: str | None = getenv("POSTGRES_DB")
    user: str | None = getenv("POSTGRES_USER")
    passwd: str | None = getenv("POSTGRES_PASSWORD", None)
    port: int = int(getenv("POSTGRES_PORT", 5432))
    host: str = getenv("POSTGRES_HOST", "db")

    driver: str = "asyncpg"
    database_system: str = "postgresql"

    def build_connection_str(self) -> str:
        """This function build a connection string."""
        return URL.create(
            drivername=f"{self.database_system}+{self.driver}",
            username=self.user,
            database=self.name,
            password=self.passwd,
            port=self.port,
            host=self.host,
        ).render_as_string(hide_password=False)


@dataclass
class RedisConfig:
    """Redis connection variables."""

    db: int = int(getenv("REDIS_DATABASE")) if getenv("REDIS_DATABASE") else None
    """ Redis Database ID """
    host: str = getenv("REDIS_HOST", None)
    port: int = int(getenv("REDIS_PORT", 6379))
    passwd: str | None = getenv("REDIS_PASSWORD", None)
    username: str | None = getenv("REDIS_USERNAME", None)
    state_ttl: int | None = getenv("REDIS_TTL_STATE", None)
    data_ttl: int | None = getenv("REDIS_TTL_DATA", None)


@dataclass
class BotConfig:
    """Bot configuration."""

    token: str = getenv("BOT_TOKEN")


@dataclass
class TranslationsConfig:
    """Translations configuration."""

    locale_identify_mode = LocaleIdentificationMode.BY_DATABASE
    default_locale = "uz"


@dataclass
class Configuration:
    """All in one configuration's class."""

    debug = bool(getenv("DEBUG"))
    logging_level = int(getenv("LOGGING_LEVEL", logging.INFO))
    default_locale = Locales.UZ

    db = DatabaseConfig()
    redis = RedisConfig()
    bot = BotConfig()
    translate = TranslationsConfig()

    MEDIA_URL = Path(__file__).parent / "media"
    IMAGE_DIR = Path(__file__).parent / "media" / "images"
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    ADMINS = list(map(int, getenv("ADMINS").split(",")))
    SECRET_KEY: str = getenv("SECRET_KEY")
    ADMIN_LOGIN = getenv("ADMIN_LOGIN")
    ADMIN_PASSWORD = getenv("ADMIN_PASSWORD")


conf = Configuration()
