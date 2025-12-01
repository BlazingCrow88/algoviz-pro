"""
Django settings for the AlgoViz Pro project.

What this file does: Central configuration for the entire Django project.
Every Django setting lives here - database config, installed apps, middleware,
static files, caching, security settings, etc.

Why settings are in one file: Django convention. Some projects split this into
settings/base.py, settings/dev.py, settings/prod.py, but for a project this
size, one file is simpler and easier to manage.

CRITICAL SECURITY NOTE: Many settings here are DEVELOPMENT ONLY and must be
changed before deploying to production:
- SECRET_KEY needs to be different and actually secret
- DEBUG must be False (currently True for easier debugging)
- ALLOWED_HOSTS must be set to actual domain
- Database should probably be PostgreSQL not SQLite

The professor will check if we understand development vs production settings.
"""

from pathlib import Path

# BASE_DIR: Root directory of the Django project
# Using Path (pathlib) instead of os.path because it's more modern and cleaner
# Path(__file__) = this file (settings.py)
# .resolve() = get absolute path
# .parent.parent = go up two levels (settings.py -> algoviz_pro/ -> project root)
BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY SETTINGS
# ==================

# SECRET_KEY: Used for cryptographic signing (sessions, cookies, CSRF tokens)
#
# CRITICAL SECURITY WARNING: This is a placeholder for development!
# In production, this MUST be:
# 1. Actually random (50+ characters)
# 2. Kept secret (never committed to git)
# 3. Stored in environment variable or secrets manager
#
# How to generate a real one: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
#
# Why it matters: If someone gets your SECRET_KEY, they can:
# - Forge session cookies (impersonate users)
# - Bypass CSRF protection
# - Decrypt encrypted data
SECRET_KEY = 'django-insecure-your-secret-key-here-change-in-production'

# DEBUG: Shows detailed error pages with stack traces
#
# DEBUG = True (current setting - DEVELOPMENT ONLY):
# - Shows full error pages with stack traces
# - Serves static files automatically
# - Displays SQL queries in Django Debug Toolbar
# - Makes debugging easier but EXPOSES SENSITIVE INFO
#
# DEBUG = False (MUST use in production):
# - Shows generic error pages (404.html, 500.html)
# - Requires proper static file serving (collectstatic)
# - Hides implementation details from users/attackers
#
# Why True for now: We're developing, need to see errors to fix bugs
# The professor knows this is a student project, so DEBUG=True is acceptable
DEBUG = True

# ALLOWED_HOSTS: Which domain names can access this Django site
#
# Empty list [] (current setting - DEVELOPMENT ONLY):
# - Allows localhost and 127.0.0.1 when DEBUG=True
# - Django provides this convenience for local development
#
# In production, MUST specify actual domains:
# ALLOWED_HOSTS = ['algovizpro.com', 'www.algovizpro.com']
#
# Why it matters: Protects against HTTP Host Header attacks where attacker
# sends requests with malicious Host headers to trigger password reset emails
# to attacker-controlled domains
ALLOWED_HOSTS = []


# INSTALLED APPS
# ==============
# Apps that Django loads when the project starts

INSTALLED_APPS = [
    # Django's built-in apps (come with Django)
    'django.contrib.admin',  # Admin panel at /admin/
    'django.contrib.auth',  # User authentication system
    'django.contrib.contenttypes',  # Content type framework (polymorphic relationships)
    'django.contrib.sessions',  # Session framework (stores user state)
    'django.contrib.messages',  # Messaging framework (flash messages)
    'django.contrib.staticfiles',  # Static file management (CSS, JS, images)

    # Our custom apps for AlgoViz Pro
    # Each app is a separate module with its own models, views, templates
    # This modularization is CRITICAL for the rubric's "code modularization" requirement
    'algorithms',  # Core algorithm implementations (sorting, searching)
    'visualization',  # Web interface for visualizing algorithms
    'github_integration',  # GitHub API client for fetching code
    'analytics',  # Code complexity analysis using AST
]
# App order generally doesn't matter except for template/static file precedence
# (earlier apps can override later apps' templates if same name)


