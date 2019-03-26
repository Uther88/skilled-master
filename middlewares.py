# middlewares.py

from aiohttp import web
from models import User


async def auth_cookie_factory(app, handler):
    """ Redirect to login page if unauthorized or not login request """
    async def auth_cookie_handler(request):
        if request.path != '/login' and request.cookies.get('user') is None:
            return web.HTTPFound('/')
        return await handler(request)
    return auth_cookie_handler


async def get_user_factory(app, handler):
    async def get_user_handler(request):
        if request.cookies.get('user_id') and await User.get(_id=request.cookies.get('user_id')):
            request.user = await User.get(_id=request.cookies.get('user_id'))
        else:
            request.user = 'anon'
        return await handler(request)
    return get_user_handler

