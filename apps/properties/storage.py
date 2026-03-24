from django.conf import settings
from django.core.files.storage import FileSystemStorage

class HTTPSFileSystemStorage(FileSystemStorage):
    """Force HTTPS for file URLs"""
    
    def url(self, name):
        url = super().url(name)
        if settings.DEBUG:
            return url
        # Convert to HTTPS
        if url.startswith('http://'):
            return url.replace('http://', 'https://')
        return url