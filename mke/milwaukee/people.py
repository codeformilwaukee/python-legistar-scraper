import collections

from pupa.scrape import Person, Organization, Scraper
from legistar.people import LegistarAPIPersonScraper, LegistarPersonScraper
import re
import pdb

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
            #member is a dict itself
            #print(web_info[member['Person Name']['label']], member, 'line 35')
            
            web_info[member['Person Name']['label']] = member
        
        

        members = {}
        for member, offices in terms.items():
            #pdb.set_trace()
            print(member)
            if member in web_info.keys():
                print('47 YES')
                web = web_info[member]
                #pdb.set_trace()
                p = Person(member)
                for term in offices:
                    role = term['OfficeRecordTitle']
                    district = term['OfficeRecordSort']
                    p.add_term('Alderman',
                                'legislature',
                                district="District {}".format(int(district)),
                                start_date=self.toDate(term['OfficeRecordStartDate']),
                                end_date=self.toDate(term['OfficeRecordEndDate']))

                #pdb.set_trace()
                if web.get('Photo'):
                    p.image = web['Photo']
                
                #not in dicts

                # contact_types = {
                # "City Hall Address": ("address", "City Hall Address"),
                # "City Hall Phone": ("voice", "City Hall Phone"),
                # "District Office Phone": ("voice", "District Office Phone"),
                # "District Office Address": ("address","District Office Address"),
                # "Fax":("fax","Fax")}

                # for contact_type, (type_,_note) in contact_types.items():
                #     if web[contact_type] and web[contact_type] != 'N/A':
                #         p.add_contact_detail(type=type_, value=web[contact_type], note=_note)

                if web['E-mail'] and web['E-mail']['label'] and web['E-mail']['label'] !='N/A':
                    p.add_contact_detail(type='email',value=web['E-mail']['label'],
                    note='E-mail')

                if 'Website' in web.keys():
                    if web["Website"]:
                        p.add_link(web["Website"]['url'])

                source_urls = self.person_sources_from_office(term)
                person_api_url, person_web_url = source_urls
                p.add_source(person_api_url, note='api')
                p.add_source(person_web_url, note='web')

                members[member] = p
        
        for body in self.bodies():
            
            #pdb.set_trace() 
            if body['BodyName'] == 'COMMON COUNCIL':
                o = Organization(body['BodyName'],
                                classification='committee',
                                parent_id={'name': 'Milwaukee Common Council'})
                #pdb.set_trace()                 
                o.add_source(self.BASE_URL + '/bodies/{BodyName}'.format(**body), note='api')
                o.add_source(self.WEB_URL + '/DepartmentDetail.aspx?ID={BodyName}&GUID={BodyGuid}'.format(**body), note='web')
                
                #The legistar does not list who the president is...
                for office in self.body_offices(body):
                    if office['OfficeRecordLastName'] == 'Hamilton':
                        role = "President"
                    else:
                        role = "Member"

                person = office['OfficeRecordFullName'].strip()
                if person in members:
                    p = members[person]
                else:
                    p = Person(person)

                    source_urls = self.person_sources_from_office(term)
                    person_api_url, person_web_url = source_urls
                    p.add_source(person_api_url, note='api')
                    p.add_source(person_web_url, note='web')

                    members[person] = p

                p.add_membership(body['BodyName'],
                                role = role,
                                start_date = self.toDate(office['OfficeRecordStartDate']),
                                end_date= self.toDate(office['OfficeRecordEndDate']))
            yield o
        
        for body in self.bodies(): 
            #pdb.set_trace()
            if body['BodyTypeId'] == body_types['Policies and Standards Committee']:
                o = Organization(body['BodyName'],
                        classification='committee',
                        parent_id={'name' : 'Milwaukee Common Council'})
                o.add_source(self.BASE_URL + '/bodies/{BodyName}'.format(**body), note='api')
                o.add_source(self.WEB_URL + '/DepartmentDetail.aspx?ID={BodyName}&GUID={BodyGuid}'.format(**body), note='web')
                yield o   

        for p in  members.values():
            yield p
        #pass
