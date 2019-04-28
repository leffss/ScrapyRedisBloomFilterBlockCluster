# ScrapyRedisBloomFilterBlockCluster
Scrapy Redis with Bloom Filter and support redis cluster

Base on: 

https://github.com/rmax/scrapy-redis

https://github.com/Python3WebSpider/ScrapyRedisBloomFilter

https://github.com/thsheep/scrapy_redis_cluster

https://github.com/LiuXingMing/Scrapy_Redis_Bloomfilter

## Installation

You can easily install this package with pip:

```
pip install scrapy-redis-bloomfilter-block-cluster
```

## Usage

Add this settings to settings.py

```python
# Ensure use this Scheduler
SCHEDULER = "scrapy_redis_bloomfilter_block_cluster.scheduler.Scheduler"

# Persist
SCHEDULER_PERSIST = True

# Ensure all spiders share same duplicates filter through redis
DUPEFILTER_CLASS = "scrapy_redis_bloomfilter_block_cluster.dupefilter.RFPDupeFilter"

# queue
SCHEDULER_QUEUE_CLASS = 'scrapy_redis_bloomfilter_block_cluster.queue.PriorityQueue'

# Redis URL
#REDIS_URL = 'redis://:admin123@localhost:6379' # or redis://localhost:6379
#REDIS_HOST = 'localhost'
#REDIS_PORT = 6379

# Redis cluster, if REDIS_MASTER_NODES is set, REDIS_URL do not work.
REDIS_MASTER_NODES = [
    {"host": "localhost", "port": "7001"},
    {"host": "localhost", "port": "7002"},
    {"host": "localhost", "port": "7003"}
]

# Number of Hash Functions to use, defaults to 6
BLOOMFILTER_HASH_NUMBER = 6

# Redis Memory Bit of Bloomfilter Usage, 30 means 2^30 = 128MB, defaults to 30
BLOOMFILTER_BIT = 30

# Number of Block for Bloomfilter Usage, one Block can use maximum Memory 512MB
BLOOMFILTER_BLOCK_NUM = 1

DUPEFILTER_DEBUG = True
```

## Test

Here is a test of this project, usage: 
```
$ git clone https://github.com/leffss/ScrapyRedisBloomFilterBlockCluster.git
$ cd ScrapyRedisBloomFilterBlockCluster/demo
$ scrapy crawl tencent
```
redis-cli input start_urls
```
$ redis-cli
redis 127.0.0.1:6379> lpush tencent:start_urls https://hr.tencent.com/position.php?&start=0#a
```
or cluster
```
$ redis-cli -c
redis 127.0.0.1:7001> lpush tencent:start_urls https://hr.tencent.com/position.php?&start=0#a
```

Note: please change REDIS_URL or REDIS_MASTER_NODES in settings.py.
