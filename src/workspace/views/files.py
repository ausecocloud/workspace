from pyramid.httpexceptions import HTTPUnauthorized, HTTPBadRequest, HTTPFound
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

    params = request.oas.validate_params().body

    project = params.get('project', None)
    if not project or '/' in project:
        raise HTTPBadRequest('Invalid project name')
    path = params.get('path', None)
    if not path:
        raise HTTPBadRequest('Invalid path')
    path = '/'.join((project, path))
    file = params.get('file', None)
    if file is None:
        raise HTTPBadRequest('Invalid file')
    name = params.get('name', None)
    if name is None:
        name = file.filename
    if name is None:
        raise HTTPBadRequest('Invalid file name')

    swift = request.registry.getUtility(ISwift)
    ret = {
        'project': project,
        'path': path,
        'name': name,
        'owner': userid,
        'items': []
    }
    for res in swift.upload_file(userid, path, name,
                                 file.file, file.type, file.length):
        ret['items'].append(res)
    return ret


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
    ret = []
    for res in swift.delete_file(userid, path, name):
        ret.append(res)
    return ret
