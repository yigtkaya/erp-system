"""
Base settings for ERP System project.
"""

from pathlib import Path
import os
from django.core.exceptions import ImproperlyConfigured

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

def get_env_variable(var_name):
    try:
        return os.environ[var_name]
    except KeyError:
        error_msg = f"Set the {var_name} environment variable"
        raise ImproperlyConfigured(error_msg)

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'anymail',
    'manufacturing',
    'inventory',
    'sales',
    'purchase',
    'maintenance',
    'quality_control',
    'rest_framework',
    'guardian',
    'erp_core',
    'drf_yasg',
    'corsheaders',
    'axes',
    'defender',
]

# Custom User Model
AUTH_USER_MODEL = 'erp_core.User'

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'axes.middleware.AxesMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'erp_core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
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

WSGI_APPLICATION = 'erp_core.wsgi.application'

# Database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB', 'erp_dev'),
        'USER': os.getenv('POSTGRES_USER', 'erp_user'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'erp_password'),
        'HOST': os.getenv('POSTGRES_HOST', 'db'),
        'PORT': os.getenv('POSTGRES_PORT', '5432'),
        'OPTIONS': {
            'connect_timeout': int(os.getenv('DB_CONNECT_TIMEOUT', '5')),
        },
    }
}

# Redis configuration
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.getenv('REDIS_URL', 'redis://redis:6379/1'),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "SOCKET_CONNECT_TIMEOUT": int(os.getenv('REDIS_CONNECT_TIMEOUT', '5')),
            "SOCKET_TIMEOUT": int(os.getenv('REDIS_SOCKET_TIMEOUT', '5')),
        }
    }
}

# Django Axes Configuration
AXES_FAILURE_LIMIT = 5  # Number of login attempts before lockout
AXES_COOLOFF_TIME = 1  # 1 hour lockout
AXES_RESET_ON_SUCCESS = True  # Reset the number of failed attempts on successful login
AXES_LOCKOUT_URL = '/auth/login/'  # Redirect to login page on lockout
AXES_USE_USER_AGENT = True  # Include user agent in lockout criteria
AXES_LOCK_OUT_BY_COMBINATION_USER_AND_IP = True  # Lock out based on both username and IP
AXES_BEHIND_REVERSE_PROXY = False  # Set to True if behind a reverse proxy
AXES_ENABLE_ADMIN = True  # Enable Axes admin interface
AXES_HANDLER = 'axes.handlers.database.AxesDatabaseHandler'  # Use database handler for persistence

# Authentication Backends
AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
]

# Password validation
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

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication'
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated'
    ]
}

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Email Configuration
EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"
DEFAULT_FROM_EMAIL = f"noreply@{os.getenv('MAILGUN_SENDER_DOMAIN')}"
SERVER_EMAIL = f"server@{os.getenv('MAILGUN_SENDER_DOMAIN')}"

ANYMAIL = {
    "MAILGUN_API_KEY": os.getenv('MAIL_GUN_API_KEY'),
    "MAILGUN_SENDER_DOMAIN": os.getenv('MAILGUN_SENDER_DOMAIN'),
    "MAILGUN_API_URL": "https://api.mailgun.net/v3",
}

# Login/Logout Settings
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'login' 