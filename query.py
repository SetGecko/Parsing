'''5) Написать запрос к базе, который вернет список подписчиков только указанного пользователя
6) Написать запрос к базе, который вернет список профилей, на кого подписан указанный пользователь'''

from pymongo import MongoClient
from pprint import pprint

client = MongoClient('localhost', 27017)
mongo_base = client['Scrapy_spider_instagram']

collection_followers = mongo_base['insta_followers']
collection_following = mongo_base['insta_following']

user = input("Enter username: ")

for item in collection_followers.find({'username': user}):
    print(f'Подписчик {user}\n {item}\n "-" * 30')



for item in collection_following.find({'username': user}):
    print(f'Подписка {user}\n {item}\n {"-" * 30}')