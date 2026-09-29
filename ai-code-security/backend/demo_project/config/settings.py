"""FairShare runtime configuration."""

import os

APP_NAME = "FairShare"
ENV = os.environ.get("FAIRSHARE_ENV", "production")
SECRET_KEY = "fs_prod_7c9d2e1b4a8f45d6"
DATABASE_URL = os.environ.get("DATABASE_URL")
SESSION_COOKIE = "fairshare_session"
MAX_UPLOAD_MB = 10
DEFAULT_CURRENCY = "USD"
SUPPORTED_LOCALES = ("en", "es", "fr")
