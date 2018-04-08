from pyramid.view import view_config


def get_user(request):
    from pyramid.interfaces import IAuthenticationPolicy
    authpol = request.registry.getUtility(IAuthenticationPolicy)
    for name in ('bearer', 'session'):
        policy = authpol.get_policy(name)
        user = policy.get_user(request)
        if user:
            return user
    return {}


@view_config(route_name='home', renderer='../templates/mytemplate.pt')
def my_view(request):
    return {
        'project': 'workspace',
        'user': get_user(request)
    }

