import io
from setuptools import setup, find_packages
import scrapy_redis_bloomfilter_block_cluster


def read_file(filename):
    with io.open(filename) as fp:
        return fp.read().strip()


def read_requirements(filename):
    return [line.strip() for line in read_file(filename).splitlines()
            if not line.startswith('#')]


setup(
    name='scrapy-redis-bloomfilter-block-cluster',
    version=scrapy_redis_bloomfilter_block_cluster.__version__,
    description='Scrapy Redis BloomFilter Block Cluster',
    keywords=['scrapy', 'redis', 'bloomfilter', 'block', 'cluster'],
    author=scrapy_redis_bloomfilter_block_cluster.__author__,
    email=scrapy_redis_bloomfilter_block_cluster.__email__,
    license='MIT',
    url='https://github.com/leffss/ScrapyRedisBloomFilterBlockCluster',
    install_requires=read_requirements('requirements.txt'),
    packages=find_packages(),
    classifiers=[
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.7',
    ]
)
