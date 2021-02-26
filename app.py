import configparser
import ssl
import logging
import os
import pytz
from datetime import datetime

from aiohttp import web
# from aiohttp.client_reqrep import FormData
import aiohttp
import asyncio

from telegabot.torrentbot import TorrentConversation

global TOKEN

config = configparser.ConfigParser()
config.read('configs/bot.cfg')

TOKEN = config['secrets']['bot_token']
PORT = config['server']['port']
HOST = config['server']['host']

WEBHOOK_SSL_CERT = config['ssl']['public_cert']
WEBHOOK_SSL_PRIV = config['ssl']['private_key']

LOGPATH = config.get('logs', 'logpath')


# async def middleware_factory(app, handler):
#     async def middleware_handler(request):
#         data = await request.json()
#         if data['message']['from']['id'] in black_list:
#             return web.Response(status=200)
#         return await handler(request)
#     return middleware_handler


async def init_app():
    app = web.Application(middlewares=[])
    torrentbot = TorrentConversation(TOKEN, loop)
    app.router.add_post('/', torrentbot.handler)
    # app.middlewares.append(middleware_factory)
    return app


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    app = loop.run_until_complete(init_app())

    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.load_cert_chain(WEBHOOK_SSL_CERT, WEBHOOK_SSL_PRIV)

    if LOGPATH:
        os.makedirs(LOGPATH, exist_ok=True)
        logging.basicConfig(
            filename='{LOGPATH}/telegram_bot_{date}.log'.format(LOGPATH=LOGPATH, date=datetime.utcnow().astimezone(pytz.timezone('Europe/Moscow')).strftime("%Y-%m-%d")), 
            level=logging.DEBUG, 
            format='%(asctime)s - %(name)s - %(levelname)s : %(message)s', 
            datefmt='%m/%d/%Y %I:%M:%S %p')
    else:
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s : %(message)s',
            level=logging.DEBUG 
        )
    web.run_app(app, host=HOST, port=PORT, ssl_context=context)
    logging.info(f'Torrent bot start on {HOST}:{PORT}')
