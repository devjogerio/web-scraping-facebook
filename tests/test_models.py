"""Testes para os modelos de dados."""

import pytest
from datetime import datetime, timedelta
from app.models.scraping_task import ScrapingTask
from app.models.facebook_data import FacebookData
from app.models.export_job import ExportJob


class TestScrapingTask:
    """Testes para o modelo ScrapingTask."""
    
    def test_create_scraping_task(self, db_session):
        """Testar criação de tarefa de scraping."""
        task = ScrapingTask(
            name="Teste Task",
            url="https://facebook.com/test",
            description="Descrição de teste",
            config={"max_posts": 10},
            status="pending"
        )
        
        db_session.add(task)
        db_session.commit()
        
        assert task.id is not None
        assert task.name == "Teste Task"
        assert task.url == "https://facebook.com/test"
        assert task.status == "pending"
        assert task.config["max_posts"] == 10
        assert task.created_at is not None
    
    def test_scraping_task_validation(self, db_session):
        """Testar validações do modelo ScrapingTask."""
        # Teste com dados inválidos
        with pytest.raises(Exception):
            task = ScrapingTask(
                name="",  # Nome vazio deve falhar
                url="invalid-url",  # URL inválida
                status="invalid-status"  # Status inválido
            )
            db_session.add(task)
            db_session.commit()
    
    def test_scraping_task_relationships(self, db_session, sample_scraping_task, sample_facebook_data):
        """Testar relacionamentos do ScrapingTask."""
        # Verificar relacionamento com FacebookData
        assert len(sample_scraping_task.facebook_data) == 3
        assert all(data.task_id == sample_scraping_task.id for data in sample_scraping_task.facebook_data)
    
    def test_scraping_task_status_transitions(self, db_session):
        """Testar transições de status da tarefa."""
        task = ScrapingTask(
            name="Status Test",
            url="https://facebook.com/test",
            status="pending"
        )
        
        db_session.add(task)
        db_session.commit()
        
        # Testar transição para running
        task.status = "running"
        task.started_at = datetime.utcnow()
        db_session.commit()
        
        assert task.status == "running"
        assert task.started_at is not None
        
        # Testar transição para completed
        task.status = "completed"
        task.completed_at = datetime.utcnow()
        task.progress = 100
        db_session.commit()
        
        assert task.status == "completed"
        assert task.completed_at is not None
        assert task.progress == 100
    
    def test_scraping_task_config_serialization(self, db_session):
        """Testar serialização da configuração JSON."""
        config = {
            "max_posts": 50,
            "max_comments": 20,
            "extract_posts": True,
            "extract_comments": False,
            "headless": True,
            "scroll_delay": 2000
        }
        
        task = ScrapingTask(
            name="Config Test",
            url="https://facebook.com/test",
            config=config
        )
        
        db_session.add(task)
        db_session.commit()
        
        # Recuperar da base e verificar
        retrieved_task = ScrapingTask.query.get(task.id)
        assert retrieved_task.config == config
        assert retrieved_task.config["max_posts"] == 50
        assert retrieved_task.config["extract_posts"] is True


