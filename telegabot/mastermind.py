import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote, quote
import re

def find_film_on_rutracker(file_name, size, format_film):
    #fill login pass for rutracker.org, file name for searching and range of size in GB like 1-3
    login = 'eldar011'
    password = 'Wy6iK'

    size_range = size.split('-')

    # open session for request rutracker.org
    s = requests.Session()

    # generate body and url for login in rutracker.org
    data_for_login = {'redirect': 'index.php', 'login_username': login, 'login_password': password, 'login': 'Вход'}
    login_url = 'https://rutracker.org/forum/login.php'

    # login in rutracker.org with generated body and sessions cookies
    resp = s.post(login_url, data=data_for_login, cookies=s.cookies)
    #soup = BeautifulSoup(resp.content)
    #print(soup.decode("utf-8"), file=open('test.html','w'))

    # generate body and url for searching in rutracker in same session with sessions cookies
    file_url_encoded = quote(file_name.encode("utf8"))
    #data_for_searching = {'max': '1', 'nm': file_name}
    data_for_searching = {'f[]': '-1', 'o': '4', 's': '2', 'pn': '', 'nm': file_name}
    search_url = "https://rutracker.org/forum/tracker.php?nm=" + file_url_encoded
    #print(data_for_searching, search_url)

    # search on rutracker and write result in file
    resp_searching = s.post(search_url, data=data_for_searching, cookies=s.cookies)
    soup = BeautifulSoup(resp_searching.content, features="lxml")
    # print(soup.decode("utf-8"), file=open('test.html','w'))


    # find all tags that contain film size, then find size 1 or 2 or 3 GB, 
    # then find tag that contain meto info about tracker, 
    # find in that list only tag that contain quality hdrip or bdrip and topik id equals topic id films that was finded in first step  
    # go to page with full info about finded tracker
    # check if format is avi then stop all find process and 
    # print name of finded tracker, url for download .torrent file, topic id, size, full info about film
    i=0
    for item in soup.find_all('a', {"class": "small tr-dl dl-stub"}):
        if i == 1:
            break
        else:
            if 'GB' in item.get_text():
                size = item.get_text()
                if '.' in item.get_text():
                    m = item.get_text().split('.')[0]
                else:
                    m = item.get_text().split(' GB')[0]
                if int(m) in list(range(int(size_range[0]), int(size_range[1]))):
                    url_for_torrent = item.get('href')
                    get_data_topic_id = item.get('href').split('=')[1]
                    #print(get_data_topic_id, url_for_torrent)
                    for link in soup.find_all('a', {"class": "med tLink ts-text hl-tags bold"}):
                        if i == 1:
                            break 
                        else:
                            if (('DVDRip' in link.get_text()) or ('HDRip' in link.get_text()) or ('BDRip' in link.get_text()) or ('WEB-DLRip' in link.get_text())) and (get_data_topic_id == link.get('data-topic_id')):
                                resp_check_format = s.get('https://rutracker.org/forum/' + link.get('href'), cookies=s.cookies)
                                bsoup = BeautifulSoup(resp_check_format.content, features="lxml")
                                for form in bsoup.find_all('span'):
                                    #download_url='https://rutracker.org/forum/' + url_for_torrent
                                    #meto_info = link.get_text()
                                    if i == 1:
                                        break
                                    else:
                                        if format_film == 'в любом':
                                            download_url = 'https://rutracker.org/forum/' + url_for_torrent
                                            meto_info = link.get_text()
                                            i+=1
                                            break
                                        else:
                                            if format_film.lower() in form.get_text().lower():
                                                download_url = 'https://rutracker.org/forum/' + url_for_torrent
                                                meto_info = link.get_text()
                                                # full_info = form.get_text()
                                                i+=1
                                                break
                                            else:
                                                for findformat in bsoup.find_all('div', {"class": "post_body"}):
                                                    if format_film.lower() in findformat.get_text().lower():
                                                        download_url = 'https://rutracker.org/forum/' + url_for_torrent
                                                        meto_info = link.get_text()
                                                        # full_info = findformat.get_text()
                                                        i+=1
                                                        break

    try:
        download_url
    except:
        i=0
        for item in soup.find_all('a', {"class": "small tr-dl dl-stub"}):
            if i == 1:
                break
            else:
                size = item.get_text()
                m = item.get_text().split('.')[0]
                if int(m) in list(range(int(size_range[0]), int(size_range[1])+1)):
                    url_for_torrent = item.get('href')
                    get_data_topic_id = item.get('href').split('=')[1]
                    #print(get_data_topic_id, url_for_torrent)
                    for link in soup.find_all('a', {"class": "med tLink ts-text hl-tags bold"}):
                        if (('DVDRip' in link.get_text()) or ('HDRip' in link.get_text()) or ('BDRip' in link.get_text()) or ('WEB-DLRip' in link.get_text())) and (get_data_topic_id == link.get('data-topic_id')):
                            download_url='https://rutracker.org/forum/' + url_for_torrent
                            meto_info = link.get_text()
                            i+=1
                            break
                                
    # print(download_url)
    for i in soup.find_all('script'):
        if 'form_token' in str(i):
            # print(re.split(r'(.*): \'(.*)\'', re.search( r'form_token: .*', i.get_text())[0])[2])
            token_id = re.search( r'form_token: \'([\w\d]+)\'', str(i))[1]

            data_for_download = {'form_token': token_id}
            resp_download_file = s.post(download_url, data=data_for_download, cookies=s.cookies)
            file = open('torrent_file/'+file_name+'.torrent', 'wb')
            for chunk in resp_download_file.iter_content(100000):
                file.write(chunk)
            file.close()
            print(file_name, download_url, size, 'Downloaded successfull')
        break
    return(meto_info, size)


