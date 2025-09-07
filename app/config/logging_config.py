"""Configuração do sistema de logs da aplicação."""

import os
import logging
import logging.config
from datetime import datetime
from pathlib import Path


class LoggingConfig:
    """Configuração centralizada do sistema de logs."""
    
    def __init__(self, app=None):
        """Inicializar configuração de logs.
        
        Args:
            app: Instância da aplicação Flask (opcional)
        """
        self.app = app
        self.logs_dir = Path('logs')
        self._ensure_logs_directory()
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Inicializar logs para aplicação Flask.
        
        Args:
            app: Instância da aplicação Flask
        """
        self.app = app
        
        # Configurar nível de log baseado no ambiente
        log_level = app.config.get('LOG_LEVEL', 'INFO')
        
        # Aplicar configuração
        self._setup_logging(log_level)
        
        # Configurar logs do Flask
        self._setup_flask_logging(app)
    
    def _ensure_logs_directory(self):
        """Garantir que o diretório de logs existe."""
        self.logs_dir.mkdir(exist_ok=True)
        
        # Criar subdiretórios para diferentes tipos de log
        (self.logs_dir / 'app').mkdir(exist_ok=True)
        (self.logs_dir / 'scraping').mkdir(exist_ok=True)
        (self.logs_dir / 'export').mkdir(exist_ok=True)
        (self.logs_dir / 'error').mkdir(exist_ok=True)
    
    def _setup_logging(self, log_level='INFO'):
        """Configurar sistema de logging.
        
        Args:
            log_level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        # Configuração de formatação
        formatters = {
            'detailed': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'simple': {
                'format': '%(asctime)s - %(levelname)s - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'json': {
                'format': '%(asctime)s %(name)s %(levelname)s %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            }
        }
        
        # Configuração de handlers
        handlers = {
            'console': {
                'class': 'logging.StreamHandler',
                'level': log_level,
                'formatter': 'simple',
                'stream': 'ext://sys.stdout'
            },
            'app_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'INFO',
                'formatter': 'detailed',
                'filename': str(self.logs_dir / 'app' / 'app.log'),
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'encoding': 'utf8'
            },
            'scraping_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'DEBUG',
                'formatter': 'detailed',
                'filename': str(self.logs_dir / 'scraping' / 'scraping.log'),
                'maxBytes': 20971520,  # 20MB
                'backupCount': 10,
                'encoding': 'utf8'
            },
            'export_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'INFO',
                'formatter': 'detailed',
                'filename': str(self.logs_dir / 'export' / 'export.log'),
                'maxBytes': 5242880,  # 5MB
                'backupCount': 3,
                'encoding': 'utf8'
            },
            'error_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'ERROR',
                'formatter': 'detailed',
                'filename': str(self.logs_dir / 'error' / 'error.log'),
                'maxBytes': 10485760,  # 10MB
                'backupCount': 10,
                'encoding': 'utf8'
            }
        }
        
        # Configuração de loggers
        loggers = {
            '': {  # Root logger
                'level': log_level,
                'handlers': ['console', 'app_file', 'error_file']
            },
            'app.services.scraping_service': {
                'level': 'DEBUG',
                'handlers': ['scraping_file', 'console'],
                'propagate': False
            },
            'app.services.excel_service': {
                'level': 'INFO',
                'handlers': ['export_file', 'console'],
                'propagate': False
            },
            'app.use_cases': {
                'level': 'INFO',
                'handlers': ['app_file', 'console'],
                'propagate': False
            },
            'selenium': {
                'level': 'WARNING',
                'handlers': ['scraping_file'],
                'propagate': False
            },
            'urllib3': {
                'level': 'WARNING',
                'handlers': ['error_file'],
                'propagate': False
            }
        }
        
        # Aplicar configuração
        config = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': formatters,
            'handlers': handlers,
            'loggers': loggers
        }
        
        logging.config.dictConfig(config)
    
    def _setup_flask_logging(self, app):
        """Configurar logs específicos do Flask.
        
        Args:
            app: Instância da aplicação Flask
        """
        # Configurar logger do Flask
        if not app.debug and not app.testing:
            # Em produção, usar arquivo de log
            file_handler = logging.handlers.RotatingFileHandler(
                str(self.logs_dir / 'app' / 'flask.log'),
                maxBytes=10240000,
                backupCount=10
            )
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            
            app.logger.setLevel(logging.INFO)
            app.logger.info('Aplicação Flask iniciada')
    
    def get_logger(self, name):
        """Obter logger configurado.
        
        Args:
            name: Nome do logger
            
        Returns:
            logging.Logger: Logger configurado
        """
        return logging.getLogger(name)
    
    def log_scraping_start(self, task_id, task_name, url):
        """Log de início de scraping.
        
        Args:
            task_id: ID da tarefa
            task_name: Nome da tarefa
            url: URL sendo processada
        """
        logger = self.get_logger('app.services.scraping_service')
        logger.info(
            f"Iniciando scraping - Task ID: {task_id}, Nome: {task_name}, URL: {url}"
        )
    
    def log_scraping_progress(self, task_id, progress, items_processed):
        """Log de progresso do scraping.
        
        Args:
            task_id: ID da tarefa
            progress: Percentual de progresso
            items_processed: Número de itens processados
        """
        logger = self.get_logger('app.services.scraping_service')
        logger.info(
            f"Progresso scraping - Task ID: {task_id}, Progresso: {progress}%, "
            f"Itens: {items_processed}"
        )
    
    def log_scraping_complete(self, task_id, total_items, duration):
        """Log de conclusão do scraping.
        
        Args:
            task_id: ID da tarefa
            total_items: Total de itens extraídos
            duration: Duração em segundos
        """
        logger = self.get_logger('app.services.scraping_service')
        logger.info(
            f"Scraping concluído - Task ID: {task_id}, Total: {total_items} itens, "
            f"Duração: {duration:.2f}s"
        )
    
    def log_scraping_error(self, task_id, error, context=None):
        """Log de erro no scraping.
        
        Args:
            task_id: ID da tarefa
            error: Erro ocorrido
            context: Contexto adicional (opcional)
        """
        logger = self.get_logger('app.services.scraping_service')
        context_str = f" - Contexto: {context}" if context else ""
        logger.error(
            f"Erro no scraping - Task ID: {task_id}, Erro: {str(error)}{context_str}",
            exc_info=True
        )
    
    def log_export_start(self, job_id, task_ids, data_types):
        """Log de início de exportação.
        
        Args:
            job_id: ID do job de exportação
            task_ids: IDs das tarefas sendo exportadas
            data_types: Tipos de dados sendo exportados
        """
        logger = self.get_logger('app.services.excel_service')
        logger.info(
            f"Iniciando exportação - Job ID: {job_id}, Tasks: {task_ids}, "
            f"Tipos: {data_types}"
        )
    
    def log_export_complete(self, job_id, filename, file_size):
        """Log de conclusão da exportação.
        
        Args:
            job_id: ID do job de exportação
            filename: Nome do arquivo gerado
            file_size: Tamanho do arquivo em bytes
        """
        logger = self.get_logger('app.services.excel_service')
        logger.info(
            f"Exportação concluída - Job ID: {job_id}, Arquivo: {filename}, "
            f"Tamanho: {file_size / 1024 / 1024:.2f}MB"
        )
    
    def log_export_error(self, job_id, error, context=None):
        """Log de erro na exportação.
        
        Args:
            job_id: ID do job de exportação
            error: Erro ocorrido
            context: Contexto adicional (opcional)
        """
        logger = self.get_logger('app.services.excel_service')
        context_str = f" - Contexto: {context}" if context else ""
        logger.error(
            f"Erro na exportação - Job ID: {job_id}, Erro: {str(error)}{context_str}",
            exc_info=True
        )
    
    def cleanup_old_logs(self, days_to_keep=30):
        """Limpar logs antigos.
        
        Args:
            days_to_keep: Número de dias para manter os logs
        """
        import time
        from datetime import timedelta
        
        cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)
        
        for log_file in self.logs_dir.rglob('*.log*'):
            try:
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    print(f"Log removido: {log_file}")
            except Exception as e:
                print(f"Erro ao remover log {log_file}: {e}")


# Instância global para facilitar uso
logging_config = LoggingConfig()


def setup_logging(app):
    """Função de conveniência para configurar logs.
    
    Args:
        app: Instância da aplicação Flask
    """
    logging_config.init_app(app)
    return logging_config


def get_logger(name):
    """Função de conveniência para obter logger.
    
    Args:
        name: Nome do logger
        
    Returns:
        logging.Logger: Logger configurado
    """
    return logging_config.get_logger(name)