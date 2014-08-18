class SanFrancisco(Config):
    root_url = 'https://sfgov.legistar.com'
    classification = 'government'
    division_id = 'ocd-division/country:us/state:ca/place:san_francisco'

    TIMEZONE = 'America/Los_Angeles'

    TOPLEVEL_ORG_MEMBERSHIP_TITLE = 'Supervisor'
    TOPLEVEL_ORG_MEMBERSHIP_NAME = 'Board of Supervisors'
    EVT_SEARCH_TABLE_TEXT_AUDIO = 'Audio'  # sfgov has this
    EVT_SEARCH_TIME_PERIOD = 'This Year'
    BILL_SEARCH_TABLE_TEXT_INTRO_DATE = 'Introduced'

    def get_district(self, data):
        return self.DEFAULT_AT_LARGE_STRING


class Philadelphia(Config):
    '''XXX: Philadelphia's Legistar instance doesn't have people
    detail pages, so we can't get orgs and memberships from a people
    scrape. They also don't have org detail pages, so all we can
    get are org names, requiring a separate org scrape.
    '''
    TIMEZONE = 'America/New_York'
    root_url = 'https://phila.legistar.com'
    division_id = 'ocd-division/country:us/state:pa/place:philadelphia'
    classification = 'government'

    # C'mon Philly, what's up with that.
    EVT_SEARCH_TABLE_DETAIL_AVAILABLE = False

    CREATE_LEGISLATURE_MEMBERSHIP = True
    PPL_SEARCH_TABLE_DETAIL_AVAILABLE = False
    PPL_PARTY_REQUIRED = False

    BILL_DETAIL_TEXT_COMMITTEE = 'In control'

    EXCLUDE_TOPLEVEL_ORG_MEMBERSHIPS = False
    TOPLEVEL_ORG_MEMBERSHIP_NAME = 'CITY COUNCIL'

    ORG_CLASSIFICATIONS = {
        'CITY COUNCIL': 'legislature',
    }

    def get_district(self, data):
        return self.DEFAULT_AT_LARGE_STRING

    person_titles = ('Council President', 'Councilmember')

    def person_name(self):
        rgx = '(%s)' % '|'.join(self.person_titles)
        return re.sub(rgx, '', )

    #overrides('OrgsAdapter.should_drop_organization')
    def should_drop_organization(self, data):
        allowed_orgs = ('committee', 'department', 'city council')
        return data['type'].lower() not in allowed_orgs

    #overrides('MembershipConverter.should_create_legislature_membership')
    def should_create_legislature_membership(self):
        if 'council' not in self.person.name:
            return True


class Chicago(Config):
    division_id = 'ocd-division/country:us/state:il/place:chicago'
    root_url = 'https://chicago.legistar.com'
    classification = 'government'
    TIMEZONE = 'America/Chicago'

    EXCLUDE_TOPLEVEL_ORG_MEMBERSHIPS = True

    PPL_DETAIL_TABLE_TEXT_ORG = 'Legislative Body'
    PPL_SEARCH_TABLE_TEXT_FULLNAME = 'Person Name'
    PPL_SEARCH_TABLE_TEXT_WEBSITE =  'Website'
    ORG_SEARCH_TABLE_TEXT_NAME = 'Legislative Body'

    BILL_SEARCH_TABLE_TEXT_FILE_NUMBER = 'Record #'
    BILL_DETAIL_TEXT_COMMITTEE = 'Current Controlling Legislative Body'

    #overrides('OrgsAdapter.get_classification')
    def orgs_get_classn(self):
        return self.cfg.get_org_classification(self.data['name'])

    #overrides('OrgsAdapter.should_drop_organization')
    def should_drop_organization(self, data):
        # Skip phone orgs like "Office of the Mayor"
        return data['name'].lower().startswith('office of')

    #overrides('BillsAdapter.should_drop_bill')
    def should_drop_bill(self, data):
        '''The chicago legistar site has type error where two bills in the
        same session have the same id. One is just to approve a handicapped
        parking permit. This drops it.
        '''
        drop_guids = [
            'B99F2EAD-A0CF-44FA-899D-1AC5D8A561C7'
            ]
        for identifier in data['identifiers']:
            if identifier['scheme'] == 'legistar_guid':
                if identifier['identifier'] in drop_guids:
                    return True

        return False

    #overrides('PeopleAdapter.should_drop_person')
    def should_drop_bill(self, data):
        if data['name'] in ('Emanuel, Rahm', 'Mendoza, Susana A.'):
            return True
        return False


