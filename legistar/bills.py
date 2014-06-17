import re
import json
import time
import collections
from datetime import datetime

from legistar.forms import Form
from legistar.tables import Table, TableRow
from legistar.views import SearchView, DetailView
from legistar.fields import FieldAggregator, make_item, gen_items
from legistar.fields import ElementAccessor
from legistar.base import DictSetDefault, NoClobberDict
from legistar.jurisdictions.utils import resolve_name
# https://github.com/guelo/legistar-scrape/compare/fgregg:master...master

class DateGetter:
    '''Parse a date using the datetime format string defined in
    the current jxn's config.
    '''
    def _get_date(self, label_text):
        fmt = self.get_config_value('datetime_format')
        text = self.get_field_text(label_text)
        if text is not None:
            return datetime.strptime(text, fmt)


class BillsFields(FieldAggregator):

    text_fields = (
        'file_number', 'law_number', 'type', 'status',
        'final_action', 'title', 'name', 'version')

    @make_item('sources', wrapwith=list)
    def gen_sources(self):
        grouped = collections.defaultdict(set)
        for note, url in self.chainmap['sources'].items():
            grouped[url].add(note)
        for url, notes in grouped.items():
            yield dict(url=url, note=', '.join(sorted(notes)))


class BillsSearchView(SearchView):
    sources_note = 'bills search'


class BillsSearchTableRow(TableRow, BillsFields):
    def get_detail_url(self):
        return self.get_field_url('file_number')


class BillsSearchTable(Table):
    sources_note = 'bills search table'


class BillsSearchForm(Form):
    '''Model the legistar "Legislation" search form.
    '''
    sources_note = 'bills search table'

    def get_query(self, time_period=None, bodies=None):
        configval = self.get_config_value
        time_period = time_period or configval('time_period')
        bodies = bodies or configval('types')
        clientstate = json.dumps({'value': time_period})

        query = {
            configval('types_el_name'): bodies,
            configval('time_period_el_name'): time_period,
            configval('clientstate_el_name'): clientstate,
            configval('id_el_name'): configval('id'),
            configval('text_el_name'): configval('text'),
            }
        self.debug('Query is %r' % query)
        query = dict(self.client.state, **query)
        return query


class BillsDetailView(DetailView, BillsFields, DateGetter):
    sources_note = 'bill detail'

    text_fields = ('version', 'name')

    @make_item('agenda', wrapwith=list)
    def get_agenda_date(self):
        return self._get_date('agenda')

    @make_item('enactment_date', wrapwith=list)
    def get_enactment_date(self):
        return self._get_date('enactment_date')

    @make_item('final_action', wrapwith=list)
    def get_enactment_date(self):
        return self._get_date('final_action')

    @make_item('sponsors', wrapwith=list)
    def gen_sponsors(self):
        for name in self.xpath('sponsors', './/a/text()'):
            name = name.strip()
            if name:
                yield dict(name=name)

    @make_item('documents', wrapwith=list)
    def gen_documents(self):
        for el in self.xpath('attachments', './/a'):
            data = ElementAccessor(el)
            url = data.get_url()

            self.debug('Sleeping in between head requests.')
            time.sleep(1)
            resp = self.client.head(url=url)
            mimetype = resp.headers['content-type']
            yield dict(
                name=data.get_text(),
                links=[dict(
                    url=data.get_url(),
                    mimetype=mimetype)])

    @make_item('actions', wrapwith=list)
    def gen_action(self):
        yield from self.Form(self)


class BillsDetailTable(Table):
    sources_note = 'bill detail table'


class BillsDetailForm(Form):
    skip_first_submit = True
    sources_note = 'bill detail'


class BillsDetailTableRow(TableRow, FieldAggregator, DateGetter):
    sources_node = 'bill action table'

    text_fields = (
        ('action_by', 'organization'),
        ('action', 'text'),
        'version',
        )

    def get_detail_viewtype(self):
        return BillsDetailAction

    def get_detail_url(self):
        return self.get_media_url('action_details')

    @make_item('date')
    def get_date(self):
        return self._get_date('date')


class ActionBase(FieldAggregator):

    def get_prefix(self):
        '''The settings prefix for this view.
        '''
        return 'BILL_ACTION'


class BillsDetailAction(DetailView, ActionBase):
    sources_note = 'bill action detail'

    text_fields = (
        'file_number', 'type', 'title', 'mover', 'seconder',
        'result', 'agenda_note', 'minutes_note', 'action',
        'action_text')

    @make_item('votes', wrapwith=list)
    def gen_votes(self):
        table_path = self.get_config_value('table_class')
        Table = resolve_name(table_path)
        yield from self.make_child(Table, self)


class BillsDetailActionTable(Table, ActionBase):
    sources_note = 'bill action detail table'

    def get_table_cell_type(self):
        path = self.get_config_value('tablecell_class')
        return resolve_name(path)

    def get_table_row_type(self):
        path = self.get_config_value('tablerow_class')
        return resolve_name(path)


class BillsDetailActionTableRow(TableRow, ActionBase):
    sources_node = 'bill action detail table'
    text_fields = ('person', 'vote')