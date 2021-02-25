import configparser
import ssl
import json
import requests
import os

from aiohttp import web
# from aiohttp.client_reqrep import FormData
import aiohttp
import asyncio

from telegabot.mastermind import Bot

global TOKEN
global API_URL

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

class Api(object):
    URL = 'https://api.telegram.org/bot%s/%s'

    def __init__(self, token, loop):
        self._token = token
        self._loop = loop

    async def _request(self, method, message, headers):
        async with aiohttp.ClientSession(loop=self._loop) as session:
            async with session.post(self.URL % (self._token, method),
                                    data=message,
                                    headers=headers) as resp:
                try:
                    assert resp.status == 200
                except HTTPError as http_err:
                    print(f'HTTP error occurred: {http_err}') 
                except Exception as err:
                    print(f'Other error occurred: {err}') 

    async def sendMessage(self, chat_id, text, **kwargs):

        message = {
            "chat_id": chat_id,
            "text": text
        }

        headers = {
            'Content-Type': 'application/json'
        }

        if kwargs.get('reply_markup'):
            message['reply_markup'] = kwargs['reply_markup']

        await self._request('sendMessage', json.dumps(message), headers)

    async def sendDocument(self, chat_id, document, **kwargs):
        # data = FormData()
        # data.add_field('chat_id', chat_id)
        # data.add_field('document',
        #             open('requirements.txt', 'rb'),
        #             content_type='multipart/form-data')
        message = {
            'chat_id': str(chat_id),
            'document':  open(document, 'rb')
        }

        if kwargs.get('thumb'):
            message['thumb'] = kwargs['thumb']
        if kwargs.get('caption'):
            message['caption'] = kwargs['caption']
        if kwargs.get('parse_mode'):
            message['parse_mode'] = kwargs['parse_mode']      
        if kwargs.get('caption_entities'):
            message['caption_entities'] = kwargs['caption_entities'] 
        if kwargs.get('disable_content_type_detection'):
            message['disable_content_type_detection'] = kwargs['disable_content_type_detection'] 
        if kwargs.get('disable_notification'):
            message['disable_notification'] = kwargs['disable_notification']  
        if kwargs.get('reply_to_message_id'):
            message['reply_to_message_id'] = kwargs['reply_to_message_id'] 
        if kwargs.get('allow_sending_without_reply'):
            message['allow_sending_without_reply'] = kwargs['allow_sending_without_reply'] 
        if kwargs.get('reply_markup'):
            message['reply_markup'] = kwargs['reply_markup']

        await self._request('sendDocument', message, headers=None)

    async def answerCallbackQuery(self, callback_query_id, **kwargs):

        message = {
            "callback_query_id": callback_query_id
        }

        headers = {
            'Content-Type': 'application/json'
        }

        if kwargs.get('text'):
            message['text'] = kwargs['text']
        if kwargs.get('show_alert'):
            message['show_alert'] = kwargs['show_alert']
        if kwargs.get('url'):
            message['url'] = kwargs['url']
        if kwargs.get('cache_time'):
            message['cache_time'] = kwargs['cache_time']

        await self._request('answerCallbackQuery', json.dumps(message), headers)


class Conversation(Api):
    def __init__(self, token, loop):
        super().__init__(token, loop)

    async def message_handler(self, message):
        pass

    async def callback_handler(self, message):
        pass

    async def handler(self, request):
        message = await request.json()
        if message.get('message'):
            asyncio.ensure_future(self.message_handler(message.get('message')))
        elif message.get('callback_query'):
            asyncio.ensure_future(self.callback_handler(message.get('callback_query')))
        return aiohttp.web.Response(status=200)


class EchoConversation(Conversation):
    def __init__(self, token, loop):
        super().__init__(token, loop)
        self.chat_state = dict()
        self.chat_state_history = dict()

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
                bot.downloadTorrent(rutracker[0])
                await self.sendDocument( chat_id=chat_id, caption=f'{rutracker[1]} {filmRait[1]} {filmRait[2]} {filmRait[3]} {trailer}', document=f'torrent_file/{filmRait[0]}.torrent' )
            else:
                await self.sendMessage(chat_id=chat_id, text=f'{filmRait[1]} {filmRait[2]} {filmRait[3]} {trailer}')
        else:
            await self.sendDocument( chat_id=chat_id, caption=f'{filmRait[1]} {filmRait[2]} {filmRait[3]} {trailer}', document=f'torrent_file/{filmRait[0]}.torrent' )

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

class InlineKeyboard:
    def __init__(self):
        self.keyboard = {'inline_keyboard': []}

    def button(self, text, callback_data):
        button = {
            "text": text,
            "callback_data": callback_data
        }
        return button
    
    def add(self, *args):
        button_lst = list()
        button_lst.extend(args)
        self.keyboard['inline_keyboard'].append(button_lst)

    def get_keyboard(self):
        return self.keyboard

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
