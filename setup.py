import io
from setuptools import setup, find_packages
import scrapy_redis_bloomfilter_block_cluster


setup(
    name='scrapy-redis-bloomfilter-block-cluster',
    version=scrapy_redis_bloomfilter_block_cluster.__version__,
    description='Scrapy Redis BloomFilter Block Cluster',
    keywords=['scrapy', 'redis', 'bloomfilter', 'block', 'cluster'],
    author=scrapy_redis_bloomfilter_block_cluster.__author__,
    author_email=scrapy_redis_bloomfilter_block_cluster.__author_email__,
    license='MIT',
    url='https://github.com/leffss/ScrapyRedisBloomFilterBlockCluster',
    packages=find_packages(),
    classifiers=[
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.7',
    ],
    install_requires=[
        'six>=1.13.0',
        'mmh3>=2.5.1',
        'twisted==19.10.0',
        'scrapy==1.8.0',
        'redis-py-cluster==2.0.0',
        'redis==3.0.1'  # redis-py-cluster 2.0.0, latest support redis 3.0.1
        # 'redis-py-cluster==2.1.0',
        # 'redis==3.3.11',
    ]
)
