import json
from hashlib import md5
from email.utils import formatdate
from urllib.request import Request, urlopen
from urllib.parse import urlencode, urlparse

__version__ = '1.0.8'


class CerbException(Exception):
    pass


class Cerb(object):

    def __init__(self, access_key, secret, base='https://localhost/index.php/rest/'):
        self._access_key = access_key
        self._secret = md5(secret.encode()).hexdigest()
        self._base = base

        # Test the connection and set values for version and build
        test = self.get_contexts()
        self._version = test['__version']
        self._build = test['__build']

    def send(self, verb, endpoint, payload=None, params=None):
        query = urlencode(params or {})
        url = self._base + endpoint + '.json' + ('?' + query if query else '')

        data = urlencode(payload or {})

        r = Request(url, data=data.encode(), method=verb)

        date = formatdate()

        r.headers = {
            'Date': date,
            'Content-Length': len(data),
            'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8',
            'Cerb-Auth': self._access_key + ':' + md5('\n'.join([
                verb, date, urlparse(url).path, query, data, self._secret, '']).encode()).hexdigest()
        }

        with urlopen(r) as f:

            response = json.loads(f.read().decode())

            if '__status' in response:
                if response['__status'] != 'success':
                    raise CerbException(response['message'])

            return response

    @property
    def access_key(self):
        return self._access_key

    @property
    def base(self):
        return self._base

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
        return self.send('POST', 'contexts/link', payload=(('on', on), ('targets', json.dumps(targets))))

    def unlink(self, on: str, targets: list):
        return self.send('POST', 'contexts/unlink', payload=(('on', on), ('targets', json.dumps(targets))))

    def get_contexts(self):
        return self.send('GET', 'contexts/list')

    def get_activity_events(self):
        return self.send('GET', 'contexts/activity/events')

    def create_activity_event(self, on: str, activity_point: str, variables: list=None, urls: list=None):
        return self.send('POST', 'contexts/activity/create', payload=(
            ('activity_point', activity_point),
            ('on', on),
            ('urls', json.dumps(urls or [])),
            ('variables', json.dumps(variables or [])),
        ))

    ##############################
    # Package Module
    ##############################

    def import_package(self, package_json: dict or list, prompts: dict=None):
        payload = [('package_json', json.dumps(package_json))]

        for k in sorted(prompts or {}):
            payload.append(('prompts[{}]'.format(k), prompts[k]))

        return self.send('POST', 'packages/import', payload=payload)

    ##############################
    # Parse Module
    ##############################

    def parse_new_message(self, from_address: str, to_address: str, subject: str, message='No Content'):
        return self.send('POST', 'parser/parse', payload=((
            'message', '\n'.join([
                'From: ' + from_address,
                'To: ' + to_address,
                'Subject: ' + subject,
                '',
                message,
            ])),))

    def parse_reply(self, from_address: str, to_address: str, ticket_mask: str, message='No Content'):
        return self.send('POST', 'parser/parse', payload=((
            'message', '\n'.join([
                'From: ' + from_address,
                'To: ' + to_address,
                'Subject: [parser #' + ticket_mask + '] Reply',
                '',
                message,
            ])),))

    ##############################
    # Records Module
    ##############################

    def get_record(self, uri, id, expand: list=None):
        return self.send('GET', 'records/{}/{}'.format(uri, id), params=(('expand', ','.join(expand or [])),))

    def create_record(self, uri, expand: list=None, fields: dict=None):
        return self.send('POST', 'records/{}/create'.format(uri),
                         params=(('expand', ','.join(expand or [])),),
                         payload=[('fields[{}]'.format(f), fields[f]) for f in sorted(fields or {})]
                         )

    def update_record(self, uri, id, expand: list=None, fields: dict=None):
        return self.send('PUT', 'records/{}/{}'.format(uri, id),
                         params=(('expand', ','.join(expand or [])),),
                         payload=[('fields[{}]'.format(f), fields[f]) for f in sorted(fields or {})]
                         )

    def upsert_record(self, uri, query: str, expand: list=None, fields: dict=None):
        return self.send('PATCH', 'records/{}/upsert'.format(uri),
                         params=(('expand', ','.join(expand or [])), ('query', query)),
                         payload=[('fields[{}]'.format(f), fields[f]) for f in sorted(fields or {})]
                         )

    def delete_record(self, uri, id):
        return self.send('DELETE', 'records/{}/{}'.format(uri, id))

    def search_records(self, uri, query: str='', expand: list=None, limit: int=100, page: int=0):
        return self.send('GET', 'records/{}/search'.format(uri), params=(
            ('expand', ','.join(expand or [])), ('limit', limit), ('page', page), ('q', query)
        ))
