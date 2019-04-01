# handlers.py

from aiohttp import web, log
import aiohttp
import aiohttp_jinja2

from models import User, Channel, Request


routes = web.RouteTableDef()


@routes.view('/auth')
class AuthHandler(web.View):

    """ Authenticate login/pass and return user instance with token """

    async def post(self):
        headers = {'Access-Control-Allow-Origin': '*'}
        data = await self.request.post()
        username = data.get('username')
        password = data.get('password')

        if username and password:
            user = await User.login(username, password)
            if user:
                return web.json_response(user.to_json(), headers=headers)
            else:
                # Return 401 if login/ password is incorrect
                return web.json_response(
                    {"error": "Wrong login/password"},
                    status=401, headers=headers
                )
        else:
            # Return 400 if no login/password
            return web.json_response(
                {"error": "Expected login/password"},
                status=400, headers=headers
            )

    # Set headers for CORS
    async def options(self):
        headers = {
            'Allow': 'GET POST OPTIONS',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'X-CSRFTOKEN'
        }
        return web.Response(headers=headers)


@routes.view(r'/ws/{channel:\d+}/{token}')
class WebSocketView(web.View):

    """ WebSocket for handling requests """

    async def get(self):
        # Get token from url match and user by token
        token = self.request.match_info.get('token')
        user = await User.get_by_token(token)

        # Get channel id from url match and channel by id
        channel_id = self.request.match_info.get('channel')
        channel = await Channel.get(channel_id)

        # If user and channel ok - channel access check
        if user and channel:
            if not user.is_staff and user.channel.id != channel.id:
                return web.Response(text="User does not belong to this channel", status=403)

            waiters = self.request.app['waiters'][channel.id]
            try:
                # Prepare websocket and add user and ws to waiters list
                ws = web.WebSocketResponse(autoclose=False)
                await ws.prepare(self.request)
                waiters.append({'user': user, 'ws': ws})

                # Handle messages from websocket
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        if msg.data == 'close':
                            await ws.close()
                        else:
                            try:
                                data = msg.json()
                            except Exception as e:
                                log.ws_logger.error('Error on handling data: %s' % e)
                            else:
                                # Handle actions
                                if data.get('action') == 'new_request':
                                    await self.new_request(data.get('request'))

                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        log.ws_logger.error(
                            'ws connection closed with exception %s' % ws.exception()
                            )
            # Close websocket and remove it from channel
            finally:
                for w in waiters:
                    if w['ws'] == ws:
                        await ws.close(code=1000, message="Connection closed")
                        log.ws_logger.info('Is WebSocket closed?: {}'.format(ws.closed))
                        waiters.remove(w)
            return ws
        else:
            return web.Response(text="Bad request", status=400)

    async def new_request(self, request_data):

        """ Create new request and send it to channel waiters """

        new_req = await Request.create(request_data)
        if new_req:
            await self.request.app['waiters'][new_req.channel.id].send_data('request', new_req)


@routes.get('/')
@aiohttp_jinja2.template('index.html')
async def index_handler(request):
    return {'text': 'OK'}
