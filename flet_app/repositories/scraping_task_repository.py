"""Repositório para tarefas de scraping - Versão Flet.

Este módulo implementa operações específicas de banco de dados
para o modelo ScrapingTask.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from flet_app.models.scraping_task import ScrapingTask
from flet_app.repositories.base_repository import BaseRepository


class ScrapingTaskRepository(BaseRepository[ScrapingTask]):
    """Repositório para operações com tarefas de scraping.
    
    Implementa operações específicas para gerenciar tarefas
    de scraping do Facebook.
    """
    
    def __init__(self, db_session: Session):
        """Inicializar repositório de tarefas.
        
        Args:
            db_session: Sessão do banco de dados
        """
        super().__init__(ScrapingTask, db_session)
    
    def get_by_status(self, status: str, limit: Optional[int] = None) -> List[ScrapingTask]:
        """Buscar tarefas por status.
        
        Args:
            status: Status das tarefas (pending, running, completed, failed, cancelled)
            limit: Limite de resultados
            
        Returns:
            Lista de tarefas com o status especificado
        """
        try:
            query = self.db_session.query(ScrapingTask).filter(ScrapingTask.status == status)
            query = query.order_by(desc(ScrapingTask.created_at))
            
            if limit:
                query = query.limit(limit)
            
            results = query.all()
            self.logger.debug(f'Encontradas {len(results)} tarefas com status {status}')
            return results
        except Exception as e:
            self.logger.error(f'Erro ao buscar tarefas por status {status}: {str(e)}')
            return []
    
    def get_active_tasks(self) -> List[ScrapingTask]:
        """Buscar tarefas ativas (em execução).
        
        Returns:
            Lista de tarefas em execução
        """
        return self.get_by_status('running')
    
    def get_pending_tasks(self) -> List[ScrapingTask]:
        """Buscar tarefas pendentes.
        
        Returns:
            Lista de tarefas pendentes
        """
        return self.get_by_status('pending')
    
    def get_completed_tasks(self, limit: Optional[int] = 10) -> List[ScrapingTask]:
        """Buscar tarefas concluídas.
        
        Args:
            limit: Limite de resultados
            
        Returns:
            Lista de tarefas concluídas
        """
        return self.get_by_status('completed', limit)
    
    def get_failed_tasks(self, limit: Optional[int] = 10) -> List[ScrapingTask]:
        """Buscar tarefas que falharam.
        
        Args:
            limit: Limite de resultados
            
        Returns:
            Lista de tarefas que falharam
        """
        return self.get_by_status('failed', limit)
    
    def search_by_name(self, name: str) -> List[ScrapingTask]:
        """Buscar tarefas por nome (busca parcial).
        
        Args:
            name: Nome ou parte do nome da tarefa
            
        Returns:
            Lista de tarefas que contêm o nome especificado
        """
        try:
            query = self.db_session.query(ScrapingTask)
            query = query.filter(ScrapingTask.name.ilike(f'%{name}%'))
            query = query.order_by(desc(ScrapingTask.created_at))
            
            results = query.all()
            self.logger.debug(f'Encontradas {len(results)} tarefas com nome contendo "{name}"')
            return results
        except Exception as e:
            self.logger.error(f'Erro ao buscar tarefas por nome "{name}": {str(e)}')
            return []
    
    def search_by_url(self, url: str) -> List[ScrapingTask]:
        """Buscar tarefas por URL.
        
        Args:
            url: URL ou parte da URL
            
        Returns:
            Lista de tarefas que contêm a URL especificada
        """
        try:
            query = self.db_session.query(ScrapingTask)
            query = query.filter(ScrapingTask.url.ilike(f'%{url}%'))
            query = query.order_by(desc(ScrapingTask.created_at))
            
            results = query.all()
            self.logger.debug(f'Encontradas {len(results)} tarefas com URL contendo "{url}"')
            return results
        except Exception as e:
            self.logger.error(f'Erro ao buscar tarefas por URL "{url}": {str(e)}')
            return []
    
    def get_recent_tasks(self, limit: int = 10) -> List[ScrapingTask]:
        """Buscar tarefas mais recentes.
        
        Args:
            limit: Número máximo de tarefas
            
        Returns:
            Lista das tarefas mais recentes
        """
        try:
            query = self.db_session.query(ScrapingTask)
            query = query.order_by(desc(ScrapingTask.created_at))
            query = query.limit(limit)
            
            results = query.all()
            self.logger.debug(f'Encontradas {len(results)} tarefas recentes')
            return results
        except Exception as e:
            self.logger.error(f'Erro ao buscar tarefas recentes: {str(e)}')
            return []
    
    def get_statistics(self) -> dict:
        """Obter estatísticas das tarefas.
        
        Returns:
            Dicionário com estatísticas das tarefas
        """
        try:
            stats = {
                'total': self.count(),
                'pending': len(self.get_by_status('pending')),
                'running': len(self.get_by_status('running')),
                'completed': len(self.get_by_status('completed')),
                'failed': len(self.get_by_status('failed')),
                'cancelled': len(self.get_by_status('cancelled'))
            }
            
            self.logger.debug(f'Estatísticas das tarefas: {stats}')
            return stats
        except Exception as e:
            self.logger.error(f'Erro ao obter estatísticas: {str(e)}')
            return {
                'total': 0,
                'pending': 0,
                'running': 0,
                'completed': 0,
                'failed': 0,
                'cancelled': 0
            }
    
    def get_tasks_with_data_count(self) -> List[tuple]:
        """Buscar tarefas com contagem de dados extraídos.
        
        Returns:
            Lista de tuplas (tarefa, contagem_dados)
        """
        try:
            from flet_app.models.facebook_data import FacebookData
            
            query = self.db_session.query(
                ScrapingTask,
                self.db_session.query(FacebookData)
                .filter(FacebookData.task_id == ScrapingTask.id)
                .count().label('data_count')
            )
            
            results = query.all()
            self.logger.debug(f'Encontradas {len(results)} tarefas com contagem de dados')
            return results
        except Exception as e:
            self.logger.error(f'Erro ao buscar tarefas com contagem de dados: {str(e)}')
            return []
    
    def update_status(self, task_id: str, status: str, error_message: str = None) -> bool:
        """Atualizar status de uma tarefa.
        
        Args:
            task_id: ID da tarefa
            status: Novo status
            error_message: Mensagem de erro (opcional)
            
        Returns:
            True se atualizado com sucesso
        """
        try:
            task = self.get_by_id(task_id)
            if not task:
                self.logger.warning(f'Tarefa não encontrada para atualização: {task_id}')
                return False
            
            if status == 'running':
                task.start_execution()
            elif status == 'completed':
                task.complete_execution()
            elif status == 'failed':
                task.fail_execution(error_message or 'Erro desconhecido')
            elif status == 'cancelled':
                task.cancel_execution()
            else:
                task.status = status
            
            self.update(task)
            return True
        except Exception as e:
            self.logger.error(f'Erro ao atualizar status da tarefa {task_id}: {str(e)}')
            return False
    
    def increment_items_processed(self, task_id: str, count: int = 1) -> bool:
        """Incrementar contador de itens processados.
        
        Args:
            task_id: ID da tarefa
            count: Número de itens a incrementar
            
        Returns:
            True se atualizado com sucesso
        """
        try:
            task = self.get_by_id(task_id)
            if not task:
                return False
            
            task.increment_processed_items(count)
            self.update(task)
            return True
        except Exception as e:
            self.logger.error(f'Erro ao incrementar itens processados da tarefa {task_id}: {str(e)}')
            return False