# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import scrapy
from scrapy.pipelines.images import ImagesPipeline
from os.path import exists
from urllib.parse import urlparse
from shop.settings import IMAGES_STORE

# Обязательно должен быть установлен модуль "pillow": pip install pillow
# И прописана директива IMAGES_STORE = 'путь_к_папкес_фото' в settings.py


class ShopPipeline:
    def process_item(self, item, spider):
        return item


class ShopPhotosPipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        """Загружаем фото по полученным адресам"""
        if item['photos']:
            for img in item['photos']:
                try:
                    yield scrapy.Request(img)
                except Exception as e:
                    print(e)

    def file_path(self, request, response=None, info=None, *, item=None):
        """Изменяем пути сохранения фалов фото, чтобы привести к виду:
        '/id_товара/порядковый_номер_фото'.
        """
        # расширение файла фото из url
        ext = urlparse(request.url).path.split('.')[-1]

        # название папки с фото -  это id товара в магазине
        _id = item['url'].strip('/').split('-')[-1]

        # имя файла фото - порядковый номер загруженного файла: 1, 2, 3...
        photo_num = 1
        while exists(f'{IMAGES_STORE}/{_id}/{photo_num}.{ext}'):
            photo_num += 1

        return f'{_id}/{photo_num}.{ext}'