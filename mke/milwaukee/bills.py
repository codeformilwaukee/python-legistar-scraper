from legistar.bills import LegistarBillScraper, LegistarAPIBillScraper
from pupa.scrape import Bill, VoteEvent, Scraper
from pupa.utils import _make_pseudo_id
import datetime
#import itertools
import pytz
import requests

class MilwaukeeBillScraper(Scraper):

    def sort_actions(actions):
        action_time = 'MatterHistoryActionDate'
        action_name = 'MatterHistoryActionName'
        sorted_actions = sorted(actions,
                                key=lambda x: (x[action_time].split('T')[0],
                                            ACTION[x[action_name]]['order'],
                                            x[action_time].split('T')[1]))
        return sorted_actions

    def sponsorships(self, matter_id):
        for i, sponsor in enumerate(self.sponsors(matter_id)):
            sponsorship = {}
            if i == 0:
                sponsorship['primary'] = True
                sponsorship['classification'] = "Primary"
            else:
                sponsorship['primary'] = False
                sponsorship['classification'] = "Regular"

            sponsor_name = sponsor['MatterSponsorName'].strip()

            if sponsor_name.startswith(('City Clerk',)):
                sponsorship['name'] = 'Office of the City Clerk'
                sponsorship['entity_type'] = 'organization'
            else:
                sponsorship['name'] = sponsor_name
                sponsorship['entity_type'] = 'person'

            if not sponsor_name.startswith(('Misc. Transmittal',
                                            'No Sponsor',
                                            'Dept./Agency')):
                yield sponsorship

    class ChicagoBillScraper(LegistarAPIBillScraper, Scraper):
        BASE_URL = 'http://webapi.legistar.com/v1/milwaukee'
        BASE_WEB_URL = 'https://milwaukee.legistar.com'
        TIMEZONE = "US/Central"

        #ignoring for now
        # VOTE_OPTIONS = {'yea': 'yes',
        #                 'rising vote': 'yes',
        #                 'nay': 'no',
        #                 'recused': 'excused'}

    def scrape(self):
        # needs to be implemented
        pass