class TestFacebookData:
    """Testes para o modelo FacebookData."""
    
    def test_create_facebook_data(self, db_session, sample_scraping_task):
        """Testar criação de dados do Facebook."""
        data = FacebookData(
            task_id=sample_scraping_task.id,
            data_type="post",
            content="Conteúdo de teste",
            author="Autor Teste",
            timestamp=datetime.utcnow(),
            likes=15,
            shares=3,
            comments_count=5
        )
        
        db_session.add(data)
        db_session.commit()
        
        assert data.id is not None
        assert data.task_id == sample_scraping_task.id
        assert data.data_type == "post"
        assert data.content == "Conteúdo de teste"
        assert data.likes == 15
        assert data.created_at is not None
    
    def test_facebook_data_types(self, db_session, sample_scraping_task):
        """Testar diferentes tipos de dados do Facebook."""
        data_types = ["post", "comment", "profile", "like", "share"]
        
        for data_type in data_types:
            data = FacebookData(
                task_id=sample_scraping_task.id,
                data_type=data_type,
                content=f"Conteúdo {data_type}",
                author="Autor"
            )
            db_session.add(data)
        
        db_session.commit()
        
        # Verificar que todos os tipos foram salvos
        for data_type in data_types:
            found = FacebookData.query.filter_by(
                task_id=sample_scraping_task.id,
                data_type=data_type
            ).first()
            assert found is not None
            assert found.data_type == data_type
    
    def test_facebook_data_metadata(self, db_session, sample_scraping_task):
        """Testar metadados dos dados do Facebook."""
        metadata = {
            "post_id": "123456789",
            "url": "https://facebook.com/post/123",
            "media_urls": ["https://example.com/image1.jpg"],
            "hashtags": ["#teste", "#facebook"]
        }
        
        data = FacebookData(
            task_id=sample_scraping_task.id,
            data_type="post",
            content="Post com metadados",
            metadata=metadata
        )
        
        db_session.add(data)
        db_session.commit()
        
        # Recuperar e verificar metadados
        retrieved = FacebookData.query.get(data.id)
        assert retrieved.metadata == metadata
        assert retrieved.metadata["post_id"] == "123456789"
        assert len(retrieved.metadata["hashtags"]) == 2
    
    def test_facebook_data_relationship(self, db_session, sample_facebook_data):
        """Testar relacionamento com ScrapingTask."""
        for data in sample_facebook_data:
            assert data.task is not None
            assert data.task.id == data.task_id


class TestExportJob:
    """Testes para o modelo ExportJob."""
    
    def test_create_export_job(self, db_session, sample_scraping_task):
        """Testar criação de job de exportação."""
        job = ExportJob(
            task_ids=[sample_scraping_task.id],
            filename="test_export.xlsx",
            options={
                "data_types": ["post", "comment"],
                "include_summary": True
            },
            status="pending"
        )
        
        db_session.add(job)
        db_session.commit()
        
        assert job.id is not None
        assert job.task_ids == [sample_scraping_task.id]
        assert job.filename == "test_export.xlsx"
        assert job.status == "pending"
        assert job.created_at is not None
    
    def test_export_job_options_serialization(self, db_session, sample_scraping_task):
        """Testar serialização das opções de exportação."""
        options = {
            "data_types": ["post", "comment", "profile"],
            "sheet_organization": "by_type",
            "include_summary": True,
            "include_charts": False,
            "date_from": "2024-01-01",
            "date_to": "2024-12-31"
        }
        
        job = ExportJob(
            task_ids=[sample_scraping_task.id],
            filename="options_test.xlsx",
            options=options
        )
        
        db_session.add(job)
        db_session.commit()
        
        # Recuperar e verificar
        retrieved = ExportJob.query.get(job.id)
        assert retrieved.options == options
        assert retrieved.options["sheet_organization"] == "by_type"
        assert len(retrieved.options["data_types"]) == 3
    
    def test_export_job_status_transitions(self, db_session, sample_scraping_task):
        """Testar transições de status do job de exportação."""
        job = ExportJob(
            task_ids=[sample_scraping_task.id],
            filename="status_test.xlsx",
            status="pending"
        )
        
        db_session.add(job)
        db_session.commit()
        
        # Transição para processing
        job.status = "processing"
        job.started_at = datetime.utcnow()
        job.progress = 25
        db_session.commit()
        
        assert job.status == "processing"
        assert job.started_at is not None
        assert job.progress == 25
        
        # Transição para completed
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        job.progress = 100
        job.file_path = "/path/to/export.xlsx"
        job.file_size = 1024000
        db_session.commit()
        
        assert job.status == "completed"
        assert job.completed_at is not None
        assert job.progress == 100
        assert job.file_path is not None
        assert job.file_size == 1024000
    
    def test_export_job_multiple_tasks(self, db_session):
        """Testar job de exportação com múltiplas tarefas."""
        # Criar múltiplas tarefas
        tasks = []
        for i in range(3):
            task = ScrapingTask(
                name=f"Task {i+1}",
                url=f"https://facebook.com/test{i+1}",
                status="completed"
            )
            db_session.add(task)
            tasks.append(task)
        
        db_session.commit()
        
        # Criar job com múltiplas tarefas
        task_ids = [task.id for task in tasks]
        job = ExportJob(
            task_ids=task_ids,
            filename="multi_task_export.xlsx",
            options={"data_types": ["post"]}
        )
        
        db_session.add(job)
        db_session.commit()
        
        assert len(job.task_ids) == 3
        assert all(task_id in job.task_ids for task_id in task_ids)
    
    def test_export_job_error_handling(self, db_session, sample_scraping_task):
        """Testar tratamento de erros no job de exportação."""
        job = ExportJob(
            task_ids=[sample_scraping_task.id],
            filename="error_test.xlsx",
            status="processing"
        )
        
        db_session.add(job)
        db_session.commit()
        
        # Simular erro
        job.status = "failed"
        job.error_message = "Erro de teste na exportação"
        job.completed_at = datetime.utcnow()
        db_session.commit()
        
        assert job.status == "failed"
        assert job.error_message == "Erro de teste na exportação"
        assert job.completed_at is not None


