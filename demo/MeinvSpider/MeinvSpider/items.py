# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class MeinvspiderItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    name = scrapy.Field()
    parent_ImgUrl = scrapy.Field()
    child_ImgUrl = scrapy.Field()
    capture_time = scrapy.Field()
