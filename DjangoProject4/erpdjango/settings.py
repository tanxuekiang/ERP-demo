from pathlib import Path
import os
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-q7ynp#%t3c7hai5a&bvgp9atta+)@%v9d8i79&8=)hmy6^snyx'
DEBUG = True
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '0.0.0.0']  # 允许所有开发地址

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'myerpapp',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    #'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'erpdjango.urls'
WSGI_APPLICATION = 'erpdjango.wsgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = False

STATIC_URL = 'static/'


# 跨域配置（关键）
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173", # 前端地址
    "http://127.0.0.1:5173",
]
CORS_ALLOW_CREDENTIALS = True # 允许携带Cookie
CORS_ALLOW_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
CORS_ALLOW_HEADERS = ['Content-Type', 'Authorization']

# Session配置
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_SAMESITE = 'Lax' # 允许跨域Cookie
SESSION_COOKIE_HTTPONLY = False # 开发环境关闭HTTPONLY
SESSION_COOKIE_SECURE = False # 开发环境关闭HTTPS
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_AGE = 86400 # 24小时过期


import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')  # 项目根目录下的 media 文件夹
MEDIA_URL = '/media/'

# 大文件上传限制（必须配置）
DATA_UPLOAD_MAX_MEMORY_SIZE = 1 * 1024 * 1024 * 1024  # 1GB
FILE_UPLOAD_MAX_MEMORY_SIZE = 1 * 1024 * 1024 * 1024
FILE_UPLOAD_HANDLERS = [
    'django.core.files.uploadhandler.TemporaryFileUploadHandler',  # 大文件用临时文件处理
]
CORS_ALLOW_CREDENTIALS = True  # 允许携带 Cookie