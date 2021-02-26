import configparser
import ssl
import re
import logging
import os
import pytz
from datetime import datetime

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
HOST = config['server']['host']

LOGIN = config['rutracker']['login']
PASSWORD = config['rutracker']['password']
API_KEY = config['google']['api_key']
KINOPOISK_CSE = config['kinopoisk']['cse']
YOUTUBE_CSE = config['youtube']['cse']

WEBHOOK_SSL_CERT = config['ssl']['public_cert']
WEBHOOK_SSL_PRIV = config['ssl']['private_key']

LOGPATH = config.get('logs', 'logpath')

bot = Bot()

class TorrentConversation(Conversation):
    def __init__(self, token, loop):
        super().__init__(token, loop)

    async def message_handler(self, message):
        chat_id = message['chat']['id']
        text = message['text']
        size = '2-5'

        filmRait = bot.find_ball(API_KEY, KINOPOISK_CSE, text)
        trailer = bot.find_trailer(API_KEY, YOUTUBE_CSE, filmRait[0])
        
        bot.openSession(LOGIN,PASSWORD)
        rutracker = bot.findTorrent(filmRait[0], size)
        text = f'Трейлер: {trailer}\nСтраница на Кинопоиск: {filmRait[3]}\n{filmRait[1]}\n{filmRait[2]}\n\n\n'
        for k,v in rutracker.items():
            text += f'{v[1]}\nРазмер: {v[2]}\nCкачать: /download{k}\n\n'
        await self.sendMessage(chat_id=chat_id, text=text)

    async def callback_handler(self, message):
        chat_id = message['message']['chat']['id']
        call_back = message['data']
        callback_query_id = message['callback_query_id']
        await self.sendMessage( chat_id=chat_id, text=call_back )

    async def sticker_handler(self, message):
        chat_id = message['message']['chat']['id']
        sticker = message['message']['sticker']['file_id']
        await self.sendSticker( chat_id=chat_id, sticker=sticker )

    async def download_handler(self, message):
        chat_id = message['chat']['id']
        text = message['text']
        download_url = 'https://rutracker.org/forum/dl.php?t=' + re.search(r'^/download(.*)', text)[1]
        file_nm = bot.downloadTorrent(download_url)
        await self.sendDocument(chat_id=chat_id, caption=file_nm[1] document=f'torrent_file/{file_nm[0]}.torrent')

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
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.DEBUG 
        )
    web.run_app(app, host=HOST, port=PORT, ssl_context=context)
    logging.info(f'Torrent bot start on {HOST}:{PORT}')
