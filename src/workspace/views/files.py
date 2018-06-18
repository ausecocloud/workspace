import logging

from pyramid.httpexceptions import HTTPUnauthorized, HTTPBadRequest, HTTPFound, HTTPNoContent
from pyramid.view import view_config

from ..interfaces import ISwift


@view_config(route_name='api_v1_files', renderer='json',
             request_method='GET', permission='view', cors=True)
def download_file(request):
    userid = request.authenticated_userid
    if not userid:
        raise HTTPUnauthorized()

    params = request.oas.validate_params().parameters
    params = params.get('query', {})

    project = params.get('project', None)
    if not project or '/' in project:
        raise HTTPBadRequest('Invalid project name')
    path = params.get('path', None)
    if not path:
        raise HTTPBadRequest('Invalid path')
    name = params.get('name', None)
    if not name or '/' in name:
        raise HTTPBadRequest('Invalid name')
    path = '/'.join((project, path))
    swift = request.registry.getUtility(ISwift)
    temp_url = swift.generate_temp_url(userid, path, name)
    return HTTPFound(temp_url)


@view_config(route_name='api_v1_files', renderer='json',
             request_method='POST', permission='file/upload', cors=True)
def upload_file(request):
    userid = request.authenticated_userid
    if not userid:
        raise HTTPUnauthorized()

    # TODO: openapi-core does not support media type wildcards
    #       for now we just handle the request validation manually.

    params = request.params

    # required parameters
    project = params.get('project', None)
    if not project or '/' in project:
        raise HTTPBadRequest('Invalid project name')
    path = params.get('path', None)
    if not path:
        raise HTTPBadRequest('Invalid path')
    path = '/'.join((project, path))
    # get path and file name; there is always one '/' in path, 'project/path|name'
    path, name = path.rsplit('/', 1)
    if not name:
        raise HTTPBadRequest('Invalid file name')

    # file content
    if not request.content_length:
        raise HTTPBadRequest('Missing Content-Length header')

    # TODO: We use body_file_seekable here, to allow swiftclient to retry the
    #       upload if necessary. However, this may mean, that the file get's
    #       cached on local disk before it is being passed on to swift.
    file = request.body_file_seekable
    file.seek(0)
    if not file:
        raise HTTPBadRequest('Invalid file')

    swift = request.registry.getUtility(ISwift)
    log = logging.getLogger(__name__)
    log.info('Start Swift upload %s', name)
    swift.upload_file(userid, path, name,
                      file, request.content_type, request.content_length)
    log.info('Finished Swift upload %s', name)
    return HTTPNoContent()


@view_config(route_name='api_v1_files', renderer='json',
             request_method='DELETE', permission='file/delete', cors=True)
def delete_file(request):
    userid = request.authenticated_userid
    if not userid:
        raise HTTPUnauthorized()

    params = request.oas.validate_params().parameters
    params = params.get('query', {})

    project = params.get('project', None)
    if not project or '/' in project:
        raise HTTPBadRequest('Invalid project name')
    path = params.get('path', None)
    if not path:
        raise HTTPBadRequest('Invalid path')
    name = params.get('name', None)
    if not name or '/' in name:
        raise HTTPBadRequest('Invalid name')
    path = '/'.join((project, path))

    swift = request.registry.getUtility(ISwift)
    swift.delete_file(userid, path, name)
    return HTTPNoContent()
