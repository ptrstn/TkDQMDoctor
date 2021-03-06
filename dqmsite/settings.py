"""
Django settings for dqmsite project.

Generated by 'django-admin startproject' using Django 1.11.7.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
from decouple import config

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('DJANGO_SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DJANGO_DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = [
    config('DJANGO_ALLOWED_HOSTS', default='localhost'),
    'tkdqmdoctor.web.cern.ch',
    'dev-tkdqmdoctor.web.cern.ch',
    'test-tkdqmdoctor.web.cern.ch',
    '127.0.0.1'
]

# Application definition

INSTALLED_APPS = [
    'django_tables2',
    'django_filters',
    'widget_tweaks',
    'bootstrap3',
    'certhelper.apps.CerthelperConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.cern',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'categories',
    'categories.editor',
    'nested_admin',
    'ckeditor',
    'dynamic_preferences',
    # comment the following line if you don't want to use user preferences
    # 'dynamic_preferences.users.apps.UserPreferencesConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
]

ROOT_URLCONF = 'dqmsite.urls'

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
                'dynamic_preferences.processors.global_preferences',
            ],
        },
    },
]

WSGI_APPLICATION = 'dqmsite.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': config('DJANGO_DATABASE_ENGINE', default=''),
        'NAME': config('DJANGO_DATABASE_NAME', default=''),
        'USER': config('DJANGO_DATABASE_USER', default=''),
        'PASSWORD': config('DJANGO_DATABASE_PASSWORD', default=''),
        'HOST': config('DJANGO_DATABASE_HOST', default=''),
        'PORT': config('DJANGO_DATABASE_PORT', default=''),
    },
}

# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

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

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)

# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = (os.path.join(BASE_DIR, 'static'),)
STATIC_ROOT = os.path.join(BASE_DIR, 'wsgi/static')

# Redirecting from the default account/profile after login
LOGIN_REDIRECT_URL = '/'

# Needed for django-allauth
SITE_ID = 1
ACCOUNT_EMAIL_REQUIRED = 'false'
ACCOUNT_EMAIL_VERIFICATION = 'none'

ADMINS = [('Peter Stein', 'peter.stein@cern.ch')]

EMAIL_HOST = config('DJANGO_EMAIL_HOST', default='localhost')
EMAIL_PORT = config('DJANGO_EMAIL_PORT', default=25, cast=int)
EMAIL_HOST_USER = config('DJANGO_EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('DJANGO_EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = config('DJANGO_EMAIL_USE_TLS', default=False, cast=bool)
SERVER_EMAIL = config('DJANGO_SERVER_EMAIL', default='root@localhost')
