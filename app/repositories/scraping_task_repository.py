"""Repositório para tarefas de scraping.

Este módulo implementa operações específicas de acesso a dados
para a entidade ScrapingTask.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from datetime import datetime, timedelta

from .base_repository import BaseRepository
from app.models.scraping_task import ScrapingTask


class ScrapingTaskRepository(BaseRepository[ScrapingTask]):
    """Repositório para operações com tarefas de scraping.
    
    Implementa operações específicas para gerenciar tarefas de scraping,
    incluindo busca por status, estatísticas e operações de controle.
    """
    
    def __init__(self, db_session: Session):
        """Inicializar repositório de tarefas de scraping.
        
        Args:
            db_session: Sessão do SQLAlchemy
        """
        super().__init__(db_session, ScrapingTask)
    
    def get_by_status(self, status: str, limit: Optional[int] = None) -> List[ScrapingTask]:
        """Buscar tarefas por status.
        
        Args:
            status: Status das tarefas (pending, running, completed, failed, cancelled)
            limit: Limite de registros (opcional)
            
        Returns:
            Lista de tarefas com o status especificado
        """
        query = self.db_session.query(ScrapingTask).filter(
            ScrapingTask.status == status
        ).order_by(desc(ScrapingTask.created_at))
        
        if limit:
            query = query.limit(limit)
            
        return query.all()
    
    def get_active_tasks(self) -> List[ScrapingTask]:
        """Buscar tarefas ativas (executando).
        
        Returns:
            Lista de tarefas em execução
        """
        return self.get_by_status('running')
    
    def get_pending_tasks(self, limit: Optional[int] = None) -> List[ScrapingTask]:
        """Buscar tarefas pendentes.
        
        Args:
            limit: Limite de registros (opcional)
            
        Returns:
            Lista de tarefas pendentes
        """
        return self.get_by_status('pending', limit)
    
    def get_completed_tasks(self, limit: Optional[int] = None) -> List[ScrapingTask]:
        """Buscar tarefas concluídas.
        
        Args:
            limit: Limite de registros (opcional)
            
        Returns:
            Lista de tarefas concluídas
        """
        return self.get_by_status('completed', limit)
    
    def get_failed_tasks(self, limit: Optional[int] = None) -> List[ScrapingTask]:
        """Buscar tarefas que falharam.
        
        Args:
            limit: Limite de registros (opcional)
            
        Returns:
            Lista de tarefas que falharam
        """
        return self.get_by_status('failed', limit)
    
    def get_recent_tasks(self, days: int = 7, limit: Optional[int] = None) -> List[ScrapingTask]:
        """Buscar tarefas recentes.
        
        Args:
            days: Número de dias para considerar como recente
            limit: Limite de registros (opcional)
            
        Returns:
            Lista de tarefas criadas nos últimos dias
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = self.db_session.query(ScrapingTask).filter(
            ScrapingTask.created_at >= cutoff_date
        ).order_by(desc(ScrapingTask.created_at))
        
        if limit:
            query = query.limit(limit)
            
        return query.all()
    
    def get_by_url(self, url: str) -> List[ScrapingTask]:
        """Buscar tarefas por URL.
        
        Args:
            url: URL do Facebook
            
        Returns:
            Lista de tarefas para a URL especificada
        """
        return self.db_session.query(ScrapingTask).filter(
            ScrapingTask.url == url
        ).order_by(desc(ScrapingTask.created_at)).all()
    
    def search_by_name(self, name_pattern: str, limit: Optional[int] = None) -> List[ScrapingTask]:
        """Buscar tarefas por padrão no nome.
        
        Args:
            name_pattern: Padrão para busca no nome
            limit: Limite de registros (opcional)
            
        Returns:
            Lista de tarefas que correspondem ao padrão
        """
        query = self.db_session.query(ScrapingTask).filter(
            ScrapingTask.name.ilike(f'%{name_pattern}%')
        ).order_by(desc(ScrapingTask.created_at))
        
        if limit:
            query = query.limit(limit)
            
        return query.all()
    
    def get_statistics(self) -> dict:
        """Obter estatísticas das tarefas.
        
        Returns:
            Dicionário com estatísticas das tarefas
        """
        total = self.count()
        pending = len(self.get_by_status('pending'))
        running = len(self.get_by_status('running'))
        completed = len(self.get_by_status('completed'))
        failed = len(self.get_by_status('failed'))
        cancelled = len(self.get_by_status('cancelled'))
        
        return {
            'total': total,
            'pending': pending,
            'running': running,
            'completed': completed,
            'failed': failed,
            'cancelled': cancelled,
            'success_rate': (completed / total * 100) if total > 0 else 0
        }
    
    def get_tasks_with_data_count(self) -> List[tuple]:
        """Buscar tarefas com contagem de dados extraídos.
        
        Returns:
            Lista de tuplas (tarefa, contagem_dados)
        """
        from app.models.facebook_data import FacebookData
        
        return self.db_session.query(
            ScrapingTask,
            self.db_session.query(FacebookData).filter(
                FacebookData.task_id == ScrapingTask.id
            ).count().label('data_count')
        ).all()
    
    def get_long_running_tasks(self, hours: int = 2) -> List[ScrapingTask]:
        """Buscar tarefas executando há muito tempo.
        
        Args:
            hours: Número de horas para considerar como longa execução
            
        Returns:
            Lista de tarefas executando há mais tempo que o especificado
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        return self.db_session.query(ScrapingTask).filter(
            and_(
                ScrapingTask.status == 'running',
                ScrapingTask.started_at <= cutoff_time
            )
        ).all()
    
    def cancel_long_running_tasks(self, hours: int = 24) -> int:
        """Cancelar tarefas executando há muito tempo.
        
        Args:
            hours: Número de horas para considerar como timeout
            
        Returns:
            Número de tarefas canceladas
        """
        long_running_tasks = self.get_long_running_tasks(hours)
        
        cancelled_count = 0
        for task in long_running_tasks:
            task.cancel_execution()
            self.update(task)
            cancelled_count += 1
        
        return cancelled_count
    
    def cleanup_old_tasks(self, days: int = 30) -> int:
        """Limpar tarefas antigas concluídas ou falhadas.
        
        Args:
            days: Número de dias para considerar como antigas
            
        Returns:
            Número de tarefas removidas
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        old_tasks = self.db_session.query(ScrapingTask).filter(
            and_(
                ScrapingTask.completed_at <= cutoff_date,
                ScrapingTask.status.in_(['completed', 'failed', 'cancelled'])
            )
        ).all()
        
        removed_count = 0
        for task in old_tasks:
            self.delete_entity(task)
            removed_count += 1
        
        return removed_count
    
    def get_tasks_by_date_range(self, start_date: datetime, 
                                end_date: datetime) -> List[ScrapingTask]:
        """Buscar tarefas por intervalo de datas.
        
        Args:
            start_date: Data inicial
            end_date: Data final
            
        Returns:
            Lista de tarefas no intervalo especificado
        """
        return self.db_session.query(ScrapingTask).filter(
            and_(
                ScrapingTask.created_at >= start_date,
                ScrapingTask.created_at <= end_date
            )
        ).order_by(desc(ScrapingTask.created_at)).all()
    
    def get_most_processed_tasks(self, limit: int = 10) -> List[ScrapingTask]:
        """Buscar tarefas com mais itens processados.
        
        Args:
            limit: Limite de registros
            
        Returns:
            Lista das tarefas que mais processaram itens
        """
        return self.db_session.query(ScrapingTask).order_by(
            desc(ScrapingTask.items_processed)
        ).limit(limit).all()