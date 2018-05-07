"""
BETA

This module holds a couple functions that generate a more
full-featured API Wrapper.  Since Cerb is so dynamic and
customizable it doesn't make sense to manually create wrappers
for each Record; however, a human-readable way to retrieve
custom fields and custom records would be nice:

cerb.get_record('contexts.custom_record.58', expand=['custom_', 'links'])['custom_field_387']

vs

ComputerAsset.find_one(cerb, query='name:"Unique Name"').get_ip()

When you connect to cerb and run the print_records_module function
the output should be a syntactically sound module to use elsewhere.

BETA BETA BETA

"""
import json
from datetime import datetime
from cerbapi import Cerb, CerbException

import re

RX = re.compile('([^a-z0-9_])')
nums = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine']






def _func_safe(text):
    """ Make a word or phrase safe for use as a function name. """
    if text.startswith(tuple(str(i) for i in range(10))):
        text = text.replace(text[0], nums[int(text[0])], 1)  # Ugly as hell
    return RX.sub('', text.lower().replace(' ', '_').replace('.', '_').replace('-', '_'))


def _print_getter(func_name, identifier):
    print(f"""
    def get_{_func_safe(func_name)}(self):
        return self._backbone['{identifier}']""")

def _print_setter(func_name, field_name):
    print(f"""
    def set_{_func_safe(func_name)}(self, value):
        self.cerb.update_record(self.alias, self.id, fields={{"{field_name}": value}})
        self.reload()""")

def print_records_module(cerb: Cerb):
    print(f"""\"\"\" Auto generated on {datetime.now()}, Cerb Build: {cerb.build}\"\"\"""")
    print("""
from cerbapi import Cerb, CerbException
from collections import OrderedDict
import json


class Record:
    _id = None
    name = None
    plugin_id = None
    alias = None
    params = {
        "names": {},
        "acl": [],
        "options": []
    }
    custom_fields = []
    custom_fieldsets = []

    @staticmethod
    def get_record_by_context(context):
        for sub in Record.__subclasses__():
            if sub._id == context:
                return sub

    @classmethod
    def find_many(cls, cerb: Cerb, query: str="", limit=10000):
        for x in cerb.search_records(cls.alias, query=query, expand=['custom_', 'links'], limit=limit)['results']:
            yield Record.get_record_by_context(cls._id)._create(cerb, x)

    @classmethod
    def find_one(cls, cerb: Cerb, query: str=""):
        result = [r for r in cls.find_many(cerb, query)]
        if len(result) > 1:
            raise Exception(cls.__name__ + " find_one found too many! query: " + query + "")
        if len(result) < 1:
            raise Exception(cls.__name__ + " find_one didn't find enough! query: " + query + "")
        return result[0]

    @classmethod
    def load(cls, cerb: Cerb, record_id: int):
        c = cls.__new__(cls)
        c.cerb = cerb
        c.id = record_id
        c.reload()
        return c

    @classmethod
    def _create(cls, cerb, backbone):
        \"\"\" Bypass the init function (don't create a new instance in Cerb, just locally \"\"\"
        c = cls.__new__(cls)
        c.cerb = cerb
        c.id = backbone['id']
        c._backbone = backbone
        return c

    def __init__(self, cerb: Cerb, **kwargs):
        self.cerb = cerb
        self._backbone = self.cerb.create_record(self.alias, fields=OrderedDict(kwargs))
        self.id = self._backbone['id']

    def reload(self):
        self._backbone = self.cerb.get_record(self.alias, self.id, expand=['links', 'custom_'])

    def get_links(self, record_type=None):
        return self._backbone['links']

    def load_links(self, record):
        \"\"\" Using a record subclass, load full objects from the links (instead of IDs)\"\"\"
        def chunks(lst):
            for i in range(0, len(lst), 1000):
                yield lst[i:i + 1000]
        if record._id in self.get_links():
            for chunk in chunks(self.get_links()[record._id]):
                for rec in record.find_many(self.cerb, "id:" + json.dumps(chunk, separators=(',', ''))):
                    yield rec

    def link(self, other_records):
        if not hasattr(other_records, '__iter__'):
            other_records = [other_records]
        self.cerb.link(f'{self._id}:{self.id}', targets=[f'{r._id}:{r.id}' for r in other_records])

    def unlink(self, other_records):
        if not hasattr(other_records, '__iter__'):
            other_records = [other_records]
        self.cerb.unlink(f'{self._id}:{self.id}', targets=[f'{r._id}:{r.id}' for r in other_records])

    def __eq__(self, other):
        return self.alias == other.alias and self.id == other.id

    def __str__(self):
        if 'name' in self._backbone:
            return f"{self.__class__.__name__}({self.id}, {self._backbone['name']})"
        else:
            return f"{self.__class__.__name__}({self.id})"

    def __repr__(self):
        return json.dumps(self._backbone, indent=4)
""")

    json.dumps({}, indent=4, )
    for x in cerb.get_contexts()['results']:
        print()
        print()
        print(f"class {x['name'].replace(' ', '')}(Record):")

        example = None

        try:
            results = cerb.search_records(x['alias'], expand=['custom_'], limit=1)['results']

            if len(results) == 1:
                example = results[0]
            else:
                print(f"    \"\"\" No records to build getters/setters from \"\"\"")

        except CerbException as e:
            print(f"    \"\"\" {e} \"\"\"")

        def indent(string):
            return string.replace('\n', '\n    ')

        print(f"""        
    _id = '{x['id']}'
    name = '{x['name']}'
    plugin_id = '{x['plugin_id']}'
    alias = '{x['alias']}'
    params = {indent(json.dumps(x['params'], indent=4))}
    custom_fields = {indent(json.dumps(x['custom_fields'] if 'custom_fields' in x else [], indent=4))}
    custom_fieldsets = {indent(json.dumps(x['custom_fieldsets'], indent=4))}""")

        for field in example if example else []:
            if not field.startswith('_') and "__" not in field and 'custom' not in field:
                _print_getter(field, field)
                if "update" in x['params']['acl']:
                    _print_setter(field, field)

        for custom_field in x['custom_fields'] if 'custom_fields' in x else []:
            _print_getter(custom_field['name'], "custom_" + str(custom_field['id']))
            if "update" in x['params']['acl']:
                _print_setter(custom_field['name'], "custom_" + str(custom_field['id']))

        for custom_fieldset in x['custom_fieldsets']:
            for custom_field in custom_fieldset['custom_fields'] if 'custom_fields' in custom_fieldset else []:
                _print_getter(custom_fieldset['name'] + '_' + custom_field['name'], 'custom_' + str(custom_field['id']))
                if "update" in x['params']['acl']:
                    _print_setter(custom_fieldset['name'] + '_' + custom_field['name'], 'custom_' + str(custom_field['id']))



def print_cheat_sheet(cerb: Cerb):
    print(f"""\"\"\" Auto generated on {datetime.now()}, Cerb Build: {cerb.build}\"\"\"""")
    for context in cerb.get_contexts()['results']:

        print(f"""
#################################################################
{context['name']}
#################################################################

Context Information:
{json.dumps(context, indent=4)}

Example(s):
""")

        try:
            results = cerb.search_records(context['alias'], expand=['custom_', 'link'], limit=3)['results']

            if results:
                for result in results:
                    print(json.dumps(result, indent=4))
            else:
                print("No example records to pull")

            print()

        except CerbException as e:
            print(f"    {e}")

