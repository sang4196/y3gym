from urllib.parse import quote
from django.core.files.storage import FileSystemStorage

class PrivateStorage(FileSystemStorage):
    def url(self, name):
        return '/cms-files/' + quote(name, safe='/')