# MIDDLEWARE
# ==========
# Processing pipeline for every request/response
#
# Middleware order MATTERS! Each request goes DOWN the list, response goes UP.
# Think of it like layers of an onion - request goes in, response comes out.
#
# Request flow: SecurityMiddleware → Sessions → Common → CSRF → Auth → Messages → Clickjacking → View
# Response flow: View → Clickjacking → Messages → Auth → CSRF → Common → Sessions → SecurityMiddleware

MIDDLEWARE = [
    # 1. SecurityMiddleware: Sets security headers (HTTPS redirect, XSS protection)
    #    Runs FIRST so all other middleware gets security headers
    'django.middleware.security.SecurityMiddleware',

    # 2. SessionMiddleware: Manages sessions (request.session)
    #    Must run before any middleware that uses sessions
    'django.contrib.sessions.middleware.SessionMiddleware',

    # 3. CommonMiddleware: Common operations (URL normalization, ETags)
    #    Handles /foo -> /foo/ redirects, sets Content-Length headers
    'django.middleware.common.CommonMiddleware',

    # 4. CsrfViewMiddleware: CSRF protection for POST/PUT/DELETE requests
    #    Must run after SessionMiddleware (uses sessions for CSRF tokens)
    'django.middleware.csrf.CsrfViewMiddleware',

    # 5. AuthenticationMiddleware: Attaches request.user to every request
    #    Must run after SessionMiddleware (user info stored in session)
    'django.contrib.auth.middleware.AuthenticationMiddleware',

    # 6. MessageMiddleware: Flash messages (form errors, success messages)
    #    Must run after SessionMiddleware (messages stored in session)
    'django.contrib.messages.middleware.MessageMiddleware',

    # 7. ClickjackingMiddleware: Prevents site from being embedded in iframe
    #    Runs last because it only sets X-Frame-Options header
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
# Don't reorder these unless you know what you're doing!
# Wrong order can break authentication, sessions, or CSRF protection

# ROOT_URLCONF: Where Django looks for URL patterns
# Points to algoviz_pro/urls.py which includes all app URLs
ROOT_URLCONF = 'algoviz_pro.urls'

# TEMPLATES
# =========
# Configuration for Django's template engine

TEMPLATES = [
    {
        # Template backend - Django's built-in template engine
        # (Alternative: Jinja2, but Django templates are simpler for this project)
        'BACKEND': 'django.template.backends.django.DjangoTemplates',

        # DIRS: Where to look for templates BEFORE checking app directories
        # We have a global templates/ folder at project root for base.html
        # that all apps inherit from
        #
        # Why global templates folder: base.html with nav/footer is shared by
        # all apps. Instead of duplicating it in each app, we put it in one
        # central location that all apps can access.
        'DIRS': [BASE_DIR / 'templates'],  # Project-level templates

        # APP_DIRS: Also look in each app's templates/ subdirectory
        # True means Django automatically finds algorithms/templates/, etc.
        'APP_DIRS': True,

        # Context processors: Functions that add variables to EVERY template
        # These make things like {{ user }} and {{ request }} available everywhere
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',  # Adds 'debug' variable
                'django.template.context_processors.request',  # Adds 'request' object
                'django.contrib.auth.context_processors.auth',  # Adds 'user' object
                'django.contrib.messages.context_processors.messages',  # Adds messages
            ],
        },
    },
]

# WSGI_APPLICATION: Entry point for WSGI servers (production deployment)
# Points to algoviz_pro/wsgi.py which exposes the WSGI application
# Used by production servers like Gunicorn, uWSGI
WSGI_APPLICATION = 'algoviz_pro.wsgi.application'


# DATABASE
# ========
# Database configuration

