"""
Django settings for AlgoViz Pro.

SECURITY NOTE: Several settings are development-only and must change for production:
- SECRET_KEY must be environment variable
- DEBUG must be False
- ALLOWED_HOSTS must be set
- Database should be PostgreSQL
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY SETTINGS
# ==================

# Cryptographic signing for sessions, cookies, CSRF tokens
# DEVELOPMENT ONLY - must be random and secret in production
SECRET_KEY = 'django-insecure-your-secret-key-here-change-in-production'

# Shows detailed error pages with stack traces for debugging
# Must be False in production to avoid exposing sensitive info
DEBUG = True

# Empty list allows localhost when DEBUG=True
# Must specify actual domains in production to prevent Host Header attacks
ALLOWED_HOSTS = []


# INSTALLED APPS
# ==============

INSTALLED_APPS = [
    # Django built-in apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Custom apps - modular design per project requirements
    'algorithms',  # Algorithm implementations (sorting, searching)
    'visualization',  # Web interface for visualizations
    'github_integration',  # GitHub API client
    'analytics',  # Code complexity analysis
]


# MIDDLEWARE
# ==========
# Order matters - request flows down, response flows up

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',  # Security headers
    'django.contrib.sessions.middleware.SessionMiddleware',  # Manages sessions
    'django.middleware.common.CommonMiddleware',  # URL normalization
    'django.middleware.csrf.CsrfViewMiddleware',  # CSRF protection
    'django.contrib.auth.middleware.AuthenticationMiddleware',  # Adds request.user
    'django.contrib.messages.middleware.MessageMiddleware',  # Flash messages
    'django.middleware.clickjacking.XFrameOptionsMiddleware',  # Prevents iframes
]

ROOT_URLCONF = 'algoviz_pro.urls'


# TEMPLATES
# =========

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Global templates folder for shared base.html
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,  # Also check each app's templates/ directory
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


# DATABASE
# ========

DATABASES = {
    'default': {
        # SQLite for development - zero config, file-based
        # Should use PostgreSQL in production for concurrent writes and scalability
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# PASSWORD VALIDATION
# ===================

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# INTERNATIONALIZATION
# ====================

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'  # Store all times in UTC
USE_I18N = True
USE_TZ = True


# STATIC FILES
# ============

STATIC_URL = '/static/'
# Look for static files in project-level static/ folder
STATICFILES_DIRS = [BASE_DIR / 'static']
# collectstatic copies files here for production serving
STATIC_ROOT = BASE_DIR / 'staticfiles'


# DEFAULT SETTINGS
# ================

# BigAutoField supports up to ~9 quintillion records vs 2 billion for AutoField
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# CACHING
# =======

CACHES = {
    'default': {
        # In-memory cache for development (fast, zero config)
        # Should use Redis in production for multi-server support
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'algoviz-cache',
        # 30 minutes - balances fresh data with reduced API calls
        'TIMEOUT': 1800,
        'OPTIONS': {
            'MAX_ENTRIES': 1000  # Reasonable limit for local memory
        }
    }
}


# GITHUB API CONFIGURATION
# ========================

GITHUB_API_BASE_URL = 'https://api.github.com'

# 10 seconds - long enough for normal response, short enough to prevent hanging
GITHUB_API_TIMEOUT = 10

# 30 minutes - GitHub data doesn't change frequently
GITHUB_CACHE_TIMEOUT = 1800

# 3 retries with exponential backoff (1s, 2s, 4s) handles transient failures
GITHUB_API_MAX_RETRIES = 3
GITHUB_API_RETRY_DELAY = 1


# ALGORITHM EXECUTION LIMITS
# ===========================

# 100 elements max prevents DoS and keeps animations smooth
# O(n²) with 1000 elements = 1M operations (too slow)
MAX_ARRAY_SIZE = 100

# 30 seconds max prevents runaway algorithms from hanging server
MAX_EXECUTION_TIME = 30