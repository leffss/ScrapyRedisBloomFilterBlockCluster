# ScrapyRedisBloomFilterBlockCluster
ScrapyRedisBloomFilterBlockCluster 基于 scrapy-redis + bloomfilter 算法去重，支持分配多个 redis 内存块（1个最大 512MB），并且支持 redis 单机和 redis-cluster 集群，适用于超大型分布式 scrapy 爬虫。
本项目基于以下项目修改：
https://github.com/rmax/scrapy-redis

https://github.com/Python3WebSpider/ScrapyRedisBloomFilter

https://github.com/thsheep/scrapy_redis_cluster

https://github.com/LiuXingMing/Scrapy_Redis_Bloomfilter


支持 python 版本 3.7+

## 安装

使用 pip:
```
pip install scrapy-redis-bloomfilter-block-cluster
```
- 依赖： twisted==19.10.0, scrapy==1.8.0,  redis-py-cluster==2.0.0, redis==3.0.1

## 使用方法

添加响应配置到 scrapy 爬虫 settings.py中

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

## 示例

### 下载 demo 并启动
```
$ git clone https://github.com/leffss/ScrapyRedisBloomFilterBlockCluster.git
$ cd ScrapyRedisBloomFilterBlockCluster/demo
$ scrapy crawl cnblogs
```
- redis 环境需提前准备好

### redis 中设置 start_urls

redis 单机版
```
$ redis-cli
redis 127.0.0.1:6379> lpush cnblogs:start_urls https://www.cnblogs.com/sitehome/p/1
```

redis-cluster 版本
```
$ redis-cli -c
redis 127.0.0.1:7001> lpush cnblogs:start_urls https://www.cnblogs.com/sitehome/p/1
```

注意：请在 settings.py 设置正确的 REDIS_URL 或者 REDIS_MASTER_NODES
