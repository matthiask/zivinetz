import os

from speckenv import env
from speckenv_django import django_database_url


BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DATABASES = {
    "default": django_database_url(
        env("DATABASE_URL", default="postgres://127.0.0.1:5432/zivinetz")
    )
}
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.admin",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "django.contrib.messages",
    "testapp",
    "towel",
    "zivinetz",
    "towel_foundation",
]

MIDDLEWARE = (
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "testapp.middleware.UglynessMiddleware",
)

MEDIA_ROOT = "/media/"
STATIC_URL = "/static/"
BASEDIR = os.path.dirname(__file__)
MEDIA_ROOT = os.path.join(BASEDIR, "media/")
STATIC_ROOT = os.path.join(BASEDIR, "static/")
SECRET_KEY = "supersikret"
LOGIN_REDIRECT_URL = "/?login=1"

ROOT_URLCONF = "testapp.urls"
LANGUAGES = (("en", "English"), ("de", "German"))
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASEDIR, "templates")],
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
            "loaders": [
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
        },
    }
]
