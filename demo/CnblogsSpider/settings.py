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
# CONCURRENT_REQUESTS = 32
CONCURRENT_REQUESTS = 4

# Configure a delay for requests for the same website (default: 0)
# See https://doc.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
#DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

SCHEDULER = "scrapy_redis_bloomfilter_block_cluster.scheduler.Scheduler"

SCHEDULER_PERSIST = True

# DUPEFILTER_CLASS = "scrapy_redis_bloomfilter_block_cluster.dupefilter.RFPDupeFilter"
DUPEFILTER_CLASS = "scrapy_redis_bloomfilter_block_cluster.dupefilter.LockRFPDupeFilter"

DUPEFILTER_KEY = '%(spider)s:dupefilter'

SCHEDULER_QUEUE_CLASS = 'scrapy_redis_bloomfilter_block_cluster.queue.FifoQueue'

SCHEDULER_QUEUE_KEY = '%(spider)s:requests'

DUPEFILTER_DEBUG = True

DUPEFILTER_LOCK_KEY = '%(spider)s:lock'

DUPEFILTER_LOCK_NUM = 16

DUPEFILTER_LOCK_TIMEOUT = 15

SCHEDULER_FLUSH_ON_START = False

REDIS_ENCODING = 'utf-8'

# REDIS_URL = 'redis://localhost:6379'    # or 'redis://:admin123@localhost:6379'

REDIS_HOST = 'localhost'

REDIS_PORT = 6379

REDIS_PASSWORD = None

REDIS_PARAMS = {
    'db': 0,
}

REDIS_PIPELINE_KEY = '%(spider)s:items'

REDIS_PIPELINE_SERIALIZER = 'scrapy.utils.serialize.ScrapyJSONEncoder'


# REDIS_CLUSTER_URL = ''

# REDIS_CLUSTER_NODES = [
#     {"host": "192.168.223.111", "port": "7001"},
#     {"host": "192.168.223.111", "port": "7002"},
#     {"host": "192.168.223.111", "port": "7003"},
#     {"host": "192.168.223.111", "port": "7004"},
#     {"host": "192.168.223.111", "port": "7005"},
#     {"host": "192.168.223.111", "port": "7006"}
# ]

# REDIS_CLUSTER_PASSWORD = '123456'

# REDIS_CLUSTER_PARAMS = {
#     'socket_timeout': 30,
# }

BLOOMFILTER_HASH_NUMBER = 20

BLOOMFILTER_BIT = 32

BLOOMFILTER_BLOCK_NUM = 2

# Enable or disable extensions
# See https://doc.scrapy.org/en/latest/topics/extensions.html
EXTENSIONS = {
    # 'scrapy.extensions.telnet.TelnetConsole': None,
    'scrapy_redis_bloomfilter_block_cluster.extensions.RedisSpiderSmartIdleClosedExensions': 200,
}

CLOSE_EXT_ENABLED = True
IDLE_NUMBER_BEFORE_CLOSE = 12

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

# Configure item pipelines
# See https://doc.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    'CnblogsSpider.pipelines.CnblogsspiderPipeline': 300,
    'scrapy_redis_bloomfilter_block_cluster.pipelines.RedisPipeline': 200,
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
