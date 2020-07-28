# -*- coding: utf-8 -*-
import scrapy


class OhioSentenceSpider(scrapy.Spider):
    name = 'ohio-sentence'
    allowed_domains = ['appgateway.drc.ohio.gov/OffenderSearch/']
    start_urls = ['https://appgateway.drc.ohio.gov/OffenderSearch/']

    def parse(self, response):
        for letter in "abcdefghijklmnopqrstuvwxyz":
            yield scrapy.FormRequest.from_response(
                response,
                formdata={'LastName': letter, 'Status': 'I'},
                formid="lgForm",
                clickdata={'type': 'submit'},
                callback=self.parse_result_page
            )
    

    def parse_result_page(self, response):
        offenders = response.css('table tr:nth-child(n+1) td:nth-child(3)').xpath('.//@href')
        yield from response.follow_all(offenders, callback=self.parse_offender_page)
        # goto next page if page exists
        page = int(response.css('.btn-primary').attrib['value'])
        next_page = response.xpath(f'//input[@value={page + 1}]')

        if len(next_page) > 0:
            yield scrapy.FormRequest.from_response(
                response,
                formid="pagerForm",
                clickdata={'type': 'button', 'name': str(page+1)},
                callback=self.parse_result_page
            )

    def _get_table_value(self, table, name):
        return table.xpath(f'.//dt[contains(., "{name}")]/following-sibling::dd[1]/text()').get()

    def parse_offender_page(self, response):
        info_table = response.css('.panel-primary dl')
        sentence_info_table = response.xpath('//div[contains(@class, "panel-default") and contains(./div[contains(@class, "panel-heading")]/., "Sentence Information")]')

        number = self._get_table_value(info_table, "Number")
        dob = self._get_table_value(info_table, "DOB")
        admission_date = self._get_table_value(info_table, "Admission Date")

        stated_prison_term = self._get_table_value(sentence_info_table, "Stated Prison Term")
        expiration_term = self._get_table_value(sentence_info_table, "Expiration Stated Term")

        yield {
            'id': number,
            'state': 'Ohio',
            'dob': dob,
            'admission_date': admission_date,
            'prison_term': stated_prison_term,
            'end_of_term_date': expiration_term
        }

