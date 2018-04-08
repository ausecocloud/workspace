from pyramid.security import Allow
from pyramid.security import Authenticated


class Root(object):
    # Context object to map roles to permissions

    __parent__ = None
    __name__ = None

    __acl__ = [
        (Allow, Authenticated, 'view'),
        (Allow, Authenticated, 'project/create'),
        (Allow, Authenticated, 'project/delete'),
        (Allow, Authenticated, 'folders/create'),
        (Allow, Authenticated, 'folders/delete'),
        (Allow, Authenticated, 'file/upload'),
        (Allow, Authenticated, 'file/delete'),
        (Allow, 'admin', 'admin'),
    ]

    def __init__(self, request):
        pass
