# -*- coding: utf-8 -*-
import scrapy


class TexasSentenceSpider(scrapy.Spider):
    name = 'texas-sentence'
    allowed_domains = ['texastribune.org/library/data/texas-prisons/']
    start_urls = ['http://texastribune.org/library/data/texas-prisons/units/']

    def parse_inmate_info_row(self, response, name):
        return response.xpath(f'//tr[th="{name}"]/td/text()').get()

    def parse_inmate_crimes_row(self, row):
        crime = row.xpath('td[@data-title="Crime"]/text()').get()
        sentence_length = row.xpath('td[@data-title="Sentence"]/text()').get()
        sentence_start_date = row.xpath('td[@data-title="Sentence Began"]/text()').get()

        return {
            'crime': crime,
            'sentence-length': sentence_length,
            'sentence-start-date': sentence_start_date
        }


    def parse(self, response):
        units = response.xpath('//td[@data-title="Name"/a/@href]')
        yield from response.follow_all(units, callback=self.parse_unit)

    def parse_unit(self, response):
        units = response.xpath('//td[@data-title="Name"/a/@href]')
        yield from response.follow_all(units, callback=self.parse_inmate)

    def parse_inmate(self, response):
        inmate_id = self.parse_inmate_info_row(response, "TDCJ ID")
        dob = self.parse_inmate_info_row(response, "DOB")
        release_date = self.parse_inmate_info_row(response, "Projected release date")
        age = self.parse_inmate_info_row(response, "Age")
        crimes_rows = response.css('table.table-new tr')

        yield {
            'id': inmate_id,
            'state': 'Texas',
            'dob': dob,
            'age': age,
            'projected-release-date': release_date,
            'crimes': [self.parse_inmate_crimes_row(crime_row) for crime_row in crimes_rows]
        }

