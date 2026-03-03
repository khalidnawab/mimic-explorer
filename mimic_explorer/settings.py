"""Django settings for MIMIC Explorer.

Single-user local application — no auth, hybrid SQLite + DuckDB.
Data directory: ~/.mimic_explorer/
"""

import os
from pathlib import Path

# --- Paths ---

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = Path.home() / '.mimic_explorer'
DATA_DIR.mkdir(parents=True, exist_ok=True)

# --- Security ---
_secret_key_path = DATA_DIR / 'secret_key'
if _secret_key_path.exists():
    SECRET_KEY = _secret_key_path.read_text().strip()
else:
    from django.core.management.utils import get_random_secret_key
    SECRET_KEY = get_random_secret_key()
    _secret_key_path.write_text(SECRET_KEY)

DEBUG = os.environ.get('MIMIC_DEBUG', 'false').lower() == 'true'

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# --- Apps & Middleware ---

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'core',
    'patients',
    'clinical',
    'fhir',
    'research',
    'dashboards',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'mimic_explorer.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.static',
            ],
        },
    },
]

WSGI_APPLICATION = 'mimic_explorer.wsgi.application'

# --- Database ---

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': DATA_DIR / 'mimic_explorer.db',
    }
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- DuckDB (clinical data) ---

DUCKDB_PATH = DATA_DIR / 'clinical.duckdb'

# --- Static files ---

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = DATA_DIR / 'staticfiles'

# --- CORS & DRF ---

CORS_ALLOW_ALL_ORIGINS = DEBUG or os.environ.get('MIMIC_CORS_ALL', 'false').lower() == 'true'

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'UNAUTHENTICATED_USER': None,
}
