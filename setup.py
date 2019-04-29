import io
from setuptools import setup, find_packages
import scrapy_redis_bloomfilter_block_cluster


setup(
    name='scrapy-redis-bloomfilter-block-cluster',
    version=scrapy_redis_bloomfilter_block_cluster.__version__,
    description='Scrapy Redis BloomFilter Block Cluster',
    keywords=['scrapy', 'redis', 'bloomfilter', 'block', 'cluster'],
    author=scrapy_redis_bloomfilter_block_cluster.__author__,
    email=scrapy_redis_bloomfilter_block_cluster.__email__,
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
        'twisted==18.9.0',
        'Scrapy>=1.4',
        'redis>=2.10',
        'six>=1.5.2',
        'redis-py-cluster>=1.3.4'
    ]
)
