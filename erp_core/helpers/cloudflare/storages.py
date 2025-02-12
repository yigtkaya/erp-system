from storages.backends.s3 import S3Storage

class StaticFileStorage(S3Storage):
    location = 'static'
    file_overwrite = False

class MediaFileStorage(S3Storage):
    location = 'technical_drawings'
    file_overwrite = False 