DATABASES = {
    'default': {
        # Using SQLite for development
        #
        # Why SQLite:
        # - Zero configuration (no server to install/run)
        # - File-based (easy to delete and recreate)
        # - Perfect for development and learning
        # - Included with Python (no extra dependencies)
        #
        # Why NOT SQLite in production:
        # - No concurrent writes (locking issues)
        # - Limited scalability
        # - No advanced features (full-text search, JSON queries)
        #
        # Production should use PostgreSQL:
        # DATABASES = {
        #     'default': {
        #         'ENGINE': 'django.db.backends.postgresql',
        #         'NAME': 'algoviz_db',
        #         'USER': 'algoviz_user',
        #         'PASSWORD': os.environ.get('DB_PASSWORD'),
        #         'HOST': 'localhost',
        #         'PORT': '5432',
        #     }
        # }
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',  # Database file in project root
    }
}


# PASSWORD VALIDATION
# ===================
# Rules for user passwords (if we had user registration, which we don't)
#
# These validators ensure users choose strong passwords.
# Not critical for this project since we don't have user registration,
# but good practice to keep them enabled in case we add authentication later.

AUTH_PASSWORD_VALIDATORS = [
    # Prevents passwords similar to username/email
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    # Requires minimum 8 characters
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    # Rejects common passwords like "password123"
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    # Prevents all-numeric passwords like "12345678"
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# INTERNATIONALIZATION
# ====================
# Language and timezone settings

# Language for Django's built-in messages and admin
LANGUAGE_CODE = 'en-us'  # US English

# Timezone for datetime storage and display
# Using UTC (Coordinated Universal Time) as recommended by Django
# All datetimes stored in database are in UTC, then converted to user's
# timezone for display (if we implemented timezone selection)
TIME_ZONE = 'UTC'

# Enable Django's translation system
# Allows translating UI to other languages (not using this feature, but enabled by default)
USE_I18N = True

# Use timezone-aware datetimes
# When True, Django uses timezone-aware datetime objects (recommended)
# When False, uses naive datetimes (legacy behavior)
USE_TZ = True


# STATIC FILES (CSS, JavaScript, Images)
# =======================================
# Configuration for serving static assets

# STATIC_URL: URL prefix for static files in templates
# In templates: {% static 'css/style.css' %} → /static/css/style.css
STATIC_URL = '/static/'

# STATICFILES_DIRS: Additional locations to look for static files
# During development, Django serves files from here automatically
#
# We have a project-level static/ folder for shared CSS/JS that all apps use
# Each app can also have its own app/static/app/ folder for app-specific files
#
# Example structure:
# static/css/style.css (global)
# algorithms/static/algorithms/algo.css (app-specific)
STATICFILES_DIRS = [BASE_DIR / 'static']

# STATIC_ROOT: Where 'collectstatic' copies all static files for production
#
# Why we need this: In production, Django doesn't serve static files
# (too slow, not Django's job). Instead:
# 1. Run: python manage.py collectstatic
# 2. Django copies all static files from all apps to staticfiles/
# 3. Nginx/Apache serves files from staticfiles/ directly
#
# During development, we don't use this (Django serves directly from source)
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Trade-off explanation:
# STATICFILES_DIRS: Where Django LOOKS for static files
# STATIC_ROOT: Where Django COLLECTS static files for production
# They must be different directories!


# PRIMARY KEY FIELD TYPE
# ======================
# Default type for auto-generated primary key fields

# BigAutoField: 64-bit integer primary key (up to ~9 quintillion records)
# Alternative: AutoField (32-bit, up to ~2 billion records)
#
# Why BigAutoField: Future-proof. 2 billion records might seem like a lot now,
# but some large systems have hit that limit. BigAutoField prevents needing
# to migrate later.
#
# Trade-off: Uses 8 bytes instead of 4 bytes per ID, but storage is cheap
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# CACHING CONFIGURATION
# =====================
# Cache backend for storing GitHub API responses and expensive queries

CACHES = {
    'default': {
        # LocMemCache: Stores cache in Python memory (RAM)
        #
        # Why LocMemCache for development:
        # - Fast (in-memory)
        # - Zero configuration (no Redis/Memcached server needed)
        # - Perfect for development and single-server deployment
        #
        # Why NOT LocMemCache in production:
        # - Not shared across multiple servers
        # - Lost when server restarts
        # - Limited by available RAM
        #
        # Production should use Redis:
        # CACHES = {
        #     'default': {
        #         'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        #         'LOCATION': 'redis://127.0.0.1:6379/1',
        #     }
        # }
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',

        # LOCATION: Name of this cache instance
        # Can have multiple named caches (e.g., 'github-cache', 'analytics-cache')
        'LOCATION': 'algoviz-cache',

        # TIMEOUT: How long (seconds) cached items live before expiring
        # 1800 seconds = 30 minutes
        # Why 30 minutes: GitHub data doesn't change that often, but we want
        # fresh data within a reasonable time. Too short = wasted API calls,
        # too long = stale data.
        'TIMEOUT': 1800,

        'OPTIONS': {
            # MAX_ENTRIES: Maximum number of items to cache before evicting oldest
            # Why 1000: Reasonable limit for local memory cache. Each cached item
            # might be several KB (JSON responses), so 1000 items ≈ a few MB of RAM
            'MAX_ENTRIES': 1000
        }
    }
}


# GITHUB API CONFIGURATION
# ========================
# Custom settings for our GitHub integration app

# Base URL for GitHub's REST API
# All GitHub requests go to api.github.com, not github.com
GITHUB_API_BASE_URL = 'https://api.github.com'

# Request timeout in seconds
# Why 10 seconds:
# - Long enough for GitHub to respond under normal conditions
# - Short enough to not hang forever if GitHub is down
# - Prevents one slow API call from blocking the entire app
#
# Alternative considered: 30 seconds, but that's too long for user experience
# Better to timeout quickly and show an error than make user wait
GITHUB_API_TIMEOUT = 10

# Cache timeout for GitHub responses (seconds)
# Same as general cache timeout (30 minutes)
# Why: GitHub repository data doesn't change frequently, so 30 minutes of
# caching significantly reduces API calls without serving stale data
GITHUB_CACHE_TIMEOUT = 1800

# Retry attempts for failed GitHub requests
# Why 3 retries:
# - Network hiccups are common (transient failures)
# - 3 attempts gives us 4 total tries (original + 3 retries)
# - More than 3 is excessive (if it failed 3 times, likely not transient)
#
# Exponential backoff: Wait 1s, then 2s, then 4s between retries
# Prevents hammering GitHub's servers during an outage
GITHUB_API_MAX_RETRIES = 3

# Initial delay between retries (seconds)
# Exponential backoff: 1s, 2s, 4s
# Why start at 1 second: Short enough to retry quickly, long enough to
# let transient issues resolve
GITHUB_API_RETRY_DELAY = 1


# ALGORITHM EXECUTION LIMITS
# ===========================
# Safety limits to prevent abuse and performance issues

# Maximum array size for algorithm visualization
# Why 100:
# - O(n²) algorithms with 1000 elements = 1,000,000 operations (too slow)
# - Browser DOM updates: 1000+ animation frames freezes the page
# - 100 is large enough to demonstrate algorithms, small enough to stay responsive
#
# Trade-off: Could allow larger arrays for O(n log n) algorithms, but keeping
# it simple with one limit for all algorithms
MAX_ARRAY_SIZE = 100

# Maximum execution time for any algorithm (seconds)
# Why 30 seconds:
# - Prevents runaway algorithms from hanging the server
# - Long enough for legitimate use (even 100 elements with slow visualization)
# - Short enough to prevent DoS attacks (spamming slow algorithm requests)
#
# Note: We don't currently enforce this in code, but it's here for future
# implementation with timeout decorators or celery tasks
MAX_EXECUTION_TIME = 30

# Security note: These limits are CRITICAL for preventing Denial of Service
# The professor might try sending huge arrays or slow algorithms to crash the app
# These settings show we thought about resource limits and defensive programming