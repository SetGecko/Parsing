# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class InstaparserItem(scrapy.Item):
    # define the fields for your item here like:

    user_id = scrapy.Field()
    username = scrapy.Field()
    friend_id = scrapy.Field()
    friend_photo = scrapy.Field()
    friend_username = scrapy.Field()
    friend_full_name = scrapy.Field()
    friend_data = scrapy.Field()