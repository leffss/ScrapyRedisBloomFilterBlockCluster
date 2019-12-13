import redis
import rediscluster

# Scheduler default settings
SCHEDULER_PERSIST = True
SCHEDULER_QUEUE_CLASS = 'scrapy_redis_bloomfilter_block_cluster.queue.PriorityQueue'
SCHEDULER_QUEUE_KEY = '%(spider)s:requests'
DUPEFILTER_CLASS = 'scrapy_redis_bloomfilter_block_cluster.dupefilter.RFPDupeFilter'
DUPEFILTER_DEBUG = False
DUPEFILTER_KEY = '%(spider)s:dupefilter'

SCHEDULER_FLUSH_ON_START = False
SCHEDULER_IDLE_BEFORE_CLOSE = 0

# Pipeline default settings
REDIS_PIPELINE_KEY = '%(spider)s:items'
REDIS_PIPELINE_SERIALIZER = 'scrapy.utils.serialize.ScrapyJSONEncoder'

# Redis default settings
REDIS_START_URLS_KEY = '%(spider)s:start_urls'
REDIS_START_URLS_AS_SET = False

REDIS_ENCODING = 'utf-8'
REDIS_PARAMS = {
    'socket_timeout': 30,
    'socket_connect_timeout': 30,
    'retry_on_timeout': True,
    'password': None,
    'encoding': REDIS_ENCODING,
}
REDIS_CLUSTER_PARAMS = {
    'socket_timeout': 30,
    'socket_connect_timeout': 30,
    'retry_on_timeout': True,
    'password': None,
    'encoding': REDIS_ENCODING,
}
REDIS_CLS = redis.Redis
REDIS_CLUSTER_CLS = rediscluster.RedisCluster

# BloomFilter default settings
BLOOMFILTER_HASH_NUMBER = 6
BLOOMFILTER_BIT = 32
BLOOMFILTER_BLOCK_NUM = 1
