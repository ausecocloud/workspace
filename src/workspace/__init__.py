from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator

from pyramid_oidc.authentication import OIDCBearerAuthenticationPolicy
from pyramid_oidc.authentication.keycloak import keycloak_callback


from .resources import Root

# FIXME: load patch into process
import workspace.patch


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings, root_factory=Root)

    # setup oidc auth and session store if requested
    config.include('pyramid_oidc', route_prefix='/oidc')
    # add openapi support
    config.include('pyramid_openapi')
    # add cors support
    config.include('pyramid_cors')
    config.add_cors_preflight_handler()

    # set up authentication
    authn_policy = OIDCBearerAuthenticationPolicy(
        # probably don't need callback, as we don't need any roles
        callback=keycloak_callback,
    )
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(ACLAuthorizationPolicy())

    from .interfaces import ISwift
    from .utilities import Swift
    config.registry.registerUtility(Swift(settings), ISwift)

    # app specific stuff
    config.add_route(name='api_v1_stats', pattern='/api/v1/stat')
    config.add_route(name='api_v1_folders', pattern='/api/v1/folders')
    config.add_route(name='api_v1_files_tempurl', pattern='/api/v1/files/tempurl')
    config.add_route(name='api_v1_files', pattern='/api/v1/files')

    config.scan('.views')
    return config.make_wsgi_app()
