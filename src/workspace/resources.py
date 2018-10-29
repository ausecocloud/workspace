from pyramid.security import Allow


class Root(object):
    # Context object to map roles to permissions

    __parent__ = None
    __name__ = None

    __acl__ = [
        (Allow, 'workspace/user', 'view'),
        (Allow, 'workspace/user', 'folders/create'),
        (Allow, 'workspace/user', 'folders/delete'),
        (Allow, 'workspace/user', 'file/upload'),
        (Allow, 'workspace/user', 'file/delete'),
        (Allow, 'workspace/user', 'file/tempurl'),
        (Allow, 'admin', 'admin'),
    ]

    def __init__(self, request):
        pass
