"""Configurações da aplicação Flask.

Este módulo contém as classes de configuração para diferentes ambientes
(desenvolvimento, teste, produção) seguindo as melhores práticas do Flask.
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()


class Config:
    """Configuração base da aplicação."""
    
    # Configurações básicas do Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    FLASK_APP = os.environ.get('FLASK_APP') or 'run.py'
    
    # Configurações do banco de dados
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    
    # Configurações de segurança
    WTF_CSRF_ENABLED = os.environ.get('CSRF_ENABLED', 'True').lower() == 'true'
    WTF_CSRF_TIME_LIMIT = int(os.environ.get('WTF_CSRF_TIME_LIMIT', 3600))
    
    # Configurações de scraping
    SCRAPING_DELAY_MIN = int(os.environ.get('SCRAPING_DELAY_MIN', 1))
    SCRAPING_DELAY_MAX = int(os.environ.get('SCRAPING_DELAY_MAX', 3))
    MAX_RETRY_ATTEMPTS = int(os.environ.get('MAX_RETRY_ATTEMPTS', 3))
    REQUEST_TIMEOUT = int(os.environ.get('REQUEST_TIMEOUT', 30))
    USER_AGENT = os.environ.get('USER_AGENT', 
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    # Configurações do Selenium
    WEBDRIVER_PATH = os.environ.get('WEBDRIVER_PATH')
    HEADLESS_MODE = os.environ.get('HEADLESS_MODE', 'True').lower() == 'true'
    WINDOW_SIZE = os.environ.get('WINDOW_SIZE', '1920,1080')
    
    # Configurações de logs
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/facebook_scraper.log')
    MAX_LOG_SIZE = int(os.environ.get('MAX_LOG_SIZE', 10485760))  # 10MB
    LOG_BACKUP_COUNT = int(os.environ.get('LOG_BACKUP_COUNT', 5))
    
    # Configurações de exportação
    EXPORT_DIR = os.environ.get('EXPORT_DIR', 'exports')
    MAX_EXPORT_SIZE = int(os.environ.get('MAX_EXPORT_SIZE', 104857600))  # 100MB
    
    # Configurações do Celery
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    
    @staticmethod
    def init_app(app):
        """Inicializar configurações específicas da aplicação."""
        pass


class DevelopmentConfig(Config):
    """Configuração para ambiente de desenvolvimento."""
    
    DEBUG = True
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///facebook_scraper.db'
    
    # Logs mais verbosos em desenvolvimento
    LOG_LEVEL = 'DEBUG'
    
    # Rate limiting mais relaxado
    RATELIMIT_STORAGE_URL = os.environ.get('RATE_LIMIT_STORAGE_URL', 
        'redis://localhost:6379/1')
    

class TestingConfig(Config):
    """Configuração para ambiente de testes."""
    
    TESTING = True
    DEBUG = False
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL_TEST') or \
        'sqlite:///test_facebook_scraper.db'
    
    # Configurações específicas para testes
    SCRAPING_DELAY_MIN = 0
    SCRAPING_DELAY_MAX = 0
    

class ProductionConfig(Config):
    """Configuração para ambiente de produção."""
    
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///facebook_scraper.db'
    
    # Configurações de segurança mais rigorosas
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    
    @classmethod
    def init_app(cls, app):
        """Configurações específicas para produção."""
        Config.init_app(app)
        
        # Log para syslog em produção
        import logging
        from logging.handlers import SysLogHandler
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)


# Dicionário de configurações disponíveis
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}