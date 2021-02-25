from flask import Flask, request
import telegram
from telegabot.credentials import bot_token, bot_user_name,URL
from telegabot.mastermind import find_film_on_rutracker, find_ball, find_trailer
import json
import logging
import telebot
from telebot import types
from datetime import datetime


global bot
global TOKEN
global dict_state
global dict_state_history
global format_video
TOKEN = bot_token
bot = telebot.TeleBot(token=TOKEN)
dict_state = {}
dict_state_history = {}
format_video = ['avi', 'mov', 'rm', 'mpeg', 'dvd', 'wmv', 'mp4', 'flv', 'mkv', 'm4v', 'mpg', 'swf', 'asf', 'mpeg-4', 'в любом']
# k = """{"inline_keyboard": [[{ "text": "avi", "callback_data": "avi"},{ "text": "mp4", "callback_data": "mp4"},{ "text": "mkv", "callback_data": "mkv"}],[{ "text": "mov", "callback_data": "mov"},{ "text": "wmv", "callback_data": "wmv"},{ "text": "dvd", "callback_data": "dvd"}],[{ "text": "В любом", "callback_data": "в любом"}]]}"""

app = Flask(__name__)

@app.route('/', methods=['POST'])
def respond():
    # retrieve the message in JSON and then transform it to Telegram object
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    
    resp_json = request.get_json(force=True)
    app.logger.info(resp_json)

    if 'message' in resp_json:
        chat_id = update.message.chat.id
        if 'text' in resp_json['message']:
            text = update.message.text.encode('utf-8').decode()
            # print("got text message :", text)
            if chat_id not in dict_state.keys():
                dict_state[chat_id] = [text]
                keyboard = types.InlineKeyboardMarkup() 
                key_1 = types.InlineKeyboardButton(text='Размер', callback_data='only_size') 
                keyboard.add(key_1) 
                key_2 = types.InlineKeyboardButton(text='Формат', callback_data='only_format')
                keyboard.add(key_2)
                key_3 = types.InlineKeyboardButton(text='Размер и формат', callback_data='size_format')
                keyboard.add(key_3)
                key_3 = types.InlineKeyboardButton(text='Не важно', callback_data='any')
                keyboard.add(key_3)
                question = 'Ты можешь указать параметры поиска, если хочешь'
                bot.send_message(chat_id=chat_id, text=question, reply_markup=keyboard)
            elif chat_id in dict_state.keys() and len(dict_state[chat_id]) == 2 and (dict_state[chat_id][1] == 'only_size' or dict_state[chat_id][1] == 'size_format' or dict_state[chat_id][1] == 'size_any'):
                try:
                    size_list = text.split('-')
                    if len(size_list) > 2:
                        bot.send_message(chat_id=chat_id, text="Не понимаю, укажи интервал в гигабайтах, например 2-5")
                    else:
                        int(size_list[0])
                        int(size_list[1])
                        dict_state[chat_id].append(text)
                        if dict_state[chat_id][1] == 'size_format':
                            bot.send_message(chat_id=chat_id, text="В каком формате мне искать торрент (avi, mp4 и т.д.)? Если вам все равно в каком формате будет видео, можешь написать - в любом")
                        elif dict_state[chat_id][1] == 'size_any':
                            dict_state[chat_id].append(dict_state_history[chat_id][0])
                            keyboard = types.InlineKeyboardMarkup() 
                            key_1 = types.InlineKeyboardButton(text='Да', callback_data='yes') 
                            keyboard.add(key_1) 
                            key_2 = types.InlineKeyboardButton(text='Нет', callback_data='no')
                            keyboard.add(key_2)
                            question = 'Ты ищешь ' + dict_state[chat_id][0] + ' размером ' + dict_state[chat_id][2] + ' GB в ' + dict_state[chat_id][3] + ' формате?'
                            bot.send_message(chat_id=chat_id, text=question, reply_markup=keyboard)
                        else:
                            dict_state[chat_id].append('в любом')
                            keyboard = types.InlineKeyboardMarkup() 
                            key_1 = types.InlineKeyboardButton(text='Да', callback_data='yes') 
                            keyboard.add(key_1) 
                            key_2 = types.InlineKeyboardButton(text='Нет', callback_data='no')
                            keyboard.add(key_2)
                            question = 'Ты ищешь ' + dict_state[chat_id][0] + ' размером ' + dict_state[chat_id][2] + ' GB в ' + dict_state[chat_id][3] + ' формате?'
                            bot.send_message(chat_id=chat_id, text=question, reply_markup=keyboard)
                except Exception:
                    bot.send_message(chat_id=chat_id, text="Не понимаю, укажи интервал в гигабайтах, например 2-5")
            elif (chat_id in dict_state and len(dict_state[chat_id]) == 3) or (chat_id in dict_state and len(dict_state[chat_id]) == 2 and dict_state[chat_id][1] == 'only_format'):
                if text.lower() not in format_video and dict_state[chat_id][1] != 'only_size':
                    bot.send_message(chat_id=chat_id, text="Не знаю такого формата. Могу искать в любом формате видео, просто напиши - в любом")
                else:
                    if dict_state[chat_id][1] == 'only_size':
                        dict_state[chat_id].append('в любом')
                    elif dict_state[chat_id][1] == 'only_format':
                        dict_state[chat_id].append('любой')
                        dict_state[chat_id].append(text)
                    else:
                        dict_state[chat_id].append(text)
                    keyboard = types.InlineKeyboardMarkup() 
                    key_1 = types.InlineKeyboardButton(text='Да', callback_data='yes') 
                    keyboard.add(key_1) 
                    key_2 = types.InlineKeyboardButton(text='Нет', callback_data='no')
                    keyboard.add(key_2)
                    question = 'Ты ищешь ' + dict_state[chat_id][0] + ' размером ' + dict_state[chat_id][2] + ' GB в ' + dict_state[chat_id][3] + ' формате?'
                    bot.send_message(chat_id=chat_id, text=question, reply_markup=keyboard)
        elif 'sticker' in resp_json['message']:
            sticker = update.message.sticker.file_id
            # print("got sticker :", sticker)
            bot.send_sticker(chat_id=chat_id, data=sticker)
    elif 'callback_query' in resp_json:
        chat_id = update.callback_query.message.chat.id
        call_back = update.callback_query.data
        if call_back == 'yes':
            bot.answer_callback_query(callback_query_id=update.callback_query.id, text='Секундочку, уже ищу =)', cache_time=4)
            print(dict_state[chat_id])
            try:
                ball = find_ball(file_name=dict_state[chat_id][0])
                try:
                    trailer = find_trailer(file_name=dict_state[chat_id][0]+' '+ball[2])
                    try:
                        if ball[2] == '':
                            if dict_state[chat_id][2] == 'любой':
                                info = find_film_on_rutracker(file_name=dict_state[chat_id][0], size='1-400', format_film=dict_state[chat_id][3])
                            else:
                                info = find_film_on_rutracker(file_name=dict_state[chat_id][0], size=dict_state[chat_id][2], format_film=dict_state[chat_id][3])
                            bot.send_document(chat_id=chat_id, data=open('torrent_file/'+dict_state[chat_id][0] +'.torrent', 'rb'), caption=info[0]+' \r\n\r\nРазмер: '+info[1]+'\r\n\r\n'+ball[0]+'\r\n\r\n'+ball[1]+' \r\n\r\nТрейлер: '+trailer+' \r\n\r\nСтраничка на кинопоиске: '+ball[3])
                        else:
                            if dict_state[chat_id][2] == 'любой':
                                info = find_film_on_rutracker(file_name=dict_state[chat_id][0]+' '+ball[2], size='1-400', format_film=dict_state[chat_id][3])
                            else:
                                info = find_film_on_rutracker(file_name=dict_state[chat_id][0]+' '+ball[2], size=dict_state[chat_id][2], format_film=dict_state[chat_id][3])
                            bot.send_document(chat_id=chat_id, data=open('torrent_file/'+dict_state[chat_id][0] +' '+ball[2]+'.torrent', 'rb'), caption=info[0]+' \r\n\r\nРазмер: '+info[1]+'\r\n\r\n'+ball[0]+'\r\n\r\n'+ball[1]+' \r\n\r\nТрейлер: '+trailer+' \r\n\r\nСтраничка на кинопоиске: '+ball[3])
                    except:        
                        bot.send_message(chat_id=chat_id, text='Не смог найти фильм/сериал на рутрекере\r\n'+ball[0]+'\r\n'+ball[1]+' \r\nТрейлер: '+trailer+' \r\nСтраничка на кинопоиске: '+ball[3])
                except:
                    if ball[2] == '':
                        if dict_state[chat_id][2] == 'любой':
                            info = find_film_on_rutracker(file_name=dict_state[chat_id][0], size='1-400', format_film=dict_state[chat_id][3])
                        else:
                            info = find_film_on_rutracker(file_name=dict_state[chat_id][0], size=dict_state[chat_id][2], format_film=dict_state[chat_id][3])
                        bot.send_document(chat_id=chat_id, data=open('torrent_file/'+dict_state[chat_id][0]+'.torrent', 'rb'), caption=info[0]+' \r\nРазмер: '+info[1]+'\r\n'+ball[0]+'\r\n'+ball[1]+' \r\nСтраничка на кинопоиске: '+ball[3])
                    else:
                        if dict_state[chat_id][2] == 'любой':
                            info = find_film_on_rutracker(file_name=dict_state[chat_id][0]+' '+ball[2], size='1-400', format_film=dict_state[chat_id][3])
                        else:
                            info = find_film_on_rutracker(file_name=dict_state[chat_id][0]+' '+ball[2], size=dict_state[chat_id][2], format_film=dict_state[chat_id][3])
                        bot.send_document(chat_id=chat_id, data=open('torrent_file/'+dict_state[chat_id][0]+' '+ball[2]+'.torrent', 'rb'), caption=info[0]+' \r\nРазмер: '+info[1]+'\r\n'+ball[0]+'\r\n'+ball[1]+' \r\nСтраничка на кинопоиске: '+ball[3])
            except:
                bot.send_message(chat_id=chat_id, text='Не смог найти такой фильм')
            del dict_state[chat_id]
        elif call_back == 'name':
            bot.answer_callback_query(callback_query_id=update.callback_query.id)
            del dict_state[chat_id]
            bot.send_message(chat_id=chat_id, text="Что ты ищешь?")
        elif call_back == 'size':
            bot.answer_callback_query(callback_query_id=update.callback_query.id)
            try:
                if dict_state[chat_id][1] == 'any':
                    dict_state[chat_id] = [dict_state[chat_id][0], 'only_size']
                elif dict_state[chat_id][1] == 'only_format':
                    dict_state_history[chat_id] = [dict_state[chat_id][3]]
                    dict_state[chat_id] = [dict_state[chat_id][0], 'size_any']
                else:
                    dict_state[chat_id] = [dict_state[chat_id][0], dict_state[chat_id][1]]
                bot.send_message(chat_id=chat_id, text="В каком диапазоне мне искать торрент? (укажи интервал в гигабайтах, например 2-5)")
            except Exception:
                del dict_state[chat_id]
                bot.send_message(chat_id=chat_id, text="Что-то я запутался, давай сначала. Что ты ищешь?")
        elif call_back == 'format':
            bot.answer_callback_query(callback_query_id=update.callback_query.id)
            try:
                if dict_state[chat_id][1] == 'any':
                    dict_state[chat_id][1] == 'only_format'
                    dict_state[chat_id].remove(dict_state[chat_id][3])
                elif dict_state[chat_id][1] == 'only_size':
                    dict_state_history[chat_id] = [dict_state[chat_id][2]]
                    dict_state[chat_id].remove(dict_state[chat_id][3])
                    dict_state[chat_id][1] == 'any_format'
                else:
                    dict_state[chat_id].remove(dict_state[chat_id][3])
                bot.send_message(chat_id=chat_id, text="В каком формате мне искать торрент (avi, mp4 и т.д.)? Если вам все равно в каком формате будет видео, можете написать - в любом")
            except Exception:
                del dict_state[chat_id]
                bot.send_message(chat_id=chat_id, text="Что-то я запутался, давай сначала. Что ты ищешь?")
        elif call_back == 'only_size':
            bot.answer_callback_query(callback_query_id=update.callback_query.id)
            dict_state[chat_id].append('only_size')
            bot.send_message(chat_id=chat_id, text="В каком диапазоне мне искать торрент? (укажи интервал в гигабайтах, например 2-5)")
        elif call_back == 'only_format':
            bot.answer_callback_query(callback_query_id=update.callback_query.id)
            dict_state[chat_id].append('only_format')
            bot.send_message(chat_id=chat_id, text="В каком формате мне искать торрент (avi, mp4 и т.д.)? Если вам все равно в каком формате будет видео, можете написать - в любом")
        elif call_back == 'size_format':
            bot.answer_callback_query(callback_query_id=update.callback_query.id)
            dict_state[chat_id].append('size_format')
            bot.send_message(chat_id=chat_id, text="В каком диапазоне мне искать торрент? (укажи интервал в гигабайтах, например 2-5)")
        elif call_back == 'any':
            bot.answer_callback_query(callback_query_id=update.callback_query.id)
            dict_state[chat_id] = [dict_state[chat_id][0],'any','любой','в любом']
            keyboard = types.InlineKeyboardMarkup() 
            key_1 = types.InlineKeyboardButton(text='Да', callback_data='yes') 
            keyboard.add(key_1) 
            key_2 = types.InlineKeyboardButton(text='Нет', callback_data='no')
            keyboard.add(key_2)
            question = 'Ты ищешь ' + dict_state[chat_id][0] + ' в любом размере и формате?'
            bot.send_message(chat_id=chat_id, text=question, reply_markup=keyboard)
        elif chat_id in dict_state:
            bot.answer_callback_query(callback_query_id=update.callback_query.id)
            keyboard = """{"inline_keyboard": [[{"text": "Название","callback_data": "name"},{"text": "Размер","callback_data": "size"}],[{"text": "Формат","callback_data": "format"}]]}"""
            question = 'Какой параметр поиска мне нужно изменить?'
            bot.send_message(chat_id=chat_id, text=question, reply_markup=keyboard)

    return 'ok'

if __name__ == '__main__':
    app.debug = False

    logging.basicConfig(filename='logs/telegram_bot_{:%Y-%m-%d}.log'.format(datetime.now()), level=logging.DEBUG, format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    app.run(host='0.0.0.0', port=8443, ssl_context=('./ssl/cert.pem', './ssl/key.key'), threaded=True)