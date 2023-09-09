import os
import dj_database_url
from .common import *


from dotenv import load_dotenv

load_dotenv()

DEBUG = True

SECRET_KEY = os.environ["SECRET_KEY"]

ALLOWED_HOSTS = ["friendnet-fju8.onrender.com"]

CLOUD_NAME = os.environ["CLOUD_NAME"]
API_KEY = os.environ["API_KEY"]
API_SECRET = os.environ["API_SECRET"]

CLOUDINARY_STORAGE = {
    "CLOUD_NAME": CLOUD_NAME,
    "API_KEY": API_KEY,
    "API_SECRET": API_SECRET,
}


DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"

# HTTPS Settings
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True

# HSTS Settings
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_PRELOAD = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True


DATABASES = {"default": dj_database_url.config()}


REDIS_URL = os.environ["REDIS_URL"]

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [REDIS_URL],
        },
    },
}