class TestModelIntegration:
    """Testes de integração entre modelos."""
    
    def test_cascade_delete_scraping_task(self, db_session, sample_scraping_task, sample_facebook_data):
        """Testar exclusão em cascata da tarefa de scraping."""
        task_id = sample_scraping_task.id
        
        # Verificar que existem dados associados
        data_count = FacebookData.query.filter_by(task_id=task_id).count()
        assert data_count == 3
        
        # Excluir tarefa
        db_session.delete(sample_scraping_task)
        db_session.commit()
        
        # Verificar que dados associados foram removidos
        remaining_data = FacebookData.query.filter_by(task_id=task_id).count()
        assert remaining_data == 0
    
    def test_data_consistency(self, db_session):
        """Testar consistência dos dados entre modelos."""
        # Criar tarefa
        task = ScrapingTask(
            name="Consistency Test",
            url="https://facebook.com/test",
            status="completed",
            items_processed=10,
            items_extracted=8
        )
        db_session.add(task)
        db_session.commit()
        
        # Criar dados do Facebook
        for i in range(8):
            data = FacebookData(
                task_id=task.id,
                data_type="post" if i % 2 == 0 else "comment",
                content=f"Conteúdo {i+1}",
                author=f"Autor {i+1}"
            )
            db_session.add(data)
        
        db_session.commit()
        
        # Verificar consistência
        actual_data_count = FacebookData.query.filter_by(task_id=task.id).count()
        assert actual_data_count == task.items_extracted
        
        # Verificar tipos de dados
        post_count = FacebookData.query.filter_by(task_id=task.id, data_type="post").count()
        comment_count = FacebookData.query.filter_by(task_id=task.id, data_type="comment").count()
        
        assert post_count == 4
        assert comment_count == 4
        assert post_count + comment_count == task.items_extracted
    
    def test_query_performance(self, db_session):
        """Testar performance de consultas básicas."""
        import time
        
        # Criar dados de teste em volume
        task = ScrapingTask(
            name="Performance Test",
            url="https://facebook.com/test",
            status="completed"
        )
        db_session.add(task)
        db_session.commit()
        
        # Criar muitos dados
        start_time = time.time()
        for i in range(100):
            data = FacebookData(
                task_id=task.id,
                data_type="post",
                content=f"Post {i+1}",
                author=f"Autor {i+1}",
                likes=i,
                timestamp=datetime.utcnow() - timedelta(days=i)
            )
            db_session.add(data)
        
        db_session.commit()
        creation_time = time.time() - start_time
        
        # Testar consultas
        start_time = time.time()
        
        # Consulta simples
        count = FacebookData.query.filter_by(task_id=task.id).count()
        assert count == 100
        
        # Consulta com filtro
        recent_posts = FacebookData.query.filter(
            FacebookData.task_id == task.id,
            FacebookData.likes > 50
        ).count()
        assert recent_posts > 0
        
        # Consulta com ordenação
        top_posts = FacebookData.query.filter_by(task_id=task.id).order_by(
            FacebookData.likes.desc()
        ).limit(10).all()
        assert len(top_posts) == 10
        assert top_posts[0].likes >= top_posts[-1].likes
        
        query_time = time.time() - start_time
        
        # Verificar que as operações são razoavelmente rápidas
        assert creation_time < 5.0  # Criação deve ser < 5s
        assert query_time < 1.0     # Consultas devem ser < 1s