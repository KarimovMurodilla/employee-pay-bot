#!/usr/bin/env python3

from fastapi import FastAPI
from sqladmin import Admin
from sqlalchemy.ext.asyncio import async_sessionmaker

from ..configuration import conf
from .auth import AdminAuth
from .settings import engine
from .views import ADMIN_VIEWS

app = FastAPI()
authentication_backend = AdminAuth(secret_key=conf.SECRET_KEY)
admin = Admin(
    app=app,
    engine=engine,
    authentication_backend=authentication_backend,
)

async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


# Register your views
for view in ADMIN_VIEWS:
    admin.add_view(view)
