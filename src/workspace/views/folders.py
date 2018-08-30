import logging

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
    path = params.get('path', '').strip('/')
    ret = []
    for data in swift.list(userid, path):
        ret.append(data)
    return ret


@view_config(route_name='api_v1_folders', permission='folders/create',
             request_method='POST', renderer='json', cors=True)
def create_folder(request):
    userid = request.authenticated_userid
    if not userid:
        raise HTTPUnauthorized()
    params = request.oas.validate_params()
    query = params.parameters['query']

    path = query.get('path', '').strip('/')

    body = params.body
    name = body.get('name', None)
    if not name or '/' in name:
        raise HTTPBadRequest('Invalid folder name')

    swift = request.registry.getUtility(ISwift)
    res = swift.create_folder(userid, '/'.join((path, name)))
    return HTTPNoContent()


@view_config(route_name='api_v1_folders', permission='folders/delete',
             request_method='DELETE', renderer='json', cors=True)
def delete_folder(request):
    userid = request.authenticated_userid
    if not userid:
        raise HTTPUnauthorized()
    params = request.oas.validate_params().parameters['query']

    # TODO: maybd use name or foler parameter to identify folder to delee?
    #       would be more consistent with the usage of path in rest of API
    path = params.get('path', '').strip('/')
    if not path:
        raise HTTPBadRequest('Invalid path name')

    swift = request.registry.getUtility(ISwift)
    res = []
    for data in swift.delete_folder(userid, path):
        # TODO: this contains everything (userid/project/path..)
        res.append(data)
    return res
