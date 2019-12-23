import six
from scrapy.utils.misc import load_object
from . import defaults
"""
根据不同配置选择返回 redis 单机实例或者 redis 集群实例
"""


# Shortcut maps 'setting name' -> 'parmater name'.
REDIS_SETTINGS_PARAMS_MAP = {
    'REDIS_CLS': 'redis_cls',
    'REDIS_URL': 'url',
    'REDIS_HOST': 'host',
    'REDIS_PORT': 'port',
    'REDIS_PASSWORD': 'password',
    'REDIS_ENCODING': 'encoding',
}


def get_redis_from_settings(settings):
    """Returns a redis client instance from given Scrapy settings object.

    This function uses ``get_client`` to instantiate the client and uses
    ``defaults.REDIS_PARAMS`` global as defaults values for the parameters. You
    can override them using the ``REDIS_PARAMS`` setting.

    Parameters
    ----------
    settings : Settings
        A scrapy settings object. See the supported settings below.

    Returns
    -------
    server
        Redis client instance.

    Other Parameters
    ----------------
    REDIS_URL : str, optional
        Server connection URL.
    REDIS_HOST : str, optional
        Server host.
    REDIS_PORT : str, optional
        Server port.
    REDIS_ENCODING : str, optional
        Data encoding.
    REDIS_PARAMS : dict, optional
        Additional client parameters.

    """
    params = defaults.REDIS_PARAMS.copy()
    params.update(settings.getdict('REDIS_PARAMS'))
    # XXX: Deprecate REDIS_* settings.
    for setting_name, name in REDIS_SETTINGS_PARAMS_MAP.items():
        val = settings.get(setting_name)
        if val:
            params[name] = val

    # Allow ``redis_cls`` to be a path to a class.
    if isinstance(params.get('redis_cls'), six.string_types):
        params['redis_cls'] = load_object(params['redis_cls'])

    return get_redis(**params)


def get_redis(**kwargs):
    """
    返回一个 redis 单机实例
    """
    redis_cls = kwargs.pop('redis_cls', defaults.REDIS_CLS)
    url = kwargs.pop('url', None)
    if url:     # 使用 url 连接时忽略 db 参数
        try:
            kwargs.pop('db')
        except BaseException:
            pass
        try:
            kwargs.pop('host')
        except BaseException:
            pass
        try:
            kwargs.pop('port')
        except BaseException:
            pass
        return redis_cls.from_url(url, **kwargs)
    else:
        return redis_cls(**kwargs)


# 集群连接配置
REDIS_CLUSTER_SETTINGS_PARAMS_MAP = {
    'REDIS_CLUSTER_CLS': 'redis_cluster_cls',
    'REDIS_CLUSTER_URL': 'url',
    'REDIS_CLUSTER_NODES': 'startup_nodes',
    'REDIS_CLUSTER_PASSWORD': 'password',
    'REDIS_ENCODING': 'encoding',
}


def get_redis_cluster_from_settings(settings):
    params = defaults.REDIS_CLUSTER_PARAMS.copy()
    params.update(settings.getdict('REDIS_CLUSTER_PARAMS'))
    # XXX: Deprecate REDIS_CLUSTER* settings.
    for setting_name, name in REDIS_CLUSTER_SETTINGS_PARAMS_MAP.items():
        val = settings.get(setting_name)
        if val:
            params[name] = val

    # Allow ``redis_cluster_cls`` to be a path to a class.
    if isinstance(params.get('redis_cluster_cls'), six.string_types):
        params['redis_cluster_cls'] = load_object(params['redis_cluster_cls'])

    return get_redis_cluster(**params)


def get_redis_cluster(**kwargs):
    """
    返回一个 redis 集群实例
    """
    redis_cluster_cls = kwargs.pop('redis_cluster_cls', defaults.REDIS_CLUSTER_CLS)
    url = kwargs.pop('url', None)
    # redis cluster 只有 db0，不支持 db 参数
    try:
        kwargs.pop('db')
    except BaseException:
        pass
    if url:
        try:
            kwargs.pop('startup_nodes')
        except BaseException:
            pass
        return redis_cluster_cls.from_url(url, **kwargs)
    else:
        return redis_cluster_cls(**kwargs)


# 哨兵连接配置
REDIS_SENTINEL_SETTINGS_PARAMS_MAP = {
    'REDIS_SENTINEL_CLS': 'redis_sentinel_cls',
    'REDIS_SENTINEL_NODES': 'sentinel_nodes',
    'REDIS_SENTINEL_SERVICE_NAME': 'service_name',
    'REDIS_SENTINEL_PASSWORD': 'password',
    'REDIS_ENCODING': 'encoding',
}


def get_redis_sentinel_from_settings(settings):
    params = defaults.REDIS_SENTINEL_PARAMS.copy()
    params.update(settings.getdict('REDIS_SENTINEL_PARAMS'))
    # XXX: Deprecate REDIS_CLUSTER* settings.
    for setting_name, name in REDIS_SENTINEL_SETTINGS_PARAMS_MAP.items():
        val = settings.get(setting_name)
        if val:
            params[name] = val

    # Allow ``redis_cluster_cls`` to be a path to a class.
    if isinstance(params.get('redis_sentinel_cls'), six.string_types):
        params['redis_sentinel_cls'] = load_object(params['redis_sentinel_cls'])

    return get_redis_sentinel(**params)


def get_redis_sentinel(**kwargs):
    """
    返回一个 redis sentinel实例
    """
    redis_sentinel_cls = kwargs.pop('redis_sentinel_cls', defaults.REDIS_SENTINEL_CLS)
    sentinel_nodes = kwargs.pop('sentinel_nodes')
    service_name = kwargs.pop('service_name')
    redis_sentinel_conn = redis_sentinel_cls(sentinel_nodes, **kwargs)
    # return [redis_sentinel_conn.master_for(service_name), redis_sentinel_conn.slave_for(service_name)]
    return redis_sentinel_conn.master_for(service_name)


def from_settings(settings):
    """
    根据settings中的配置来决定返回不同 redis 实例，优先级： 集群 > 哨兵 > 单机
    """
    if "REDIS_CLUSTER_NODES" in settings or 'REDIS_CLUSTER_URL' in settings:
        return get_redis_cluster_from_settings(settings)
    elif "REDIS_SENTINEL_NODES" in settings:
        return get_redis_sentinel_from_settings(settings)
    return get_redis_from_settings(settings)
