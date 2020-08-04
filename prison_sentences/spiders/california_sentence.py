import scrapy


class CaliforniaSentenceSpider(scrapy.Spider):
    name = 'california-sentence'
    allowed_domains = ['inmatelocator.cdcr.ca.gov']
    start_urls = ['https://inmatelocator.cdcr.ca.gov/']

    def parse(self, response):
        yield scrapy.FormRequest.from_response(
            response,
            formid="frmDisclaimer",
            clickdata={'type': 'submit'},
            callback=self.parse_search_page
        )

    def parse_search_page(self, response):
        for first_name_letter in "abcdefghijklmnopqrstuvwxyz":
            for last_name_letter in "abcdefghijklmnopqrstuwxyz":
                yield scrapy.FormRequest.from_response(
                    response,
                    formdata={'ctl00$LocatorPublicPageContent$txtLastName': last_name_letter, 'ctl00$LocatorPublicPageContent$txtFirstName': first_name_letter},
                    formid="frmOffenderSearch",
                    clickdata={'id': 'LocatorPublicPageContent_btnSearch'},
                    callback=self.parse_search_results
                )

    def parse_search_results(self, response):
        offenders = response.xpath('//a[@href]/@href').re(r'Details\.aspx\?ID=[A-Z0-9]+')
        yield from response.follow_all(offenders, callback=self.parse_person_page)

        # Get next page
        next_button = response.xpath('//a[@href and text() = "Next Page"]/@href').get()
        if next_button:
            yield scrapy.FormRequest.from_response(
                response,
                formid="form1",
                clickdata={'href': next_button},
                callback=self.parse_search_results
            )

    
    def _parse_person_row(self, table, text):
        return table.xpath(f'./tr[./td[1]/text() = "{text}"]/td[2]/text()').get()


    def parse_person_page(self, response):
        person_table = response.css('table#LocatorPublicPageContent_DetailsView1')
        cdcr_number = self._parse_person_row(person_table, "CDCR Number")
        age = self._parse_person_row(person_table, "Age")
        admission_date = self._parse_person_row(person_table, "Admission Date")
        parole_eligible_date = self._parse_person_row(person_table, "Parole Eligible Date (Month/Year)")


        yield {
            'id': cdcr_number,
            'age': age,
            'admission_date': admission_date,
            'parole_date': parole_eligible_date
        }