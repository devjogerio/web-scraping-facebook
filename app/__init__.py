"""Factory da aplicação Flask.

Este módulo implementa o padrão Application Factory
para criar e configurar a aplicação Flask.
"""

import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import sessionmaker

# Instância global do SQLAlchemy
db = SQLAlchemy()


def create_app(config_name: str = 'development') -> Flask:
    """Criar e configurar aplicação Flask.
    
    Args:
        config_name: Nome da configuração (development, testing, production)
        
    Returns:
        Aplicação Flask configurada
    """
    app = Flask(__name__)
    
    # Configurar aplicação
    _configure_app(app, config_name)
    
    # Inicializar extensões
    _init_extensions(app)
    
    # Registrar blueprints
    _register_blueprints(app)
    
    # Configurar handlers de erro
    _register_error_handlers(app)
    
    # Configurar contexto da aplicação
    _setup_app_context(app)
    
    return app


def _configure_app(app: Flask, config_name: str) -> None:
    """Configurar aplicação com base no ambiente.
    
    Args:
        app: Aplicação Flask
        config_name: Nome da configuração
    """
    from config.config import config
    
    # Aplicar configuração
    config_class = config.get(config_name, config['default'])
    app.config.from_object(config_class)
    
    # Inicializar configuração específica
    config_class.init_app(app)


def _init_extensions(app: Flask) -> None:
    """Inicializar extensões Flask.
    
    Args:
        app: Aplicação Flask
    """
    # Inicializar SQLAlchemy
    db.init_app(app)
    
    # Criar tabelas se não existirem
    with app.app_context():
        _create_tables()


def _create_tables() -> None:
    """Criar tabelas do banco de dados."""
    try:
        # Importar modelos para registrar no SQLAlchemy
        from app.models import ScrapingTask, FacebookData, ExportJob
        
        # Criar todas as tabelas
        db.create_all()
        
        logging.info("Tabelas do banco de dados criadas/verificadas")
        
    except Exception as e:
        logging.error(f"Erro ao criar tabelas: {str(e)}")
        raise


def _register_blueprints(app: Flask) -> None:
    """Registrar blueprints da aplicação.
    
    Args:
        app: Aplicação Flask
    """
    with app.app_context():
        # Criar instâncias dos repositórios e use cases
        repositories = _create_repositories()
        services = _create_services()
        use_cases = _create_use_cases(repositories, services)
        
        # Criar controllers
        controllers = _create_controllers(use_cases, repositories, services)
        
        # Registrar blueprints
        app.register_blueprint(controllers['dashboard'].get_blueprint())
        app.register_blueprint(controllers['scraping'].get_blueprint())
        app.register_blueprint(controllers['export'].get_blueprint())


def _create_repositories() -> dict:
    """Criar instâncias dos repositórios.
    
    Returns:
        Dicionário com repositórios
    """
    from app.repositories import (
        ScrapingTaskRepository,
        FacebookDataRepository,
        ExportJobRepository
    )
    
    # Usar sessão do SQLAlchemy
    session = db.session
    
    return {
        'task': ScrapingTaskRepository(session),
        'data': FacebookDataRepository(session),
        'export': ExportJobRepository(session)
    }


def _create_services() -> dict:
    """Criar instâncias dos serviços.
    
    Returns:
        Dicionário com serviços
    """
    from app.services import ScrapingService, ExcelService
    from flask import current_app
    
    # Configurações para o serviço de scraping
    scraping_config = {
        'delay_min': current_app.config.get('SCRAPING_DELAY_MIN', 1),
        'delay_max': current_app.config.get('SCRAPING_DELAY_MAX', 3),
        'timeout': current_app.config.get('REQUEST_TIMEOUT', 30),
        'max_retries': current_app.config.get('MAX_RETRY_ATTEMPTS', 3),
        'headless': current_app.config.get('HEADLESS_MODE', True),
        'user_agent': current_app.config.get('USER_AGENT', '')
    }
    
    return {
        'scraping': ScrapingService(scraping_config),
        'excel': ExcelService()
    }


def _create_use_cases(repositories: dict, services: dict) -> dict:
    """Criar instâncias dos use cases.
    
    Args:
        repositories: Dicionário com repositórios
        services: Dicionário com serviços
        
    Returns:
        Dicionário com use cases
    """
    from app.use_cases import (
        CreateScrapingTaskUseCase,
        ExecuteScrapingUseCase,
        ExportToExcelUseCase
    )
    
    return {
        'create_task': CreateScrapingTaskUseCase(repositories['task']),
        'execute_scraping': ExecuteScrapingUseCase(
            repositories['task'],
            repositories['data'],
            services['scraping']
        ),
        'export_excel': ExportToExcelUseCase(
            repositories['task'],
            repositories['data'],
            repositories['export'],
            services['excel']
        )
    }


def _create_controllers(use_cases: dict, repositories: dict, services: dict) -> dict:
    """Criar instâncias dos controllers.
    
    Args:
        use_cases: Dicionário com use cases
        repositories: Dicionário com repositórios
        services: Dicionário com serviços
        
    Returns:
        Dicionário com controllers
    """
    from app.controllers import (
        DashboardController,
        ScrapingController,
        ExportController
    )
    
    return {
        'dashboard': DashboardController(
            repositories['task'],
            repositories['data'],
            repositories['export']
        ),
        'scraping': ScrapingController(
            use_cases['create_task'],
            use_cases['execute_scraping'],
            repositories['task'],
            repositories['data']
        ),
        'export': ExportController(
            use_cases['export_excel'],
            repositories['export'],
            repositories['task']
        )
    }


def _register_error_handlers(app: Flask) -> None:
    """Registrar handlers de erro.
    
    Args:
        app: Aplicação Flask
    """
    @app.errorhandler(404)
    def not_found_error(error):
        """Handler para erro 404."""
        try:
            return render_template('errors/404.html'), 404
        except:
            return '<h1>404 - Página não encontrada</h1>', 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handler para erro 500."""
        try:
            db.session.rollback()
            return render_template('errors/500.html'), 500
        except:
            return '<h1>500 - Erro interno do servidor</h1>', 500
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        """Handler genérico para exceções."""
        try:
            app.logger.error(f"Erro não tratado: {str(error)}")
            db.session.rollback()
            return render_template('errors/500.html'), 500
        except:
            return f'<h1>Erro: {str(error)}</h1>', 500


def _setup_app_context(app: Flask) -> None:
    """Configurar contexto da aplicação.
    
    Args:
        app: Aplicação Flask
    """
    @app.context_processor
    def inject_template_vars():
        """Injetar variáveis nos templates."""
        return {
            'app_name': 'Facebook Scraper',
            'app_version': '1.0.0'
        }
    
    # Configurar logging na inicialização
    if not app.debug and not app.testing:
        # Configurar logging para produção
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler(
            'logs/facebook_scraper.log',
            maxBytes=10240000,
            backupCount=10
        )
        
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Facebook Scraper startup')


# Importar render_template para os error handlers
from flask import render_template