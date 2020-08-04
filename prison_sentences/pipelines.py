# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


class PrisonSentencesPipeline(object):
    def process_item(self, item, spider):
        state = item['state']

        if state == 'Georgia':
            pass
        elif state == 'New York':
            pass
        elif state == 'New Jersey':
            pass
        elif state == 'Ohio':
            pass
        elif state == 'Florida':
            pass
        elif state == 'Texas':
            pass
        elif state == 'California':
            pass

        return item
