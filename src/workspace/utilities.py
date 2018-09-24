from datetime import datetime, timezone
import logging
from urllib.parse import urlparse, urljoin
import os

from swiftclient.service import (
    SwiftService, SwiftError, SwiftUploadObject, SwiftPostObject, get_conn
)
from swiftclient.utils import generate_temp_url, LengthWrapper
from swiftclient.service import SwiftError
from zope.interface import implementer

from .interfaces import ISwift

# TODO: there may be a weird situation where a folder can disappear
#       if all files inside are deleted (e.g. if it was a pseudo folder)


def get_os_settings(settings):
    # SwiftService reads standard env vars
    prefix = 'os_'
    options = {
        key: val for (key, val) in settings.items()
        if key.startswith(prefix)
    }
    return options


def get_swift_settings(settings):
    prefix = 'workspace.'
    options = {
        key[len(prefix):]: val for (key, val) in settings.items()
        if key.startswith(prefix)
    }
    # check env vars as well
    # TODO: rename WORKSPACE_CONTAINER to somethig with prefix or even
    #       user container template
    for var, key in (('WORKSPACE_CONTAINER', 'container'),
                     ('WORKSPACE_TEMP_URL_KEY', 'temp_url_key')):
        if var in os.environ:
            options[key] = os.environ[var]
    return options


def safe_int(value):
    try:
        return int(value)
    except Exception:
        return None


def safe_isodate(timestamp):
    try:
        return datetime.fromtimestamp(float(timestamp),
                                      tz=timezone.utc).isoformat()
    except Exception as e:
        return None


