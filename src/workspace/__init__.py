from pyramid.config import Configurator

from .resources import Root


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings, root_factory=Root)

    # setup oidc auth and session store if requested
    config.include('pyramid_oidc', route_prefix='/oidc')
    config.add_cors_preflight_handler()

    # webassets
    # from webassets import Bundle
    # app_js = Bundle('app/app.js')
    # config.add_webasset('app', app_js)

    from .interfaces import ISwift
    from .utilities import Swift
    config.registry.registerUtility(Swift(settings), ISwift)

    # app specific stuff
    config.add_route(name='api_v1_projects', pattern='/api/v1/projects')
    config.add_route(name='api_v1_folders', pattern='/api/v1/folders')
    config.add_route(name='api_v1_files', pattern='/api/v1/files')

    # web routes
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')

    config.scan('.views')
    return config.make_wsgi_app()