def find_ball(file_name):
    file_url_encoded = quote(file_name.encode("utf8"))

    s = requests.Session()

    search_url = 'https://www.google.com/search?&q='+file_url_encoded + ' site:kinopoisk.ru'

    resp_searching = s.get(search_url)
    soup = BeautifulSoup(resp_searching.content, features="lxml")
    #print(soup.decode("utf-8"), file=open('google.html','w'))

    for item in soup.find_all('a'):
        if '/url?q=https://www.kinopoisk.ru/film/' in item.get('href').lower():
            #print(item.get('href'))
            #print(re.search(r'/film/(\d{1,20})/', item.get('href'))[1])
            film_id = re.search(r'/film/(\d{1,20})/', item.get('href'))[1]
            try:
                year = re.search(r'(\d{4})', item.get_text())[0]
                break
            except:
                year = ''
                break

    ball_url = 'https://rating.kinopoisk.ru/'+film_id+'.xml'
    resp = s.get(ball_url)
    soup = BeautifulSoup(resp.content, features="lxml")
    for item in soup.find_all('kp_rating'):
        kinopoisk_ball = 'Кинопоиск: ' + item.get_text()
    for item in soup.find_all('imdb_rating'):
        IMDb_ball = 'IMDb: ' + item.get_text()
    try:
        kinopoisk_ball
        try:
            IMDb_ball
            print(kinopoisk_ball, IMDb_ball, year, 'https://www.kinopoisk.ru/film/'+film_id)
            return(kinopoisk_ball, IMDb_ball, year, 'https://www.kinopoisk.ru/film/'+film_id)
        except:
            print(kinopoisk_ball, year, 'https://www.kinopoisk.ru/film/'+film_id)
            return(kinopoisk_ball,'IMDb: 0', year, 'https://www.kinopoisk.ru/film/'+film_id)
    except:
        try:
            IMDb_ball
            print(IMDb_ball, year, 'https://www.kinopoisk.ru/film/'+film_id)
            return('Кинопоиск: 0',IMDb_ball, year, 'https://www.kinopoisk.ru/film/'+film_id)
        except:
            print(year, 'https://www.kinopoisk.ru/film/'+film_id)
            return('Кинопоиск: 0','IMDb: 0',year, 'https://www.kinopoisk.ru/film/'+film_id)
            
def find_trailer(file_name):
    file_url_encoded = quote(file_name.encode("utf8"))
    
    s = requests.Session()

    #search_url = 'https://www.youtube.com/results?search_query='+file_url_encoded+quote(' трейлер'.encode("utf8"))+'&pbj=1'
    #print(search_url)
    search_url = 'https://www.google.com/search?&q='+file_url_encoded + quote(' трейлер'.encode("utf8")) + ' site:youtube.com'
    
    resp_searching = s.get(search_url)
    soup = BeautifulSoup(resp_searching.content, features="lxml")
    for item in soup.find_all('a'):
        #print(item.get('href').lower())
        if '/url?q=https://www.youtube.com/watch' in item.get('href').lower():
            trailer_url=unquote(item.get('href').split('/url?q=')[1].split('&sa')[0])
            print(trailer_url)
            return(trailer_url)   
        
# def find_trailer(file_name):
#     file_url_encoded = quote(file_name.encode("utf8"))
    
#     s = requests.Session()

#     #search_url = 'https://www.youtube.com/results?search_query='+file_url_encoded+quote(' трейлер'.encode("utf8"))+'&pbj=1'
#     #print(search_url)
#     search_url = 'https://www.google.com/search?&q='+file_url_encoded + ' site:youtube.com'
    
#     resp_searching = s.get(search_url)
#     soup = BeautifulSoup(resp_searching.content, features="lxml")
#     for item in soup.find_all('a'):
#         item.get('href').lower()
#         if '/url?q=https://www.kinopoisk.ru/film/' in item.get('href').lower():
#             #print(item.get('href'))
#             #print(re.search(r'/film/(\d{1,20})/', item.get('href'))[1])
#             film_id = re.search(r'/film/(\d{1,20})/', item.get('href'))[1]
#             try:
#                 year = re.search(r'(\d{4})', item.get_text())[0]
#                 break
#             except:
#                 year = ''
#                 break
    #print('x')
#     for item in soup.find_all('a'):
#         if 'трейлер' in str(item.get('title')).lower() or 'trailer' in str(item.get('title')).lower():
#             trailer_url ='https://www.youtube.com' + item.get('href')
#             print(trailer_url)
#             break
#     return(trailer_url)
