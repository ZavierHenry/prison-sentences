# -*- coding: utf-8 -*-
import scrapy


class NewYorkSentenceSpider(scrapy.Spider):
    name = 'new-york-sentence'
    allowed_domains = ['nysdoccslookup.doccs.ny.gov']
    start_urls = ['http://nysdoccslookup.doccs.ny.gov/']

    def parse(self, response):
        yield scrapy.FormRequest.from_response(
            response,
            formdata={'M00_LAST_NAMEI': 'a'},
            formxpath='//div[@id="il"]/form',
            clickdata={'type': 'submit'},
            callback=self.parse_search_result
        )
        

    def parse_search_result(self, response):
        number_rows = len(response.css('table#dinlist tr:nth-child(n+2)'))
        for row in range(0, number_rows):
            yield scrapy.FormRequest.from_response(
                response,
                formcss=f'table#dinlist tr:nth-child({row+2}) form',
                clickdata={'class': 'buttolink'},
                callback=self.parse_person_page
            )
        
        if len(response.xpath('//p[contains(text(), "NO MORE NAMES ON FILE")]')) == 0:
            yield scrapy.FormRequest.from_response(
                response,
                formcss="table#dinlist ~ form",
                clickdata={'name': 'next'},
                callback=self.parse_search_result
            )

    def _parse_identifying_table_value(self, table, name):
        return table.xpath(f'./tr[contains(./td/., "{name}")]').xpath('./td[2]/text()').getall()[0].strip()


    def parse_person_page(self, response):
        identifying_table = response.xpath('//table[contains(@summary, "location information")]')
        sentence_terms_table = response.xpath('//table[contains(@summary, "sentence terms")]')

        din = self._parse_identifying_table_value(identifying_table, "Department Identification Number")
        dob = self._parse_identifying_table_value(identifying_table, "Date of Birth")
        custody_status = self._parse_identifying_table_value(identifying_table, "Custody Status")
        date_received_current = self._parse_identifying_table_value(identifying_table, "Date Received (Current)")
        release_date_type = self._parse_identifying_table_value(identifying_table, "Latest Release Date")

        min_sentence = self._parse_identifying_table_value(sentence_terms_table, "Aggregate Minimum Sentence")
        max_sentence = self._parse_identifying_table_value(sentence_terms_table, "Aggregate Maximum Sentence")
        earliest_release_date = self._parse_identifying_table_value(sentence_terms_table, "Earliest Release Date")
        conditional_release_date = self._parse_identifying_table_value(sentence_terms_table, "Conditional Release Date")

    
        yield {
            'state': 'New York',
            'din': din,
            'dob': dob,
            'custody_status': custody_status,
            'current_received_date': date_received_current,
            'release_date': release_date_type,
            'min_sentence': min_sentence,
            'max_sentence': max_sentence,
            'earliest_release_date': earliest_release_date,
            'conditional_release_date': conditional_release_date
        }
