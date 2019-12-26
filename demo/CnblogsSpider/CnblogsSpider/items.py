# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class CnblogsspiderItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    title = scrapy.Field()
    diggnum = scrapy.Field()
    link = scrapy.Field()
    post_item_summary = scrapy.Field()
    author = scrapy.Field()
    author_link = scrapy.Field()
    article_comment = scrapy.Field()
    article_view = scrapy.Field()
    