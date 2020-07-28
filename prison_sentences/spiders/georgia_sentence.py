import scrapy
import re

class GeorgiaSentenceSpider(scrapy.Spider):
    name = 'georgia-sentence'
    allowed_domains = ['dcor.state.ga.us/GDC/Offender/Query']
    start_urls = ['http://www.dcor.state.ga.us/GDC/Offender/Query/']

    def parse(self, response):
        src = response.css('iframe').attrib['src']
        yield response.follow(src, callback=self.parse_iframe_disclaimer)
    
    def parse_iframe_disclaimer(self, response):
        yield scrapy.FormRequest.from_response(
            response,
            formname="disclaimerFM",
            clickdata={'id', 'submit2'},
            callback=self.parse_query_page
        )


    def parse_query_page(self, response):
        institutions = response.xpath('//select[@id="vCurrentInstitution"]/option[@value != "ALL"]/@value').getall()
        for letter in "abcdefghijklmnopqrstuvwxyz":
            for institution in institutions:
                yield scrapy.FormRequest.from_response(
                    response,
                    formdata={'vLastName': letter, 'vCurrentInstitution': institution},
                    formid="OffenderQueryForm",
                    clickdata={'id': 'NextButton2'},
                    callback=self.parse_search_results
                )

    def parse_search_results(self, response):

        offenders = response.css('form[name^="fm"]')
        for offender in offenders:
            yield scrapy.FormRequest.from_response(
                response,
                formname=offender.attrib['name'],
                clickdata={'type': 'submit'},
                callback=self.parse_offender_page
            )
        
        pagination = response.css('span').re(r'Page (\d+) of (\d+)')

        if len(pagination) == 2 and pagination[0] != pagination[1]:
            scrapy.FormRequest.from_response(
                response,
                formid="form1",
                clickdata={'id': 'oq-nav-nxt'},
                callback=self.parse_search_results
            )

    def _parse_offender_table_row(self, response, name):
        return response.xpath(f'//*[starts-with(text(), "{name}")]/following-sibling::text()').get().strip()

    def parse_offender_page(self, response):
        gdc_id = response.xpath('//text()').re(r'GDC ID: (\d+)')
        year_of_birth = self._parse_offender_table_row(response, "YOB")
        major_offense = self._parse_offender_table_row(response, "MAJOR OFFENSE")
        recent_institution = self._parse_offender_table_row(response, "MOST RECENT INSTITUTION")
        max_release_date = self._parse_offender_table_row(response, "MAX POSSIBLE RELEASE DATE")
        sentence_length = self._parse_offender_table_row(response, "SENTENCE LENGTH")

        # TODO: possibly scrape prior crimes to put in risk calculator

        yield {
            'id': gdc_id,
            'state': 'Georgia',
            'year_of_birth': year_of_birth,
            'major_offense': major_offense,
            'recent_institution': recent_institution,
            'mex_release_date': max_release_date,
            'sentence_length': re.sub(r'  +', ' ', sentence_length)
        }