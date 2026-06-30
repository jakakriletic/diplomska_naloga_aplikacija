"""Scrapy nastavitve za modul zajema podatkov (web scraping)."""

BOT_NAME = "scraper"

SPIDER_MODULES = ["scraper.spiders"]
NEWSPIDER_MODULE = "scraper.spiders"

# Vljudno strganje: predstavimo se in spoštujemo robots.txt
USER_AGENT = "DiplomskaScraper/1.0 (+raziskovalni-prototip)"
ROBOTSTXT_OBEY = True

# Omejitve obremenitve strežnika
CONCURRENT_REQUESTS_PER_DOMAIN = 2
DOWNLOAD_DELAY = 0.5
DOWNLOAD_TIMEOUT = 20

# Čiščenje HTML poteka v pipeline (BeautifulSoup)
ITEM_PIPELINES = {
    "scraper.pipelines.CleaningPipeline": 300,
}

# Robustnost
RETRY_ENABLED = True
RETRY_TIMES = 2
HTTPERROR_ALLOW_ALL = False
AJAXCRAWL_ENABLED = True

FEED_EXPORT_ENCODING = "utf-8"
LOG_LEVEL = "INFO"

# Privzeto izklopljeno; orkestrator ga nastavi prek -s CLOSESPIDER_PAGECOUNT
# CLOSESPIDER_PAGECOUNT = 40
