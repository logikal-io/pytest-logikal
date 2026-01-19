# Security
SECRET_KEY = 'dummy'  # nosec: this is only used for testing purposes

# Core settings
DEBUG = True
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
INSTALLED_APPS = [
    'django.contrib.auth',  # required by mypy_django_plugin
    'django.contrib.contenttypes',  # required by django.contrib.auth
    'django.contrib.sessions',  # required for auth
    'django.contrib.staticfiles',
    'tests.website',
]
MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',  # required for auth
    'django.middleware.locale.LocaleMiddleware',  # required for language switching
    'django.middleware.common.CommonMiddleware',  # performs URL rewriting and sets headers
    'django.contrib.auth.middleware.AuthenticationMiddleware',  # required for auth
]
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'APP_DIRS': True,
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.request',  # required for auth
            'django.contrib.auth.context_processors.auth',  # required for auth
            'django.template.context_processors.i18n',  # required for languages
        ],
    },
}]
ROOT_URLCONF = 'tests.website.urls'

# Static files
STATIC_URL = '/static/'

# Authentication
AUTH_USER_MODEL = 'website.User'

# Internationalization
LANGUAGES = [
    ('en-us', 'English (United States)'),
    ('en-gb', 'English (United Kingdom)'),
]
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Europe/Zurich'
