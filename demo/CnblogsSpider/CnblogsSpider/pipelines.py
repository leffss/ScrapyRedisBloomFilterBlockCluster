# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import json


class CnblogsspiderPipeline(object):
    def __init__(self):
        self.filename = open("cnblogs.json", "w", encoding='utf-8')
    
    def process_item(self, item, spider):
        try:
            text = json.dumps(dict(item), ensure_ascii=False) + "\n"
            self.filename.write(text)
        except BaseException as e:
            print(e)
        return item
    
    def close_spider(self, spider):
        self.filename.close()