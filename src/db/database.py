"""Database class with all-in-one features."""

from sqlalchemy.engine.url import URL
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import create_async_engine as _create_async_engine

from src.configuration import conf


def create_async_engine(url: URL | str) -> AsyncEngine:
    """Create async engine with given URL.

    :param url: URL to connect
    :return: AsyncEngine
    """
    return _create_async_engine(url=url, echo=conf.debug, pool_pre_ping=True)
