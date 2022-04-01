import argparse
import json
import re
import time
import unicodedata
from pprint import pprint

import requests
from bs4 import BeautifulSoup as bs


def get_response(address):
    # проверяем ответ сервера, маскируемся :)
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
    parser = argparse.ArgumentParser(description='Script for scrapping hh.ru site and searching '
                                                 'for information about the entered value ')

    parser.add_argument("-p", "--position", nargs='+', type=str, default='',
                        help="indicate the position for which you want to "
                             "collect information about vacancies (default ' ')")
    parser.add_argument("-n", "--number", type=int, default=0,
                        help="number of pages")

    return parser.parse_args()


def validate_arguments(args):
    validated_args = {}
    if args.position:
        validated_args['position'] = '+'.join(args.position)
    else:
        input_string = input(
            'Кем собираемся работать? ')
        validated_args['position'] = '+'.join(input_string.split())
    if args.number:
        validated_args['numbers_of_page'] = args.number
    else:
        while True:
            try:
                pages = int(input('Сколько страничек будем разглядывать?: '))
            except ValueError:
                print('check input. must be integers')
                continue
            if pages:
                validated_args['numbers_of_page'] = pages
                break

    return validated_args


def create_url(args, page=0) -> str:
    base_url = args['site']
    url = f'{base_url}search/vacancy?area=113&text={args["position"]}&page={page}'
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
        # наличие условий от или до
        salary_terms = re.findall(r'^(\D+)', salary)
        salary_terms = [_.replace(' ', '') for _ in salary_terms]

        # ищем ЗП
        salary_values = re.findall(r'(?:\d+)\D(?:\d+)', salary)
        salary_values = [_.replace(' ', '') for _ in salary_values]

        # ищем значение валюты
        salary_currency = re.findall(r'(\S+)$', salary)
        # print()
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
        salary_data['currency'] = salary_currency[0]

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
    page_block = dom.find('div', {'data-qa': 'pager-block'})
    if not page_block:
        last_page = 1
    else:
        last_page = int(page_block.find('a', {'data-qa': 'pager-next'}).previous_element.previous_element)
    return last_page


def get_hh_vacancies_data(args):
    args['site'] = 'https://hh.ru/'

    # сколько страничек отдаст поиск
    url = create_url(args)
    response = get_response(url)
    dom = bs(response.text, 'html.parser')

    # находим последнюю страничку
    last_page = check_last_search_page(dom)

    # сколько ввёл юзер + ограничение
    nums_of_pages = args['numbers_of_page'] if last_page > args['numbers_of_page'] else last_page

    vacancies_list = []

    for page in range(nums_of_pages):
        url = create_url(args, page)
        print(f'Проверяем страницу по адресу:\n{url}')
        response = get_response(url)
        time.sleep(1)
        dom = bs(response.text, 'html.parser')
        vacancies = dom.find_all('div', {'class': 'vacancy-serp-item'})
        for vacancy in vacancies:
            vacancies_list.append(get_vacancy_data(vacancy))
        check_last_search_page(dom)

    save_result_to_json('hh_ru', vacancies_list)
    pprint(vacancies_list)
    print(f'Общее количество полученных вакансий: {len(vacancies_list)}')


# создаём функцию конвертации данных в json
def save_result_to_json(site: str, vacancies_list: list) -> None:
    filename = f'vacancies_{site}.json'
    with open(filename, 'w', encoding='utf-8') as json_file:
        json.dump(vacancies_list, json_file, ensure_ascii=False, indent=4)


def main():
    args = parse()
    correct_args = validate_arguments(args)
    get_hh_vacancies_data(correct_args)
    print()


if __name__ == '__main__':
    main()
