import os
from pathlib import Path


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-bl)n69ebpr(0!+a2+hewg7rnt$tj5i^m7yzlr*_guy_qirrq_t'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# List of allowed hosts
ALLOWED_HOSTS = []

# CORS settings for cross-origin requests (if needed)
INSTALLED_APPS = [ 
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',  # Django REST framework
    'rest_framework.authtoken',  # For token-based authentication
    'corsheaders',  # CORS Headers
    'notes',  # Your application
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # CORS Middleware
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',  # Update with your frontend URL if needed
]
ROOT_URLCONF = 'KMSimba.urls'

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

WSGI_APPLICATION = 'KMSimba.wsgi.application'

# Database configuration using environment variables
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'RARE_db',
        'USER': 'remote_user',
        'PASSWORD': 'Password',
        'HOST': '127.0.0.1',
        'PORT': '3306',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Django REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',  
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',  # Adjusted for more secure defaults
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        # 'rest_framework.renderers.BrowsableAPIRenderer',  # Enable for development only
    ],
}

# Logging configuration for better debugging and monitoring
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'django': {
        'handlers': ['console'],
        'level': 'DEBUG' if DEBUG else 'INFO',
        'propagate': False,
    },
}


# Other settings
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# Notes directory configuration
NOTES_DIR = os.path.join(BASE_DIR, 'notes_files')
os.makedirs(NOTES_DIR, exist_ok=True)  # Create the directory if it doesn't exist

# Hugging Face Transformers cache directory
TRANSFORMERS_CACHE = os.path.join(BASE_DIR, 'transformers_cache')
os.environ['TRANSFORMERS_CACHE'] = TRANSFORMERS_CACHE

# Large file upload settings
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10 MB