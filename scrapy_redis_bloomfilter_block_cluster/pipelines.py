from scrapy.utils.misc import load_object
from twisted.internet.threads import deferToThread
from . import connection, defaults


class RedisPipeline(object):
    """Pushes serialized item into a redis list/queue

    Settings
    --------
    REDIS_ITEMS_KEY : str
        Redis key where to store items.
    REDIS_ITEMS_SERIALIZER : str
        Object path to serializer function.

    """

    def __init__(self, server, key, serialize_cls):
        """Initialize pipeline.

        Parameters
        ----------
        server : Redis
            Redis client instance.
        key : str
            Redis key where to store items.
        serialize_cls : callable
            Items serializer class.

        """
        self.server = server
        self.key = key
        self.serialize = serialize_cls

    @classmethod
    def from_settings(cls, settings):
        params = {
            'server': connection.from_settings(settings),
            'key': settings.get('REDIS_PIPELINE_KEY', defaults.REDIS_PIPELINE_KEY),
            'serialize_cls': load_object(settings.get('REDIS_PIPELINE_SERIALIZER', defaults.REDIS_PIPELINE_SERIALIZER))
        }
        return cls(**params)

    @classmethod
    def from_crawler(cls, crawler):
        return cls.from_settings(crawler.settings)

    def process_item(self, item, spider):
        return deferToThread(self._process_item, item, spider)

    def _process_item(self, item, spider):
        key = self.item_key(spider)
        data = self.serialize().encode(item)
        self.server.rpush(key, data)
        return item

    def item_key(self, spider):
        """Returns redis key based on given spider.

        Override this function to use a different key depending on the item
        and/or spider.

        """
        return self.key % {'spider': spider.name}

    # def close_spider(self, spider):
    #     self.server.close()
