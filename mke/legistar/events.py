import time
import datetime
from collections import deque

import lxml.html
import pytz
import icalendar

from .base import LegistarScraper, LegistarAPIScraper


class LegistarEventsScraper(LegistarScraper):
    def eventPages(self, since):
        response = self.get(self.EVENTSPAGE, verify=False)
        entry = response.text
        page = lxml.html.fromstring(entry)
        page.make_links_absolute(self.EVENTSPAGE)

        for page in self.eventSearch(page, since):
            yield page

    def should_cache_response(self, response):
        # Never cache the top level events page, because that may result in
        # expired .NET state values.
        return (super().should_cache_response(response) and
                response.url != self.EVENTSPAGE)

    def eventSearch(self, page, since):
        payload = self.sessionSecrets(page)

        payload['ctl00_ContentPlaceHolder1_lstYears_ClientState'] = '{"value":"%s"}' % since

        payload['__EVENTTARGET'] = 'ctl00$ContentPlaceHolder1$lstYears'

        return self.pages(self.EVENTSPAGE, payload)

    def events(self, follow_links=True, since=None):
        # If an event is added to the the legistar system while we
        # are scraping, it will shift the list of events down and
        # we might revisit the same event. So, we keep track of
        # the last few events we've visited in order to
        # make sure we are not revisiting
        scraped_events = deque([], maxlen=10)

        current_year = self.now().year

        if since:
            if since > current_year:
                raise ValueError(
                    'Value of :since cannot exceed {}'.format(current_year))
            else:
                since_year = since - 1

        else:
            since_year = 0

        # Anticipate events will be scheduled for the following year to avoid
        # missing upcoming events during scrapes near the end of the current
        # year.
        for year in range(current_year + 1, since_year, -1):
            no_events_in_year = True

            for page in self.eventPages(year):
                no_events_in_year = False
                events_table = page.xpath("//table[@class='rgMasterTable']")[0]
                for event, _, _ in self.parseDataTable(events_table):
                    if follow_links and type(event["Meeting Details"]) == dict:
                        detail_url = event["Meeting Details"]['url']
                        if detail_url in scraped_events:
                            continue
                        else:
                            scraped_events.append(detail_url)

                        agenda = self.agenda(detail_url)

                    else:
                        agenda = None

                    yield event, agenda

            if no_events_in_year:  # Bail from scrape if no results returned from year
                break

    def agenda(self, detail_url):
        page = self.lxmlize(detail_url)

        payload = self.sessionSecrets(page)

        payload.update({"__EVENTARGUMENT": "3:1",
                        "__EVENTTARGET": "ctl00$ContentPlaceHolder1$menuMain"})

        for page in self.pages(detail_url, payload):
            agenda_table = page.xpath(
                "//table[@id='ctl00_ContentPlaceHolder1_gridMain_ctl00']")[0]
            agenda = self.parseDataTable(agenda_table)
            yield from agenda

    def addDocs(self, e, events, doc_type):
        try:
            if events[doc_type] != 'Not\xa0available':
                e.add_document(note=events[doc_type]['label'],
                               url=events[doc_type]['url'],
                               media_type="application/pdf")
        except ValueError:
            pass

    def extractRollCall(self, action_detail_url):
        action_detail_page = self.lxmlize(action_detail_url)
        try:
            rollcall_table = action_detail_page.xpath(
                "//table[@id='ctl00_ContentPlaceHolder1_gridRollCall_ctl00']")[0]
        except IndexError:
            self.warning("No rollcall found in table")
            return []
        roll_call = list(self.parseDataTable(rollcall_table))
        call_list = []
        for call, _, _ in roll_call:
            option = call['Attendance']
            call_list.append((option,
                              call['Person Name']['label']))

        return call_list

    def ical(self, ical_text):
        value = icalendar.Calendar.from_ical(ical_text)
        return value


