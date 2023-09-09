from .common import *


MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")


DEBUG = True

SECRET_KEY = "django-insecure-p4%x02srzav%zc!)8!dn=76$$4h8s8ihv-qa4m)ynhbp*!^mp2"

ALLOWED_HOSTS = []


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
