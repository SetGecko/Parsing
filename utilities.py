# ░░░░░░░░░░░▄▄▄████████████▄▄▄░░░░░░░░░░░
# ░░░░░░▄▄██▀▀▀░░░░▄░░░░▄░░░░▀▀▀██▄▄░░░░░░
# ░░░░▄█▀▀░▄▄██░░░░██▄▄██░░░░██▄▄░▀▀█▄░░░░
# ░░▄█▀░▄█████░░░░░██████░░░░░█████▄░▀█▄░░
# ░██░▄███████▄░░░▄██████▄░░░▄███████▄░██░
# ██░██████████████████████████████████░██
# ██░██████████████████████████████████░██
# ██░██████████████████████████████████░██
# ░██░▀████▀░░███▀████████▀███░░▀████▀░██░
# ░░▀█▄░▀██▄░░░▀░░░░████░░░░▀░░░▄██▀░▄█▀░░
# ░░░░▀█▄▄▀▀░░░░░░░░░██░░░░░░░░░▀▀▄▄█▀░░░░
# ░░░░░░▀▀██▄▄▄░░░░░░░░░░░░░░▄▄▄██▀▀░░░░░░
# ░░░░░░░░░░▀▀▀▀████████████▀▀▀▀░░░░░░░░░░

import unicodedata
import requests
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

def validate_arguments():
    dict_of_sites = {
        '1': 'lenta.ru',
        '2': 'news.mail.ru',
        '3': 'yandex.ru/news'
    }

    print('Web-sites for news scrapping: ')
    for key, val in dict_of_sites.items():
        print(f'{key}: {val}')

    print('Выберите сайт. Для этого введите номер (от "1" to "3") или '
          'введите "0" для поиска по всем сайтам')
    input_string = input('Вы выбрали: ')

    validated_args = {}
    if input_string == '0':
        validated_args['site'] = list(dict_of_sites.values())
    else:
        validated_args['site'] = dict_of_sites[input_string]

    return validated_args


def get_response(address):
    # проверяем ответ от сервера - не послал ли он нас в щель козы
    headers = {
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:98.0) Gecko/20100101 Firefox/98.0'}

    response = requests.get(address, headers=headers)
    if response.status_code == 200:
        return response
    else:
        print(f'Запрос к адресу {response.url} завершился ошибкой: {response.status_code}. '
              f'Текст ошибки: {response.text}')
        return response


def create_url(site) -> str:
    url_dict = {
        'lenta.ru': f'https://lenta.ru/',
        'news.mail.ru': f'https://news.mail.ru/',
        'yandex.ru/news': f'https://yandex.ru/news/'
    }
    url = url_dict[site]
    return url


def validate_data(data):
    if data:
        data = unicodedata.normalize("NFKD", data)
    else:
        data = None
    return data


def save_result_in_db(data: dict, collection) -> None:
    # функц для записи в БиДе
    if not is_data_in_db(data, collection):
        try:
            collection.insert_one(data)
        except DuplicateKeyError:
            print(f"Document with id = {data['_id']} already exist")


def is_data_in_db(data: dict, collection) -> bool:
    # функц для проверки записей БиДе
    result = collection.find(
            {
                'name': {'$eq': data['name']},
            }
        )
    if result:
        return True
    else:
        return False


def connect_2_db_server(address=None):
    # функция подключения к серваку
    try:
        return MongoClient('127.0.0.1', 27017)
    except ConnectionError:
        print('Ошибка соедниения с базой данных')
        return None