class LegistarAPIEventScraper(LegistarAPIScraper):

    def events(self, since_datetime=None):
        # Set attribute equal to an instance of our generator yielding events
        # scraped from the Legistar web interface. This allows us to pause
        # and resume iteration as needed.
        self._events = self._scrapeWebCalendar()

        # Instantiate dictionary where events from generator are stored as they
        # are scraped.
        self._scraped_events = {}

        for api_event in self.api_events(since_datetime):

            time_str = api_event['EventTime']
            if not time_str:  # If we don't have an event time, skip it
                continue

            start_time = time.strptime(time_str, '%I:%M %p')

            start = self.toTime(api_event['EventDate'])
            api_event['start'] = start.replace(hour=start_time.tm_hour,
                                               minute=start_time.tm_min)

            api_event['status'] = self._event_status(api_event)

            if self._not_in_web_interface(api_event):
                continue

            else:
                # None if entire web calendar scraped but API event not found
                web_event = self.web_results(api_event)

                if web_event:
                    yield api_event, web_event

                else:
                    event_url = '{0}/events/{1}'.format(self.BASE_URL, api_event['EventId'])
                    self.warning('API event could not be found in web interface: {0}'.format(event_url))
                    continue

    def api_events(self, since_datetime=None):
        # scrape from oldest to newest. This makes resuming big
        # scraping jobs easier because upon a scrape failure we can
        # import everything scraped and then scrape everything newer
        # then the last event we scraped
        params = {'$orderby': 'EventLastModifiedUtc'}

        if since_datetime:
            # Minutes are often published after an event occurs – without a
            # corresponding event modification. Query all update fields so later
            # changes are always caught by our scraper, particularly when
            # scraping narrower windows of time.
            update_fields = ('EventLastModifiedUtc',
                             'EventAgendaLastPublishedUTC',
                             'EventMinutesLastPublishedUTC')

            since_fmt = " gt datetime'{}'".format(since_datetime.isoformat())
            since_filter = ' or '.join(field + since_fmt for field in update_fields)

            params['$filter'] = since_filter

        events_url = self.BASE_URL + '/events/'

        yield from self.pages(events_url,
                              params=params,
                              item_key="EventId")

    def agenda(self, event):
        agenda_url = (self.BASE_URL +
                      '/events/{}/eventitems'.format(event['EventId']))

        response = self.get(agenda_url)

        # If an event item does not have a value for
        # EventItemAgendaSequence, it is not on the agenda
        filtered_items = (item for item in response.json()
                          if (item['EventItemTitle'] and
                              item['EventItemAgendaSequence']))
        sorted_items = sorted(filtered_items,
                              key=lambda item: item['EventItemAgendaSequence'])

        for item in sorted_items:
            self._suppress_item_matter(item, agenda_url)
            yield item

    def minutes(self, event):
        minutes_url = (self.BASE_URL +
                       '/events/{}/eventitems'.format(event['EventId']))

        response = self.get(minutes_url)

        # If an event item does not have a value for
        # EventItemMinutesSequence, it is not in the minutes
        filtered_items = (item for item in response.json()
                          if (item['EventItemTitle'] and
                              item['EventItemMinutesSequence']))
        sorted_items = sorted(filtered_items,
                              key=lambda item: item['EventItemMinutesSequence'])

        for item in sorted_items:
            self._suppress_item_matter(item, minutes_url)
            yield item

    def _suppress_item_matter(self, item, agenda_url):
        '''
        Agenda items in Legistar do not always display links to
        associated matter files even if the same agenda item
        in the API references a Matter File. The agenda items
        we scrape should honor the suppression on the Legistar
        agendas.

        This is also practical because matter files that are hidden
        in the Legistar Agenda do not seem to available for scraping
        on Legistar or through the API

        Since we are not completely sure that the same suppression
        logic should be used for all Legislative Bodies, this method
        is currently just a hook for being overridden in particular
        scrapers. As of now, at least LA Metro uses this hook.
        '''
        pass

    def rollcalls(self, event):
        for item in self.agenda(event):
            if item['EventItemRollCallFlag']:
                rollcall_url = self.BASE_URL + \
                    '/eventitems/{}/rollcalls'.format(item['EventItemId'])

                response = self.get(rollcall_url)

                for item in response.json():
                    yield item

    def web_results(self, event):
        api_key = (event['EventBodyName'].strip(),
                   event['start'])

        # Check the cache of events we've already scraped from the web interface
        # for the API event at hand.
        if api_key in self._scraped_events:
            return self._scraped_events[api_key]

        else:
            # If API event not in web scrape cache, continue scraping the web
            # interface.
            for web_key, event in self._events:
                self._scraped_events[web_key] = event
                # When we find the API event, stop scraping.
                if web_key == api_key:
                    return event

    def _scrapeWebCalendar(self):
        '''Generator yielding events from Legistar in roughly reverse
        chronological order.
        '''
        web_scraper = LegistarEventsScraper(
            requests_per_minute=self.requests_per_minute,
            retry_attempts=self.retry_attempts)

        if self.cache_storage:
            web_scraper.cache_storage = self.cache_storage

        if self.requests_per_minute == 0:
            web_scraper.cache_write_only = False

        web_scraper.EVENTSPAGE = self.EVENTSPAGE
        web_scraper.BASE_URL = self.WEB_URL
        web_scraper.TIMEZONE = self.TIMEZONE
        web_scraper.date_format = '%m/%d/%Y'

        for event, _ in web_scraper.events(follow_links=False):
            event_key = self._event_key(event, web_scraper)
            yield event_key, event

    def _event_key(self, event, web_scraper):
        '''Since Legistar InSite contains more information about events than
        are available in the API, we need to scrape both. Then, we have
        to line them up. This method makes a key that should be
        uniquely identify every event and will allow us to link
        events from the two data sources.
        '''
        response = web_scraper.get(event['iCalendar']['url'], verify=False)
        event_time = web_scraper.ical(response.text).subcomponents[0]['DTSTART'].dt
        event_time = pytz.timezone(self.TIMEZONE).localize(event_time)

        key = (event['Name']['label'],
               event_time)

        return key

    def addDocs(self, e, events, doc_type):
        try:
            if events[doc_type] != 'Not\xa0available':
                e.add_document(note=events[doc_type]['label'],
                               url=events[doc_type]['url'],
                               media_type="application/pdf")
        except ValueError:
            pass

    def _event_status(self, event):
        '''Events can have a status of tentative, confirmed, cancelled, or
        passed (http://docs.opencivicdata.org/en/latest/data/event.html). By
        default, set status to passed if the current date and time exceeds the
        event date and time, or confirmed otherwise. Available for override in
        jurisdictional scrapers.
        '''
        if datetime.datetime.utcnow().replace(tzinfo=pytz.utc) > event['start']:
            status = 'passed'
        else:
            status = 'confirmed'

        return status

    def _not_in_web_interface(self, event):
        '''Occasionally, an event will appear in the API, but not in the web
        interface. This method checks attributes of the API event that tell us
        whether the given event is one of those cases, returning True if so, and
        False otherwise. Available for override in jurisdictional scrapers.
        '''
        return False
