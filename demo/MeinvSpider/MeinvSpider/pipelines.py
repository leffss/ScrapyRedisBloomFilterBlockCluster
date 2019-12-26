# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import json
import time
import re
from scrapy.pipelines.images import ImagesPipeline
from scrapy import Request


class MeinvspiderPipeline(object):
    def __init__(self):
        file_time = time.strftime('%Y%m%d%H%M%S',time.localtime(time.time()))
        self.filename = open("meinv_{0}.json".format(file_time), "w", encoding='utf-8')

    def process_item(self, item, spider):
        try:
            text = json.dumps(dict(item), ensure_ascii=False) + "\n"
            self.filename.write(text)
        except BaseException as e:
            print(e)
        return item

    def close_spider(self, spider):
        self.filename.close()


class MeinvspiderImagesPipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        # meta里面的数据是从spider获取，然后通过meta传递给下面方法：file_path
        yield Request(item['child_ImgUrl'], headers={'Referer': item['parent_ImgUrl']}, meta={'name': item['name']})

    # 重命名，若不重写这函数，图片名为哈希，就是一串乱七八糟的名字
    def file_path(self, request, response=None, info=None):
        # 提取url前面名称作为图片名。
        image_guid = request.url.split('/')[-1]
        # 接收上面meta传递过来的图片名称
        name = request.meta['name']
        # 过滤windows字符串，不经过这么一个步骤，你会发现有乱码或无法下载
        name = re.sub(r'[\\/:\*\?"<>\|\.]', '', name)
        image_guid = re.sub(r'[\\/:\*\?"<>\|]', '', image_guid)
        # 分文件夹存储的关键：{0}对应着name；{1}对应着image_guid
        filename = u'{0}/{1}'.format(name, image_guid)
        return filename
