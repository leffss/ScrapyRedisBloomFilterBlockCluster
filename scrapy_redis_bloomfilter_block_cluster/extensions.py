# -*- coding: utf-8 -*-

# Define here the models for your scraped Extensions
import logging
from scrapy import signals
from scrapy.exceptions import NotConfigured
from . import defaults
import traceback

logger = logging.getLogger(__name__)


class RedisSpiderSmartIdleClosedExensions(object):
    def __init__(self, idle_number_before_close, crawler, list_spider=False):
        self.crawler = crawler
        self.idle_number_before_close = idle_number_before_close
        self.idle_count = 0
        self.list_spider = list_spider

    @classmethod
    def from_crawler(cls, crawler):
        # first check if the extension should be enabled and raise
        # NotConfigured otherwise

        if not crawler.settings.getbool('CLOSE_EXT_ENABLED', defaults.CLOSE_EXT_ENABLED):
            raise NotConfigured('CLOSE_EXT_ENABLED setting is False or not configured')
        if 'redis_key' not in crawler.spidercls.__dict__.keys() and 'REDIS_START_URLS_KEY' not in crawler.settings:
            raise NotConfigured('Only supports RedisSpider or RedisCrawlSpider')

        list_spider = False
        if crawler.settings.get('DUPEFILTER_CLASS') == 'scrapy_redis_bloomfilter_block_cluster.dupefilter.ListLockRFPDupeFilter':
            list_spider = True

        # idle_time ≈ idle_number_before_close * 5s
        idle_number_before_close = crawler.settings.getint('IDLE_NUMBER_BEFORE_CLOSE', defaults.IDLE_NUMBER_BEFORE_CLOSE)
        if idle_number_before_close <= 0:
            raise NotConfigured('IDLE_NUMBER_BEFORE_CLOSE setting must > 0')

        # instantiate the extension object
        ext = cls(idle_number_before_close, crawler, list_spider)

        # connect the extension object to signals
        crawler.signals.connect(ext.spider_opened, signal=signals.spider_opened)
        # crawler.signals.connect(ext.spider_closed, signal=signals.spider_closed)
        crawler.signals.connect(ext.spider_idle, signal=signals.spider_idle)
        crawler.signals.connect(ext.request_scheduled, signal=signals.request_scheduled)
        # return the extension object
        return ext

    def spider_opened(self, spider):
        logger.info("Opened spider %s, continuous idle limit: %d times", spider.name, self.idle_number_before_close)

    def spider_closed(self, spider):
        logger.info("Closed spider %s, idle %d times", spider.name, self.idle_number_before_close)

    def spider_idle(self, spider):
        self.idle_count += 1
        # 判断 redis 中是否存在 start urls key, 如果 key 被用完，则 key 就会不存在
        if self.idle_count > self.idle_number_before_close and not spider.server.exists(spider.redis_key):
            # 关闭爬虫前删除列表页去重 key
            if self.list_spider:
                key_list = self.crawler.settings.get('DUPEFILTER_KEY_LIST', defaults.DUPEFILTER_KEY_LIST) % {'spider': spider.name}
                block_num_list = self.crawler.settings.getint('BLOOMFILTER_BLOCK_NUM_LIST', defaults.BLOOMFILTER_BLOCK_NUM_LIST)
                keys_list = [key_list + str(num) for num in range(block_num_list)]
                logger.info("delete spider %s list bloomfilter key: %s", spider.name, ','.join(keys_list))
                try:
                    spider.server.delete(*keys_list)
                except Exception:
                    logger.error(traceback.format_exc())
            # 执行关闭爬虫操作
            self.crawler.engine.close_spider(spider, 'Close spider after idle {} times'.format(self.idle_number_before_close))

    def request_scheduled(self, spider):
        self.idle_count = 0
        # logger.info("spider %s redis spider Idle Num set to 0", spider.name)
