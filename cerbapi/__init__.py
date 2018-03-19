import json
from hashlib import md5
from email.utils import formatdate
from urllib.request import Request, urlopen
from urllib.parse import urlencode, urlparse

__version__ = '1.0.3'


class CerbException(Exception):
    pass


class Cerb(object):

    def __init__(self, access_key, secret, base='https://localhost/index.php/rest/'):
        self.access = access_key
        self.secret = md5(secret.encode()).hexdigest()
        self.base = base

        # Test the connection and set values for version and build
        test = self.send('GET', 'contexts/list')
        self._version = test['__version']
        self._build = test['__build']

    def send(self, verb, endpoint, payload=None, params=None):
        query = urlencode(params or {})
        url = self.base + endpoint + '.json' + ('?' + query if query else '')

        data = urlencode(payload or {})

        r = Request(url, data=data.encode(), method=verb)

        date = formatdate()

        r.headers = {
            'Date': date,
            'Content-Length': len(data),
            'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8',
            'Cerb-Auth': self.access + ':' + md5('\n'.join([
                verb, date, urlparse(url).path, query, data, self.secret, '']).encode()).hexdigest()
        }

        with urlopen(r) as f:

            response = json.loads(f.read().decode())

            if '__status' in response:
                if response['__status'] != 'success':
                    raise CerbException(response['message'])

            return response

    @property
    def version(self):
        return self._version

    @property
    def build(self):
        return self._build

    ##############################
    # Contexts Module
    ##############################

    def link(self, on: str, targets: list):
        return self.send('POST', 'contexts/link', payload={'on': on, 'targets': json.dumps(targets)})

    def unlink(self, on: str, targets: list):
        return self.send('POST', 'contexts/unlink', payload={'on': on, 'targets': json.dumps(targets)})

    def get_contexts(self):
        return self.send('GET', 'contexts/list')

    def get_activity_events(self):
        return self.send('GET', 'contexts/activity/events')

    def create_activity_event(self, on: str, activity_point: str, variables: list=None, urls: list=None):
        return self.send('POST', 'contexts/activity/create', payload={
            'on': on,
            'activity_point': activity_point,
            'variables': json.dumps(variables or []),
            'urls': json.dumps(urls or [])
        })

    ##############################
    # Package Module
    ##############################

    def import_package(self, package_json: dict or list, prompts: dict=None):
        payload = {'prompts[{}]'.format(k): prompts[k] for k in prompts}
        payload['package_json'] = json.dumps(package_json)

        return self.send('POST', 'packages/import', payload=payload)

    ##############################
    # Parse Module
    ##############################

    def parse_new_message(self, from_address: str, to_address: str, subject: str, message='No Content'):
        return self.send('POST', 'parser/parse', payload={
            'message': '\n'.join([
                'From: ' + from_address,
                'To: ' + to_address,
                'Subject: ' + subject,
                '',
                message,
            ])
        })

    def parse_reply(self, from_address: str, to_address: str, ticket_mask: str, message='No Content'):
        return self.send('POST', 'parser/parse', payload={
            'message': '\n'.join([
                'From: ' + from_address,
                'To: ' + to_address,
                'Subject: [parser #' + ticket_mask + '] Reply',
                '',
                message,
            ])
        })

    ##############################
    # Records Module
    ##############################

    def get_record(self, uri, id, expand: list=None):
        return self.send('GET', 'records/{}/{}'.format(uri, id), params={'expand': ','.join(expand or [])})

    def create_record(self, uri, expand: list=None, fields: dict=None):
        return self.send('POST', 'records/{}/create'.format(uri),
                         params={'expand': ','.join(expand or [])},
                         payload={'fields[{}]'.format(f): fields[f] for f in (fields or {})}
                         )

    def update_record(self, uri, id, expand: list=None, fields: dict=None):
        return self.send('PUT', 'records/{}/{}'.format(uri, id),
                         params={'expand': ','.join(expand or [])},
                         payload={'fields[{}]'.format(f): fields[f] for f in (fields or {})}
                         )

    def upsert_record(self, uri, query: str, expand: list=None, fields: dict=None):
        return self.send('PATCH', 'records/{}/upsert'.format(uri),
                         params=(('expand', ','.join(expand or [])), ('query', query or '')),
                         payload={'fields[{}]'.format(f): fields[f] for f in (fields or {})}
                         )

    def delete_record(self, uri, id):
        return self.send('DELETE', 'records/{}/{}'.format(uri, id))

    def search_records(self, uri, query: str=None, expand: list=None, limit: int=None, page: int=None):
        return self.send('GET', 'records/{}/search'.format(uri), params=(
            ('expand', ','.join(expand or [])),
            ('limit', limit or 100),
            ('page', page or ''),
            ('q', query or '')
        ))
