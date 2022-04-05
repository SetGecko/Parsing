"""
___________________¶¶¶¶¶
_________________¶¶_____¶¶¶
______________¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶
___________¶¶¶_________________¶¶¶
_________¶¶_______________________¶¶
_______¶¶____________¶¶¶____________¶¶
______¶¶_____¶¶¶¶¶¶¶¶¶__¶¶¶¶¶¶¶¶¶¶¶¶_¶¶
_____¶¶__¶¶¶¶¶¶¶¶¶____¶¶____¶¶___¶¶¶¶¶¶¶
_____¶¶¶¶¶¶___¶¶______¶¶_____¶¶_______¶¶
_____¶¶_______¶¶___¶_¶¶¶_¶___¶¶_______¶¶
_____¶¶_______¶¶____¶¶_¶¶____¶¶_______¶¶
_____¶¶________¶¶¶¶¶¶¶__¶¶¶¶¶¶_______¶¶
______¶¶____________________________¶¶
____¶¶¶¶¶¶¶________¶¶_____¶¶_____¶¶¶¶¶¶¶¶
___¶¶____¶¶¶¶________¶¶¶¶¶____¶¶¶¶¶______¶¶
__¶¶¶¶¶______¶¶¶¶¶¶__________¶¶¶¶¶¶____¶¶¶¶¶
¶¶____¶¶________¶¶¶¶¶¶¶¶¶¶¶¶¶________¶¶___¶¶
¶¶_____¶¶______________¶¶___________¶¶____¶¶
¶¶_____¶¶_____________¶¶¶____________¶¶¶__¶¶
_¶¶¶__¶¶_______________¶¶_______________¶¶¶
___¶¶¶________________¶¶¶________________¶¶
____¶¶_________________¶¶_______________¶¶
_____¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶__¶¶___¶¶¶¶¶¶¶¶¶¶¶¶
______¶¶____________¶¶_¶¶_¶¶_________¶¶
_____¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶
"""

import argparse
import json
import re
import time
import unicodedata
from pprint import pprint

import requests
from bs4 import BeautifulSoup as bs
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError


def get_response(address):
    # проверяем ответ сервера
    # + маскируемся :)
    headers = {
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:98.0) Gecko/20100101 Firefox/98.0'}
    response = requests.get(address, headers=headers)
    if response.status_code == 200:
        return response
    else:
        print(f'Запрос к адресу {response.url} завершился ошибкой: {response.status_code}. '
              f'Текст ошибки: {response.text}')
        return response


def parse():
    parser = argparse.ArgumentParser(description='Скрипт парсинга hh и поиска '
                                                 'и поиска информации по введённым значениям ')

    parser.add_argument("-p", "--position", nargs='+', type=str, default='',
                        help="укажите наименование, по которой вы хотите "
                             "собрать информацию о вакансиях (default ' ')")
    parser.add_argument("-n", "--number", type=int, default=0,
                        help="number of pages")

    return parser.parse_args()


def validate_arguments(args):
    validated_args = {}
    if args.position:
        validated_args['position'] = '+'.join(args.position)
    else:
        input_string = input(
            'Укажите наименование, по которой вы хотите собрать информацию о вакансиях: ')
        validated_args['position'] = '+'.join(input_string.split())
    if args.number:
        validated_args['numbers_of_page'] = args.number
    else:
        while True:
            try:
                pages = int(input('Specify the number of pages: '))
            except ValueError:
                print('check input. must be integers')
                continue
            if pages:
                validated_args['numbers_of_page'] = pages
                break

    return validated_args


def create_url(args, page=0) -> str:
    base_url = args['site']
    url = f'{base_url}search/vacancy?area=113&text={args["position"]}&items_on_page=20&page={page}'
    return url


def validate_data(data):
    if data:
        data = data.getText()
        data = unicodedata.normalize("NFKD", data)
    else:
        data = None
    return data


def validate_salary_data(salary):
    salary_data = {}
    if not salary:
        salary_data['min'] = None
        salary_data['max'] = None
        salary_data['currency'] = None
    else:
        salary = validate_data(salary)
        # проверяем на наличие условий "от" или "до"
        salary_terms = re.findall(r'^(\D+)', salary)
        salary_terms = [_.replace(' ', '') for _ in salary_terms]

        # находим значения ЗП
        salary_values = []
        # salary_values_old = re.findall(r'(?:\d+)\D(?:\d+)', salary)
        # temp_values = re.findall(r'((?:\d+)\D(?:\d+))|(\d+)', salary)
        temp_values = re.finditer(r'((?:\d+)\D(?:\d+))|(\d+)', salary)
        for match in temp_values:
            salary_values.append(match.group())
        salary_values = [item.replace(' ', '') for item in salary_values]

        # находим валюту
        salary_currency = re.findall(r'(\S+)$', salary)
        if not salary_terms:
            salary_data['min'] = int(salary_values[0])
            salary_data['max'] = int(salary_values[1])
        else:
            if salary_terms[0] == 'до':
                salary_data['min'] = None
                salary_data['max'] = int(salary_values[0])
            elif salary_terms[0] == 'от':
                salary_data['min'] = int(salary_values[0])
                salary_data['max'] = None
        salary_data['currency'] = salary_currency[0].lower()

    return salary_data


