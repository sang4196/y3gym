from urllib.parse import quote
from django.core.files.storage import FileSystemStorage


class PrivateMediaStorage(FileSystemStorage):
    """CMS-generated URLs always pass through authenticated object authorization."""
    def url(self, name):
        return "/cms-files/" + quote(name, safe="/")
