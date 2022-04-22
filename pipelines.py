# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from pymongo import MongoClient
from scrapy.pipelines.images import ImagesPipeline
import scrapy


class InstaparserPipeline:

    def __init__(self):
        client = MongoClient('localhost', 27017)
        self.mongo_base = client['Scrapy_spider_instagram']

    def process_item(self, item, spider):
        # print(item)

        collection = self.mongo_base[spider.name]
        collection.update_one({'friend_id': item['friend_id']}, {'$set': item}, upsert=True)


        return item


class InstaImagesPipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        if item['friend_photo']:
            for img in item['friend_photo']:
                try:
                    yield scrapy.Request(img)
                except Exception as error:
                    print(f'Ошибка при обработке фото! {error}')

    def item_completed(self, results, item, info):
        item['friend_photo'] = [itm[1] for itm in results if itm[0]]
        return item