@implementer(ISwift)
class Swift(object):

    def __init__(self, settings):
        options = get_os_settings(settings)
        self.swift = SwiftService(options)

        options = get_swift_settings(settings)
        self.temp_url_key = options['temp_url_key']
        # TODO: hard coded template
        self.name_template = options['container'] + '_{name}'


    # TODO: this should be a module level method
    def build_object_name(self, user_id, path='', name=None):
        # - if name is None, return full folder path with trailing slash
        # - the returned does not have a leading slash
        if not user_id or '/' in user_id:
            raise ValueError('Invalid userid', user_id)
        container = self.name_template.format(name=user_id)
        parts = []
        if path:
            # disallow '..'
            if '..' in path:
                raise ValueError('Invalid path', path)
            # strip all leading trailing slashes from path
            # deduplicate double slashes
            path = '/'.join(x for x in path.split('/') if x)
            if path:
                parts.append(path)
        if name:
            # build a file path
            if '/' in name or name in ('..', '.'):
                raise ValueError('Invalid name', name)
            parts.append(name)
        else:
            # ensure we get a trailing slash if there is no name
            # -> it is a folder
            parts.append('')
        return container, '/'.join(parts)

    def _create_container(self, container):
        return self.swift.post(
            container=container,
            options={
                # swiftservice converts this to X-Container-Meta-Temp-Url-Key
                'meta': {
                    'temp-url-key': self.temp_url_key,
                    # TODO: hard coded 10G quota
                    'quota-bytes': str(int(10e9)),
                }
            }
        )

    def stat(self, user_id, path=''):
        container, object_prefix = self.build_object_name(user_id, path)
        if path:
            # object stat requested
            pass
        else:
            # container stat requested
            try:
                stat = self.swift.stat(container=container)
            except SwiftError as e:
                if e.exception.http_status == 404:
                    # container does not exists
                    res = self._create_container(container)
                    stat = self.swift.stat(container=container)
                else:
                    raise
            headers = stat['headers']
            return {
                'used': safe_int(headers.get('x-container-bytes-used', None)),
                'quota': safe_int(headers.get('x-container-meta-quota-bytes', None)),
                'count': safe_int(headers.get('x-container-object-count', None)),
                'created': safe_isodate(headers.get('x-timestamp', None)),
            }
            return {
                stat.items
            }

    def list(self, user_id, path=''):
        container, object_prefix = self.build_object_name(user_id, path)
        for data in self.swift.list(
                container=container,
                options={
                    'delimiter': '/',
                    'prefix': object_prefix
                }):
            if data['action'] == ['list_container_part'] and not data['success']:
                data = self._create_container(container)
            if data['success']:
                for item in data['listing']:
                    # filter current folder
                    if item.get('subdir', None) == object_prefix:
                        # ignore current directory
                        continue
                    elif item.get('name', None) == object_prefix:
                        # ignore the current directory
                        continue
                    else:
                        if item.get('subdir', None):
                            # it is a pseudo dir
                            yield {
                                'name': item.get('subdir')[len(object_prefix):].strip('/'),
                                'bytes': 0,
                                'content_type': 'application/directory',
                            }
                        else:
                            item['name'] = item['name'][len(object_prefix):]
                            yield item
            # skip error handling below
            continue
            # TODO: we are raising an exception here... jumping out fo the
            #       generator.... should be fine for this method, but
            #       does this have the potential to leak threads?
            #       SwiftService uses threads to generate results
            ex = data['error']
            if isinstance(ex, SwiftError):
                if not path and ex.exception.http_status == 404:
                    # ex.exception should be a ClientException, not found
                    # if path is empty, we ignore it, it means, the
                    # user container does not exist yet.
                    break
            raise ex

    def create_folder(self, user_id, path='', description=None):
        container, object_path = self.build_object_name(user_id, path)

        # create upload object
        object_path = SwiftUploadObject(
            None,
            object_name=object_path,
            options={
                'dir_marker': True,
                'meta': {
                    'description': description or '',
                },
            }
        )

        folders = []
        for res in self.swift.upload(container, [object_path]):
            if not res['success']:
                raise res['error']
            if res['action'] == 'create_container':
                # if res['response_dict']['reason'] == 'Created'
                # status will be 202 if container already existed
                if res['response_dict']['status'] == 201:
                    # set up metadata for user container
                    res = self._create_container(container)
            # TODO: project only:
            if res['action'] == 'create_dir_marker':
                meta = {}
                if description:
                    meta['description'] = description
                folder = SwiftPostObject(
                    object_name=res['object'],
                    options={
                        'header': res['headers'],
                        'meta': meta,
                    }
                )
                folders.append(folder)
        # TODO: check whether we should use post above instead of upload
        #       maybe we can avoid calling swift twice?
        #       also woke sure container get's created in case of post
        ret = []
        for res in self.swift.post(container, folders):
            if not res['success']:
                raise res['error']
            ret.append(res)
        return ret

    def delete_folder(self, user_id, path=''):
        container, object_path = self.build_object_name(user_id, path)
        # don't use delimiter here, otherwise swift.delete will only see
        # one level of subfolders and won't be able to delete everything
        # TODO: can this delete the container as well?
        for res in self.swift.delete(
                container=container,
                options={
                    'prefix': object_path
                }):
            yield res['object'][len(object_path):]

    def upload_file(self, user_id, path, name, file,
                    content_type='application/octet-stream',
                    content_length=-1):
        container, object_name = self.build_object_name(user_id, path, name)
        # prepend account and container to path
        headers = {
            'Content-Type': content_type or 'application/octet-stream'
        }
        # if content_length >= 0:
        #     headers['Content-Length'] = str(content_length)
        upload_obj = SwiftUploadObject(
            source=LengthWrapper(file, content_length, True),
            object_name=object_name,
            options={
                'header': headers
            }
        )
        log = logging.getLogger(__name__)
        log.info('Tool Upload %s', upload_obj)
        for res in self.swift.upload(container, [upload_obj]):
            if res['action'] == 'create_container':
                res = self._create_container(container)
            # Getting a funny response iterator here
            # 1. action: create_container
            # 2. action: upload_object
            log.info('Tool Result %s', res)
            if res.get('error', None):
                # res['error'].http_status == 413:
                # -> Request Entity Too Large
                # res['error'].http_resonse_content == 'Upload exceeds quota'
                raise res['error']

    def delete_file(self, user_id, path, name):
        container, object_name = self.build_object_name(user_id, path, name)
        # TODO: could set options['prefix'] to make sure we don't delete
        #       anything outside project/folder
        # TODO: coould this delete the container?
        res = self.swift.delete(
            container=container,
            objects=[object_name]
        )
        for res in self.swift.delete(container=container, objects=[object_name]):
            if res.get('error', None):
                raise res['error']

    def generate_temp_url(self, user_id, path, name):
        container, object_name = self.build_object_name(user_id, path, name)
        # discover swift endpoint urls
        conn = get_conn(self.swift._options)
        url, token = conn.get_auth()
        urlparts = urlparse(url)
        # generate swift path /v1/<account>/<container>/<userid>/path
        path = '/'.join((urlparts.path, container, object_name))
        # TODO: valid for 5 minutes
        temp_url = generate_temp_url(
            path, 300, self.temp_url_key, method='GET'
        )
        return urljoin(url, temp_url)
