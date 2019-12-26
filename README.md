# ScrapyRedisBloomFilterBlockCluster
ScrapyRedisBloomFilterBlockCluster 基于 scrapy-redis + bloomfilter 算法去重，支持分配多个 Redis 内存块（ Redis 1个 string 最大 512MB），并且支持 Redis 单机，Redis Sentinel 和 Redis-Cluster 集群，适用于超大型分布式 scrapy 爬虫。
本项目基于以下项目修改：

https://github.com/rmax/scrapy-redis

https://github.com/Python3WebSpider/ScrapyRedisBloomFilter

https://github.com/thsheep/scrapy_redis_cluster

https://github.com/LiuXingMing/Scrapy_Redis_Bloomfilter


支持 python 版本 3.7+，并且 scrapy 爬虫 demo 在单机 Redis 3.2.100，Redis Sentinel 5.0.5 以及集群 Redis Cluster 5.0.7 测试通过。

## 安装

使用 pip:
```
pip install scrapy-redis-bloomfilter-block-cluster
```
- 依赖： twisted==19.10.0, scrapy==1.8.0,  redis-py-cluster==2.0.0, redis==3.0.1

## 使用方法

### 添加适当的配置到 scrapy 爬虫 settings.py 中

以下为支持的所有配置：
```python
# 开启 scrapy_redis_bloomfilter_block_cluster，必须配置
SCHEDULER = "scrapy_redis_bloomfilter_block_cluster.scheduler.Scheduler"

# -------------------------------- Scheduler 配置 --------------------------------
SCHEDULER_PERSIST = True	# 是否持久化，True 则退出时不会删除种子队列和去重队列，默认 True

# 种子队列类，支持 FifoQueue（先进先出）, LifoQueue（先进后出）, PriorityQueue（优先级） or 
# SimpleQueue（简化版先进先出），默认 FifoQueue
SCHEDULER_QUEUE_CLASS = 'scrapy_redis_bloomfilter_block_cluster.queue.FifoQueue'

# 种子队列 key，用于保存 scrapy 待请求 Request 对象（序列化），默认 %(spider)s:requests，其中
# %(spider)s 表示当前爬虫名称
SCHEDULER_QUEUE_KEY = '%(spider)s:requests'

# 去重类，可以是 RFPDupeFilter，LockRFPDupeFilter 或者 ListLockRFPDupeFilter，后 2 个在使用
# BloomFilter 判断时会加锁以确保准确性，但是性能大概会降低 30% 左右，推荐分布式爬虫使用
# 这里特别说明一下 ListLockRFPDupeFilter 的作用。实际在写爬虫的过程中，可能会遇到这类问题：比如
# 爬取一个新闻咨询类网站的具体新闻内容，网站结构是列表页 /page/1，/page/2，...，每个列表页都存放
# 了固定条数的新闻链接，现在爬虫需要通过列表页去提取新闻链接，然后再进一步获取到新闻内容。如果此爬
# 虫是个一次性爬虫就没什么问题，如果想增量爬取问题就来了：虽然 /page/1 包含的新闻链接在第二次增量
# 爬取时变更了，但是因为第一次爬取时已经把 /page/1 加入 bloomfilter 去重了，第二次爬取时肯定无法
# 再次爬取/page/1 了，也就是无法获取最新的新闻链接了。ListLockRFPDupeFilter 就是为解决这个而产生
# 的，原理是把列表页 /page/1，/page/2，...单独存放到一个临时的去重实例，其他新闻页放另外一个去重
# 实例，当一次爬取完成退出时，删除存放列表页去重的 redis key 即可，这样子就可以在下一次爬取时又可以
# 爬取 /page/1 了，并且还不会重复爬取前面已经爬取过的新闻。需要注意的点是：默认情况下，在没有新的 url
# 爬取时，爬虫会一直循环等待新的请求队列，不退出，也就是无法删除存放列表页去重的 redis key，所以当
# 使用 ListLockRFPDupeFilter 去重类时必须开启智能退出扩展，具体参考后面的：智能退出爬虫扩展设置。
DUPEFILTER_CLASS = 'scrapy_redis_bloomfilter_block_cluster.dupefilter.LockRFPDupeFilter'

DUPEFILTER_DEBUG = False	# 去重是否显示详细 debug 信息，默认 False

DUPEFILTER_KEY = '%(spider)s:dupefilter'    # 去重 key，用于 bloomfilter 算法去重

# 当使用 ListLockRFPDupeFilter 去重类时，第二个去重 key
DUPEFILTER_KEY_LIST = '%(spider)s:dupefilter_list'

# 当使用 ListLockRFPDupeFilter 去重类时，满足以下条件时会使用第二个去重实例
# 设置为 list 类型的正则表达式，优先级低于项目编写的 spider 类中设置的变量: rules_list
DUPEFILTER_RULES_LIST = []

# Redis BloomFilter 锁需要的 key 与超时时间，去重类使用 LockRFPDupeFilter 或者 ListLockRFPDupeFilter 时有效
# 使用 ListLockRFPDupeFilter 时，第二个去重实例不会使用锁
DUPEFILTER_LOCK_KEY = '%(spider)s:lock'

DUPEFILTER_LOCK_NUM = 16    # Redis bloomfilter 锁个数，可以设置值：16，256，4096

DUPEFILTER_LOCK_TIMEOUT = 15

# 启动时是否先删除种子队列 key 与 去重 key，分布式爬虫时谨慎设置，默认 False
SCHEDULER_FLUSH_ON_START = False

# -------------------------------- 智能退出爬虫扩展设置 --------------------------------
# 默认没有新的 url 爬取时会一直循环等待新的请求队列，不退出，如果需要退出可以加入以下配置:
EXTENSIONS = {
    # ...其他扩展
    'scrapy_redis_bloomfilter_block_cluster.extensions.RedisSpiderSmartIdleClosedExensions': 300,
    # ...其他扩展
}

CLOSE_EXT_ENABLED = True    # 是否启用智能退出扩展，默认 True

# 运行连续空闲次数（scrapy 的一个空闲周期 5s 左右，空闲总时间则约等于 IDLE_NUMBER_BEFORE_CLOSE * 5s）退出，
# 大于 0 的整数，默认 360
IDLE_NUMBER_BEFORE_CLOSE = 360 

# -------------------------------- Redis Pipeline 设置 --------------------------------
# 保存爬取的数据到 Redis:
ITEM_PIPELINES = {
    # ...其他 pipeline
    'scrapy_redis_bloomfilter_block_cluster.pipelines.RedisPipeline': 300,
    # ...其他 pipeline
}

REDIS_PIPELINE_KEY = '%(spider)s:items'   # 保存结果数据 key

# 保存结果数据使用的序列化类，类必须有 encode 方法
REDIS_PIPELINE_SERIALIZER = 'scrapy.utils.serialize.ScrapyJSONEncoder'

# -------------------------------- Redis 设置 --------------------------------
# start_urls key，优先级低于项目编写的 spider 类中设置的变量: redis_key
REDIS_START_URLS_KEY = '%(spider)s:start_urls'

# start urls key 是否使用 set（可以排重）。使用 list 时 redis 中插入 start_urls: 
# lpush [REDIS_START_URLS_KEY] [start_urls]；使用 set 时 redis 中插入 start_urls: 
# sadd [REDIS_START_URLS_KEY] [start_urls]，默认 False，使用 list
REDIS_START_URLS_AS_SET = False

# 是否在启动时自动向 redis 中插入 start_urls，优先级低于项目编写的 spider 类中设置的变量: auto_insert，
# 当为 True 时，spider 类必须包含 start_urls 列表变量，默认 True
REDIS_START_URLS_AUTO_INSERT = True

REDIS_ENCODING = 'utf-8'	# redis 编码，默认 utf-8

# -------------------------------- redis 单机连接设置 --------------------------------
# 共两种连接方式， REDIS_URL 的优先级是高于 REDIS_HOST + REDIS_PORT 的
# REDIS_URL = 'redis://localhost:6379/0'	# 单机 url ，有密码验证时：redis://:admin123@localhost:6379/0

REDIS_HOST = 'localhost'	# 单机地址

REDIS_PORT = 6379		# 单机端口

REDIS_PASSWORD = None	# 单机密码，None 表示无密码

REDIS_PARAMS = {	# 单机连接参数设置，具体支持的参数参考 redis-py 库连接参数
    'socket_timeout': 30,
    'socket_connect_timeout': 30,
    'db': 0,
    # ...其他参数
}

# -------------------------------- redis sentinel 集群连接设置 --------------------------------
# REDIS_SENTINEL_NODES = [
#     ('localhost', 26379),
#     ('localhost', 26380),
#     ('localhost', 26381)
# ]		# sentinel 集群节点

# REDIS_SENTINEL_SERVICE_NAME = 'mymaster'  # sentinel 服务名
# REDIS_SENTINEL_PASSWORD = '123456'		# sentinel 密码

# REDIS_SENTINEL_PARAMS = {	# sentinel 集群连接参数设置，具体支持的参数参考 redis-py 库连接参数
#     'socket_timeout': 30,
#     'socket_connect_timeout': 30,
#     'retry_on_timeout': True,
#     'db': 0,
#     # ...其他参数
# }

# -------------------------------- redis 集群连接设置 --------------------------------
# 共两种连接方式， REDIS_CLUSTER_URL 的优先级是高于 REDIS_CLUSTER_NODES 的
# REDIS_CLUSTER_URL = 'redis://localhost:7001/'		# 没试过，不正确是不是这样设置

#REDIS_CLUSTER_NODES = [
#    {"host": "localhost", "port": "7001"},
#    {"host": "localhost", "port": "7002"},
#    {"host": "localhost", "port": "7003"},
#    {"host": "localhost", "port": "7004"},
#    {"host": "localhost", "port": "7005"},
#    {"host": "localhost", "port": "7006"}
#]		# 集群所有可用节点

# REDIS_CLUSTER_PASSWORD = '123456'		# 集群密码

# REDIS_CLUSTER_PARAMS = {	# 集群连接参数设置，具体支持的参数参考 redis-py-cluster 库连接参数
#     'socket_timeout': 30,
#     'socket_connect_timeout': 30,
#     'retry_on_timeout': True,
#     # ...其他参数
# }

# 注意：redis 连接优先级：集群 > 哨兵 > 单机

# -------------------------------- BloomFilter 过滤算法设置 --------------------------------
BLOOMFILTER_HASH_NUMBER = 15		# hash 函数个数，越多误判率越小，但是越慢，默认 15

# BIT 位数，设置 32 即 2^32，受限于 redis string 类型最大容量，最大 2^32，默认 32
BLOOMFILTER_BIT = 32

# 分配 redis string 数量，设置更高则支持的排重元素就越多，占用 redis 资源越多，最大 4096，默认 1
BLOOMFILTER_BLOCK_NUM = 1		

# 当使用 ListLockRFPDupeFilter 去重类时，第二个去重 BloomFilter 过滤算法设置
BLOOMFILTER_HASH_NUMBER_LIST = 15

BLOOMFILTER_BIT_LIST = 32

BLOOMFILTER_BLOCK_NUM_LIST = 1

# 实际使用中根据爬虫需要排重的 url 量合理设置

```

