"""Configuração e inicialização do banco de dados SQLite."""

import os
import sqlite3
from pathlib import Path
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event, text
from sqlalchemy.engine import Engine

# Instância global do SQLAlchemy
db = SQLAlchemy()


class DatabaseConfig:
    """Configuração do banco de dados."""
    
    def __init__(self, app=None):
        """Inicializar configuração do banco.
        
        Args:
            app: Instância da aplicação Flask (opcional)
        """
        self.app = app
        self.db_path = Path('data')
        self._ensure_data_directory()
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Inicializar banco para aplicação Flask.
        
        Args:
            app: Instância da aplicação Flask
        """
        self.app = app
        
        # Configurar URI do banco
        database_url = self._get_database_url()
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_timeout': 20,
            'pool_recycle': -1,
            'pool_pre_ping': True
        }
        
        # Inicializar SQLAlchemy
        db.init_app(app)
        
        # Configurar eventos do SQLite
        self._setup_sqlite_events()
        
        # Registrar comandos CLI
        self._register_cli_commands(app)
    
    def _ensure_data_directory(self):
        """Garantir que o diretório de dados existe."""
        self.db_path.mkdir(exist_ok=True)
        
        # Criar subdiretórios para backups e exports
        (self.db_path / 'backups').mkdir(exist_ok=True)
        (self.db_path / 'exports').mkdir(exist_ok=True)
    
    def _get_database_url(self):
        """Obter URL do banco de dados.
        
        Returns:
            str: URL de conexão do banco
        """
        # Usar variável de ambiente se disponível
        database_url = os.getenv('DATABASE_URL')
        
        if database_url:
            return database_url
        
        # Usar SQLite local por padrão
        db_file = self.db_path / 'facebook_scraper.db'
        return f'sqlite:///{db_file.absolute()}'
    
    def _setup_sqlite_events(self):
        """Configurar eventos específicos do SQLite."""
        
        @event.listens_for(Engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Configurar pragmas do SQLite para melhor performance.
            
            Args:
                dbapi_connection: Conexão DBAPI
                connection_record: Registro da conexão
            """
            if 'sqlite' in str(dbapi_connection):
                cursor = dbapi_connection.cursor()
                
                # Habilitar foreign keys
                cursor.execute("PRAGMA foreign_keys=ON")
                
                # Configurar journal mode para WAL (melhor concorrência)
                cursor.execute("PRAGMA journal_mode=WAL")
                
                # Configurar synchronous para NORMAL (balance performance/segurança)
                cursor.execute("PRAGMA synchronous=NORMAL")
                
                # Configurar cache size (em páginas, negativo = KB)
                cursor.execute("PRAGMA cache_size=-64000")  # 64MB
                
                # Configurar timeout para locks
                cursor.execute("PRAGMA busy_timeout=30000")  # 30 segundos
                
                # Habilitar otimizações de query
                cursor.execute("PRAGMA optimize")
                
                cursor.close()
    
    def _register_cli_commands(self, app):
        """Registrar comandos CLI para gerenciamento do banco.
        
        Args:
            app: Instância da aplicação Flask
        """
        
        @app.cli.command()
        def init_db():
            """Inicializar banco de dados."""
            self.create_tables()
            print("Banco de dados inicializado com sucesso!")
        
        @app.cli.command()
        def reset_db():
            """Resetar banco de dados (CUIDADO: apaga todos os dados)."""
            import click
            if click.confirm('Tem certeza que deseja resetar o banco? Todos os dados serão perdidos!'):
                self.reset_database()
                print("Banco de dados resetado!")
        
        @app.cli.command()
        def backup_db():
            """Criar backup do banco de dados."""
            backup_file = self.create_backup()
            print(f"Backup criado: {backup_file}")
        
        @app.cli.command()
        def optimize_db():
            """Otimizar banco de dados."""
            self.optimize_database()
            print("Banco de dados otimizado!")
        
        @app.cli.command()
        def db_info():
            """Mostrar informações do banco de dados."""
            info = self.get_database_info()
            for key, value in info.items():
                print(f"{key}: {value}")
    
    def create_tables(self):
        """Criar todas as tabelas do banco."""
        with self.app.app_context():
            # Importar modelos para garantir que estão registrados
            from app.models import ScrapingTask, FacebookData, ExportJob
            
            # Criar tabelas
            db.create_all()
            
            # Criar índices personalizados se necessário
            self._create_custom_indexes()
    
    def _create_custom_indexes(self):
        """Criar índices personalizados para melhor performance."""
        try:
            # Índices para FacebookData
            db.engine.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_facebook_data_task_type "
                "ON facebook_data(task_id, data_type)"
            ))
            
            db.engine.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_facebook_data_timestamp "
                "ON facebook_data(timestamp)"
            ))
            
            # Índices para ScrapingTask
            db.engine.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_scraping_task_status "
                "ON scraping_task(status)"
            ))
            
            db.engine.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_scraping_task_created "
                "ON scraping_task(created_at)"
            ))
            
            # Índices para ExportJob
            db.engine.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_export_job_status "
                "ON export_job(status)"
            ))
            
        except Exception as e:
            print(f"Aviso: Erro ao criar índices personalizados: {e}")
    
    def reset_database(self):
        """Resetar banco de dados (apagar e recriar)."""
        with self.app.app_context():
            db.drop_all()
            self.create_tables()
    
    def create_backup(self):
        """Criar backup do banco de dados.
        
        Returns:
            Path: Caminho do arquivo de backup
        """
        from datetime import datetime
        import shutil
        
        # Nome do arquivo de backup com timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'facebook_scraper_backup_{timestamp}.db'
        backup_path = self.db_path / 'backups' / backup_filename
        
        # Caminho do banco atual
        current_db = self.db_path / 'facebook_scraper.db'
        
        if current_db.exists():
            # Criar backup usando SQLite backup API
            with sqlite3.connect(str(current_db)) as source:
                with sqlite3.connect(str(backup_path)) as backup:
                    source.backup(backup)
        
        return backup_path
    
    def restore_backup(self, backup_path):
        """Restaurar banco de dados a partir de backup.
        
        Args:
            backup_path: Caminho do arquivo de backup
        """
        import shutil
        
        backup_file = Path(backup_path)
        if not backup_file.exists():
            raise FileNotFoundError(f"Arquivo de backup não encontrado: {backup_path}")
        
        # Fazer backup do banco atual antes de restaurar
        current_backup = self.create_backup()
        print(f"Backup atual salvo em: {current_backup}")
        
        # Restaurar backup
        current_db = self.db_path / 'facebook_scraper.db'
        shutil.copy2(backup_file, current_db)
        
        print(f"Banco restaurado a partir de: {backup_path}")
    
    def optimize_database(self):
        """Otimizar banco de dados."""
        with self.app.app_context():
            try:
                # Executar VACUUM para compactar banco
                db.engine.execute(text("VACUUM"))
                
                # Executar ANALYZE para atualizar estatísticas
                db.engine.execute(text("ANALYZE"))
                
                # Executar PRAGMA optimize
                db.engine.execute(text("PRAGMA optimize"))
                
            except Exception as e:
                print(f"Erro ao otimizar banco: {e}")
    
    def get_database_info(self):
        """Obter informações do banco de dados.
        
        Returns:
            dict: Informações do banco
        """
        info = {}
        
        try:
            with self.app.app_context():
                # Tamanho do arquivo
                db_file = self.db_path / 'facebook_scraper.db'
                if db_file.exists():
                    size_mb = db_file.stat().st_size / 1024 / 1024
                    info['Tamanho do arquivo'] = f"{size_mb:.2f} MB"
                
                # Número de tabelas
                result = db.engine.execute(text(
                    "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
                ))
                info['Número de tabelas'] = result.scalar()
                
                # Contagem de registros por tabela
                from app.models import ScrapingTask, FacebookData, ExportJob
                
                info['Tarefas de scraping'] = ScrapingTask.query.count()
                info['Dados do Facebook'] = FacebookData.query.count()
                info['Jobs de exportação'] = ExportJob.query.count()
                
                # Versão do SQLite
                result = db.engine.execute(text("SELECT sqlite_version()"))
                info['Versão SQLite'] = result.scalar()
                
        except Exception as e:
            info['Erro'] = str(e)
        
        return info
    
    def cleanup_old_data(self, days_to_keep=90):
        """Limpar dados antigos do banco.
        
        Args:
            days_to_keep: Número de dias para manter os dados
        """
        from datetime import datetime, timedelta
        from app.models import ScrapingTask, FacebookData, ExportJob
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        with self.app.app_context():
            try:
                # Remover tarefas antigas concluídas
                old_tasks = ScrapingTask.query.filter(
                    ScrapingTask.completed_at < cutoff_date,
                    ScrapingTask.status == 'completed'
                ).all()
                
                for task in old_tasks:
                    # Remover dados associados
                    FacebookData.query.filter_by(task_id=task.id).delete()
                    db.session.delete(task)
                
                # Remover jobs de exportação antigos
                ExportJob.query.filter(
                    ExportJob.created_at < cutoff_date,
                    ExportJob.status.in_(['completed', 'failed'])
                ).delete()
                
                db.session.commit()
                print(f"Dados anteriores a {cutoff_date.date()} foram removidos")
                
            except Exception as e:
                db.session.rollback()
                print(f"Erro ao limpar dados antigos: {e}")


# Instância global para facilitar uso
database_config = DatabaseConfig()


def setup_database(app):
    """Função de conveniência para configurar banco.
    
    Args:
        app: Instância da aplicação Flask
        
    Returns:
        DatabaseConfig: Configuração do banco
    """
    database_config.init_app(app)
    return database_config


def get_db():
    """Função de conveniência para obter instância do banco.
    
    Returns:
        SQLAlchemy: Instância do SQLAlchemy
    """
    return db