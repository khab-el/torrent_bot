import configparser
import ssl
import json
import requests
import os

from aiohttp import web
# from aiohttp.client_reqrep import FormData
import aiohttp
import asyncio

from telegabot.bot import Bot
from telegabot.api import Conversation

global TOKEN

config = configparser.ConfigParser()
config.read('configs/bot.cfg')

TOKEN = config['secrets']['bot_token']
PORT = config['server']['port']

LOGIN = config['rutracker']['login']
PASSWORD = config['rutracker']['password']
API_KEY = config['google']['api_key']
KINOPOISK_CSE = config['kinopoisk']['cse']
YOUTUBE_CSE = config['youtube']['cse']

WEBHOOK_SSL_CERT = "ssl/cert.pem"
WEBHOOK_SSL_PRIV = "ssl/key.key"

bot = Bot()

class EchoConversation(Conversation):
    def __init__(self, token, loop):
        super().__init__(token, loop)

    async def message_handler(self, message):
        chat_id = message['chat']['id']
        text = message['text']
        size = '2-5'
        filmRait = bot.find_ball(API_KEY, KINOPOISK_CSE, text)
        trailer = bot.find_trailer(API_KEY, YOUTUBE_CSE, filmRait[0])
        if not os.path.exists(f'torrent_file/{filmRait[0]}.torrent'):
            bot.openSession(LOGIN,PASSWORD)
            rutracker = bot.findTorrent(filmRait[0], size)
            if rutracker:
                file_nm = bot.downloadTorrent(rutracker[0])
                await self.sendDocument( chat_id=chat_id, caption=f'{rutracker[1]} {filmRait[1]} {filmRait[2]} {filmRait[3]} {trailer}', document=f'torrent_file/{file_nm}.torrent' )
            else:
                await self.sendMessage(chat_id=chat_id, text=f'{filmRait[1]} {filmRait[2]} {filmRait[3]} {trailer}')
        else:
            await self.sendDocument( chat_id=chat_id, caption=f'{filmRait[1]} {filmRait[2]} {filmRait[3]} {trailer}', document=f'torrent_file/{file_nm}.torrent' )

    async def callback_handler(self, message):
        chat_id = message['message']['chat']['id']
        call_back = message['data']
        callback_query_id = message['callback_query_id']
        await self.sendMessage( chat_id, call_back )

# async def middleware_factory(app, handler):
#     async def middleware_handler(request):
#         data = await request.json()
#         if data['message']['from']['id'] in black_list:
#             return web.Response(status=200)
#         return await handler(request)
#     return middleware_handler


async def init_app():
    app = web.Application(middlewares=[])
    echobot = EchoConversation(TOKEN, loop)
    app.router.add_post('/', echobot.handler)
    # app.middlewares.append(middleware_factory)
    return app


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    app = loop.run_until_complete(init_app())
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.load_cert_chain(WEBHOOK_SSL_CERT, WEBHOOK_SSL_PRIV)
    web.run_app(app, host='0.0.0.0', port=PORT, ssl_context=context)
