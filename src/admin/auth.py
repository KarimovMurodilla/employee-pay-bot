from fastapi import Request
from sqladmin.authentication import AuthenticationBackend


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        # form = await request.form()

        # if (
        #     form["username"] == conf.ADMIN_LOGIN
        #     and form["password"] == conf.ADMIN_PASSWORD
        # ):
        #     print(conf.ADMIN_LOGIN)
        #     print(conf.ADMIN_PASSWORD)
        #     request.session.update({"token": conf.SECRET_KEY})
        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        # token = request.session.get("token")

        # if not token:
        #     return False

        return True
