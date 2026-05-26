# settings.py — Django project configuration.
# This is the control center: database, installed apps, timezone, etc.

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # Project root folder

# ⚠️ Change this in production! Keep it secret.
SECRET_KEY = 'django-insecure-wdtl_f_a$8jprl+l0-+g5q!s$3ha+lgrva85#az0wstu9e)y^c'

# On Vercel, DEBUG must be False and ALLOWED_HOSTS must include the domain
DEBUG = False

import os

ALLOWED_HOSTS = [
    '.vercel.app',           # Your Vercel deployment URL
    '.kymgriffins.vercel.app',
    'evoting-kymgriffins.vercel.app',
    'localhost',
    '127.0.0.1',
]

# Allow overriding/extending via environment variables
env_hosts = os.environ.get('ALLOWED_HOSTS')
if env_hosts:
    ALLOWED_HOSTS.extend([host.strip() for host in env_hosts.split(',') if host.strip()])

# Automatically add Vercel dynamic URLs if available
vercel_url = os.environ.get('VERCEL_URL')
if vercel_url:
    ALLOWED_HOSTS.append(vercel_url)
    ALLOWED_HOSTS.append(f".{vercel_url}")


# ── Installed Apps (plugins the project uses) ──────────────
INSTALLED_APPS = [
    'django.contrib.admin',          # Admin panel at /admin/
    'django.contrib.auth',           # User authentication system
    'django.contrib.contenttypes',   # Framework for permissions
    'django.contrib.sessions',       # Browser session management
    'django.contrib.messages',       # Flash messages (success/error popups)
    'django.contrib.staticfiles',    # CSS/JS file serving
    'corsheaders',                   # CORS support
    'rest_framework',                # Django REST Framework for APIs
    'core',                          # OUR APP — all the code
]

# Whitenoise MUST be first — it serves static files in production
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',    # Serves CSS/JS in production
    'corsheaders.middleware.CorsMiddleware',         # CORS headers middleware (must be before CommonMiddleware)
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',       # CSRF protection for forms
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'evoting_project.urls'  # Master URL config file

# ── Template Configuration ─────────────────────────────────
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'core' / 'templates'],  # Look for HTML files here
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',  # Makes {{ user }} available
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# ── Database ───────────────────────────────────────────────
# Vercel deployments are read-only filesystem, so SQLite won't persist.
# For a real deployment, switch to PostgreSQL (Vercel Postgres or Neon).
# If a DATABASE_URL or POSTGRES_URL environment variable is provided, we use it.
import dj_database_url
import shutil

db_url = os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL')
if db_url:
    DATABASES = {
        'default': dj_database_url.config(
            default=db_url,
            conn_max_age=600,
            ssl_require=True
        )
    }
else:
    # If running on Vercel but no Postgres URL is provided, we copy the pre-populated SQLite DB
    # to the writeable '/tmp' directory so write operations (like login, voting, ratings) don't crash.
    if os.environ.get('VERCEL') == '1':
        db_path = '/tmp/db.sqlite3'
        original_db = BASE_DIR / 'db.sqlite3'
        if not os.path.exists(db_path) and os.path.exists(original_db):
            try:
                shutil.copy2(original_db, db_path)
            except Exception:
                pass
    else:
        db_path = BASE_DIR / 'db.sqlite3'

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': db_path,
        }
    }

# ── Password Validation ───────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ── Internationalization ──────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Nairobi'
USE_I18N = True
USE_TZ = True

# ── Static Files (CSS, JS, Images) ─────────────────────────
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'core' / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'   # Whitenoise collects static files here
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── Custom User Model ──────────────────────────────────────
AUTH_USER_MODEL = 'core.User'

# ── Authentication URLs ───────────────────────────────────
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# ── Security Settings for Production ──────────────────────
CSRF_TRUSTED_ORIGINS = [
    'https://*.vercel.app',
    'https://evoting-kymgriffins.vercel.app',
]

# Allow overriding/extending CSRF trusted origins via environment variables
env_csrf = os.environ.get('CSRF_TRUSTED_ORIGINS')
if env_csrf:
    CSRF_TRUSTED_ORIGINS.extend([origin.strip() for origin in env_csrf.split(',') if origin.strip()])
else:
    # Fallback to local HTTP environments for testing
    CSRF_TRUSTED_ORIGINS.extend([
        'http://localhost:8000',
        'http://127.0.0.1:8000',
    ])

# Automatically add Vercel dynamic url with HTTPS scheme
if vercel_url:
    CSRF_TRUSTED_ORIGINS.append(f"https://{vercel_url}")
    CSRF_TRUSTED_ORIGINS.append(f"https://*.{vercel_url}")

# ── CORS Settings ──────────────────────────────────────────
# Default allowed origins for frontend applications
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',  # Standard React/Next.js local port
    'http://127.0.0.1:3000',
    'https://evoting-kymgriffins.vercel.app',
]

env_cors = os.environ.get('CORS_ALLOWED_ORIGINS')
if env_cors:
    CORS_ALLOWED_ORIGINS.extend([origin.strip() for origin in env_cors.split(',') if origin.strip()])

# Automatically add Vercel dynamic URL to CORS if available
if vercel_url:
    CORS_ALLOWED_ORIGINS.append(f"https://{vercel_url}")

# Allow all origins in development or if explicitly set via env var
CORS_ALLOW_ALL_ORIGINS = os.environ.get('CORS_ALLOW_ALL_ORIGINS', 'False').lower() in ('true', '1', 'yes')
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOW_CREDENTIALS = True

