from pyramid.httpexceptions import HTTPUnauthorized, HTTPBadRequest, HTTPNoContent
from pyramid.view import view_config

from ..interfaces import ISwift


@view_config(route_name='api_v1_folders', renderer='json',
             request_method='GET', permission='view', cors=True)
def list_contents(request):
    userid = request.authenticated_userid
    if not userid:
        raise HTTPUnauthorized()

    params = request.oas.validate_params().parameters
    params = params.get('query', {})

    swift = request.registry.getUtility(ISwift)
    project = params.get('project', None)
    if not project or '/' in project:
        raise HTTPBadRequest('Invalid project name')
    path = params.get('path', '')
    ret = {
        'project': project,
        'path': path,
        'contents': []
    }
    for data in swift.list(userid, '/'.join((project, path))):
        ret['contents'].append(data)
    return ret


@view_config(route_name='api_v1_folders', permission='folders/create',
             request_method='POST', renderer='json', cors=True)
def create_folder(request):
    userid = request.authenticated_userid
    if not userid:
        raise HTTPUnauthorized()
    params = request.oas.validate_params().body

    project = params.get('project', None)
    if not project or '/' in project:
        raise HTTPBadRequest('Invalid project name')

    path = params.get('path', None)
    if not path:
        raise HTTPBadRequest('Invalid path name')

    swift = request.registry.getUtility(ISwift)
    res = swift.create_folder(userid, '/'.join((project, path)))
    return HTTPNoContent()


@view_config(route_name='api_v1_folders', permission='folders/delete',
             request_method='DELETE', renderer='json', cors=True)
def delete_folder(request):
    userid = request.authenticated_userid
    if not userid:
        raise HTTPUnauthorized()
    params = request.oas.validate_params().parameters['query']

    project = params.get('project', None)
    if not project or '/' in project:
        raise HTTPBadRequest('Invalid project name')

    path = params.get('path', None)
    if not path:
        raise HTTPBadRequest('Invalid path name')

    swift = request.registry.getUtility(ISwift)
    res = []
    for data in swift.delete_folder(userid, '/'.join((project, path))):
        # TODO: this contains everything (userid/project/path..)
        res.append(data['object'])
    return res
