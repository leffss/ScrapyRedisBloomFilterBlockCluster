# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy_redis_bloomfilter_block_cluster.spiders import RedisCrawlSpider
from MeinvSpider.items import MeinvspiderItem
import os
import traceback
import time


def get_time_stamp(format_time="%Y-%m-%d %H:%M:%S", tmp='.'):
    ct = time.time()
    local_time = time.localtime(ct)
    date_head = time.strftime(format_time, local_time)
    date_secs = (ct - int(ct)) * 1000
    time_stamp = "%s%s%03d" % (date_head, tmp, date_secs)
    return time_stamp


class MeinvSpider(RedisCrawlSpider):
    name = 'meinv'
    allowed_domains = ['www.2717.com']
    start_urls = ['https://www.2717.com/ent/meinvtupian/list_11_1.html']

    redis_key = 'meinv:start_urls'
    auto_insert = True

    rules = (
        Rule(LinkExtractor(allow=r'list_11_\d+.html'), callback='parse_item', follow=True),
    )

    rules_list = [r'list_11_\d+.html']

    # CrawlSpider的rules属性是直接从response对象的文本中提取url，然后自动创建新的请求。
    # 与Spider不同的是，CrawlSpider已经重写了parse函数
    # scrapy crawl spidername开始运行，程序自动使用start_urls构造Request并发送请求，
    # 然后调用parse函数对其进行解析，在这个解析过程中使用rules中的规则从html（或xml）文本中提取匹配的链接，
    # 通过这个链接再次生成Request，如此不断循环，直到返回的文本中再也没有匹配的链接，或调度器中的Request对象用尽，程序才停止。
    # 如果起始的url解析方式有所不同，那么可以重写CrawlSpider中的另一个函数parse_start_url(self, response)用来解析第一个url返回的Response，但这不是必须的。

    def parse_start_url(self, response):
        try:
            items = []
            url_header = 'https://www.2717.com'
            for each in response.xpath("//div[@class='MeinvTuPianBox']/ul"):
                for each2 in each.xpath("./li"):
                    try:
                        item = MeinvspiderItem()
                        item['name'] = each2.xpath("./a[1]/@title").extract()[0].strip()
                        item['parent_ImgUrl'] = url_header + each2.xpath("./a[1]/@href").extract()[0].strip()

                        items.append(item)
                        # yield item
                    except BaseException:
                        print(traceback.format_exc())
            for item in items:
                tmp_time = get_time_stamp()
                item['capture_time'] = tmp_time
                yield scrapy.Request(url=item['parent_ImgUrl'], meta={'meta_1': item}, callback=self.second_parse_item)
        except BaseException:
            print(traceback.format_exc())

    def parse_item(self, response):
        try:
            items = []
            url_header = 'https://www.2717.com'
            for each in response.xpath("//div[@class='MeinvTuPianBox']/ul"):
                for each2 in each.xpath("./li"):
                    try:
                        item = MeinvspiderItem()
                        item['name'] = each2.xpath("./a[1]/@title").extract()[0].strip()
                        item['parent_ImgUrl'] = url_header + each2.xpath("./a[1]/@href").extract()[0].strip()

                        items.append(item)
                        # yield item
                    except BaseException:
                        print(traceback.format_exc())
            for item in items:
                tmp_time = get_time_stamp()
                item['capture_time'] = tmp_time
                yield scrapy.Request(url=item['parent_ImgUrl'], meta={'meta_1': item}, callback=self.second_parse_item)
        except BaseException:
            print(traceback.format_exc())

    def second_parse_item(self, response):
        item = MeinvspiderItem()
        meta_1 = response.meta['meta_1']
        item['name'] = meta_1['name']
        item['parent_ImgUrl'] = meta_1['parent_ImgUrl']
        item['capture_time'] = meta_1['capture_time']
        item['child_ImgUrl'] = response.xpath("//div[@class='articleV4Body']/p/a[1]/img/@src").extract()[0].strip()
        yield item
        next_url = response.xpath("//div[@class='page-tag oh']/ul[@class='articleV4Page l']/li[@id='nl']/a/@href").extract()[0].strip()
        if next_url != '##':
            yield response.follow(url=next_url, meta={'meta_1': item}, callback=self.second_parse_item)