### 修改 spider
具体参考示例。


## 示例

### 下载 demo 并启动
```
$ git clone https://github.com/leffss/ScrapyRedisBloomFilterBlockCluster.git
$ cd ScrapyRedisBloomFilterBlockCluster/demo
$ scrapy crawl cnblogs
```
- redis 环境需提前准备好

### redis 中添加 start_urls

redis 单机 & Sentinel 版本
```
$ redis-cli
redis 127.0.0.1:6379> lpush cnblogs:start_urls https://www.cnblogs.com/sitehome/p/1
```

redis-cluster 版本
```
$ redis-cli -c
redis 127.0.0.1:7001> lpush cnblogs:start_urls https://www.cnblogs.com/sitehome/p/1
```

- 如果设置 auto_insert = True 或者 REDIS_START_URLS_AUTO_INSERT = True，则不需要以上操作，具体参考前面的配置说明

## 补充
BloomFilter 如何根据去重的数量 (n) 和错误率 (p) 得到最优的位数组大小 (m) 和哈希函数个数 (k) ，以及需要多少内存 (mem)，需要多少个 Redis 512M 的内存块 (block_num)，方法如下：
```python
from scrapy_redis_bloomfilter_block_cluster.bloomfilter import calculation_bloom_filter

n = 100000000   # 去重数量 1 亿 
p = 0.000001     # 错误率 100 万分之一
m, k, mem, block_num = calculation_bloom_filter(n, p)
print(m, k, mem, block_num)

```
- 位数组大小为 2875517514 (28亿)，哈希函数个数为 20，内存 343 MB，1 个 Redis String 内存块
- 从结果来看，占用内存资源并不多，但是哈希函数个数较多，故最影响 BloomFilter 去重性能的还是哈希函数的质量
