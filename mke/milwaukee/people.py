import collections

from pupa.scrape import Scraper
from legistar.people import LegistarAPIPersonScraper, LegistarPersonScraper
import re


class MilwaukeePersonScraper(LegistarAPIPersonScraper, Scraper):
    BASE_URL = 'http://webapi.legistar.com/v1/milwaukee'
    WEB_URL = "https://milwaukee.legistar.com"
    TIMEZONE = "America/Chicago"
    def scrape(self):
        body_types = self.body_types()

        city_council, = [body for body in self.bodies()
                            if body['BodyName'] == 'COMMON COUNCIL']

        terms = collections.defaultdict(list)
        for office in self.body_offices(city_council):
            terms[office['OfficeRecordFullName'].strip()].append(office)

        web_scraper = LegistarPersonScraper(
            requests_per_minute=self.requests_per_minute)
        web_scraper.MEMBERLIST ='https://milwaukee.legistar.com/DepartmentDetail.aspx?ID=1998&GUID=74273156-5389-46F3-9D09-3D850BDE32A1'
        #web_scraper.ALL_MEMBERS = '3:3'

        if self.cache_storage:
            web_scraper.cache_storage = self.cache_storage

        if self.requests_per_minute == 0:
            web_scraper.cache_write_only = False

        web_info = {}
        for member, _ in web_scraper.councilMembers({'ctl00$ContentPlaceHolder$lstName': 'COMMON COUNCIL'}):
            web_info[member['Person Name']['label']] = member
        
        members = {}
        for member, offices in terms.items():
            web = web_info[member]
            p = Person(member)
            for term in offices:
                role = term['OfficeRecordTitle']
                district = re.search('(?<=(/{1}district))[\w]+',
                          web['Website']['url']).group(0)
                p.add_term('Alderman',
                            'legislature',
                            district="District {}".format(int(district)),
                            start_date=self.toDate(term['OfficeRecordStartDate']),
                            end_date=self.toDate(term['OfficeRecordEndDate']))
            if web.get('Photo'):
                p.image = web['Photo']

            contact_types = {
            "City Hall Address": ("address", "City Hall Address"),
            "City Hall Phone": ("voice", "City Hall Phone"),
            "District Office Phone": ("voice", "District Office Phone"),
            "District Office Address": ("address","District Office Address"),
            "Fax":("fax","Fax")}

            for contact_type, (type_,_note) in contat_ctypes.items():
                if web[contact_type] and web[contact_type] != 'N/A':
                    p.add_contact_detail(type=type_, value=web[contact_type], note=_note)

            if web['E-mail'] and web['E-mail']['label'] and web['E-mail']['label'] !='N/A':
                p.add_contact_detail(type='email',value=web['E-mail']['label'],
                note='E-mail')


            if web["Website"]:
                p.add_link(web["Website"]['url'])

            source_urls = self.person_sources_from_office(term)
            person_api_url, person_web_url = source_urls
            p.add_source(person_api_url, note='api')
            p.add_source(person_web_url, note='web')
        #pass
