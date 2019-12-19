# -*- coding: utf-8 -*-

from hashlib import md5
import mmh3
import math


class HashMapOld:
    """
    返回字符串 hash 出来的 offset (整数)，范围 0 - self.m
    """
    def __init__(self, m, seed):
        self.m = m
        self.seed = seed
    
    def hash(self, value):
        ret = 0
        for i in range(len(value)):
            ret += self.seed * ret + ord(value[i])
        return (self.m - 1) & ret


class HashMap:
    """
    使用 murmurhash3，C 模块性能更好
    返回字符串 hash 出来的 offset (整数)，范围 0 - self.m，最大范围 0 - (2^32 - 1)
    """

    def __init__(self, m, seed):
        self.m = m
        self.seed = seed

    def hash(self, value):
        return mmh3.hash(value, self.seed, signed=False) % self.m


def calculation_bloom_filter(n, p):
    """
    根据 https://www.jianshu.com/p/c3ed818f9531 中描述，这个计算比 calculation_bloom_filter_old 好像要准确点
    通过数据量和期望的误报率 计算出 位数组大小 和 哈希函数的数量
    k为哈希函数个数    m为位数组大小
    n为数据量          p为误报率
    m = - (nlnp)/(ln2)^2
    k = (m/n) ln2
    """
    m = - (n * (math.log(p, math.e)) / (math.log(2, math.e))**2)
    k = m / n * math.log(2, math.e)
    mem = math.ceil(m / 8 / 1024 / 1024)  # 需要的多少 M 内存
    block_num = math.ceil(mem / 512)  # 需要多少个 Redis 512M 的内存块
    return math.ceil(m), math.ceil(k), mem, block_num


class BloomFilter:
    """
    基于 redis 的 BloomFilter 去重，原理简单点说就是有几个 seeds（hash 函数），然后申请一段内存空间
    ，一个 seed 可以和字符串哈希映射到这段内存上的一个位，几个位都为 1 即表示该字符串已经存在。插入的
    时候也是，将映射出的几个位都置为 1。根据去重数量适当地调整 seeds 的数量和 block_num 数量 seeds 数
    量越少去重速度越快，但漏失率越大;block_num 数量越大，占用 redis 内存越高，去重的数据量越大
    BloomFilter 之所以能做到在时间和空间上的效率比较高，是因为牺牲了判断的准确率、删除的便利性:
    1. 存在误判，可能要查到的元素并没有在容器中，但是 hash 之后得到的k个位置上值都是1。对于爬虫来说就是
    可能会少抓取一些页面，可以容忍。
    2. 删除困难。一个放入容器的元素映射到 bit 数组的 k 个位置上是 1，删除的时候不能简单的直接置为 0，
    可能会影响其他元素的判断。如果有删除需求可以查阅 Counting Bloom Filter 实现删除。
    其他类似有布谷鸟过滤器。
    """
    SEEDS = [543, 460, 171, 876, 796, 607, 650, 81, 837, 545, 591, 946, 846, 521, 913, 636, 878, 735, 414, 372,
             344, 324, 223, 180, 327, 891, 798, 933, 493, 293, 836, 10, 6, 544, 924, 849, 438, 41, 862, 648, 338,
             465, 562, 693, 979, 52, 763, 103, 387, 374, 349, 94, 384, 680, 574, 480, 307, 580, 71, 535, 300, 53,
             481, 519, 644, 219, 686, 236, 424, 326, 244, 212, 909, 202, 951, 56, 812, 901, 926, 250, 507, 739, 371,
             63, 584, 154, 7, 284, 617, 332, 472, 140, 605, 262, 355, 526, 647, 923, 199, 518]

    def __init__(self, server, key, bit, hash_number, block_num):
        self.m = 1 << bit if bit <= 32 else 1 << 32   # redis string 最大 512MB，即 2^32
        # self.seeds = range(hash_number)
        self.seeds = self.SEEDS[0:hash_number] if hash_number < 100 else self.SEEDS
        self.server = server
        self.key = key
        self.block_num = block_num
        self.value_split_num = 2
        # 截取 value 位数以确定使用哪一个 Redis Block，位数越大能够支持的 block_num 越大
        # 因为 value 是 scrapy 经过哈希过的 sha1 值，故
        # 1 时最大能够使用的 block_num 为 16
        # 2 时最大能够使用的 block_num 为 256
        # 3 时最大能够使用的 block_num 为 4096
        # 增加 1 则，则最大能够使用的 block_num 增加 16 倍
        if block_num > 256:
            self.value_split_num = 3    # 最大截取三位，则 block_num 最高 4096，再高也没有意义
        self.maps = [HashMap(self.m, seed) for seed in self.seeds]
    
    def exists(self, value):
        """
        代码中使用了 MD5 加密压缩，将字符串压缩到了 32 个字符（也可用 hashlib.sha1() 压缩成 40 个字符，更不容易重复，
        hashlib 中还有更多加强版的 hash 加密函数）。它有两个作用，一是 Bloomfilter 对一个很长的字符串哈希映射的时候会出错，
        经常误判为已存在，压缩后就不再有这个问题；二是压缩后的字符为 0~f 共 16 中可能，我截取了前两个字符，再根据
        block_num 将字符串指定到不同的去重块进行去重
        """
        if not value:
            return False
        # scrapy 传递过来的 value 本身已经 sha1 过了
        # m5 = md5()
        # m5.update(value.encode('utf-8'))
        # value = m5.hexdigest()
        # 16 进制转 int，故不管 block_num 取多大，求出 string 个数都会受 self.value_split_num 限制
        redis_dupefilter_name = self.key + str(int(value[0:self.value_split_num], 16) % self.block_num)
        with self.server.pipeline() as pipe:
            for map in self.maps:
                offset = map.hash(value)
                pipe.getbit(redis_dupefilter_name, offset)
            decides = pipe.execute()
            for decide in decides:
                # 所有的 seed 都命中（即 self.server.getbit(redis_dupefilter_name, offset) 返回 1）时才判断为存在
                # exist = exist & decide
                if decide == 0:
                    return False
        return True
        
    def insert(self, value):
        redis_dupefilter_name = self.key + str(int(value[0:self.value_split_num], 16) % self.block_num)
        with self.server.pipeline() as pipe:
            for map in self.maps:
                offset = map.hash(value)
                pipe.setbit(redis_dupefilter_name, offset, 1)
            pipe.execute()


