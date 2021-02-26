import json
import requests
import os
import re
import logging

from aiohttp import web
from aiohttp.client_reqrep import FormData
import aiohttp
import asyncio

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
                responseCode = resp.status
                if ((responseCode - (responseCode % 100)) / 100) == 2:
                    # print('Successful send')
                    logging.info(f'Successful send message method {method}')
                else:
                    # print(resp.text())
                    logging.error(f'Request text - {message}; Response text - {resp.text()}')

    async def sendMessage(self, chat_id, text, **kwargs):

        message = {
            "chat_id": chat_id,
            "text": text
        }

        headers = {
            'Content-Type': 'application/json'
        }

        if kwargs.get('parse_mode'):
            message['parse_mode'] = kwargs['parse_mode']
        if kwargs.get('entities'):
            message['entities'] = kwargs['entities']
        if kwargs.get('disable_web_page_preview'):
            message['disable_web_page_preview'] = kwargs['disable_web_page_preview']
        if kwargs.get('disable_notification'):
            message['disable_notification'] = kwargs['disable_notification']
        if kwargs.get('reply_to_message_id'):
            message['reply_to_message_id'] = kwargs['reply_to_message_id']
        if kwargs.get('allow_sending_without_reply'):
            message['allow_sending_without_reply'] = kwargs['allow_sending_without_reply']
        if kwargs.get('reply_markup'):
            message['reply_markup'] = kwargs['reply_markup']

        await self._request('sendMessage', json.dumps(message), headers)

    async def sendSticker(self, chat_id, sticker, **kwargs):

        message = {
            "chat_id": chat_id,
            "sticker": sticker
        }

        headers = {
            'Content-Type': 'application/json'
        }

        if kwargs.get('disable_notification'):
            message['disable_notification'] = kwargs['disable_notification']
        if kwargs.get('reply_to_message_id'):
            message['reply_to_message_id'] = kwargs['reply_to_message_id']
        if kwargs.get('allow_sending_without_reply'):
            message['allow_sending_without_reply'] = kwargs['allow_sending_without_reply']
        if kwargs.get('reply_markup'):
            message['reply_markup'] = kwargs['reply_markup']

        await self._request('sendSticker', json.dumps(message), headers)

    async def sendDocument(self, chat_id, document, **kwargs):

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

    async def download_handler(self, message):
        pass

    async def sticker_handler(self, message):
        pass

    async def handler(self, request):
        message = await request.json()
        if message.get('message'):
            if re.search(r'^/download(.*)', message['message'].get('text')):
                asyncio.ensure_future(self.download_handler(message.get('message')))
            elif message['message'].get('sticker'):
                asyncio.ensure_future(self.sticker_handler(message.get('message')))
            else:
                asyncio.ensure_future(self.message_handler(message.get('message')))
        elif message.get('callback_query'):
            asyncio.ensure_future(self.callback_handler(message.get('callback_query')))
        return aiohttp.web.Response(status=200)


class InlineKeyboard(object):
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
