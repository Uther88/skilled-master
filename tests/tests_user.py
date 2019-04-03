# test_user.py

from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from aiohttp import web

from models import User, get_db


class UserTestCase(AioHTTPTestCase):
    async def setUpAsync(self):
        User.Meta.db = get_db(name='test_db')
        self.user = User

    async def test_creating_user(self):
        user_data = dict(
            username="username",
            password="password",
            name="name",
            surname="surname",
            patronymic="patronymic",
            position="master",
            channel=1
        )
        self.instance = await User.create(**user_data)
        self.assertIsInstance(self.instance, User)