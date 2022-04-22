import scrapy
import re
from scrapy.http import HtmlResponse
from scrapy.loader import ItemLoader
from shop.items import ShopItem


class LeroymerlinruSpider(scrapy.Spider):
    name = 'leroymerlinru'
    allowed_domains = ['leroymerlin.ru']
    page = 1
    pages_total = None
    search_url = 'https://leroymerlin.ru/offer/oborudovanie-dlya-dusha/?page={page}'
    start_urls = [search_url.replace('{page}', str(page))]

    def parse(self, response: HtmlResponse):
        """Получаем список страниц для разбора"""
        if response.status != 200:
            print('Сайт не возвращает страницу')
            return

        # адрес текущей страницы со списком элементов
        print('Список: ' + response.url)

        # Получаем список будущих страниц на обработку из пагинации
        if self.pages_total is None:
            self.pages_total = self.get_pages_total(response)
            if self.pages_total:
                for i in range(2, self.pages_total + 1):
                    su = self.search_url.replace('{page}', str(i))
                    # yield response.follow(su, callback=self.parse)

        # Получаем ссылки на элементы, чтобы затем собрать данные со
        # страниц детального просмостра
        links = response.xpath("//product-card//a/@href").getall()
        links = list(set(links))  # удалим дубликаты

        for link in links:
            yield response.follow(link, callback=self.parse_item)

    def parse_item(self, response: HtmlResponse):
        """Разбираем информацию на странцие детального просмотра товара"""
        if response.status != 200:
            print('Сайт не возвращает страницу детального просмотра товара!')
            return

        # адрес страницы с детальной информацией
        print('Элемент: ' + response.url)

        loader = ItemLoader(item=ShopItem(), response=response)
        loader.add_xpath('name', "//h1/text()")  # название

        # цена
        loader.add_xpath('price', "//*[@class='primary-price']"
                                              "//*[@itemprop='price']/@content")

        # фото
        loader.add_xpath('photos', "//*[@slot='media-content']//picture"
                                          "//source[position()=1]/@data-origin")

        loader.add_value('url', response.url)  # ссылка
        yield loader.load_item()

    def get_pages_total(self, response: HtmlResponse):
        """Получает максимальное количество страниц в поисковой выдаче"""
        try:
            pages_total = response.css(".list-paginator .items-wrapper"
                                       " :last-child a::attr(href)").get()
            m = re.search(r'page=([0-9]*)', pages_total)
            pages_total = int(m.group(1))
            print(f'Всего страниц на сайте {self.name}: {pages_total}')
            return pages_total
        except:
            print(f'Ошибка определения макс. количества страниц в {self.name}!')
        return 0