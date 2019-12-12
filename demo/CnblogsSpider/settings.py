# -*- coding: utf-8 -*-

# Scrapy settings for CnblogsSpider project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://doc.scrapy.org/en/latest/topics/settings.html
#     https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://doc.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'CnblogsSpider'

SPIDER_MODULES = ['CnblogsSpider.spiders']
NEWSPIDER_MODULE = 'CnblogsSpider.spiders'


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'CnblogsSpider (+http://www.yourdomain.com)'
USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) ' \
             'Chrome/73.0.3683.86 Safari/537.36'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://doc.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
#DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Ensure use this Scheduler
SCHEDULER = "scrapy_redis_bloomfilter_block_cluster.scheduler.Scheduler"

# Persist
SCHEDULER_PERSIST = True

# Ensure all spiders share same duplicates filter through redis
DUPEFILTER_CLASS = "scrapy_redis_bloomfilter_block_cluster.dupefilter.RFPDupeFilter"

# queue, you can use: FifoQueue, LifoQueue, PriorityQueue or SimpleQueue
SCHEDULER_QUEUE_CLASS = 'scrapy_redis_bloomfilter_block_cluster.queue.FifoQueue'

# Redis URL
# REDIS_URL = 'redis://:admin123@localhost:6379' # or redis://localhost:6379
# REDIS_HOST = 'localhost'
# REDIS_PORT = 6379

# Redis cluster, if REDIS_MASTER_NODES is set, REDIS_URL do not work.
REDIS_CLUSTER_NODES = [
    {"host": "192.168.223.111", "port": "7001"},
    {"host": "192.168.223.111", "port": "7002"},
    {"host": "192.168.223.111", "port": "7003"},
    {"host": "192.168.223.111", "port": "7004"},
    {"host": "192.168.223.111", "port": "7005"},
    {"host": "192.168.223.111", "port": "7006"}
]

# Redis cluster auth, None means no auth
REDIS_CLUSTER_PASSWORD = None

# Number of Hash Functions to use, defaults to 6
BLOOMFILTER_HASH_NUMBER = 9

# Redis Memory Bit of Bloomfilter Usage, 30 means 2^30 = 128MB, defaults to 32
BLOOMFILTER_BIT = 32

# Number of Block for Bloomfilter Usage, one Block can use maximum Memory 512MB
BLOOMFILTER_BLOCK_NUM = 1

DUPEFILTER_DEBUG = True

# Disable Telnet Console (enabled by default)
TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
#}
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip,deflate,br',
    'accept-language': 'zh-CN,zh;q=0.9',
    'cache-control': 'no-cache',
    'pragma': 'no-cache',
    'upgrade-insecure-requests': '1',
    'host': 'www.cnblogs.com'
}

# Enable or disable spider middlewares
# See https://doc.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    'CnblogsSpider.middlewares.CnblogsspiderSpiderMiddleware': 543,
#}

# Enable or disable downloader middlewares
# See https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
#DOWNLOADER_MIDDLEWARES = {
#    'CnblogsSpider.middlewares.CnblogsspiderDownloaderMiddleware': 543,
#}

# Enable or disable extensions
# See https://doc.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
#}

# Configure item pipelines
# See https://doc.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    'CnblogsSpider.pipelines.CnblogsspiderPipeline': 300,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://doc.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://doc.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = 'httpcache'
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'
# LOG_LEVEL = 'INFO'
