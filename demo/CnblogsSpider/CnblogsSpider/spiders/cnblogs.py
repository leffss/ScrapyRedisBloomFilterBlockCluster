# -*- coding: utf-8 -*-
import scrapy
from scrapy_redis_bloomfilter_block_cluster.spiders import RedisCrawlSpider
from scrapy.spiders import Rule
from scrapy.linkextractors import LinkExtractor
from CnblogsSpider.items import CnblogsspiderItem


class CnblogsSpider(RedisCrawlSpider):
    name = 'cnblogs'
    allowed_domains = ['cnblogs.com']
    start_urls = ['https://www.cnblogs.com/sitehome/p/1']
    redis_key = 'cnblogs:start_urls'
    auto_insert = True

    # Response里链接的提取规则，返回的符合匹配规则的链接匹配对象的列表
    pagelink = LinkExtractor(allow=("/sitehome/p/\d+"))

    rules = [
        # 获取这个列表里的链接，依次发送请求，并且继续跟进，调用指定回调函数处理
        Rule(pagelink, callback="parse_item", follow=True)
    ]
    
    # CrawlSpider的rules属性是直接从response对象的文本中提取url，然后自动创建新的请求。
    # 与Spider不同的是，CrawlSpider已经重写了parse函数
    # scrapy crawl spidername开始运行，程序自动使用start_urls构造Request并发送请求，
    # 然后调用parse函数对其进行解析，在这个解析过程中使用rules中的规则从html（或xml）文本中提取匹配的链接，
    # 通过这个链接再次生成Request，如此不断循环，直到返回的文本中再也没有匹配的链接，或调度器中的Request对象用尽，程序才停止。
    # 如果起始的url解析方式有所不同，那么可以重写CrawlSpider中的另一个函数parse_start_url(self, response)用来解析第一个url返回的Response，但这不是必须的。
    
    def parse_item(self, response):
        for each in response.xpath("//div[@class='post_item']"):
            item = CnblogsspiderItem()
            item['diggnum'] = each.xpath("./div[1]/div[1]/span[1]/text()").extract()[0].strip()
            item['title'] = each.xpath("./div[2]/h3/a/text()").extract()[0].strip()
            item['link'] = each.xpath("./div[2]/h3/a/@href").extract()[0].strip()
            
            item['post_item_summary'] = ''.join(each.xpath("./div[2]/p[@class='post_item_summary']/text()").extract()).strip()
            item['author'] = each.xpath("./div[2]/div/a/text()").extract()[0].strip()
            item['author_link'] = each.xpath("./div[2]/div/a/@href").extract()[0].strip()
            
            item['article_comment'] = each.xpath("./div[2]/div/span[1]/a/text()").extract()[0].strip()
            item['article_view'] = each.xpath("./div[2]/div/span[2]/a/text()").extract()[0].strip()

            yield item

