import importlib
import six

from scrapy.utils.misc import load_object

from . import connection, defaults


# TODO: add SCRAPY_JOB support.
class Scheduler(object):
    """Redis-based scheduler

    Settings
    --------
    SCHEDULER_PERSIST : bool (default: False)
        Whether to persist or clear redis queue.
    SCHEDULER_FLUSH_ON_START : bool (default: False)
        Whether to flush redis queue on start.
    SCHEDULER_IDLE_BEFORE_CLOSE : int (default: 0)
        How many seconds to wait before closing if no message is received.
    SCHEDULER_QUEUE_KEY : str
        Scheduler redis key.
    SCHEDULER_QUEUE_CLASS : str
        Scheduler queue class.
    DUPEFILTER_KEY : str
        Scheduler dupefilter redis key.
    DUPEFILTER_CLASS : str
        Scheduler dupefilter class.
    SCHEDULER_SERIALIZER : str
        Scheduler serializer.

    """
    
    def __init__(self, server, persist, flush_on_start, queue_key, queue_cls, dupefilter_key, dupefilter_cls, idle_before_close):
        """Initialize scheduler.

        Parameters
        ----------
        server : Redis
            The redis server instance.
        persist : bool
            Whether to flush requests when closing. Default is False.
        flush_on_start : bool
            Whether to flush requests on start. Default is False.
        queue_key : str
            Requests queue key.
        queue_cls : str
            Importable path to the queue class.
        dupefilter_key : str
            Duplicates filter key.
        dupefilter_cls : str
            Importable path to the dupefilter class.
        idle_before_close : int
            Timeout before giving up.

        """
        if idle_before_close < 0:
            raise TypeError("idle_before_close cannot be negative")
        
        self.server = server
        self.persist = persist
        self.flush_on_start = flush_on_start
        self.queue_key = queue_key
        self.queue_cls = queue_cls
        self.dupefilter_cls = dupefilter_cls
        self.dupefilter_key = dupefilter_key
        self.idle_before_close = idle_before_close
        self.stats = None
    
    def __len__(self):
        return len(self.queue)
    
    @classmethod
    def from_settings(cls, settings):
        kwargs = {
            'persist': defaults.SCHEDULER_PERSIST,
            'flush_on_start': defaults.SCHEDULER_FLUSH_ON_START,
            'queue_key': defaults.SCHEDULER_QUEUE_KEY,
            'queue_cls': defaults.SCHEDULER_QUEUE_CLASS,
            'dupefilter_cls': defaults.DUPEFILTER_CLASS,
            'dupefilter_key': defaults.DUPEFILTER_KEY,
            'idle_before_close': defaults.SCHEDULER_IDLE_BEFORE_CLOSE,
        }

        optional = {
            'SCHEDULER_PERSIST': 'persist',
            'SCHEDULER_FLUSH_ON_START': 'flush_on_start',
            'SCHEDULER_QUEUE_KEY': 'queue_key',
            'SCHEDULER_QUEUE_CLASS': 'queue_cls',
            'DUPEFILTER_CLASS': 'dupefilter_cls',
            'DUPEFILTER_KEY': 'dupefilter_key',
            'SCHEDULER_IDLE_BEFORE_CLOSE': 'idle_before_close',
        }

        for setting_name, name in optional.items():
            val = settings.get(setting_name)
            if val:
                kwargs[name] = val

        server = connection.from_settings(settings)
        return cls(server=server, **kwargs)
    
    @classmethod
    def from_crawler(cls, crawler):
        instance = cls.from_settings(crawler.settings)
        # FIXME: for now, stats are only supported from this constructor
        instance.stats = crawler.stats
        return instance
    
    def open(self, spider):
        self.spider = spider

        try:
            self.queue = load_object(self.queue_cls)(
                server=self.server,
                spider=spider,
                key=self.queue_key % {'spider': spider.name}
            )
        except TypeError as e:
            raise ValueError("Failed to instantiate queue class '%s': %s",
                             self.queue_cls, e)
        
        try:
            if self.dupefilter_cls == 'scrapy_redis_bloomfilter_block_cluster.dupefilter.LockRFPDupeFilter':
                self.df = load_object(self.dupefilter_cls)(
                    server=self.server,
                    key=self.dupefilter_key % {'spider': spider.name},
                    debug=spider.settings.getbool('DUPEFILTER_DEBUG', defaults.DUPEFILTER_DEBUG),
                    bit=spider.settings.getint('BLOOMFILTER_BIT', defaults.BLOOMFILTER_BIT),
                    hash_number=spider.settings.getint('BLOOMFILTER_HASH_NUMBER', defaults.BLOOMFILTER_HASH_NUMBER),
                    block_num=spider.settings.getint('BLOOMFILTER_BLOCK_NUM', defaults.BLOOMFILTER_BLOCK_NUM),
                    lock_key=spider.settings.get('DUPEFILTER_LOCK_KEY', defaults.DUPEFILTER_LOCK_KEY) % {'spider': spider.name},
                    lock_num=spider.settings.getint('DUPEFILTER_LOCK_NUM', defaults.DUPEFILTER_LOCK_NUM),
                    lock_timeout=spider.settings.getint('DUPEFILTER_LOCK_TIMEOUT', defaults.DUPEFILTER_LOCK_TIMEOUT)
                )
            elif self.dupefilter_cls == 'scrapy_redis_bloomfilter_block_cluster.dupefilter.ListLockRFPDupeFilter':
                self.df = load_object(self.dupefilter_cls)(
                    server=self.server,
                    key=self.dupefilter_key % {'spider': spider.name},
                    debug=spider.settings.getbool('DUPEFILTER_DEBUG', defaults.DUPEFILTER_DEBUG),
                    bit=spider.settings.getint('BLOOMFILTER_BIT', defaults.BLOOMFILTER_BIT),
                    hash_number=spider.settings.getint('BLOOMFILTER_HASH_NUMBER', defaults.BLOOMFILTER_HASH_NUMBER),
                    block_num=spider.settings.getint('BLOOMFILTER_BLOCK_NUM', defaults.BLOOMFILTER_BLOCK_NUM),
                    lock_key=spider.settings.get('DUPEFILTER_LOCK_KEY', defaults.DUPEFILTER_LOCK_KEY) % {'spider': spider.name},
                    lock_num=spider.settings.getint('DUPEFILTER_LOCK_NUM', defaults.DUPEFILTER_LOCK_NUM),
                    lock_timeout=spider.settings.getint('DUPEFILTER_LOCK_TIMEOUT', defaults.DUPEFILTER_LOCK_TIMEOUT),
                    rules_list=spider.rules_list,
                    key_list=spider.settings.get('DUPEFILTER_KEY_LIST', defaults.DUPEFILTER_KEY_LIST) % {'spider': spider.name},
                    bit_list=spider.settings.getint('BLOOMFILTER_BIT_LIST', defaults.BLOOMFILTER_BIT_LIST),
                    hash_number_list=spider.settings.getint('BLOOMFILTER_HASH_NUMBER_LIST', defaults.BLOOMFILTER_HASH_NUMBER_LIST),
                    block_num_list=spider.settings.getint('BLOOMFILTER_BLOCK_NUM_LIST', defaults.BLOOMFILTER_BLOCK_NUM_LIST)
                )
            else:
                self.df = load_object(self.dupefilter_cls)(
                    server=self.server,
                    key=self.dupefilter_key % {'spider': spider.name},
                    debug=spider.settings.getbool('DUPEFILTER_DEBUG', defaults.DUPEFILTER_DEBUG),
                    bit=spider.settings.getint('BLOOMFILTER_BIT', defaults.BLOOMFILTER_BIT),
                    hash_number=spider.settings.getint('BLOOMFILTER_HASH_NUMBER', defaults.BLOOMFILTER_HASH_NUMBER),
                    block_num=spider.settings.getint('BLOOMFILTER_BLOCK_NUM', defaults.BLOOMFILTER_BLOCK_NUM)
                )
        except TypeError as e:
            raise ValueError("Failed to instantiate dupefilter class '%s': %s",
                             self.dupefilter_cls, e)
        
        if self.flush_on_start:
            self.flush()
            
        # notice if there are requests already in the queue to resume the crawl
        if len(self.queue):
            spider.log("Resuming crawl from redis(%d requests scheduled)" % len(self.queue))
    
    def close(self, reason):
        if not self.persist:
            self.flush()
    
    def flush(self):
        self.df.clear()
        self.queue.clear()
    
    def enqueue_request(self, request):
        if not request.dont_filter and self.df.request_seen(request):
            self.df.log(request, self.spider)
            return False
        if self.stats:
            self.stats.inc_value('scheduler/enqueued/redis', spider=self.spider)
        self.queue.push(request)
        return True
    
    def next_request(self):
        request = self.queue.pop(self.idle_before_close)     # PriorityQueue 不支持 self.idle_before_close
        if request and self.stats:
            self.stats.inc_value('scheduler/dequeued/redis', spider=self.spider)
        return request
    
    def has_pending_requests(self):
        return len(self) > 0
