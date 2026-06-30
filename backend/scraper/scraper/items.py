import scrapy


class PageItem(scrapy.Item):
    url = scrapy.Field()
    depth = scrapy.Field()
    html = scrapy.Field()  # po pipeline vsebuje očiščeno besedilo
