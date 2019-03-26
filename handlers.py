# handlers.py

from aiohttp import web, log
# Handlers.py

import base64
import secrets

import aiohttp
import aiohttp_jinja2e

import models


# Authorization handler
async def auth_handler(request):
    ws = web.WebSocketResponse(autoclose=True)
    await ws.prepare(request)
    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            auth = base64.b64decode(msg.data).decode()
            username, password = auth.split(':')
            await ws.send_json({'username': username, 'password': password})
    return ws


# Index page handler
@aiohttp_jinja2.template('index.html')
async def index_handler(request):
    requests = await models.Request.all()
    return {'requests': requests}
