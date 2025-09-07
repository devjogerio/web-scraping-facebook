"""Use case para executar scraping - Versão Flet.

Este módulo implementa a lógica de negócio para execução
de tarefas de scraping do Facebook na aplicação desktop.
"""

import threading
from typing import Optional, Callable, Dict, Any
from datetime import datetime

from flet_app.models.scraping_task import ScrapingTask
from flet_app.models.facebook_data import FacebookData
from flet_app.repositories.scraping_task_repository import ScrapingTaskRepository
from flet_app.repositories.facebook_data_repository import FacebookDataRepository
from flet_app.services.scraping_service import ScrapingService
from flet_app.config.logging_config import get_logger


class ExecuteScrapingUseCase:
    """Use case para executar scraping.
    
    Implementa a lógica de negócio para execução de tarefas
    de scraping de forma assíncrona com callbacks de progresso.
    """
    
    def __init__(self, task_repository: ScrapingTaskRepository, 
                 data_repository: FacebookDataRepository):
        """Inicializar use case.
        
        Args:
            task_repository: Repositório de tarefas
            data_repository: Repositório de dados
        """
        self.task_repository = task_repository
        self.data_repository = data_repository
        self.logger = get_logger('ExecuteScrapingUseCase')
        self.active_threads = {}
        self.scraping_services = {}
    
    def execute_async(self, task_id: str, 
                     progress_callback: Optional[Callable[[int, str], None]] = None,
                     completion_callback: Optional[Callable[[bool, str, int], None]] = None) -> bool:
        """Executar scraping de forma assíncrona.
        
        Args:
            task_id: ID da tarefa a ser executada
            progress_callback: Callback para atualizar progresso (percentual, mensagem)
            completion_callback: Callback para conclusão (sucesso, mensagem, itens_extraídos)
            
        Returns:
            True se a execução foi iniciada com sucesso
        """
        try:
            # Verificar se a tarefa existe
            task = self.task_repository.get_by_id(task_id)
            if not task:
                self.logger.error(f'Tarefa não encontrada: {task_id}')
                if completion_callback:
                    completion_callback(False, 'Tarefa não encontrada', 0)
                return False
            
            # Verificar se a tarefa já está em execução
            if task_id in self.active_threads:
                self.logger.warning(f'Tarefa já está em execução: {task_id}')
                if completion_callback:
                    completion_callback(False, 'Tarefa já está em execução', 0)
                return False
            
            # Verificar se a tarefa pode ser executada
            if task.status not in ['pending', 'failed']:
                self.logger.warning(f'Tarefa não pode ser executada. Status atual: {task.status}')
                if completion_callback:
                    completion_callback(False, f'Tarefa não pode ser executada (status: {task.status})', 0)
                return False
            
            # Criar thread para execução
            thread = threading.Thread(
                target=self._execute_scraping_thread,
                args=(task, progress_callback, completion_callback),
                daemon=True
            )
            
            # Registrar thread ativa
            self.active_threads[task_id] = thread
            
            # Iniciar execução
            thread.start()
            
            self.logger.info(f'Execução de scraping iniciada para tarefa: {task_id}')
            return True
            
        except Exception as e:
            self.logger.error(f'Erro ao iniciar execução de scraping: {str(e)}')
            if completion_callback:
                completion_callback(False, f'Erro interno: {str(e)}', 0)
            return False
    
    def _execute_scraping_thread(self, task: ScrapingTask,
                                progress_callback: Optional[Callable[[int, str], None]],
                                completion_callback: Optional[Callable[[bool, str, int], None]]) -> None:
        """Thread de execução do scraping.
        
        Args:
            task: Tarefa a ser executada
            progress_callback: Callback de progresso
            completion_callback: Callback de conclusão
        """
        extracted_data_count = 0
        
        try:
            # Atualizar status da tarefa para 'running'
            self.task_repository.update_status(task.id, 'running')
            
            if progress_callback:
                progress_callback(0, 'Iniciando scraping...')
            
            # Obter configurações da tarefa
            config = task.get_config()
            
            # Criar serviço de scraping
            scraping_service = ScrapingService(config)
            self.scraping_services[task.id] = scraping_service
            
            # Callback para processar dados extraídos
            def data_callback(fb_data: FacebookData) -> None:
                nonlocal extracted_data_count
                try:
                    # Salvar dados no banco
                    self.data_repository.create(fb_data)
                    extracted_data_count += 1
                    
                    # Atualizar contador na tarefa
                    self.task_repository.increment_items_processed(task.id, 1)
                    
                    self.logger.debug(f'Dados salvos: {fb_data.data_type} - {fb_data.get_content_preview()}')
                    
                except Exception as e:
                    self.logger.error(f'Erro ao salvar dados extraídos: {str(e)}')
            
            # Executar scraping
            extracted_data = scraping_service.extract_data_async(
                task_id=task.id,
                url=task.url,
                config=config,
                progress_callback=progress_callback,
                data_callback=data_callback
            )
            
            # Verificar se foi interrompido
            if scraping_service.stop_flags.get(task.id, False):
                self.task_repository.update_status(task.id, 'cancelled')
                if completion_callback:
                    completion_callback(False, 'Scraping cancelado pelo usuário', extracted_data_count)
            else:
                # Marcar tarefa como concluída
                self.task_repository.update_status(task.id, 'completed')
                
                success_message = f'Scraping concluído com sucesso! {extracted_data_count} itens extraídos.'
                self.logger.info(f'Tarefa {task.id} concluída: {extracted_data_count} itens')
                
                if completion_callback:
                    completion_callback(True, success_message, extracted_data_count)
            
        except Exception as e:
            error_message = f'Erro durante scraping: {str(e)}'
            self.logger.error(f'Erro na tarefa {task.id}: {str(e)}')
            
            # Marcar tarefa como falhada
            self.task_repository.update_status(task.id, 'failed', error_message)
            
            if completion_callback:
                completion_callback(False, error_message, extracted_data_count)
        
        finally:
            # Limpar recursos
            self.active_threads.pop(task.id, None)
            self.scraping_services.pop(task.id, None)
    
    def stop_scraping(self, task_id: str) -> bool:
        """Parar execução de scraping.
        
        Args:
            task_id: ID da tarefa a ser parada
            
        Returns:
            True se a parada foi solicitada com sucesso
        """
        try:
            # Verificar se a tarefa está em execução
            if task_id not in self.active_threads:
                self.logger.warning(f'Tarefa não está em execução: {task_id}')
                return False
            
            # Sinalizar parada no serviço de scraping
            if task_id in self.scraping_services:
                self.scraping_services[task_id].stop_scraping(task_id)
            
            self.logger.info(f'Parada solicitada para tarefa: {task_id}')
            return True
            
        except Exception as e:
            self.logger.error(f'Erro ao parar scraping da tarefa {task_id}: {str(e)}')
            return False
    
    def is_task_running(self, task_id: str) -> bool:
        """Verificar se uma tarefa está em execução.
        
        Args:
            task_id: ID da tarefa
            
        Returns:
            True se a tarefa está em execução
        """
        return task_id in self.active_threads and self.active_threads[task_id].is_alive()
    
    def get_running_tasks(self) -> list[str]:
        """Obter lista de tarefas em execução.
        
        Returns:
            Lista de IDs das tarefas em execução
        """
        running_tasks = []
        
        # Limpar threads mortas
        dead_threads = []
        for task_id, thread in self.active_threads.items():
            if thread.is_alive():
                running_tasks.append(task_id)
            else:
                dead_threads.append(task_id)
        
        # Remover threads mortas
        for task_id in dead_threads:
            self.active_threads.pop(task_id, None)
            self.scraping_services.pop(task_id, None)
        
        return running_tasks
    
    def validate_task_for_execution(self, task_id: str) -> tuple[bool, str]:
        """Validar se uma tarefa pode ser executada.
        
        Args:
            task_id: ID da tarefa
            
        Returns:
            Tupla (pode_executar, mensagem)
        """
        try:
            # Verificar se a tarefa existe
            task = self.task_repository.get_by_id(task_id)
            if not task:
                return False, 'Tarefa não encontrada'
            
            # Verificar se já está em execução
            if self.is_task_running(task_id):
                return False, 'Tarefa já está em execução'
            
            # Verificar status
            if task.status not in ['pending', 'failed']:
                return False, f'Tarefa não pode ser executada (status: {task.status})'
            
            # Verificar configurações
            config = task.get_config()
            if not config.get('data_types'):
                return False, 'Configuração inválida: nenhum tipo de dado selecionado'
            
            return True, 'Tarefa pode ser executada'
            
        except Exception as e:
            self.logger.error(f'Erro ao validar tarefa {task_id}: {str(e)}')
            return False, f'Erro interno: {str(e)}'
    
    def get_task_progress(self, task_id: str) -> Dict[str, Any]:
        """Obter progresso de uma tarefa.
        
        Args:
            task_id: ID da tarefa
            
        Returns:
            Dicionário com informações de progresso
        """
        try:
            task = self.task_repository.get_by_id(task_id)
            if not task:
                return {'error': 'Tarefa não encontrada'}
            
            is_running = self.is_task_running(task_id)
            progress_percentage = task.get_progress_percentage()
            
            return {
                'task_id': task_id,
                'status': task.status,
                'is_running': is_running,
                'progress_percentage': progress_percentage,
                'items_processed': task.items_processed,
                'started_at': task.started_at.isoformat() if task.started_at else None,
                'duration': task.get_duration(),
                'error_message': task.error_message
            }
            
        except Exception as e:
            self.logger.error(f'Erro ao obter progresso da tarefa {task_id}: {str(e)}')
            return {'error': f'Erro interno: {str(e)}'}
    
    def cleanup_completed_tasks(self) -> int:
        """Limpar recursos de tarefas concluídas.
        
        Returns:
            Número de tarefas limpas
        """
        cleaned_count = 0
        
        try:
            # Limpar threads mortas
            dead_threads = []
            for task_id, thread in self.active_threads.items():
                if not thread.is_alive():
                    dead_threads.append(task_id)
            
            for task_id in dead_threads:
                self.active_threads.pop(task_id, None)
                self.scraping_services.pop(task_id, None)
                cleaned_count += 1
            
            if cleaned_count > 0:
                self.logger.info(f'Limpeza concluída: {cleaned_count} tarefas removidas')
            
        except Exception as e:
            self.logger.error(f'Erro durante limpeza: {str(e)}')
        
        return cleaned_count
    
    def get_execution_statistics(self) -> Dict[str, Any]:
        """Obter estatísticas de execução.
        
        Returns:
            Dicionário com estatísticas
        """
        try:
            running_tasks = self.get_running_tasks()
            task_stats = self.task_repository.get_statistics()
            data_stats = self.data_repository.get_data_statistics()
            
            return {
                'running_tasks_count': len(running_tasks),
                'running_task_ids': running_tasks,
                'task_statistics': task_stats,
                'data_statistics': data_stats,
                'active_threads': len(self.active_threads),
                'active_services': len(self.scraping_services)
            }
            
        except Exception as e:
            self.logger.error(f'Erro ao obter estatísticas: {str(e)}')
            return {
                'error': f'Erro interno: {str(e)}',
                'running_tasks_count': 0,
                'running_task_ids': [],
                'active_threads': 0,
                'active_services': 0
            }