class Madison(Config):
    '''XXX: Something horribly wrong with people paginated results.
    Keep getting page 1 back.
    '''
    root_url = 'http://madison.legistar.com/'
    division_id = 'ocd-division/country:us/state:wi/place:madison'
    classification = 'government'
    TIMEZONE = 'America/Chicago'

    PPL_SEARCH_TABLE_TEXT_FULLNAME = 'Name'
    ORG_SEARCH_TABLE_TEXT_NAME = 'Boards, Commissions and Committees'
    ORG_CLASSIFICATIONS = {
        'ALLIED AREA TASK FORCE': 'commission',
        'TRANSPORT 2020 IMPLEMENTATION TASK FORCE': 'commission',
        'COMMON COUNCIL': 'legislature',
        'COMMON COUNCIL - DISCUSSION': 'commission',
        'COMMUNITY ACTION COALITION FOR SOUTH CENTRAL WISCONSIN INC': 'commission',
        'COMMUNITY DEVELOPMENT AUTHORITY': 'commission',
        'MADISON COMMUNITY FOUNDATION': 'commission',
        'MADISON FOOD POLICY COUNCIL': 'commission',
        'MADISON HOUSING AUTHORITY': 'commission',
        'PARKING COUNCIL FOR PEOPLE WITH DISABILITIES': 'commission',
    }

    def person_district(self, data):
        '''This corresponds to the label field on organizations posts.
        '''
        # First try to get it from bio.
        dist = re.findall(r'District\s+\d+', data['notes'])
        if dist:
            return dist.pop()

        # Then try website.
        dist = re.findall(r'/district(\d+)/', data['website'])
        if dist:
            return dist.pop()

        # Then email.
        dist = re.findall(r'district(\d+)', data['email'])
        if dist:
            return dist.pop()

    #overrides('OrgsAdapter.get_classification')
    def orgs_get_classn(self):
        return self.cfg.get_org_classification(self.data['name'])


class JonesBoro(Config):
    '''XXX: on this one, top level org is not listed on people detail
    tables, so have to create it specially.
    '''
    division_id = 'ocd-division/country:us/state:ar/place:jonesboro'
    root_url = 'http://jonesboro.legistar.com/'


class SolanoCounty(Config):
    '''Works with the defaults!
    '''
    root_url = 'https://solano.legistar.com'



class MWRD(Config):
    division_id = 'ocd-division/country:us/state:il/sewer:mwrd'
    root_url = 'https://mwrd.legistar.com'


class BoroughofSitka(Config):
    '''Works with the defaults!
    '''
    root_url = 'http://sitka.legistar.com/'


class Foley(Config):
    '''Works with the defaults!
    '''
    root_url = 'http://cityoffoley.legistar.com/'


class Maricopa(Config):
    '''XXX: Bill search Form doesn't work for Maricopa, for some reason.
    '''
    root_url = 'http://maricopa.legistar.com/'
    PPL_SEARCH_TABLE_DETAIL_AVAILABLE = False


class Mesa(Config):
    '''Works with the defaults!
    '''
    root_url = 'http://mesa.legistar.com/'


class Rialto(Config):
    root_url = 'http://rialto.legistar.com/'
    division_id = 'ocd-jurisdiction/country:us/state:az/place:rialto'
    PPL_SEARCH_TABLE_DETAIL_AVAILABLE = False


class Barrie(Config):
    root_url = 'http://barrie.legistar.com/'
    division_id = 'ocd-division/country:ca/csd:3510045/place:barrie'
    PPL_SEARCH_TABLE_DETAIL_AVAILABLE = False
    ORG_CLASSIFICATIONS = {
        'Circulation List': 'committee',
        }


class LassenCounty(Config):
    '''Works with the defaults!
    '''
    root_url = 'http://lassen.legistar.com/'
    division_id = 'ocd-division/country:us/state:ca/county:lassen'
    classification = 'government'
    TIMEZONE = 'America/Los_Angeles'

    BILL_DETAIL_TEXT_AGENDA = 'OnAgenda2'


class LongBeach(Config):
    root_url = 'http://longbeach.legistar.com/'


class MontereyCounty(Config):
    verbose_name = "County of Monterey"
    division_id = 'ocd-division/country:us/state:ca/county:monterey'
    root_url = 'http://monterey.legistar.com/'
    PPL_SEARCH_TABLE_DETAIL_AVAILABLE = False


class Oakland(Config):
    '''Has two org classifications that I can't figure out how
    to map to pupa org classifications: "Special Meeting" and "Requestor"
    '''
    root_url = 'http://oakland.legistar.com/'
    division_id = 'ocd-division/country:us/state:ca/place:oakland'
    PPL_SEARCH_TABLE_DETAIL_AVAILABLE = False


class SanLeandro(Config):
    verbose_name = 'City of San Leoandro'
    root_url = 'http://sanleandro.legistar.com/'
    division_id = 'ocd-division/country:us/state:ca/place:san_leandro'
    PPL_SEARCH_TABLE_DETAIL_AVAILABLE = False


class SantaBarbaraCounty(Config):
    root_url = 'http://santabarbara.legistar.com/'
    division_id = 'ocd-division/country:us/state:ca/county:santa_barbara'


class CommerceCity(Config):
    root_url = 'http://commerce.legistar.com/'


class CoralGables(Config):
    root_url = 'http://coralgables.legistar.com/'
    division_id = 'ocd-division/country:us/state:fl/place:coral_gables'


class Eustis(Config):
    root_url = 'http://eustis.legistar.com/'


class FortLauderdale(Config):
    root_url = 'http://fortlauderdale.legistar.com/'
    division_id = "ocd-division/country:us/state:fl/place:fort_lauderdale"


