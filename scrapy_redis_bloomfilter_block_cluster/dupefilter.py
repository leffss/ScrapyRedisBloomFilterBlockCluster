import logging
import re
from scrapy.dupefilters import BaseDupeFilter
from scrapy.utils.request import request_fingerprint
from . import connection, defaults
from .bloomfilter import BloomFilter

logger = logging.getLogger(__name__)


# TODO: Rename class to RedisDupeFilter.
class RFPDupeFilter(BaseDupeFilter):
    """Redis-based request duplicates filter.

    This class can also be used with default Scrapy's scheduler.

    """
    
    logger = logger
    
    def __init__(self, server, key, debug, bit, hash_number, block_num):
        """Initialize the duplicates filter.

        Parameters
        ----------
        server : redis.Redis
            The redis server instance.
        key : str
            Redis key Where to store fingerprints.
        debug : bool, optional
            Whether to log filtered requests.

        """
        self.server = server
        self.key = key
        self.debug = debug
        self.bit = bit
        self.hash_number = hash_number
        self.block_num = block_num
        self.logdupes = True
        self.bf = BloomFilter(server, self.key, bit, hash_number, block_num)
    
    @classmethod
    def from_settings(cls, settings):
        """Returns an instance from given settings.

        This uses by default the key ``dupefilter:<timestamp>``. When using the
        ``scrapy_redis.scheduler.Scheduler`` class, this method is not used as
        it needs to pass the spider name in the key.

        Parameters
        ----------
        settings : scrapy.settings.Settings

        Returns
        -------
        RFPDupeFilter
            A RFPDupeFilter instance.

        """
        server = connection.from_settings(settings)
        # XXX: This creates one-time key. needed to support to use this
        # class as standalone dupefilter with scrapy's default scheduler
        # if scrapy passes spider on open() method this wouldn't be needed
        # TODO: Use SCRAPY_JOB env as default and fallback to timestamp.
        # key = defaults.DUPEFILTER_KEY % {'timestamp': int(time.time())}
        key = settings.get('DUPEFILTER_KEY', defaults.DUPEFILTER_KEY)
        debug = settings.getbool('DUPEFILTER_DEBUG', defaults.DUPEFILTER_DEBUG)
        bit = settings.getint('BLOOMFILTER_BIT', defaults.BLOOMFILTER_BIT)
        hash_number = settings.getint('BLOOMFILTER_HASH_NUMBER', defaults.BLOOMFILTER_HASH_NUMBER)
        block_num = settings.getint('BLOOMFILTER_BLOCK_NUM', defaults.BLOOMFILTER_BLOCK_NUM)
        return cls(server=server, key=key, debug=debug, bit=bit, hash_number=hash_number, block_num=block_num)
    
    @classmethod
    def from_crawler(cls, crawler):
        """Returns instance from crawler.

        Parameters
        ----------
        crawler : scrapy.crawler.Crawler

        Returns
        -------
        RFPDupeFilter
            Instance of RFPDupeFilter.

        """
        instance = cls.from_settings(crawler.settings)
        # FIXME: for now, stats are only supported from this constructor
        return instance
    
    def request_seen(self, request):
        """Returns True if request was already seen.

        Parameters
        ----------
        request : scrapy.http.Request

        Returns
        -------
        bool

        """
        # scrapy 根据每个请求的 url, method, body, header 生成指纹 fp
        fp = self.request_fingerprint(request)
        # This returns the number of values added, zero if already exists.
        if self.bf.exists(fp):
            return True
        self.bf.insert(fp)
        return False
    
    def request_fingerprint(self, request):
        """Returns a fingerprint for a given request.

        Parameters
        ----------
        request : scrapy.http.Request

        Returns
        -------
        str

        """
        return request_fingerprint(request)
    
    def close(self, reason=''):
        """Delete data on close. Called by Scrapy's scheduler.

        Parameters
        ----------
        reason : str, optional

        """
        self.clear()
    
    def clear(self):
        """Clears fingerprints data."""
        keys = [self.key + str(num) for num in range(self.block_num)]
        self.server.delete(*keys)
    
    def log(self, request, spider):
        """Logs given request.

        Parameters
        ----------
        request : scrapy.http.Request
        spider : scrapy.spiders.Spider

        """
        if self.debug:
            msg = "Filtered duplicate request: %(request)s"
            self.logger.debug(msg, {'request': request}, extra={'spider': spider})
        elif self.logdupes:
            msg = ("Filtered duplicate request %(request)s"
                   " - no more duplicates will be shown"
                   " (see DUPEFILTER_DEBUG to show all duplicates)")
            self.logger.debug(msg, {'request': request}, extra={'spider': spider})
            self.logdupes = False
        spider.crawler.stats.inc_value('bloomfilter/filtered', spider=spider)


