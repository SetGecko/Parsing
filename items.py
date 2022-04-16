# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class BookparserItem(scrapy.Item):
    name = scrapy.Field()  # Наименование книги
    rating = scrapy.Field()  # Рейтинг книги
    price_base = scrapy.Field()  # Основная цена
    price_discount = scrapy.Field()  # Цена со скидкой
    authors = scrapy.Field()  # Автор(ы)
    url = scrapy.Field()  # Ссылка на книгу
