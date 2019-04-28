# -*- coding: utf-8 -*-
import scrapy
from scrapy_redis_bloomfilter_block_cluster.spiders import RedisCrawlSpider
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from TencentSpider.items import TencentspiderItem


class TencentSpider(RedisCrawlSpider):
    name = 'tencent'
    # allowed_domains = ['tencent.com']
    allowed_domains = ['hr.tencent.com']
    # start_urls = ['https://hr.tencent.com/position.php?&start=0#a']
    redis_key = 'tencent:start_urls'
    
    pagelink = LinkExtractor(allow=("start=\d+"))
    
    rules = (
        Rule(pagelink, callback='parse_item', follow=True),
    )
    
    def parse_item(self, response):
        print(response.request.headers)
        items = []
        url1 = "https://hr.tencent.com/"
        for each in response.xpath("//tr[@class='even'] | //tr[@class='odd']"):
            item = TencentspiderItem()
            try:
                item['positionname'] = each.xpath("./td[1]/a/text()").extract()[0].strip()
            except BaseException:
                item['positionname'] = ""
                
            try:
                item['positionlink'] = "{0}{1}".format(url1, each.xpath("./td[1]/a/@href").extract()[0].strip())
            except BaseException:
                item['positionlink'] = ""
            
            try:
                item['positionType'] = each.xpath("./td[2]/text()").extract()[0].strip()
            except BaseException:
                item['positionType'] = ""
            
            try:
                item['peopleNum'] = each.xpath("./td[3]/text()").extract()[0].strip()
            except BaseException:
                item['peopleNum'] = ""

            try:
                item['workLocation'] = each.xpath("./td[4]/text()").extract()[0].strip()
            except BaseException:
                item['workLocation'] = ""
            
            try:
                item['publishTime'] = each.xpath("./td[5]/text()").extract()[0].strip()
            except BaseException:
                item['publishTime'] = ""
            
            items.append(item)
        for item in items:
            yield scrapy.Request(url=item['positionlink'], meta={'meta_1': item}, callback=self.second_parseTencent)
            
    def second_parseTencent(self, response):
        item = TencentspiderItem()
        meta_1 = response.meta['meta_1']
        item['positionname'] = meta_1['positionname']
        item['positionlink'] = meta_1['positionlink']
        item['positionType'] = meta_1['positionType']
        item['peopleNum'] = meta_1['peopleNum']
        item['workLocation'] = meta_1['workLocation']
        item['publishTime'] = meta_1['publishTime']
        
        tmp = []
        tmp.append(response.xpath("//tr[@class='c']")[0])
        tmp.append(response.xpath("//tr[@class='c']")[1])
        positiondetail = ''
        for i in tmp:
            positiondetail_title = i.xpath("./td[1]/div[@class='lightblue']/text()").extract()[0].strip()
            positiondetail = positiondetail + positiondetail_title
            positiondetail_detail = i.xpath("./td[1]/ul[@class='squareli']/li/text()").extract()
            positiondetail = positiondetail + ' '.join(positiondetail_detail) + ' '
        
        item['positiondetail'] = positiondetail.strip()
        
        yield item
