import scrapy
import urllib.parse


class FloridaSentenceSpider(scrapy.Spider):
    name = 'florida-sentence'
    allowed_domains = ['dc.state.fl.us/offenderSearch/']

    def _build_init_request(self, letter):
        params = {
            'TypeSearch': 'AI',
            'Page': 'List',
            'DataAction': 'Filter',
            'dcnumber': '',
            'LastName': letter,
            'FirstName': '',
            'SearchAliases': '0',
            'OffenseCategory': '',
            'CurrentLocation': '',
            'CountyOfCommitment': '',
            'photosonly': '0',
            'nophotos': '0',
            'matches': '20'
        }

        query_params = urllib.parse.urlencode(params)
        return "http://www.dc.state.fl.us/offenderSearch/list.aspx?" + query_params

    def start_requests(self):
        return [scrapy.Request(self._build_init_request(letter), callback=self.parse) for letter in "abcdefghijklmnopqrstuvwxyz"]

    def parse(self, response):
        offenders = response.xpath('//table/tr///@href')[::2]
        yield from response.follow_all(offenders, callback=self.parse_offender_page)

        if response.xpath('//input[@value="Next" and not(@disabled)]').get():
            yield scrapy.FormRequest.from_response(
                response,
                formid="aspnetForm",
                clickdata={'type': 'submit', 'value': 'Next'},
                callback=self.parse
            )

    def _parse_prison_sentence(self, row):
        [_offense_date, offense, sentence_date, _county, _case_no, sentence_length] = row
        return {
            'offense': offense.strip(),
            'sentence_date': sentence_date.strip(),
            'sentence_length': sentence_length.strip()
        }

    def parse_offender_page(self, response):
        dc_number = response.css('span.DCNum::text').get()
        birth_date = response.xpath('//th[starts-with(text(), "Birth Date")]/following-sibling::td/text()').get()
        current_release_date = response.xpath('//th[starts-with(text(), "Current Release Date")]/following-sibling::td/text()').get()
        initial_receipt_date = response.xpath('//th[starts-with(text(), "Initial Receipt Date")]/following-sibling::td/text()').get()
        sentence_history_table = response.css('#ctl00_ContentPlaceHolder1_divCurrentPrison tr:nth-child(n+2) td::text')

        yield {
            'id': dc_number,
            'state': 'Florida',
            'dob': birth_date,
            'current_release_date': current_release_date,
            'initial_receipt_date': initial_receipt_date,
            'sentence_history': [self._parse_prison_sentence(sentence_history_table[x:x+6]) for x in range(0, len(sentence_history_table), 6)]
        }
