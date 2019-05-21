from legistar.bills import LegistarBillScraper, LegistarAPIBillScraper
from pupa.scrape import Bill, VoteEvent, Scraper
from pupa.utils import _make_pseudo_id
import datetime
#import itertools
import pytz
import requests

def sort_actions(actions):
        action_time = 'MatterHistoryActionDate'
        action_name = 'MatterHistoryActionName'
        sorted_actions = sorted(actions,
                                key=lambda x: (x[action_time].split('T')[0],
                                               ACTION[x[action_name]]['order'],
                                               x[action_time].split('T')[1]))
        return sorted_actions


class MilwaukeeBillScraper(LegistarAPIBillScraper, Scraper):
    BASE_URL = 'http://webapi.legistar.com/v1/milwaukee'
    BASE_WEB_URL = 'https://milwaukee.legistar.com'
    TIMEZONE = "US/Central"


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


    def actions(self, matter_id):
        old_action = None
        actions = self.history(matter_id)
        actions = sort_actions(actions)

        for action in actions:
            action_date = action['MatterHistoryActionDate']
            action_description = action['MatterHistoryActionName']
            responsible_org = action['MatterHistoryActionBodyName']

            action_date = self.toTime(action_date).date()

            responsible_person = None
            if responsible_org == 'COMMON COUNCIL':
                responsible_org = 'Milwaukee Common Council'
            elif responsible_org == 'Office of the Mayor':
                responsible_org = 'City of Milwaukee'
                if action_date < datetime.date(2004, 4, 15):
                    responsible_person = 'Norquist, John'
                else:
                    responsible_person = 'Barrett, Tom'

            bill_action = {'description': action_description,
                           'date': action_date,
                           'organization': {'name': responsible_org},
                           'classification': ACTION[action_description]['ocd'],
                           'responsible person': responsible_person}
            if bill_action != old_action:
                old_action = bill_action
            else:
                continue

            if (action['MatterHistoryEventId'] is not None
                and action['MatterHistoryRollCallFlag'] is not None
                    and action['MatterHistoryPassedFlag'] is not None):

                # Do we want to capture vote events for voice votes?
                # Right now we are not?
                bool_result = action['MatterHistoryPassedFlag']
                result = 'pass' if bool_result else 'fail'

                votes = (result, self.votes(action['MatterHistoryId']))
            else:
                votes = (None, [])

            yield bill_action, votes

            
    def scrape(self):
        # needs to be implemented
        pass
