"""
Django settings for OrderTango project.

Generated by 'django-admin startproject' using Django 2.1.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os

from datetime import timedelta

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '4-(h88i=$o8n9dp5rujtqq23gv@o!wl53*us&^tz%+gm_@8v=d'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = [
    'accounts',
    'chat',
    'tenant_schemas',
    'corsheaders',
    'channels',
    'rest_framework',
    'OrderTangoApp',
    'OrderTangoSubDomainApp',
    'OrderTangoOrdermgmtApp',
    'InventorymgmtApp',
    'OrderTangoOrderFulfilmtApp',
    'accounts',
    'chat',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'OrderTango.middleware.TenantTutorialMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ORIGIN_WHITELIST = (
    "http://customer12.127.0.0.1:8000",
    "http://customer12.localhost: 8000",
)
CORS_ORIGIN_ALLOW_ALL = True 
CORS_ALLOW_CREDENTIALS = True 

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'Access-Control-Allow-Origin',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    )
}

JWT_AUTH = {
    'JWT_ALLOW_REFRESH': True,
    'JWT_EXPIRATION_DELTA': timedelta(seconds=3600),
}

ROOT_URLCONF = 'OrderTango.urls'
PUBLIC_SCHEMA_URLCONF = 'OrderTango.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

SHARED_APPS = (
    'tenant_schemas',  # mandatory, should always be before any django app
    'OrderTangoApp',# you must list the app where your tenant model resides in
    'django.contrib.contenttypes',
    # everything below here is optional
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.admin',
    'chat',
)

TENANT_APPS = (
    'OrderTangoSubDomainApp',
    'OrderTangoOrdermgmtApp',
    'OrderTangoOrderFulfilmtApp',
    'InventorymgmtApp',
    'chat',
    'accounts',
    'django.contrib.sessions',
)

TENANT_MODEL = "OrderTangoApp.Schema"


DATABASE_ROUTERS = (
    'tenant_schemas.routers.TenantSyncRouter',
)

MIDDLEWARE_CLASSES = (
    'tenant_schemas.middleware.TenantMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.request',
)

DEFAULT_FILE_STORAGE = 'tenant_schemas.storage.TenantFileSystemStorage'

WSGI_APPLICATION = 'OrderTango.wsgi.application'
ASGI_APPLICATION = 'OrderTango.routing.application'
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}

# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'tenant_schemas.postgresql_backend',
        'NAME': 'syiok1',
        'USER': 'postgres',
        'PASSWORD': 'TN41at5593@',
        'HOST': '52.221.61.17',
        'PORT': '5432',
    }
}

# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

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

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.office365.com'
EMAIL_HOST_USER = 'noreply@ordertango.com'
EMAIL_HOST_PASSWORD = '99Bottles0nthewa11!@#'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = 'noreply@ordertango.com'
SERVER_EMAIL = 'noreply@ordertango.com'

# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True

USE_L10N = True

USE_TZ = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {
    'console': {
    'class': 'logging.StreamHandler',
},
},
    'loggers': {
    'django': {
    'handlers': ['console'],
    'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
},
},
}

timeTxt = open(os.path.join(PROJECT_ROOT,"time.txt")).read().split()
TIME = int(timeTxt[-1])

DOMAIN_NAME='.localhost'  # don't add your port or www here!
IP_ADDRESS="127.0.0.1"
LOCAL_HOST="localhost"  # don't add your port or www here!
SESSION_COOKIE_AGE = TIME
SESSION_SAVE_EVERY_REQUEST = True
PORT='8000'
HTTP='http://'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

IMPORT_FILES_FOLDER = os.path.join(PROJECT_ROOT, 'Importfiles')

STATIC_URL = '/static/'
#STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static')
STATICFILES_DIRS=[
    os.path.join(BASE_DIR,"__shared__"),
]

STRIPE_SECRET_KEY = 'sk_test_35oVtTbg0vLixDBY7dwhTdaU'
STRIPE_PUBLISHABLE_KEY = 'pk_test_UDdBZ8oiG9H2VXNdfar54wdL'
<<<<<<< HEAD
=======
<<<<<<< HEAD
=======
>>>>>>> drf messaging app initial commit

try:
    from .local_settings import *
except ImportError as e:
    if "local_settings" not in str(e):
        raise e
<<<<<<< HEAD
=======
>>>>>>> drf messaging app initial commit
>>>>>>> drf messaging app initial commit
