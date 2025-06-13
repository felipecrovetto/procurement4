"""
Configuración específica para producción en Heroku
"""

import os

class ProductionConfig:
    """Configuración para entorno de producción"""
    
    # Configuración básica
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'fallback-secret-key-change-in-production'
    
    # Base de datos
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or 'sqlite:///procurement.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Configuración de archivos
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = 'src/uploads'
    
    # Configuración de logging
    LOG_LEVEL = 'INFO'
    LOG_TO_STDOUT = True
    
    # Configuración de seguridad
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Configuración de CORS
    CORS_ORIGINS = ['*']  # En producción, especificar dominios específicos
    
    # Configuración de cache
    SEND_FILE_MAX_AGE_DEFAULT = 31536000  # 1 año para archivos estáticos

class DevelopmentConfig:
    """Configuración para entorno de desarrollo"""
    
    SECRET_KEY = 'dev-secret-key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///procurement.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    UPLOAD_FOLDER = 'src/uploads'
    
    LOG_LEVEL = 'DEBUG'
    LOG_TO_STDOUT = False
    
    CORS_ORIGINS = ['*']

def get_config():
    """Obtener configuración según el entorno"""
    env = os.environ.get('FLASK_ENV', 'development')
    
    if env == 'production':
        return ProductionConfig()
    else:
        return DevelopmentConfig()