def get_vacancy_data(vacancy):
    vacancy_data = {}
    vacancy_name = validate_data(vacancy.find("a", {"data-qa": "vacancy-serp__vacancy-title"}))
    vacancy_link = vacancy.find("a", {"data-qa": "vacancy-serp__vacancy-title"})["href"]
    vacancy_company_name = validate_data(vacancy.find("a", {"data-qa": "vacancy-serp__vacancy-employer"}))
    vacancy_company_city = validate_data(vacancy.find("div", {"data-qa": "vacancy-serp__vacancy-address"}))
    vacancy_salary = validate_salary_data(vacancy.find("span", {"data-qa": "vacancy-serp__vacancy-compensation"}))
    vacancy_data['company name'] = vacancy_company_name
    vacancy_data['company location'] = vacancy_company_city
    vacancy_data['vacancy name'] = vacancy_name
    vacancy_data['link'] = vacancy_link
    vacancy_data['salary_min'] = vacancy_salary['min']
    vacancy_data['salary_max'] = vacancy_salary['max']
    vacancy_data['salary_currency'] = vacancy_salary['currency']

    return vacancy_data


def check_last_search_page(dom):
    try:
        return int(dom.select('.pager a span')[-2].getText())
    except IndexError:
        return 1


def get_hh_vacancies_data(args, db=None):
    args['site'] = 'https://hh.ru/'

    # запросим web-страницу для проверки кол-ва страниц в поиске
    url = create_url(args)
    response = get_response(url)
    dom = bs(response.text, 'html.parser')

    # определим последнюю страницу в поиске
    last_page = check_last_search_page(dom)

    # если поиск длинее, то будем проверять то кол-во, которое запросил пользователь
    # иначе - ограничим поиск
    nums_of_pages = args['numbers_of_page'] if last_page > args['numbers_of_page'] else last_page

    vacancies_list = []

    # Создадим указатель на коллекцию в базе данных
    # имя коллекции - выбранная вакансия
    collection_name = args["position"]
    vacancies_collection = db.get_collection(collection_name)

    for page in range(nums_of_pages):
        url = create_url(args, page)
        print(f'Проверяем страницу по адресу:\n{url}')
        response = get_response(url)
        time.sleep(1)
        dom = bs(response.text, 'html.parser')
        vacancies = dom.find_all('div', {'class': 'vacancy-serp-item'})
        for vacancy in vacancies:
            vacancy_data = get_vacancy_data(vacancy)
            vacancies_list.append(vacancy_data)
            save_result_in_db(vacancy_data, vacancies_collection)

    results = list(vacancies_collection.find({}))
    pprint(results)

    # save_result_to_json('hh_ru', vacancies_list)
    print(f'Общее количество проверенных вакансий: {len(vacancies_list)}')


def save_result_to_json(site: str, vacancies_list: list) -> None:
    filename = f'vacancies_{site}.json'
    with open(filename, 'w', encoding='utf-8') as json_file:
        json.dump(vacancies_list, json_file, ensure_ascii=False, indent=4)


def save_result_in_db(data: dict, collection) -> None:
    if not is_data_in_db(data, collection):
        try:
            collection.insert_one(data)
        except DuplicateKeyError:
            print(f"Document with id = {data['_id']} already exist")


def is_data_in_db(data: dict, collection) -> bool:
    result = collection.find_one(
        {
            '$and':
                [
                    {
                        'company name': {'$eq': data['company name']},
                        'vacancy name': {'$eq': data['vacancy name']},
                        'company location': {'$eq': data['company location']}
                    }
                ]
        }
    )
    if result:
        return True
    else:
        return False

def vacancy_search(db, args=None) -> list:
    position = input('Укажите вакансию для поиска в базе данных: ') if args is None else args["position"]
    salary = int(input('Укажите желаемую зарплату: '))
    salary_currency = input('Укажите валюту (руб./usd/eur): ').lower()
    if salary_currency == 'руб':
        salary_currency = f'{salary_currency}.'
    # Создадим указатель на коллекцию в базе данных
    # имя коллекции - выбранная вакансия
    collection_name = position
    vacancies_collection = db.get_collection(collection_name)
    result = vacancies_collection.find(
        {
            '$or':
                [
                    {
                        'salary_max': {'$gte': salary}
                    },
                    {
                        'salary_min': {'$gte': salary}
                    },
                ],
            '$and':
                [{
                    'salary_currency': {'$eq': salary_currency}
                }]
        }
    )
    # print()
    for item in result:
        pprint(item)
    return list(result)


def connect_2_db_server(address=None):
    try:
        return MongoClient('127.0.0.1', 27017)
    except ConnectionError:
        print('Ошибка соедниения с базой данных')
        return None


def main():
    args = parse()
    correct_args = validate_arguments(args)

    # Создаем клиента для подключения к серверу
    client = connect_2_db_server()
    if client:
        # подключаемся к базе данных, указав её имя
        db = client['hh_ru_vacancies']
    else:
        print('Соединение с базой данных не установлено')

    get_hh_vacancies_data(correct_args, db)
    vacancy_search(db, correct_args)


if __name__ == '__main__':
    main()
