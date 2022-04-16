# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from pymongo import MongoClient


class BookparserPipeline:
    def __init__(self):
        client = MongoClient('127.0.0.1', 27017)  # соединение
        mongodb = client['crawler']  # база
        self.books_db = mongodb.books  # коллекция

    def process_item(self, item, spider):
        _id = item['url']

        if spider.name == 'labirintru':
            _id = item['url'].strip('/').split('/')[-1]
        elif spider.name == 'book24ru':
            _id = item['url'].strip('/').split('-')[-1]

        data = {}  # данные для сохранения в базу
        data.update(item)
        data['_id'] = f'{spider.name}/{_id}'

        if _id:
            try:
                res = self.books_db.insert_one(data)
                print('Информация о книге сохранена: ' + res.inserted_id)
            except Exception as e:
                print('Ошибка сохранения книги в базу: ' + data['_id'])
                print(e)

        return item
