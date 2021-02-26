import re
import requests
import logging
import os
from urllib.parse import unquote, quote

from bs4 import BeautifulSoup

class Bot(object):
    def __init__(self):
        pass

    def translite(self, text):
        symbols = (u"абвгдеёжзийклмнопрстуфхцчшщыэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЫЭЮЯ ",
           u"abvgdeejzijklmnoprstufhzcssyeuaABVGDEEJZIJKLMNOPRSTUFHZCSSYEUA_")
        exclude_symbols = ['ь', 'ъ', 'Ь', 'Ъ']

        tr = {ord(a):ord(b) for a, b in zip(*symbols)}
        
        for i in exclude_symbols:
            tr[ord(i)] = None

        text= u'%s' % text
        
        return text.translate(tr)

    def openSession(self, login, password):
        # open session for request rutracker.org
        self.session = requests.Session()

        # generate body and url for login in rutracker.org
        data_for_login = {'redirect': 'index.php', 'login_username': login, 'login_password': password, 'login': 'Вход'}
        login_url = 'https://rutracker.org/forum/login.php'

        # login in rutracker.org with generated body and sessions cookies
        resp = self.session.post(login_url, data=data_for_login, cookies=self.session.cookies)
        responseCode = resp.status_code
        if ((responseCode - (responseCode % 100)) / 100) == 2:
            # print('Successful send')
            logging.info(f'Successful login in rutracker')
            soup = BeautifulSoup(resp.content, features="lxml")
            for i in soup.find_all('script'):
                if 'form_token' in str(i):
                    # print(re.split(r'(.*): \'(.*)\'', re.search( r'form_token: .*', i.get_text())[0])[2])
                    #print(soup.decode("utf-8"), file=open('test.html','w'))
                    self.token_id = re.search( r'form_token: \'([\w\d]+)\'', str(i))[1]
                    break
        else:
            # print(resp.text())
            logging.error(f'Request text - {message}; Response code - {responseCode}; Response header - {resp.headers}')

    def searchPage(self, file_name):
        # self.file_name = file_name
        # generate body and url for searching in rutracker in same session with sessions cookies
        file_url_encoded = quote(file_name.encode("utf8"))
        #data_for_searching = {'max': '1', 'nm': file_name}
        data_for_searching = {'f[]': '-1', 'o': '4', 's': '2', 'pn': '', 'nm': file_name}
        search_url = "https://rutracker.org/forum/tracker.php?nm=" + file_url_encoded
        #print(data_for_searching, search_url)

        # search on rutracker and write result in file
        resp_searching = self.session.post(search_url, data=data_for_searching, cookies=self.session.cookies)
        return BeautifulSoup(resp_searching.content, features="lxml")
        # print(soup.decode("utf-8"), file=open('test.html','w'))

    def findTorrent(self, file_name, size):
        aval_size = list(range(int(size.split('-')[0]), int(size.split('-')[1])))

        soup = self.searchPage(file_name)
        logging.debug(f'Starting search film {file_name}')
        info = dict()
        cnt =  0
        for item in soup.find_all('a', {"class": "small tr-dl dl-stub"}):
            if 'GB' in item.get_text():
                item_size = item.get_text()
                if '.' in item.get_text():
                    m = item.get_text().split('.')[0]
                else:
                    m = item.get_text().split(' GB')[0]
                if int(m) in aval_size:
                    url_for_torrent = item.get('href')
                    get_data_topic_id = item.get('href').split('=')[1]
                    # print(get_data_topic_id, url_for_torrent)
                    for link in soup.find_all('a', {"class": "med tLink ts-text hl-tags bold"}):
                        if (('DVDRip' or 'HDRip' or 'BDRip' or 'WEB-DLRip' in link.get_text())) and (get_data_topic_id == link.get('data-topic_id')):
                            download_url = 'https://rutracker.org/forum/' + url_for_torrent
                            meta_info = link.get_text()
                            info[get_data_topic_id] = [download_url, meta_info, item_size]
                            cnt += 1
                            if cnt == 3:
                                logging.info(f'Found >= 3 torrents film {file_name}')
                                return(info)
        if cnt > 0 and cnt < 3:
            logging.info(f'Found {cnt} torrents film {file_name}')
            return(info)

    def downloadTorrent(self, torrent_id):
        # file_tr = self.translite(self.file_name)
        os.makedirs('torrent_file/', exist_ok=True)

        data_for_download = {'form_token': self.token_id}
        download_url = 'https://rutracker.org/forum/dl.php?t=' + torrent_id
        resp_download_file = self.session.post(download_url, data=data_for_download, cookies=self.session.cookies)
        
        responseCode = resp_download_file.status_code
        if ((responseCode - (responseCode % 100)) / 100) == 2:
            cd = resp_download_file.headers.get('content-disposition')
            fname = re.findall('filename\*=UTF-8\'\'(.+)', cd) 
            if len(fname) == 0: 
                filename = f'film_{torrent_id}.torrent'
            else:
                filename = self.translite(unquote(fname[0]))

            file = open(f'torrent_file/{filename}', 'wb')
            for chunk in resp_download_file.iter_content(100000):
                file.write(chunk)
            file.close()

            logging.info(f'Downloaded film {filename} successfull')
        else:
            logging.error(f'Response code - {responseCode}; Response header - {resp.headers}')
        return filename
        
    def google_search(self, key, cse, file_name):
        url = 'https://www.googleapis.com/customsearch/v1'

        s = requests.Session()
        payload = {
            "key": key,
            "cx": cse,
            "q": file_name,
            "num": 10
        }
        resp_searching = s.get(url=url, params=payload)
        data = resp_searching.json()

        return data['items']

    def find_ball(self, key, cse, file_name):
        kinopoisk_ball = 'Кинопоиск: '
        IMDb_ball = 'IMDb: '

        searchRes = self.google_search(key, cse, file_name)
        for result in searchRes:
            url = result['link']
            film_id = re.search(r'/film/(\d{1,20})/', url)[1]
            try:
                year = re.search(r'(\d{4})', result['title'])[0]
            except:
                year = str()
            break

        logging.debug(f'End searching kinopoisk link for film {file_name}')

        ball_url = f'https://rating.kinopoisk.ru/{film_id}.xml'
        file_name += f' {year}'

        s = requests.Session()
        resp = s.get(ball_url)
        soup = BeautifulSoup(resp.content, features="lxml")
        
        for item in soup.find_all('kp_rating'):
            kinopoisk_ball += item.get_text()
        for item in soup.find_all('imdb_rating'):
            IMDb_ball += item.get_text()

        logging.debug(f'End searching ball for film {file_name}')
        return(file_name, kinopoisk_ball, IMDb_ball, url)

    def find_trailer(self, key, cse, file_name):
        file_name += ' трейлер'
        
        searchRes = self.google_search(key, cse, file_name)

        for result in searchRes:
            url = result['link']
            return url
