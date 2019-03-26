# main.py

from collections import defaultdict
import logging

import asyncio
import aiohttp_jinja2
import aiohttp_debugtoolbar
from aiohttp_debugtoolbar import toolbar_middleware_factory

import jinja2
from aiohttp import web, log
import sys

from routes import routes
from middlewares import get_user_factory
import settings
import models


if sys.platform not in ('win32',):
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


async def static_processor(request):
    return {'STATIC_URL': '/static/'}


async def auth_processor(request):
    return {'user': request.user}


class BList(list):
	
    def send_data(self, resource, data):
        log.ws_logger.info("Sending {} for {} waiters".format(resource, len(self)))
        for waiter in self:
            try:
                waiter.send_json({resource: data})
            except Exception:
                log.ws_logger.error('Error was happened during broadcasting: ', exec_info=True)


async def get_app(debug=False):
    middlewares = [get_user_factory]

    if debug:
        middlewares += [toolbar_middleware_factory]

    app = web.Application(middlewares=middlewares)

    if debug:
        aiohttp_debugtoolbar.setup(app, intercept_redirects=False)

    router = app.router
    for route in routes:
        router.add_route(route[0], route[1], route[2])
    router.add_static('/static', 'static')

    aiohttp_jinja2.setup(
        app, loader=jinja2.FileSystemLoader('templates'),
        context_processors=[static_processor, auth_processor]
    )

    app['masters'] = defaultdict(BList)
    app['curators'] = defaultdict(BList)

    async def close_websockets(app):
        for master in app['masters'].values():
            for ws in master:
                await ws.close(code=1000, message="Server shutdown")

        for curator in app['curators'].values():
            for ws in curator:
                await ws.close(code=1000, message="Server shutdown")

    app.on_shutdown.append(close_websockets)

    return app


if __name__ == '__main__':
    debug = True

    if debug:
        logging.basicConfig(level='DEBUG')

    loop = asyncio.get_event_loop()
    app = loop.run_until_complete(get_app(debug))
    web.run_app(app)
