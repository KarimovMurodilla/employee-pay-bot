from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from ..configuration import conf
from ..db.database import create_async_engine

engine = create_async_engine(conf.db.build_connection_str())
Session = sessionmaker(bind=engine, class_=AsyncSession)
