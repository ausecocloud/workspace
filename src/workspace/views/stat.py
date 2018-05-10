from pyramid.httpexceptions import HTTPUnauthorized
from pyramid.view import view_config

from ..interfaces import ISwift


@view_config(route_name='api_v1_stats', renderer='json',
             request_method='GET', permission='view', cors=True)
def stat(request):
    userid = request.authenticated_userid
    if not userid:
        raise HTTPUnauthorized()
    # verify to OAS spec
    request.oas.validate_params()

    swift = request.registry.getUtility(ISwift)

    return swift.stat(userid)
