"""
Django settings for AlgoViz Pro.

Central configuration for the entire project. Handles database, static files,
installed apps, caching, and custom settings for GitHub API integration.
"""

from pathlib import Path

# Base directory - everything else builds off this path
BASE_DIR = Path(__file__).resolve().parent.parent


# Security Settings
# TODO: Move SECRET_KEY to environment variable before deploying!

SECRET_KEY = 'django-insecure-your-secret-key-here-change-in-production'

# DEBUG = True shows detailed error pages (helpful for development, dangerous in production)
DEBUG = True

# Empty list means only localhost works - add your domain before deploying
ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    # Django's built-in apps (admin, auth, etc.)
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Our custom apps - each handles a different feature
    'algorithms',           # Core algorithm implementations and models
    'visualization',        # Frontend visualization interface
    'github_integration',   # GitHub API client and code fetching
    'analytics',            # Code complexity analysis
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'algoviz_pro.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # Global templates shared across apps
        'APP_DIRS': True,  # Also look for templates inside each app
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'algoviz_pro.wsgi.application'


# Database
# Using SQLite for development - simple and requires no setup
# For production, would switch to PostgreSQL or MySQL

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# Django enforces these rules when creating user accounts

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# Django needs to know where to find and collect static files

STATIC_URL = '/static/'

# Where to look for static files during development
STATICFILES_DIRS = [BASE_DIR / 'static']

# Where collectstatic puts everything for deployment
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Caching for GitHub API responses
# Using in-memory cache for development - fast and no extra setup needed
# Prevents hitting GitHub's rate limits by caching search results

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'algoviz-cache',
        'TIMEOUT': 1800,  # Cache for 30 minutes (1800 seconds)
        'OPTIONS': {
            'MAX_ENTRIES': 1000  # Drops the oldest entries after 1000 cached items
        }
    }
}

# GitHub API Configuration
# These control our GitHub integration - keeps rate limits under control

GITHUB_API_BASE_URL = 'https://api.github.com'
GITHUB_API_TIMEOUT = 10  # Give up after 10 seconds (prevents hanging requests)
GITHUB_CACHE_TIMEOUT = 1800  # Cache GitHub responses for 30 minutes
GITHUB_API_MAX_RETRIES = 3  # Try 3 times before giving up
GITHUB_API_RETRY_DELAY = 1  # Wait 1 second between retries

# Algorithm Execution Limits
# These prevent users from crashing the server with huge inputs

MAX_ARRAY_SIZE = 100  # Cap at 100 elements (keeps visualization smooth)
MAX_EXECUTION_TIME = 30  # Kill algorithm if it runs longer than 30 seconds