"""Configuração dos testes pytest."""

import os
import pytest
import tempfile
from pathlib import Path

# Configurar variáveis de ambiente para testes
os.environ['FLASK_ENV'] = 'testing'
os.environ['TESTING'] = 'True'

from app import create_app
from app.config.database import db


@pytest.fixture(scope='session')
def app():
    """Criar aplicação Flask para testes.
    
    Returns:
        Flask: Instância da aplicação configurada para testes
    """
    # Criar diretório temporário para banco de testes
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    
    # Configurações específicas para testes
    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key',
        'LOG_LEVEL': 'ERROR'  # Reduzir logs durante testes
    }
    
    # Criar aplicação
    app = create_app(test_config)
    
    # Configurar contexto da aplicação
    with app.app_context():
        # Criar tabelas
        db.create_all()
        
        yield app
        
        # Limpeza
        db.drop_all()
    
    # Fechar e remover arquivo temporário
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Cliente de teste Flask.
    
    Args:
        app: Aplicação Flask
        
    Returns:
        FlaskClient: Cliente para fazer requisições de teste
    """
    return app.test_client()


@pytest.fixture
def runner(app):
    """Runner para comandos CLI.
    
    Args:
        app: Aplicação Flask
        
    Returns:
        FlaskCliRunner: Runner para testes de CLI
    """
    return app.test_cli_runner()


@pytest.fixture
def db_session(app):
    """Sessão de banco de dados para testes.
    
    Args:
        app: Aplicação Flask
        
    Yields:
        Session: Sessão do banco de dados
    """
    with app.app_context():
        connection = db.engine.connect()
        transaction = connection.begin()
        
        # Configurar sessão para usar a transação
        session = db.create_scoped_session(
            options={"bind": connection, "binds": {}}
        )
        db.session = session
        
        yield session
        
        # Rollback da transação
        transaction.rollback()
        connection.close()
        session.remove()


@pytest.fixture
def sample_scraping_task(db_session):
    """Criar tarefa de scraping de exemplo.
    
    Args:
        db_session: Sessão do banco de dados
        
    Returns:
        ScrapingTask: Tarefa de exemplo
    """
    from app.models.scraping_task import ScrapingTask
    
    task = ScrapingTask(
        name="Teste Scraping",
        url="https://facebook.com/test-page",
        description="Tarefa de teste",
        config={
            "max_posts": 10,
            "max_comments": 5,
            "scroll_delay": 2000,
            "extract_posts": True,
            "extract_comments": True,
            "headless": True
        },
        status="pending"
    )
    
    db_session.add(task)
    db_session.commit()
    
    return task


@pytest.fixture
def sample_facebook_data(db_session, sample_scraping_task):
    """Criar dados do Facebook de exemplo.
    
    Args:
        db_session: Sessão do banco de dados
        sample_scraping_task: Tarefa de scraping de exemplo
        
    Returns:
        list: Lista de dados do Facebook
    """
    from app.models.facebook_data import FacebookData
    from datetime import datetime
    
    data_items = [
        FacebookData(
            task_id=sample_scraping_task.id,
            data_type="post",
            content="Este é um post de teste",
            author="Usuário Teste",
            timestamp=datetime.utcnow(),
            likes=10,
            shares=2,
            comments_count=3
        ),
        FacebookData(
            task_id=sample_scraping_task.id,
            data_type="comment",
            content="Este é um comentário de teste",
            author="Comentarista Teste",
            timestamp=datetime.utcnow(),
            likes=1
        ),
        FacebookData(
            task_id=sample_scraping_task.id,
            data_type="profile",
            content="Informações do perfil de teste",
            author="Perfil Teste",
            timestamp=datetime.utcnow()
        )
    ]
    
    for item in data_items:
        db_session.add(item)
    
    db_session.commit()
    
    return data_items


@pytest.fixture
def sample_export_job(db_session, sample_scraping_task):
    """Criar job de exportação de exemplo.
    
    Args:
        db_session: Sessão do banco de dados
        sample_scraping_task: Tarefa de scraping de exemplo
        
    Returns:
        ExportJob: Job de exportação de exemplo
    """
    from app.models.export_job import ExportJob
    
    job = ExportJob(
        task_ids=[sample_scraping_task.id],
        filename="test_export.xlsx",
        options={
            "data_types": ["post", "comment"],
            "include_summary": True,
            "sheet_organization": "by_type"
        },
        status="pending"
    )
    
    db_session.add(job)
    db_session.commit()
    
    return job


@pytest.fixture
def mock_selenium_driver():
    """Mock do driver Selenium para testes.
    
    Returns:
        Mock: Driver Selenium mockado
    """
    from unittest.mock import Mock, MagicMock
    
    # Criar mock do driver
    driver = Mock()
    
    # Configurar métodos básicos
    driver.get = Mock()
    driver.quit = Mock()
    driver.close = Mock()
    driver.find_element = Mock()
    driver.find_elements = Mock(return_value=[])
    driver.execute_script = Mock()
    driver.page_source = "<html><body>Mock page</body></html>"
    driver.current_url = "https://facebook.com/test"
    
    # Mock de elementos
    mock_element = Mock()
    mock_element.text = "Mock element text"
    mock_element.get_attribute = Mock(return_value="mock-attribute")
    mock_element.click = Mock()
    
    driver.find_element.return_value = mock_element
    driver.find_elements.return_value = [mock_element]
    
    return driver


@pytest.fixture
def temp_export_dir():
    """Diretório temporário para arquivos de exportação.
    
    Yields:
        Path: Caminho do diretório temporário
    """
    import tempfile
    import shutil
    
    temp_dir = Path(tempfile.mkdtemp())
    
    yield temp_dir
    
    # Limpeza
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestHelpers:
    """Classe com métodos auxiliares para testes."""
    
    @staticmethod
    def assert_json_response(response, expected_status=200):
        """Verificar resposta JSON.
        
        Args:
            response: Resposta da requisição
            expected_status: Status HTTP esperado
            
        Returns:
            dict: Dados JSON da resposta
        """
        assert response.status_code == expected_status
        assert response.content_type == 'application/json'
        return response.get_json()
    
    @staticmethod
    def assert_html_response(response, expected_status=200):
        """Verificar resposta HTML.
        
        Args:
            response: Resposta da requisição
            expected_status: Status HTTP esperado
            
        Returns:
            str: Conteúdo HTML da resposta
        """
        assert response.status_code == expected_status
        assert 'text/html' in response.content_type
        return response.get_data(as_text=True)
    
    @staticmethod
    def create_test_task_data():
        """Criar dados de teste para tarefa de scraping.
        
        Returns:
            dict: Dados da tarefa
        """
        return {
            'name': 'Tarefa de Teste',
            'url': 'https://facebook.com/test-page',
            'description': 'Descrição de teste',
            'max_posts': 20,
            'max_comments': 10,
            'scroll_delay': 2000,
            'extract_posts': True,
            'extract_comments': True,
            'extract_likes': False,
            'extract_shares': False,
            'extract_profile_info': False,
            'extract_media': False,
            'headless': True,
            'timeout': 30,
            'retry_attempts': 3
        }
    
    @staticmethod
    def create_test_export_data():
        """Criar dados de teste para exportação.
        
        Returns:
            dict: Dados da exportação
        """
        return {
            'filename': 'test_export',
            'data_types': ['post', 'comment'],
            'sheet_organization': 'by_type',
            'include_summary': True,
            'include_charts': False
        }


# Disponibilizar helpers globalmente
@pytest.fixture
def helpers():
    """Helpers para testes.
    
    Returns:
        TestHelpers: Classe com métodos auxiliares
    """
    return Test