class LockRFPDupeFilter(RFPDupeFilter):
    """
    去重时，先加锁，会降低性能，但是可以保证数据正确性
    """
    def __init__(self,  lock_key, lock_num, lock_timeout, **kwargs):
        super().__init__(**kwargs)
        if lock_num <= 16:
            self.lock_value_split_num = 1
        elif 16 < lock_num <= 256:
            self.lock_value_split_num = 2
        else:
            self.lock_value_split_num = 3
        self.lock = list()
        # 初始化 N 把锁，最多 4096，缓解多个 scrapy 实例抢一个锁带来的性能下降问题
        for i in range(0, int('f' * self.lock_value_split_num, 16) + 1):
            self.lock.append(self.server.lock(lock_key + str(i), lock_timeout))

    @classmethod
    def from_settings(cls, settings):
        server = connection.from_settings(settings)
        key = settings.get('DUPEFILTER_KEY', defaults.DUPEFILTER_KEY)
        debug = settings.getbool('DUPEFILTER_DEBUG', defaults.DUPEFILTER_DEBUG)
        bit = settings.getint('BLOOMFILTER_BIT', defaults.BLOOMFILTER_BIT)
        hash_number = settings.getint('BLOOMFILTER_HASH_NUMBER', defaults.BLOOMFILTER_HASH_NUMBER)
        block_num = settings.getint('BLOOMFILTER_BLOCK_NUM', defaults.BLOOMFILTER_BLOCK_NUM)
        lock_key = settings.get('DUPEFILTER_LOCK_KEY', defaults.DUPEFILTER_LOCK_KEY)
        lock_num = settings.getint('DUPEFILTER_LOCK_NUM', defaults.DUPEFILTER_LOCK_NUM)
        lock_timeout = settings.getint('DUPEFILTER_LOCK_TIMEOUT', defaults.DUPEFILTER_LOCK_TIMEOUT)
        return cls(
            server=server, key=key, debug=debug, bit=bit, hash_number=hash_number,
            block_num=block_num, lock_key=lock_key, lock_num=lock_num, lock_timeout=lock_timeout
        )

    def request_seen(self, request):
        fp = self.request_fingerprint(request)
        # 根据 request 生成的 sha1 选择相应的锁
        lock = self.lock[int(fp[0:self.lock_value_split_num], 16)]

        while True:
            if lock.acquire(blocking=False):
                if self.bf.exists(fp):
                    lock.release()
                    return True
                self.bf.insert(fp)
                lock.release()
                return False


class ListLockRFPDupeFilter(LockRFPDupeFilter):
    def __init__(self, rules_list, key_list, bit_list, hash_number_list, block_num_list, **kwargs):
        self.rules_list = rules_list
        self.key_list = key_list
        self.bit_list = bit_list
        self.hash_number_list = hash_number_list
        self.block_num_list = block_num_list
        super().__init__(**kwargs)
        self.bf_list = BloomFilter(self.server, key_list, bit_list, hash_number_list, block_num_list)

    @classmethod
    def from_settings(cls, settings):
        server = connection.from_settings(settings)
        key = settings.get('DUPEFILTER_KEY', defaults.DUPEFILTER_KEY)
        debug = settings.getbool('DUPEFILTER_DEBUG', defaults.DUPEFILTER_DEBUG)
        bit = settings.getint('BLOOMFILTER_BIT', defaults.BLOOMFILTER_BIT)
        hash_number = settings.getint('BLOOMFILTER_HASH_NUMBER', defaults.BLOOMFILTER_HASH_NUMBER)
        block_num = settings.getint('BLOOMFILTER_BLOCK_NUM', defaults.BLOOMFILTER_BLOCK_NUM)
        lock_key = settings.get('DUPEFILTER_LOCK_KEY', defaults.DUPEFILTER_LOCK_KEY)
        lock_num = settings.getint('DUPEFILTER_LOCK_NUM', defaults.DUPEFILTER_LOCK_NUM)
        lock_timeout = settings.getint('DUPEFILTER_LOCK_TIMEOUT', defaults.DUPEFILTER_LOCK_TIMEOUT)

        rules_list = settings.get('DUPEFILTER_RULES_LIST', defaults.DUPEFILTER_RULES_LIST)
        key_list = settings.get('DUPEFILTER_KEY_LIST', defaults.DUPEFILTER_KEY_LIST)
        bit_list = settings.getint('BLOOMFILTER_BIT_LIST', defaults.BLOOMFILTER_BIT_LIST)
        hash_number_list = settings.getint('BLOOMFILTER_HASH_NUMBER_LIST', defaults.BLOOMFILTER_HASH_NUMBER_LIST)
        block_num_list = settings.getint('BLOOMFILTER_BLOCK_NUM_LIST', defaults.BLOOMFILTER_BLOCK_NUM_LIST)

        return cls(
            server=server, key=key, debug=debug, bit=bit, hash_number=hash_number,
            block_num=block_num, lock_key=lock_key, lock_num=lock_num, lock_timeout=lock_timeout,
            rules_list=rules_list, key_list=key_list, bit_list=bit_list,
            hash_number_list=hash_number_list, block_num_list=block_num_list
        )

    def request_seen(self, request):
        """
        列表页去重时不需要加锁
        """
        fp = self.request_fingerprint(request)

        for rule in self.rules_list:
            if re.search(rule, request.url, re.I):
                if self.bf_list.exists(fp):
                    return True
                self.bf_list.insert(fp)
                return False
        else:
            # 根据 request 生成的 sha1 选择相应的锁
            lock = self.lock[int(fp[0:self.lock_value_split_num], 16)]
            while 1:
                if lock.acquire(blocking=False):
                    if self.bf.exists(fp):
                        lock.release()
                        return True
                    self.bf.insert(fp)
                    lock.release()
                    return False
