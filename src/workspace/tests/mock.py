

# All the stuff we need to mock for testing

@implementer(ISwift)
class SwiftMock(Swift):

    def stat(self, user_id, path=''):
        pass

    def list(self, user_id, path=''):
        pass

    def create_folder(self, user_id, path='', description=None):
        pass

    def delete_folder(self, user_id, path=''):
        pass

    def upload_file(self, user_id, path, name, file,
                    content_type='application/octet-stream',
                    content_length=-1):
        pass

    def delete_file(self, user_id, path, name):
        pass


