from hashlib import md5


class HashMap(object):
    """
    返回字符串 hash 出来的 offset (整数)，范围 0 - self.m
    """
    def __init__(self, m, seed):
        self.m = m
        self.seed = seed
    
    def hash(self, value):
        """
        Hash Algorithm
        :param value: Value
        :return: Hash Value
        """
        ret = 0
        for i in range(len(value)):
            ret += self.seed * ret + ord(value[i])
        return (self.m - 1) & ret


class BloomFilterOld(object):
    def __init__(self, server, key, bit, hash_number, block_num):
        """
        Initialize BloomFilter
        :param server: Redis Server
        :param key: BloomFilter Key
        :param bit: m = 2 ^ bit
        :param hash_number: the number of hash function
        """
        # default to 1 << 30 = 10,7374,1824 = 2^30 = 128MB, max filter 2^30/hash_number = 1,7895,6970 fingerprints
        self.m = 1 << bit
        self.seeds = range(hash_number)
        self.server = server
        self.key = key
        self.block_num = block_num
        self.maps = [HashMap(self.m, seed) for seed in self.seeds]
    
    def exists(self, value):
        """
        if value exists
        :param value:
        :return:
        """
        if not value:
            return False
        exist = True
        for map in self.maps:
            offset = map.hash(value)
            redis_dupefilter_name = self.key + str(int(value[0:2], 16) % self.block_num)
            exist = exist & self.server.getbit(redis_dupefilter_name, offset)
        return exist
    
    def insert(self, value):
        """
        add value to bloom
        :param value:
        :return:
        """
        for f in self.maps:
            offset = f.hash(value)
            redis_dupefilter_name = self.key + str(int(value[0:2], 16) % self.block_num)
            self.server.setbit(redis_dupefilter_name, offset, 1)


class BloomFilter(object):
    """
    基于 redis 的 BloomFilter 去重，原理简单点说就是有几个 seeds（hash 函数），然后申请一段内存空间
    ，一个 seed 可以和字符串哈希映射到这段内存上的一个位，几个位都为1即表示该字符串已经存在。插入的
    时候也是，将映射出的几个位都置为1。根据去重数量适当地调整 seeds 的数量和 block_num 数量 seeds 数
    量越少去重速度越快，但漏失率越大;block_num 数量越大，占用 redis 内存越高，去重的数据量越大
    BloomFilter 之所以能做到在时间和空间上的效率比较高，是因为牺牲了判断的准确率、删除的便利性:
    1. 存在误判，可能要查到的元素并没有在容器中，但是hash之后得到的k个位置上值都是1。对于爬虫来说就是
    可能会少抓取一些页面，可以容忍。
    2. 删除困难。一个放入容器的元素映射到bit数组的k个位置上是1，删除的时候不能简单的直接置为0，
    可能会影响其他元素的判断。如果有删除需求可以查阅 Counting Bloom Filter 实现删除。
    """
    def __init__(self, server, key, bit, hash_number, block_num):
        self.m = 1 << bit if bit <= 32 else 1 << 32   # redis string 最大 512MB，即 2^32
        self.seeds = range(hash_number)
        self.server = server
        self.key = key
        self.block_num = block_num
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
        redis_dupefilter_name = self.key + str(int(value[0:2], 16) % self.block_num)
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
        # m5 = md5()
        # m5.update(value.encode('utf-8'))
        # value = m5.hexdigest()
        redis_dupefilter_name = self.key + str(int(value[0:2], 16) % self.block_num)
        with self.server.pipeline() as pipe:
            for map in self.maps:
                offset = map.hash(value)
                pipe.setbit(redis_dupefilter_name, offset, 1)
            pipe.execute()
            

class CountBloomFilter(object):
    """
    Counting Bloom Filter 实现了删除，由 Bloom Filter 的 bit 存储变更为 key 存储
    会占用更多的 redis 内存空间，以空间换取了删除功能，其中 self.m 不再受 redis 
    string 最大 512MB 的限制，只受 redis 能够设置多少 key 的限制，官方 FAQ 理论上
    是 2^32 （40 亿），但是经过验证单实例最少支持 2.5 亿个 key，相比一个 string 40 
    亿的 bit 位有点小，所以这个实现仅供参考。
    """
    def __init__(self, server, key, bit, hash_number, block_num):
        self.m = 1 << bit if bit <= 32 else 1 << 32   # Counting Bloom Filter 中已不受 redis string 最大 512MB，即 2^32 的限制，这里懒得改而已
        self.seeds = range(hash_number)
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
        redis_dupefilter_name = self.key + str(int(value[0:2], 16) % self.block_num)
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
            redis_dupefilter_name = self.key + str(int(value[0:2], 16) % self.block_num)
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
            redis_dupefilter_name = self.key + str(int(value[0:2], 16) % self.block_num)
            with self.server.pipeline() as pipe:
                for map in self.maps:
                    offset = map.hash(value)
                    pipe.decrby(redis_dupefilter_name + str(offset))
                pipe.execute()
