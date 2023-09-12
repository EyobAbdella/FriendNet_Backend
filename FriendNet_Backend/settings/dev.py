from .common import *

DEBUG = False

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

SECRET_KEY = "django-insecure-p4%x02srzav%zc!)8!dn=76$$4h8s8ihv-qa4m)ynhbp*!^mp2"

# STATIC_URL = "/static/"
# STATIC_ROOT = os.path.join(BASE_DIR, "static")

# MEDIA_URL = "/media/"
# MEDIA_ROOT = os.path.join(BASE_DIR, "media")


STATIC_URL = "/static/"
STATICFILES_STORAGE = "cloudinary_storage.storage.StaticHashedCloudinaryStorage"

CLOUD_NAME = "dzngmnqpg"
API_KEY = "556134699174437"
API_SECRET = "BysjSlPg0icAnfeC3tYfrKCQL50"

CLOUDINARY_STORAGE = {
    "CLOUD_NAME": CLOUD_NAME,
    "API_KEY": API_KEY,
    "API_SECRET": API_SECRET,
    "EXCLUDE_DELETE_ORPHANED_MEDIA_PATHS": ("file/", "image/"),
}


DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.RawMediaCloudinaryStorage"


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}
