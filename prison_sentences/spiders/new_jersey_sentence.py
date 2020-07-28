# -*- coding: utf-8 -*-
import scrapy
import urllib.parse as urlparse
import re


class NewJerseySentenceSpider(scrapy.Spider):
    name = 'new-jersey-sentence'
    allowed_domains = ['https://www20.state.nj.us/DOC_Inmate/']
    start_urls = ['https://www20.state.nj.us/DOC_Inmate/inmatefinder?i=I']

    def parse(self, response):
        yield scrapy.FormRequest.from_response(
            response, 
            formid="accept", 
            clickdata={'name': 'inmatesearch'}, 
            callback=self.parse_search_page
        )

    def parse_search_page(self, response):
        counties = response.xpath('//select[@name="County"]/option[@value != "ALL"]/@value').getall()

        base_formdata = {
            'Aliases': 'NO',
            'Eye_Color': 'ALL',
            'First_Name': '',
            'Location': 'ALL',
            'Photo_Disabled': 'checked',
            'Race': 'ALL',
            'Sex': 'ALL',
            'bday_from_day': 'None',
            'bday_from_month': 'None',
            'bday_from_year': 'None',
            'bday_to_day': 'None',
            'bday_to_month': 'None',
            'bday_to_year': 'None'
        }

        for letter in "abcdefghijklmnopqrstuvwxyz":
            for county in counties:
                formdata = {**base_formdata, 'County': county, 'Last_Name': letter}
                yield scrapy.FormRequest.from_response(
                    response,
                    formdata=formdata,
                    formid="inmatesearch",
                    clickdata={'name': 'Submit'},
                    callback=self.parse_search_results
                )


    def parse_search_results(self, response):
        inmates = response.xpath('//a[@href]/@href').re(r'/DOC_Inmate/details\?x=\d+\&n=\d+')
        yield from response.follow_all(inmates, callback=self.parse_person_page)
        
        parsed_url = urlparse.urlparse(response.url)
        paramsdict = urlparse.parse_qs(parsed_url[4])
        next_page = int(paramsdict.get('pg', '1')) + 1
        next_url = response.xpath(f'//a[@href and contains(@href, "pg={next_page}")]/@href').get()

        if next_url is not None:
            yield response.follow(next_url, callback=self.parse_search_results)

    
    def _find_offender_info_by_text(self, offender_table, text):
        return offender_table.xpath(f'./tr[contains(td[1]//text(), "{text}")]').xpath('./td[2]/text()').get()

    def _parse_crimes_table(self, crimes_table):
        crimes = []
        labels = []
        for cell in crimes_table.xpath('./tr[2]/td'):
            label = " ".join(re.sub(r'\r?\n? +', ' ', s.strip()) for s in cell.xpath('.//a/text()').getall())
            labels.append(label)
        

        for crime_row in crimes_table.xpath('./tr[position() > 2]'):
            crime = {}
            for (index, cell) in enumerate(crime_row.xpath('./td')):
                value = " ".join(re.sub(r'\r?\n? +', ' ', s.strip()) for s in cell.xpath('.//div/text()').getall())
                crime[labels[index]] = value
            crimes.append(crime)

        return crimes     



    def parse_person_page(self, response):
        offender_table = response.xpath('//div[@id="mainContent"]/table/tr[2]/td/table/tr/td/table')
        crimes_table = response.xpath('//div[@id="mainContent"]/table/tr[3]/td/table/tr[1]/td/table')

        sbi = self._find_offender_info_by_text(offender_table, "SBI Number")
        dob = self._find_offender_info_by_text(offender_table, "Birth Date")
        admission_date = self._find_offender_info_by_text(offender_table, "Admission Date")
        facility = self._find_offender_info_by_text(offender_table, "Current Facility")
        max_release = self._find_offender_info_by_text(offender_table, "Current Max Release Date")
        parole_eligibility = self._find_offender_info_by_text(offender_table, "Current Parole Eligibility Date")

        yield {
            'id': sbi,
            'state': 'New Jersey',
            'dob': dob,
            'admission_date': admission_date,
            'facility': facility,
            'max_release_date': max_release,
            'parole_eligibility_date': parole_eligibility,
            'crimes': self._parse_crimes_table(crimes_table)
        }