class KeyWest(Config):
    root_url = 'http://keywest.legistar.com/'
    division_id = 'ocd-division/country:us/state:fl/place:key_west'


class SeminoleCounty(Config):
    root_url = 'http://seminolecounty.legistar.com/'
    division_id = 'ocd-division/country:us/state:fl/county:seminole'


class PembrokePines(Config):
    root_url = 'http://ppines.legistar.com/'
    division_id = 'ocd-division/country:us/state:fl/place:pembroke_pines'
    PPL_SEARCH_TABLE_DETAIL_AVAILABLE = False


class Gainesville(Config):
    root_url = 'http://gainesville.legistar.com/'
    division_id = 'ocd-division/country:us/state:fl/place:gainesville'


class Canton(Config):
    root_url = 'http://canton.legistar.com/'
    division_id = 'ocd-division/country:us/state:ga/place:canton'


class Carrollton(Config):
    root_url = 'http://carrolltontx.legistar.com/'
    division_id = 'ocd-division/country:us/state:tx/place:carrollton'
    PPL_SEARCH_TABLE_DETAIL_AVAILABLE = False


class PowderSprings(Config):
    root_url = 'http://powd.legistar.com/'
    division_id = 'ocd-division/country:us/state:ga/place:powder_springs'


class Lombard(Config):
    root_url = 'http://lombard.legistar.com/'
    division_id = 'ocd-division/country:us/state:il/place:lombard'


class SedgwickCounty(Config):
    root_url = 'http://sedgwickcounty.legistar.com/'
    PPL_SEARCH_TABLE_DETAIL_AVAILABLE = False


class RochesterHills(Config):
    root_url = 'http://roch.legistar.com/'


class AnnArbor(Config):
    root_url = 'http://a2gov.legistar.com/'


class GrandRapids(Config):
    root_url = 'http://grandrapids.legistar.com/'


class SaintPaul(Config):
    root_url = 'http://stpaul.legistar.com/'
    PPL_SEARCH_TABLE_DETAIL_AVAILABLE = False


class Gulfport(Config):
    root_url = 'http://gulfport.legistar.com/'


class Hattiesburg(Config):
    root_url = 'http://hattiesburg.legistar.com/'


class MecklenburgCounty(Config):
    root_url = 'http://mecklenburg.legistar.com/'


class Wilmington(Config):
    root_url = 'http://wilmington.legistar.com/'


class HighPoint(Config):
    root_url = 'http://highpoint.legistar.com/'
    PPL_SEARCH_TABLE_DETAIL_AVAILABLE = False


class Newwark(Config):
    root_url = 'http://newark.legistar.com/'


class Albuquerque(Config):
    root_url = 'http://cabq.legistar.com/'
    PPL_SEARCH_TABLE_DETAIL_AVAILABLE = False


class LosAlamos(Config):
    root_url = 'http://losalamos.legistar.com/'
    PPL_SEARCH_TABLE_DETAIL_AVAILABLE = False


class Roswell(Config):
    root_url = 'http://roswell.legistar.com/'
    PPL_SEARCH_TABLE_DETAIL_AVAILABLE = False


class Columbus(Config):
    root_url = 'http://columbus.legistar.com/'
    PPL_SEARCH_TABLE_DETAIL_AVAILABLE = False


class Groveport(Config):
    root_url = 'http://groveport.legistar.com/'
    PPL_SEARCH_TABLE_DETAIL_AVAILABLE = False


class Milwaukee(Config):
    root_url = 'http://milwaukee.legistar.com/'


class MilwaukeeCounty(Config):
    root_url = 'http://milwaukeecounty.legistar.com/'


class Gahanna(Config):
    root_url = 'http://gahanna.legistar.com/'


class Norman(Config):
    root_url = 'http://norman.legistar.com/'


class Pittsburgh(Config):
    root_url = 'http://pittsburgh.legistar.com/'
    PPL_SEARCH_TABLE_DETAIL_AVAILABLE = False


class RockHill(Config):
    root_url = 'http://rockhill.legistar.com/'


class Crossville(Config):
    root_url = 'http://crossvilletn.legistar.com/'
    PPL_SEARCH_TABLE_DETAIL_AVAILABLE = False


class Coppell(Config):
    root_url = 'http://coppell.legistar.com/'


class CorpusChristi(Config):
    root_url = 'http://corpuschristi.legistar.com/'
    PPL_SEARCH_TABLE_DETAIL_AVAILABLE = False


class LeagueCity(Config):
    root_url = 'http://leaguecity.legistar.com/'


class Mansfield(Config):
    root_url = 'http://mansfield.legistar.com/'


class McKinney(Config):
    root_url = 'http://mckinney.legistar.com/'


class Pflugerville(Config):
    root_url = 'http://pflugerville.legistar.com/'


class Alexandria(Config):
    root_url = 'http://alexandria.legistar.com/'
    PPL_SEARCH_TABLE_DETAIL_AVAILABLE = False


class Longview(Config):
    root_url = 'http://longview.legistar.com/'


class Olympia(Config):
    root_url = 'http://olympia.legistar.com/'
