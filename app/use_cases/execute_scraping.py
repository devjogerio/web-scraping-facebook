"""Use case para executar scraping.

Este módulo implementa a lógica de negócio para execução
de tarefas de scraping do Facebook.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.models.scraping_task import ScrapingTask
from app.models.facebook_data import FacebookData
from app.repositories.scraping_task_repository import ScrapingTaskRepository
from app.repositories.facebook_data_repository import FacebookDataRepository


class ExecuteScrapingUseCase:
    """Use case para executar scraping.
    
    Implementa a lógica de negócio para execução de tarefas
    de scraping, incluindo validação, controle de estado e persistência.
    """
    
    def __init__(self, 
                 task_repository: ScrapingTaskRepository,
                 data_repository: FacebookDataRepository,
                 scraping_service):
        """Inicializar use case.
        
        Args:
            task_repository: Repositório de tarefas
            data_repository: Repositório de dados
            scraping_service: Serviço de scraping
        """
        self.task_repository = task_repository
        self.data_repository = data_repository
        self.scraping_service = scraping_service
        self.logger = logging.getLogger(__name__)
    
    def execute(self, task_id: str) -> Dict[str, Any]:
        """Executar tarefa de scraping.
        
        Args:
            task_id: ID da tarefa a ser executada
            
        Returns:
            Resultado da execução com estatísticas
            
        Raises:
            ValueError: Se a tarefa não existe ou não pode ser executada
            RuntimeError: Se ocorre erro durante a execução
        """
        # Buscar tarefa
        task = self.task_repository.get_by_id(task_id)
        if not task:
            raise ValueError(f"Tarefa {task_id} não encontrada")
        
        # Validar se pode executar
        self._validate_task_execution(task)
        
        try:
            # Marcar como iniciada
            task.start_execution()
            self.task_repository.update(task)
            
            self.logger.info(f"Iniciando scraping da tarefa {task_id}: {task.name}")
            
            # Executar scraping
            result = self._perform_scraping(task)
            
            # Marcar como concluída
            task.complete_execution()
            self.task_repository.update(task)
            
            self.logger.info(f"Scraping concluído para tarefa {task_id}. "
                           f"Itens processados: {task.items_processed}")
            
            return {
                'success': True,
                'task_id': task_id,
                'items_processed': task.items_processed,
                'duration': task.get_duration(),
                'data_extracted': result
            }
            
        except Exception as e:
            # Marcar como falhada
            error_message = str(e)
            task.fail_execution(error_message)
            self.task_repository.update(task)
            
            self.logger.error(f"Erro no scraping da tarefa {task_id}: {error_message}")
            
            return {
                'success': False,
                'task_id': task_id,
                'error': error_message,
                'items_processed': task.items_processed
            }
    
    def _validate_task_execution(self, task: ScrapingTask) -> None:
        """Validar se a tarefa pode ser executada.
        
        Args:
            task: Tarefa a ser validada
            
        Raises:
            ValueError: Se a tarefa não pode ser executada
        """
        if task.is_active():
            raise ValueError("Tarefa já está em execução")
        
        if task.is_completed():
            raise ValueError("Tarefa já foi concluída")
        
        # Verificar se há outras tarefas executando para a mesma URL
        active_tasks = self.task_repository.get_active_tasks()
        for active_task in active_tasks:
            if active_task.url == task.url and active_task.id != task.id:
                raise ValueError("Já existe uma tarefa executando para esta URL")
    
    def _perform_scraping(self, task: ScrapingTask) -> Dict[str, Any]:
        """Executar o processo de scraping.
        
        Args:
            task: Tarefa de scraping
            
        Returns:
            Dados extraídos organizados por tipo
        """
        config = task.get_config()
        data_types = config.get('data_types', ['post', 'comment'])
        max_items = config.get('max_items', 100)
        
        extracted_data = {
            'posts': [],
            'comments': [],
            'profiles': [],
            'likes': [],
            'shares': []
        }
        
        total_extracted = 0
        
        # Extrair cada tipo de dado solicitado
        for data_type in data_types:
            try:
                self.logger.info(f"Extraindo {data_type} da URL: {task.url}")
                
                # Calcular limite por tipo
                type_limit = max_items // len(data_types)
                if data_type == data_types[-1]:  # Último tipo pega o resto
                    type_limit = max_items - total_extracted
                
                # Executar scraping específico
                type_data = self._extract_data_type(task, data_type, type_limit)
                
                # Salvar dados extraídos
                saved_count = self._save_extracted_data(task.id, data_type, type_data)
                
                extracted_data[f"{data_type}s"] = type_data
                total_extracted += saved_count
                
                # Atualizar contador na tarefa
                task.increment_processed_items(saved_count)
                self.task_repository.update(task)
                
                self.logger.info(f"Extraídos {saved_count} itens do tipo {data_type}")
                
                # Verificar se atingiu o limite
                if total_extracted >= max_items:
                    break
                    
            except Exception as e:
                self.logger.warning(f"Erro ao extrair {data_type}: {str(e)}")
                continue
        
        return extracted_data
    
    def _extract_data_type(self, task: ScrapingTask, data_type: str, limit: int) -> List[Dict[str, Any]]:
        """Extrair dados de um tipo específico.
        
        Args:
            task: Tarefa de scraping
            data_type: Tipo de dado a extrair
            limit: Limite de itens
            
        Returns:
            Lista de dados extraídos
        """
        config = task.get_config()
        
        # Delegar para o serviço de scraping específico
        if data_type == 'post':
            return self.scraping_service.extract_posts(task.url, limit, config)
        elif data_type == 'comment':
            return self.scraping_service.extract_comments(task.url, limit, config)
        elif data_type == 'profile':
            return self.scraping_service.extract_profile_info(task.url, config)
        elif data_type == 'like':
            return self.scraping_service.extract_likes(task.url, limit, config)
        elif data_type == 'share':
            return self.scraping_service.extract_shares(task.url, limit, config)
        else:
            return []
    
    def _save_extracted_data(self, task_id: str, data_type: str, 
                           data_list: List[Dict[str, Any]]) -> int:
        """Salvar dados extraídos no banco.
        
        Args:
            task_id: ID da tarefa
            data_type: Tipo de dado
            data_list: Lista de dados extraídos
            
        Returns:
            Número de itens salvos
        """
        saved_count = 0
        
        for item_data in data_list:
            try:
                # Extrair conteúdo principal
                content = item_data.get('content', '')
                source_url = item_data.get('source_url', '')
                
                # Preparar metadados
                metadata = {
                    'author': item_data.get('author'),
                    'timestamp': item_data.get('timestamp'),
                    'likes_count': item_data.get('likes_count', 0),
                    'comments_count': item_data.get('comments_count', 0),
                    'shares_count': item_data.get('shares_count', 0),
                    'reactions': item_data.get('reactions', {}),
                    'links': item_data.get('links', []),
                    'images': item_data.get('images', []),
                    'extracted_fields': list(item_data.keys())
                }
                
                # Criar registro
                facebook_data = FacebookData(
                    task_id=task_id,
                    data_type=data_type,
                    content=content,
                    metadata=metadata,
                    source_url=source_url
                )
                
                # Salvar no repositório
                self.data_repository.create(facebook_data)
                saved_count += 1
                
            except Exception as e:
                self.logger.warning(f"Erro ao salvar item: {str(e)}")
                continue
        
        return saved_count
    
    def stop_execution(self, task_id: str) -> bool:
        """Parar execução de uma tarefa.
        
        Args:
            task_id: ID da tarefa a ser parada
            
        Returns:
            True se parada com sucesso
        """
        task = self.task_repository.get_by_id(task_id)
        if not task:
            return False
        
        if not task.is_active():
            return False
        
        try:
            # Sinalizar parada para o serviço de scraping
            self.scraping_service.stop_scraping(task_id)
            
            # Marcar tarefa como cancelada
            task.cancel_execution()
            self.task_repository.update(task)
            
            self.logger.info(f"Execução da tarefa {task_id} foi cancelada")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao parar tarefa {task_id}: {str(e)}")
            return False
    
    def get_execution_progress(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Obter progresso da execução.
        
        Args:
            task_id: ID da tarefa
            
        Returns:
            Informações de progresso ou None se não encontrada
        """
        task = self.task_repository.get_by_id(task_id)
        if not task:
            return None
        
        # Calcular progresso estimado
        config = task.get_config()
        max_items = config.get('max_items', 100)
        
        progress_percentage = 0
        if max_items > 0:
            progress_percentage = min(100, (task.items_processed / max_items) * 100)
        
        # Estimar tempo restante
        estimated_time = None
        if task.is_active() and task.started_at:
            elapsed = (datetime.utcnow() - task.started_at).total_seconds()
            if task.items_processed > 0 and progress_percentage < 100:
                rate = task.items_processed / elapsed
                remaining_items = max_items - task.items_processed
                estimated_time = remaining_items / rate if rate > 0 else None
        
        return {
            'task_id': task_id,
            'status': task.status,
            'progress': round(progress_percentage, 1),
            'items_processed': task.items_processed,
            'max_items': max_items,
            'estimated_time': estimated_time,
            'started_at': task.started_at.isoformat() if task.started_at else None,
            'duration': task.get_duration()
        }
    
    def cleanup_failed_executions(self) -> int:
        """Limpar execuções que falharam ou ficaram órfãs.
        
        Returns:
            Número de tarefas limpas
        """
        # Buscar tarefas executando há muito tempo
        long_running = self.task_repository.get_long_running_tasks(hours=2)
        
        cleaned_count = 0
        for task in long_running:
            try:
                # Tentar parar graciosamente
                self.stop_execution(task.id)
                cleaned_count += 1
                
            except Exception as e:
                self.logger.warning(f"Erro ao limpar tarefa {task.id}: {str(e)}")
        
        return cleaned_count