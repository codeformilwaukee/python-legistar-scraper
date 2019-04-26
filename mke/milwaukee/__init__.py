# encoding=utf-8
from pupa.scrape import Jurisdiction, Organization, Person
from .people import MilwaukeePersonScraper
from .bills import MilwaukeeBillScraper
from .vote_events import MilwaukeeVoteEventScraper
import datetime

class Milwaukee(Jurisdiction):
    division_id = "ocd-division/country:us/state:wi/place:milwaukee"
    classification = "government"
    name = "City of Milwaukee"
    url = "https://milwaukee.legistar.com"
    scrapers = {
        "people": MilwaukeePersonScraper,
        "bills": MilwaukeeBillScraper,
        "vote_events": MilwaukeeVoteEventScraper,
    }

    def get_organizations(self):
        #REQUIRED: define an organization using this format
        #where org_name is something like Seattle City Council
        #and classification is described here:
        org = Organization(name="Common Council", classification="legislature")
        for x in range(1, 16):
            org.add_post(
                "District {}".format(x),
                "Alderman",
                division_id='ocd-division/country:us/state:wi/place:milwaukee/council_district:{}'.format(x))
            
        # OPTIONAL: add posts to your organizaion using this format,
        # where label is a human-readable description of the post (eg "Ward 8 councilmember")
        # and role is the position type (eg councilmember, alderman, mayor...)
        # skip entirely if you're not writing a people scraper.
        #org.add_post(label="position_description", role="position_type")

        #REQUIRED: yield the organization
        yield org

        city = Organization("City of Milwaukee", classification='executive')
        city.add_post('Mayor', 'Mayor', division_id='ocd-division/country:us/state:wi/place:milwaukee')

        yield city

        barrett = Person(name="Barrett, Tom")
        barrett.add_term('Mayor',
                         'executive',
                         start_date=datetime.date(2004, 4, 15),
                         appointment=True)
        barrett.add_source('https://milwaukee.legistar.com/People.aspx')
        yield barrett

