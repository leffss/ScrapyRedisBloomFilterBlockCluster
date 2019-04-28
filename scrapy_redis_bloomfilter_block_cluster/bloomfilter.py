from .defaults import BLOOMFILTER_BIT, BLOOMFILTER_HASH_NUMBER, BLOOMFILTER_BLOCK_NUM


class HashMap(object):
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


class BloomFilter(object):
    def __init__(self, server, key, bit=BLOOMFILTER_BIT, hash_number=BLOOMFILTER_HASH_NUMBER, block_num=BLOOMFILTER_BLOCK_NUM):
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
            
