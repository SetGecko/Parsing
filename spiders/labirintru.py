import scrapy
from scrapy.http import HtmlResponse
from ..items import BookparserItem


class LabirintruSpider(scrapy.Spider):
    name = 'labirintru'
    allowed_domains = ['labirint.ru']
    page = 1
    start_urls = [f'https://www.labirint.ru/search/кулинария/']

    # def __init__(self, search = 'кулинария'):  # доработать ввод слова при старте
    #     self.start_urls = [f'https://www.labirint.ru/search/{search}/']

    def parse(self, response: HtmlResponse):
        if response.status != 200:
            print('Сайт не возвращает страницу')

        # адрес текущей страницы со списком элементов
        print('Список: ' + response.url)

        # следующая страница на обработку
        next_page = response.css("a.pagination-next__text::attr(href)").get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

        # Получаем ссылки на элементы, чтобы затем собрать данные со
        # страниц детального просмостра
        links = response.xpath("//div[contains(@class,'b-search-page')]"
                               "//a[contains(@href,'/books/') and "
                               "not(contains(@href,'#'))]/@href").getall()
        links = list(set(links))  # удаляем дубликаты

        for link in links:
            yield response.follow(link, callback=self.book_parse)


    def book_parse(self, response: HtmlResponse):
        # адрес страницы с детальной информацией
        url = response.url
        print('Элемент: ' + url)

        # Наименование книги
        h1 = response.xpath("//*[@id='product-info']/@data-name").get()

        # Рейтинг книги
        rating = response.xpath("//*[@id='product-voting']//*[@id='rate']//text()").get()

        # Основная цена
        price_base = response.xpath("//*[@id='product-info']/@data-price").get()

        # Цена со скидкой
        price_discount = response.xpath("//*[@id='product-info']/@data-discount-price").get()

        # Автор(ы)
        authors = response.xpath("//*[@id='product-specs']//*[@data-event-label='author']//text()").getall()

        yield BookparserItem(name=h1.strip() if h1 else None,
                             rating=rating.strip() if rating else None,
                             price_base=price_base.strip() if price_base else None,
                             price_discount=price_discount.strip() if price_discount else None,
                             authors=authors,
                             url=url.strip())
