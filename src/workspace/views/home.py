from pyramid.view import view_config
from pyramid_oidc.interfaces import IOIDCUtility


def get_user(request):
    claims = request.environ.get('oidc.claims')
    if claims:
        return {
            'id': claims[request.registry.getUtility(IOIDCUtility).userid_claim],
            'name': claims['name'],
            'email': claims['email']
        }
    return {}


@view_config(route_name='home', renderer='../templates/mytemplate.pt')
def my_view(request):
    return {
        'project': 'workspace',
        'user': get_user(request)
    }
