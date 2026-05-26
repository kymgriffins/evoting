# settings.py — Django project configuration.
# This is the control center: database, installed apps, timezone, etc.

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # Project root folder

# ⚠️ Change this in production! Keep it secret.
SECRET_KEY = 'django-insecure-wdtl_f_a$8jprl+l0-+g5q!s$3ha+lgrva85#az0wstu9e)y^c'

# On Vercel, DEBUG must be False and ALLOWED_HOSTS must include the domain
DEBUG = False

ALLOWED_HOSTS = [
    '.vercel.app',           # Your Vercel deployment URL
    '.kymgriffins.vercel.app',
    'evoting-kymgriffins.vercel.app',
    'localhost',
    '127.0.0.1',
]

# ── Installed Apps (plugins the project uses) ──────────────
INSTALLED_APPS = [
    'django.contrib.admin',          # Admin panel at /admin/
    'django.contrib.auth',           # User authentication system
    'django.contrib.contenttypes',   # Framework for permissions
    'django.contrib.sessions',       # Browser session management
    'django.contrib.messages',       # Flash messages (success/error popups)
    'django.contrib.staticfiles',    # CSS/JS file serving
    'rest_framework',                # Django REST Framework for APIs
    'core',                          # OUR APP — all the code
]

# Whitenoise MUST be first — it serves static files in production
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',    # Serves CSS/JS in production
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
# For this MVP demo, SQLite works within a single serverless invocation.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
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
