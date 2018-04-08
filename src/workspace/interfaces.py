from zope.interface import Interface


class ISwift(Interface):

    def list(user_id, path):
        """Return contents at path for specific user.
        """

    def create_folder(user_id, path):
        """Create a pseudo folder in swift
        """
