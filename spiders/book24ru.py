import scrapy
import re
from scrapy.http import HtmlResponse
from ..items import BookparserItem


class Book24ruSpider(scrapy.Spider):
    name = 'book24ru'
    allowed_domains = ['book24.ru']
    page = 1
    pages_total = None
    search_url = 'https://book24.ru/search/page-{page}/?q=кулинария'
    start_urls = [search_url.replace('{page}', str(page))]

    # def __init__(self, search = 'кулинария'):  # доработать ввод слова при старте
    #     self.start_urls = [f'https://book24.ru/search/?q={search}']

    def parse(self, response: HtmlResponse):
        if response.status != 200:
            print('Сайт не возвращает страницу')

        # адрес текущей страницы со списком элементов
        print('Список: ' + response.url)

        # Получаем список будущих страниц на обработку. Для этого получаем
        # номер последней страницы пагинации. Но пагинация отображается только
        # через JS, поэтому достаём макс.количество страниц из кода
        if self.pages_total is None:
            try:
                m = re.search(r'totalPages:([0-9]*),', response.text)
                self.pages_total = int(m.group(1))
                print(f'Всего страниц на сайте {self.name}: {self.pages_total}')
                for i in range(2, self.pages_total + 1):
                    su = self.search_url.replace('{page}', str(i))
                    yield response.follow(su, callback=self.parse)
            except:
                pass

        # Получаем ссылки на элементы, чтобы затем собрать данные со
        # страниц детального просмостра
        links = response.xpath("//*[@class='product-list__item']"
                               "//a[contains(@href, '/product/')]/@href").getall()
        links = list(set(links))  # удаляем дубликаты

        for link in links:
            yield response.follow(link, callback=self.book_parse)

    def book_parse(self, response: HtmlResponse):
        # адрес страницы с детальной информацией
        url = response.url
        print('Элемент: ' + url)

        # Наименование книги
        h1 = response.css("h1::text").get()

        # Рейтинг книги
        rating = response.xpath("//*[@itemprop='ratingValue']/@content").get()

        # Основная цена
        price_base = response.xpath("//*[@itemprop='price']/@content").get()

        # Цена со скидкой
        price_discount = response.xpath("//*[@class='product-sidebar-price__price-old']"
                                        "//text()").get()

        # Автор(ы)
        authors = response.xpath("//*[@itemprop='author']//*[@itemprop='name']/@content").getall()

        yield BookparserItem(name=h1.strip() if h1 else None,
                             rating=rating.strip() if rating else None,
                             price_base=price_base.strip() if price_base else None,
                             price_discount=price_discount.strip() if price_discount else None,
                             authors=authors,
                             url=url.strip())
