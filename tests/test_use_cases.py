"""Testes para os use cases da aplicação."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from app.use_cases.create_scraping_task import CreateScrapingTaskUseCase
from app.use_cases.execute_scraping import ExecuteScrapingUseCase
from app.use_cases.export_to_excel import ExportToExcelUseCase
from app.models.scraping_task import ScrapingTask
from app.models.facebook_data import FacebookData
from app.models.export_job import ExportJob


class TestCreateScrapingTaskUseCase:
    """Testes para o use case de criação de tarefas."""
    
    def test_create_task_success(self, db_session):
        """Testar criação bem-sucedida de tarefa."""
        # Criar mocks dos repositórios
        task_repo = Mock()
        task_repo.save = Mock()
        task_repo.find_by_name = Mock(return_value=None)
        
        # Dados de entrada
        task_data = {
            'name': 'Nova Tarefa',
            'url': 'https://facebook.com/test-page',
            'description': 'Descrição da tarefa',
            'max_posts': 50,
            'max_comments': 20,
            'extract_posts': True,
            'extract_comments': True
        }
        
        # Executar use case
        use_case = CreateScrapingTaskUseCase(task_repo)
        result = use_case.execute(task_data)
        
        # Verificar resultado
        assert result['success'] is True
        assert 'task' in result
        assert result['task'].name == 'Nova Tarefa'
        assert result['task'].url == 'https://facebook.com/test-page'
        
        # Verificar que repositório foi chamado
        task_repo.save.assert_called_once()
    
    def test_create_task_duplicate_name(self, db_session):
        """Testar criação de tarefa com nome duplicado."""
        # Mock de tarefa existente
        existing_task = Mock()
        existing_task.name = 'Tarefa Existente'
        
        task_repo = Mock()
        task_repo.find_by_name = Mock(return_value=existing_task)
        
        task_data = {
            'name': 'Tarefa Existente',
            'url': 'https://facebook.com/test'
        }
        
        use_case = CreateScrapingTaskUseCase(task_repo)
        result = use_case.execute(task_data)
        
        # Verificar que falhou
        assert result['success'] is False
        assert 'já existe' in result['message']
        
        # Verificar que save não foi chamado
        task_repo.save.assert_not_called()
    
    def test_create_task_invalid_url(self, db_session):
        """Testar criação de tarefa com URL inválida."""
        task_repo = Mock()
        task_repo.find_by_name = Mock(return_value=None)
        
        task_data = {
            'name': 'Tarefa Teste',
            'url': 'https://google.com'  # URL não é do Facebook
        }
        
        use_case = CreateScrapingTaskUseCase(task_repo)
        result = use_case.execute(task_data)
        
        assert result['success'] is False
        assert 'Facebook' in result['message']
    
    def test_create_task_with_default_config(self, db_session):
        """Testar criação de tarefa com configurações padrão."""
        task_repo = Mock()
        task_repo.save = Mock()
        task_repo.find_by_name = Mock(return_value=None)
        
        # Dados mínimos
        task_data = {
            'name': 'Tarefa Mínima',
            'url': 'https://facebook.com/test'
        }
        
        use_case = CreateScrapingTaskUseCase(task_repo)
        result = use_case.execute(task_data)
        
        assert result['success'] is True
        
        # Verificar configurações padrão
        task = result['task']
        assert task.config['max_posts'] == 50  # Valor padrão
        assert task.config['extract_posts'] is True  # Padrão
        assert task.config['headless'] is True  # Padrão


class TestExecuteScrapingUseCase:
    """Testes para o use case de execução de scraping."""
    
    def test_execute_scraping_success(self, db_session, sample_scraping_task):
        """Testar execução bem-sucedida de scraping."""
        # Mocks dos repositórios
        task_repo = Mock()
        data_repo = Mock()
        
        # Mock do serviço de scraping
        scraping_service = Mock()
        scraping_service.scrape_facebook_page = Mock(return_value=[
            {
                'type': 'post',
                'content': 'Post de teste',
                'author': 'Autor Teste',
                'timestamp': datetime.utcnow(),
                'likes': 10
            }
        ])
        
        # Configurar task como pending
        sample_scraping_task.status = 'pending'
        task_repo.find_by_id = Mock(return_value=sample_scraping_task)
        task_repo.save = Mock()
        data_repo.save_batch = Mock()
        
        # Executar use case
        use_case = ExecuteScrapingUseCase(task_repo, data_repo, scraping_service)
        result = use_case.execute(sample_scraping_task.id)
        
        # Verificar resultado
        assert result['success'] is True
        assert sample_scraping_task.status == 'completed'
        
        # Verificar que serviços foram chamados
        scraping_service.scrape_facebook_page.assert_called_once()
        data_repo.save_batch.assert_called_once()
    
    def test_execute_scraping_task_not_found(self, db_session):
        """Testar execução com tarefa inexistente."""
        task_repo = Mock()
        task_repo.find_by_id = Mock(return_value=None)
        
        data_repo = Mock()
        scraping_service = Mock()
        
        use_case = ExecuteScrapingUseCase(task_repo, data_repo, scraping_service)
        result = use_case.execute(999)
        
        assert result['success'] is False
        assert 'não encontrada' in result['message']
    
    def test_execute_scraping_invalid_status(self, db_session, sample_scraping_task):
        """Testar execução com status inválido."""
        # Configurar task como já em execução
        sample_scraping_task.status = 'running'
        
        task_repo = Mock()
        task_repo.find_by_id = Mock(return_value=sample_scraping_task)
        
        data_repo = Mock()
        scraping_service = Mock()
        
        use_case = ExecuteScrapingUseCase(task_repo, data_repo, scraping_service)
        result = use_case.execute(sample_scraping_task.id)
        
        assert result['success'] is False
        assert 'executada' in result['message']
    
    @patch('app.use_cases.execute_scraping.logging')
    def test_execute_scraping_with_error(self, mock_logging, db_session, sample_scraping_task):
        """Testar execução com erro no scraping."""
        # Configurar mocks
        task_repo = Mock()
        data_repo = Mock()
        
        # Mock do serviço que gera erro
        scraping_service = Mock()
        scraping_service.scrape_facebook_page = Mock(
            side_effect=Exception("Erro de scraping")
        )
        
        sample_scraping_task.status = 'pending'
        task_repo.find_by_id = Mock(return_value=sample_scraping_task)
        task_repo.save = Mock()
        
        # Executar use case
        use_case = ExecuteScrapingUseCase(task_repo, data_repo, scraping_service)
        result = use_case.execute(sample_scraping_task.id)
        
        # Verificar que falhou
        assert result['success'] is False
        assert sample_scraping_task.status == 'failed'
        assert 'Erro de scraping' in result['message']
    
    def test_stop_scraping(self, db_session, sample_scraping_task):
        """Testar parada de scraping em execução."""
        # Configurar task como running
        sample_scraping_task.status = 'running'
        
        task_repo = Mock()
        task_repo.find_by_id = Mock(return_value=sample_scraping_task)
        task_repo.save = Mock()
        
        data_repo = Mock()
        scraping_service = Mock()
        scraping_service.stop_scraping = Mock()
        
        use_case = ExecuteScrapingUseCase(task_repo, data_repo, scraping_service)
        result = use_case.stop_execution(sample_scraping_task.id)
        
        assert result['success'] is True
        assert sample_scraping_task.status == 'stopped'
        scraping_service.stop_scraping.assert_called_once()


class TestExportToExcelUseCase:
    """Testes para o use case de exportação para Excel."""
    
    def test_export_success(self, db_session, sample_scraping_task, sample_facebook_data):
        """Testar exportação bem-sucedida."""
        # Mocks dos repositórios
        task_repo = Mock()
        data_repo = Mock()
        export_repo = Mock()
        
        # Mock do serviço Excel
        excel_service = Mock()
        excel_service.create_excel_file = Mock(return_value={
            'file_path': '/path/to/export.xlsx',
            'file_size': 1024000
        })
        
        # Configurar mocks
        task_repo.find_by_ids = Mock(return_value=[sample_scraping_task])
        data_repo.find_by_task_ids = Mock(return_value=sample_facebook_data)
        export_repo.save = Mock()
        
        # Dados de exportação
        export_data = {
            'task_ids': [sample_scraping_task.id],
            'filename': 'test_export',
            'data_types': ['post', 'comment'],
            'include_summary': True
        }
        
        # Executar use case
        use_case = ExportToExcelUseCase(task_repo, data_repo, export_repo, excel_service)
        result = use_case.execute(export_data)
        
        # Verificar resultado
        assert result['success'] is True
        assert 'job' in result
        
        # Verificar que serviços foram chamados
        excel_service.create_excel_file.assert_called_once()
        export_repo.save.assert_called()
    
    def test_export_no_tasks(self, db_session):
        """Testar exportação sem tarefas selecionadas."""
        task_repo = Mock()
        task_repo.find_by_ids = Mock(return_value=[])
        
        data_repo = Mock()
        export_repo = Mock()
        excel_service = Mock()
        
        export_data = {
            'task_ids': [999],  # ID inexistente
            'filename': 'test_export'
        }
        
        use_case = ExportToExcelUseCase(task_repo, data_repo, export_repo, excel_service)
        result = use_case.execute(export_data)
        
        assert result['success'] is False
        assert 'tarefas' in result['message']
    
    def test_export_no_data(self, db_session, sample_scraping_task):
        """Testar exportação sem dados disponíveis."""
        task_repo = Mock()
        data_repo = Mock()
        export_repo = Mock()
        excel_service = Mock()
        
        # Configurar para retornar tarefa mas sem dados
        task_repo.find_by_ids = Mock(return_value=[sample_scraping_task])
        data_repo.find_by_task_ids = Mock(return_value=[])
        
        export_data = {
            'task_ids': [sample_scraping_task.id],
            'filename': 'empty_export'
        }
        
        use_case = ExportToExcelUseCase(task_repo, data_repo, export_repo, excel_service)
        result = use_case.execute(export_data)
        
        assert result['success'] is False
        assert 'dados' in result['message']
    
    def test_export_with_filters(self, db_session, sample_scraping_task, sample_facebook_data):
        """Testar exportação com filtros de data e tipo."""
        task_repo = Mock()
        data_repo = Mock()
        export_repo = Mock()
        excel_service = Mock()
        
        # Filtrar apenas posts
        filtered_data = [d for d in sample_facebook_data if d.data_type == 'post']
        
        task_repo.find_by_ids = Mock(return_value=[sample_scraping_task])
        data_repo.find_by_task_ids = Mock(return_value=filtered_data)
        export_repo.save = Mock()
        excel_service.create_excel_file = Mock(return_value={
            'file_path': '/path/to/filtered_export.xlsx',
            'file_size': 512000
        })
        
        export_data = {
            'task_ids': [sample_scraping_task.id],
            'filename': 'filtered_export',
            'data_types': ['post'],  # Apenas posts
            'date_from': '2024-01-01',
            'date_to': '2024-12-31'
        }
        
        use_case = ExportToExcelUseCase(task_repo, data_repo, export_repo, excel_service)
        result = use_case.execute(export_data)
        
        assert result['success'] is True
        
        # Verificar que filtros foram aplicados
        call_args = data_repo.find_by_task_ids.call_args
        assert 'data_types' in call_args.kwargs
        assert call_args.kwargs['data_types'] == ['post']
    
    @patch('app.use_cases.export_to_excel.logging')
    def test_export_with_error(self, mock_logging, db_session, sample_scraping_task, sample_facebook_data):
        """Testar exportação com erro no serviço Excel."""
        task_repo = Mock()
        data_repo = Mock()
        export_repo = Mock()
        
        # Mock do serviço que gera erro
        excel_service = Mock()
        excel_service.create_excel_file = Mock(
            side_effect=Exception("Erro na criação do Excel")
        )
        
        task_repo.find_by_ids = Mock(return_value=[sample_scraping_task])
        data_repo.find_by_task_ids = Mock(return_value=sample_facebook_data)
        export_repo.save = Mock()
        
        export_data = {
            'task_ids': [sample_scraping_task.id],
            'filename': 'error_export'
        }
        
        use_case = ExportToExcelUseCase(task_repo, data_repo, export_repo, excel_service)
        result = use_case.execute(export_data)
        
        assert result['success'] is False
        assert 'Erro na criação do Excel' in result['message']
    
    def test_get_export_status(self, db_session, sample_export_job):
        """Testar obtenção de status de exportação."""
        export_repo = Mock()
        export_repo.find_by_id = Mock(return_value=sample_export_job)
        
        task_repo = Mock()
        data_repo = Mock()
        excel_service = Mock()
        
        use_case = ExportToExcelUseCase(task_repo, data_repo, export_repo, excel_service)
        result = use_case.get_export_status(sample_export_job.id)
        
        assert result['success'] is True
        assert result['status'] == sample_export_job.status
        assert 'progress' in result
    
    def test_cleanup_old_exports(self, db_session):
        """Testar limpeza de exportações antigas."""
        export_repo = Mock()
        export_repo.delete_old_exports = Mock(return_value=5)  # 5 exportações removidas
        
        task_repo = Mock()
        data_repo = Mock()
        excel_service = Mock()
        
        use_case = ExportToExcelUseCase(task_repo, data_repo, export_repo, excel_service)
        result = use_case.cleanup_old_exports(days_to_keep=30)
        
        assert result['success'] is True
        assert result['deleted_count'] == 5
        export_repo.delete_old_exports.assert_called_once_with(30)


class TestUseCaseIntegration:
    """Testes de integração entre use cases."""
    
    def test_full_workflow(self, db_session):
        """Testar fluxo completo: criar tarefa -> executar scraping -> exportar."""
        # Mocks dos repositórios
        task_repo = Mock()
        data_repo = Mock()
        export_repo = Mock()
        
        # Mocks dos serviços
        scraping_service = Mock()
        excel_service = Mock()
        
        # 1. Criar tarefa
        task_repo.find_by_name = Mock(return_value=None)
        task_repo.save = Mock()
        
        create_use_case = CreateScrapingTaskUseCase(task_repo)
        task_result = create_use_case.execute({
            'name': 'Workflow Test',
            'url': 'https://facebook.com/test'
        })
        
        assert task_result['success'] is True
        created_task = task_result['task']
        
        # 2. Executar scraping
        created_task.status = 'pending'
        task_repo.find_by_id = Mock(return_value=created_task)
        
        scraping_service.scrape_facebook_page = Mock(return_value=[
            {
                'type': 'post',
                'content': 'Post do workflow',
                'author': 'Autor Workflow'
            }
        ])
        
        execute_use_case = ExecuteScrapingUseCase(task_repo, data_repo, scraping_service)
        scraping_result = execute_use_case.execute(created_task.id)
        
        assert scraping_result['success'] is True
        assert created_task.status == 'completed'
        
        # 3. Exportar dados
        mock_data = [Mock(data_type='post', content='Post do workflow')]
        
        task_repo.find_by_ids = Mock(return_value=[created_task])
        data_repo.find_by_task_ids = Mock(return_value=mock_data)
        excel_service.create_excel_file = Mock(return_value={
            'file_path': '/path/to/workflow_export.xlsx',
            'file_size': 1024
        })
        
        export_use_case = ExportToExcelUseCase(task_repo, data_repo, export_repo, excel_service)
        export_result = export_use_case.execute({
            'task_ids': [created_task.id],
            'filename': 'workflow_export'
        })
        
        assert export_result['success'] is True
        
        # Verificar que todos os serviços foram chamados na ordem correta
        task_repo.save.assert_called()
        scraping_service.scrape_facebook_page.assert_called_once()
        excel_service.create_excel_file.assert_called_once()