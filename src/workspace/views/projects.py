from pyramid.httpexceptions import (
    HTTPUnauthorized, HTTPBadRequest, HTTPNoContent
)
from pyramid.view import view_config

from ..interfaces import ISwift


@view_config(route_name='api_v1_projects', renderer='json',
             request_method='GET', permission='view', cors=True)
def list_projects(request):
    userid = request.authenticated_userid
    if not userid:
        raise HTTPUnauthorized()
    # verify to OAS spec
    request.oas.validate_params()

    swift = request.registry.getUtility(ISwift)
    ret = []

    for data in swift.list(userid):
        # TODO: we should only have subdirs here,
        #       maybe filter everything that's not 'application/directory'?
        ret.append(data)
    return ret


@view_config(route_name='api_v1_projects', permission='project/create',
             request_method='POST', renderer='json', cors=True)
def create_project(request):
    userid = request.authenticated_userid
    if not userid:
        raise HTTPUnauthorized()
    params = request.oas.validate_params().body

    project = params.get('name', None)
    if not project or '/' in project:
        raise HTTPBadRequest('Invalid project name')
    description = params.get('description', None)
    if description and len(description) > 500:
        raise HTTPBadRequest('Invalid project description')

    swift = request.registry.getUtility(ISwift)
    res = swift.create_folder(userid, project, description)
    return HTTPNoContent()


@view_config(route_name='api_v1_projects', permission='project/delete',
             request_method='DELETE', renderer='json', cors=True)
def delete_project(request):
    userid = request.authenticated_userid
    if not userid:
        raise HTTPUnauthorized()
    params = request.oas.validate_params().parameters['query']

    project = params.get('project', None)
    if not project or '/' in project:
        raise HTTPBadRequest('Invalid project name')

    swift = request.registry.getUtility(ISwift)
    res = []
    for data in swift.delete_folder(userid, project):
        # TODO: this contains everything (userid/project/path..)
        res.append(data)
    return res
