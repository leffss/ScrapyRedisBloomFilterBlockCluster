import redis
import rediscluster

# For standalone use.
DUPEFILTER_KEY = 'dupefilter:%(timestamp)s'

PIPELINE_KEY = '%(spider)s:items'
BLOOMFILTER_HASH_NUMBER = 6
BLOOMFILTER_BIT = 30
BLOOMFILTER_BLOCK_NUM = 1
DUPEFILTER_DEBUG = False
REDIS_CLS = redis.StrictRedis
REDIS_ENCODING = 'utf-8'
# Sane connection defaults.
REDIS_PARAMS = {
    'socket_timeout': 30,
    'socket_connect_timeout': 30,
    'retry_on_timeout': True,
    'encoding': REDIS_ENCODING,
}

SCHEDULER_QUEUE_KEY = '%(spider)s:requests'
SCHEDULER_QUEUE_CLASS = 'scrapy_redis_bloomfilter_block_cluster.queue.PriorityQueue'
SCHEDULER_DUPEFILTER_KEY = '%(spider)s:dupefilter'
SCHEDULER_DUPEFILTER_CLASS = 'scrapy_redis_bloomfilter_block_cluster.dupefilter.RFPDupeFilter'

START_URLS_KEY = '%(name)s:start_urls'
START_URLS_AS_SET = False
# REDIS_CLUSTER_CLS = rediscluster.StrictRedisCluster   # redis-py-cluster 2.0.0 版本无 StrictRedisCluster
REDIS_CLUSTER_CLS = rediscluster.RedisCluster
