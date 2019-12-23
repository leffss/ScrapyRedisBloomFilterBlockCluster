from rediscluster import RedisCluster       # redis-py-cluster 2.0.0 版本无 StrictRedisCluster
from scrapy.utils.reqser import request_to_dict, request_from_dict, _find_method, _get_method
from scrapy.http import Request
from scrapy.utils.python import to_unicode, to_native_str
from scrapy.utils.misc import load_object
from . import picklecompat


class Base(object):
    """Per-spider base queue class"""

    def __init__(self, server, spider, key):
        """Initialize per-spider redis queue.

        Parameters
        ----------
        server : Redis Or  RedisCluster
            Redis client instance.
        spider : Spider
            Scrapy spider instance.
        key: str
            Redis key where to put and get messages.
        serializer : object
            Serializer object with ``loads`` and ``dumps`` methods.

        """
        self.server = server
        self.spider = spider
        self.key = key % {'spider': spider.name}
        self.serializer = picklecompat

    def _encode_request(self, request):
        """Encode a request object"""
        obj = request_to_dict(request, self.spider)
        return self.serializer.dumps(obj)

    def _decode_request(self, encoded_request):
        """Decode an request previously encoded"""
        obj = self.serializer.loads(encoded_request)
        return request_from_dict(obj, self.spider)

    def __len__(self):
        """Return the length of the queue"""
        raise NotImplementedError

    def push(self, request):
        """Push a request"""
        raise NotImplementedError

    def pop(self, timeout=0):
        """Pop a request"""
        raise NotImplementedError

    def clear(self):
        """Clear queue/stack"""
        self.server.delete(self.key)


class FifoQueue(Base):
    """Per-spider FIFO queue"""

    def __len__(self):
        """Return the length of the queue"""
        return self.server.llen(self.key)

    def push(self, request):
        """Push a request"""
        self.server.lpush(self.key, self._encode_request(request))

    def pop(self, timeout=0):
        """Pop a request"""
        if timeout > 0:
            data = self.server.brpop(self.key, timeout)
            if isinstance(data, tuple):
                data = data[1]
        else:
            data = self.server.rpop(self.key)
        if data:
            return self._decode_request(data)


class PriorityQueue(Base):
    """Per-spider priority queue abstraction using redis' sorted set"""

    def __len__(self):
        """Return the length of the queue"""
        return self.server.zcard(self.key)

    def push(self, request):
        """Push a request"""
        data = self._encode_request(request)
        score = -request.priority
        # We don't use zadd method as the order of arguments change depending on
        # whether the class is Redis, and the option of using
        # kwargs only accepts strings, not bytes.
        self.server.execute_command('ZADD', self.key, score, data)

    def pop(self, timeout=0):
        """
        Pop a request
        timeout not support in this queue class
        """
        if not isinstance(self.server, RedisCluster):
            # use atomic range/remove using multi/exec
            pipe = self.server.pipeline()
            pipe.multi()
            pipe.zrange(self.key, 0, 0).zremrangebyrank(self.key, 0, 0)
            results, count = pipe.execute()
            if results:
                return self._decode_request(results[0])
        else:
            # 使用集群的时候不能使用multi/exec来完成一个事务操作；使用lua脚本来实现类似功能
            pop_lua_script = """
                    local result = redis.call('zrange', KEYS[1], 0, 0)
                    local element = result[1]
                    if element then
                        redis.call('zremrangebyrank', KEYS[1], 0, 0)
                        return element
                    else
                        return nil
                    end
                    """
            script = self.server.register_script(pop_lua_script)
            result = script(keys=[self.key])
            if result:
                return self._decode_request(result)


class LifoQueue(Base):
    """Per-spider LIFO queue."""

    def __len__(self):
        """Return the length of the stack"""
        return self.server.llen(self.key)

    def push(self, request):
        """Push a request"""
        self.server.lpush(self.key, self._encode_request(request))

    def pop(self, timeout=0):
        """Pop a request"""
        if timeout > 0:
            data = self.server.blpop(self.key, timeout)
            if isinstance(data, tuple):
                data = data[1]
        else:
            data = self.server.lpop(self.key)

        if data:
            return self._decode_request(data)


def simple_request_to_dict(request, spider=None):
    """Convert Request object to a dict.

    If a spider is given, it will try to find out the name of the spider method
    used in the callback and store that as the callback.
    """
    cb = request.callback
    if callable(cb):
        cb = _find_method(spider, cb)
    eb = request.errback
    if callable(eb):
        eb = _find_method(spider, eb)

    d = {
        'url': to_unicode(request.url),  # urls should be safe (safe_string_url)
        'callback': cb,
        'errback': eb,
        # 'method': request.method,
        # 'headers': dict(request.headers),
        # 'body': request.body,
        # 'cookies': request.cookies,
        'meta': request.meta,
        # '_encoding': request._encoding,
        # 'priority': request.priority,
        # 'dont_filter': request.dont_filter,
        # 'flags': request.flags,
        # 'cb_kwargs': request.cb_kwargs,
    }
    if type(request) is not Request:
        d['_class'] = request.__module__ + '.' + request.__class__.__name__
    return d


def simple_request_from_dict(d, spider=None):
    """Create Request object from a dict.

    If a spider is given, it will try to resolve the callbacks looking at the
    spider for methods with the same name.
    """
    cb = d['callback']
    if cb and spider:
        cb = _get_method(spider, cb)
    eb = d['errback']
    if eb and spider:
        eb = _get_method(spider, eb)
    request_cls = load_object(d['_class']) if '_class' in d else Request
    return request_cls(
        url=to_native_str(d['url']),
        callback=cb,
        errback=eb,
        # method=d['method'],
        # headers=d['headers'],
        # body=d['body'],
        # cookies=d['cookies'],
        meta=d['meta'],
        # encoding=d['_encoding'],
        # priority=d['priority'],
        # dont_filter=d['dont_filter'],
        # flags=d.get('flags'),
        # cb_kwargs=d.get('cb_kwargs'),
    )

class SimpleQueue(FifoQueue):
    """
    Per-spider simple (url + callback + errback + meta) FIFO queue, meta is important to scrapy
    meta include retry，redirect，rule and other important info. if your spider did not use callback
    or errback, you can change function simple_request_to_dict and simple_request_from_dict to omit it.
    """

    def _encode_request(self, request):
        """Encode a request object"""
        obj = simple_request_to_dict(request, self.spider)
        return self.serializer.dumps(obj)

    def _decode_request(self, encoded_request):
        """Decode an request previously encoded"""
        obj = self.serializer.loads(encoded_request)
        return simple_request_from_dict(obj, self.spider)
