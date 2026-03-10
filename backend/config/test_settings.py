import os
from .settings import *

DEBUG = False

CONNECT_TO_LOCAL_VECTOR_DB = False

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('TEST_DB_NAME', 'test_db'),
        'USER': os.getenv('TEST_DB_USER'),
        'PASSWORD': os.getenv('TEST_DB_PASSWORD'),
        'HOST': os.getenv('TEST_DB_HOST', 'localhost'),
        'PORT': os.getenv('TEST_DB_PORT', '5432'),
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.locmem.LocMemBackend'

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}
