import scrapy


class ListSpiderSpider(scrapy.Spider):
    name = "list_spider"
    allowed_domains = ["xxx"]
    start_urls = ["https://xxx"]

    def parse(self, response):
        pass
