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

from handlers import routes


if sys.platform not in ('win32',):
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


async def static_processor(request):
    return {'STATIC_URL': '/static/'}


class BList(list):

    """ Broadcast list """

    # Send data to waiters
    async def send_data(self, resource, data):

        # Create queue of tasks
        tasks = []
        for waiter in self:
            tasks.append(waiter['ws'].send_json({resource: data.to_json()}))
        try:
            # Run all task gather
            asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            log.ws_logger.error('Error was happened during broadcasting: %s' % e)


async def get_app(debug=False):
    middlewares = []

    if debug:
        middlewares += [toolbar_middleware_factory]

    app = web.Application(middlewares=middlewares)

    if debug:
        aiohttp_debugtoolbar.setup(app, intercept_redirects=False)

    router = app.router
    router.add_routes(routes)
    router.add_static('/static', 'static')

    aiohttp_jinja2.setup(
        app, loader=jinja2.FileSystemLoader('templates'),
        context_processors=[static_processor]
    )

    app['waiters'] = defaultdict(BList)

    # Close all websockets form broadcast list
    async def close_websockets(app):
        for channel in app['waiters'].values():
            for waiter in channel:
                await waiter['ws'].close(code=1000, message="Server shutdown")

    app.on_shutdown.append(close_websockets)

    return app


if __name__ == '__main__':
    debug = True

    if debug:
        logging.basicConfig(level='DEBUG', filename="logging.log", filemode='w')

    loop = asyncio.get_event_loop()
    app = loop.run_until_complete(get_app(debug))
    web.run_app(app)
