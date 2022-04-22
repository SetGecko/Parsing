
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings


from instaparser.spiders.insta_followers import InstaFollowersSpider
from instaparser.spiders.insta_following import InstaFollowingSpider
from instaparser import settings

if __name__ == '__main__':
    crawler_settings = Settings()
    crawler_settings.setmodule(settings)

    process = CrawlerProcess(settings=crawler_settings)
    process.crawl(InstaFollowersSpider)
    process.crawl(InstaFollowingSpider)
    process.start()