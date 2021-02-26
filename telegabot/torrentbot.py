import configparser
import os
import re

from aiohttp import web
# from aiohttp.client_reqrep import FormData
import aiohttp
import asyncio

from .bot import Bot
from .api import Conversation

path_current_dir = os.path.dirname(__file__).replace('telegabot', '')
path_config_file = os.path.join(path_current_dir, 'configs/bot.cfg')
config = configparser.ConfigParser()
config.read(path_config_file)

LOGIN = config['rutracker']['login']
PASSWORD = config['rutracker']['password']
API_KEY = config['google']['api_key']
KINOPOISK_CSE = config['kinopoisk']['cse']
YOUTUBE_CSE = config['youtube']['cse']

bot = Bot()
bot.openSession(LOGIN,PASSWORD)

class TorrentConversation(Conversation):
    def __init__(self, token, loop):
        super().__init__(token, loop)

    async def message_handler(self, message):
        chat_id = message['chat']['id']
        text = message['text']
        size = '2-5'

        filmRait = bot.find_ball(API_KEY, KINOPOISK_CSE, text)
        trailer = bot.find_trailer(API_KEY, YOUTUBE_CSE, filmRait[0])
        
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
        chat_id = message['chat']['id']
        sticker = message['sticker']['file_id']
        await self.sendSticker( chat_id=chat_id, sticker=sticker )

    async def download_handler(self, message):
        chat_id = message['chat']['id']
        text = message['text']
        download_url = re.search(r'^/download(.*)', text)[1]
        bot.downloadTorrent(download_url)
        await self.sendDocument(chat_id=chat_id, document=f'torrent_file/film_{download_url}.torrent')