class BloomFilterNew(BloomFilter):
    """
    此版本根据去重数量和错误率计算相应的 bit ，hash_number, block_num
    """
    def __init__(self, server, key, capacity=100000000, error_rate=0.00001):
        bit, hash_number, mem, block_num = calculation_bloom_filter(capacity, error_rate)
        super().__init__(server, key, bit, hash_number, block_num)


class CountBloomFilter:
    """
    Counting Bloom Filter 实现了删除，由 Bloom Filter 的 bit 存储变更为 key 存储
    会占用更多的 redis 内存空间，以空间换取了删除功能，其中 self.m 不再受 redis 
    string 最大 512MB 的限制，只受 redis 能够设置多少 key 的限制，官方 FAQ 理论上
    是 2^32 （40 亿），但是经过验证单实例最少支持 2.5 亿个 key，相比一个 string 40 
    亿的 bit 位有点小，所以这个实现仅供参考。
    """
    SEEDS = [543, 460, 171, 876, 796, 607, 650, 81, 837, 545, 591, 946, 846, 521, 913, 636, 878, 735, 414, 372,
             344, 324, 223, 180, 327, 891, 798, 933, 493, 293, 836, 10, 6, 544, 924, 849, 438, 41, 862, 648, 338,
             465, 562, 693, 979, 52, 763, 103, 387, 374, 349, 94, 384, 680, 574, 480, 307, 580, 71, 535, 300, 53,
             481, 519, 644, 219, 686, 236, 424, 326, 244, 212, 909, 202, 951, 56, 812, 901, 926, 250, 507, 739, 371,
             63, 584, 154, 7, 284, 617, 332, 472, 140, 605, 262, 355, 526, 647, 923, 199, 518]

    value_split_num = 3

    def __init__(self, server, key, bit, hash_number, block_num):
        self.m = 1 << bit if bit <= 32 else 1 << 32   # Counting Bloom Filter 中已不受 redis string 最大 512MB，即 2^32 的限制，这里懒得改而已
        self.seeds = self.SEEDS[0:hash_number] if hash_number < 100 else self.SEEDS
        self.server = server
        self.key = key
        self.block_num = block_num
        self.maps = [HashMap(self.m, seed) for seed in self.seeds]

    def exists(self, value):
        if not value:
            return False
        # scrapy 传递过来的 value 本身已经 sha1 过了
        m5 = md5()
        m5.update(value.encode('utf-8'))
        value = m5.hexdigest()
        redis_dupefilter_name = self.key + str(int(value[0:self.value_split_num], 16) % self.block_num)
        with self.server.pipeline() as pipe:
            for map in self.maps:
                offset = map.hash(value)
                pipe.get(redis_dupefilter_name + str(offset))
            decides = pipe.execute()
            for decide in decides:
                if not decide or int(decide.decode('utf-8')) <= 0:
                    return False
        return True

    def insert(self, value):
        if not self.exists(value):
            # m5 = md5()
            # m5.update(value.encode('utf-8'))
            # value = m5.hexdigest()
            redis_dupefilter_name = self.key + str(int(value[0:self.value_split_num], 16) % self.block_num)
            with self.server.pipeline() as pipe:
                for map in self.maps:
                    offset = map.hash(value)
                    pipe.incrby(redis_dupefilter_name + str(offset))
                pipe.execute()

    def remove(self, value):
        if self.exists(value):
            # m5 = md5()
            # m5.update(value.encode('utf-8'))
            # value = m5.hexdigest()
            redis_dupefilter_name = self.key + str(int(value[0:self.value_split_num], 16) % self.block_num)
            with self.server.pipeline() as pipe:
                for map in self.maps:
                    offset = map.hash(value)
                    pipe.decrby(redis_dupefilter_name + str(offset))
                pipe.execute()


if __name__ == '__main__':
    n = 100000000
    p = 0.000001
    m, k, mem, block_num = calculation_bloom_filter(n, p)
    print(m, k, mem, block_num)
