"""Repositório para dados do Facebook.

Este módulo implementa operações específicas de acesso a dados
para a entidade FacebookData.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func
from datetime import datetime, timedelta

from .base_repository import BaseRepository
from app.models.facebook_data import FacebookData


class FacebookDataRepository(BaseRepository[FacebookData]):
    """Repositório para operações com dados do Facebook.
    
    Implementa operações específicas para gerenciar dados extraídos
    do Facebook, incluindo busca por tipo, tarefa e estatísticas.
    """
    
    def __init__(self, db_session: Session):
        """Inicializar repositório de dados do Facebook.
        
        Args:
            db_session: Sessão do SQLAlchemy
        """
        super().__init__(db_session, FacebookData)
    
    def get_by_task_id(self, task_id: str, limit: Optional[int] = None) -> List[FacebookData]:
        """Buscar dados por ID da tarefa.
        
        Args:
            task_id: ID da tarefa de scraping
            limit: Limite de registros (opcional)
            
        Returns:
            Lista de dados da tarefa especificada
        """
        query = self.db_session.query(FacebookData).filter(
            FacebookData.task_id == task_id
        ).order_by(desc(FacebookData.extracted_at))
        
        if limit:
            query = query.limit(limit)
            
        return query.all()
    
    def get_by_data_type(self, data_type: str, limit: Optional[int] = None) -> List[FacebookData]:
        """Buscar dados por tipo.
        
        Args:
            data_type: Tipo de dado (post, comment, profile, like, share)
            limit: Limite de registros (opcional)
            
        Returns:
            Lista de dados do tipo especificado
        """
        query = self.db_session.query(FacebookData).filter(
            FacebookData.data_type == data_type
        ).order_by(desc(FacebookData.extracted_at))
        
        if limit:
            query = query.limit(limit)
            
        return query.all()
    
    def get_by_task_and_type(self, task_id: str, data_type: str, 
                             limit: Optional[int] = None) -> List[FacebookData]:
        """Buscar dados por tarefa e tipo.
        
        Args:
            task_id: ID da tarefa de scraping
            data_type: Tipo de dado
            limit: Limite de registros (opcional)
            
        Returns:
            Lista de dados filtrados por tarefa e tipo
        """
        query = self.db_session.query(FacebookData).filter(
            and_(
                FacebookData.task_id == task_id,
                FacebookData.data_type == data_type
            )
        ).order_by(desc(FacebookData.extracted_at))
        
        if limit:
            query = query.limit(limit)
            
        return query.all()
    
    def get_posts_by_task(self, task_id: str, limit: Optional[int] = None) -> List[FacebookData]:
        """Buscar posts de uma tarefa.
        
        Args:
            task_id: ID da tarefa de scraping
            limit: Limite de registros (opcional)
            
        Returns:
            Lista de posts da tarefa
        """
        return self.get_by_task_and_type(task_id, 'post', limit)
    
    def get_comments_by_task(self, task_id: str, limit: Optional[int] = None) -> List[FacebookData]:
        """Buscar comentários de uma tarefa.
        
        Args:
            task_id: ID da tarefa de scraping
            limit: Limite de registros (opcional)
            
        Returns:
            Lista de comentários da tarefa
        """
        return self.get_by_task_and_type(task_id, 'comment', limit)
    
    def get_profiles_by_task(self, task_id: str, limit: Optional[int] = None) -> List[FacebookData]:
        """Buscar dados de perfil de uma tarefa.
        
        Args:
            task_id: ID da tarefa de scraping
            limit: Limite de registros (opcional)
            
        Returns:
            Lista de dados de perfil da tarefa
        """
        return self.get_by_task_and_type(task_id, 'profile', limit)
    
    def search_content(self, search_term: str, task_id: Optional[str] = None, 
                       limit: Optional[int] = None) -> List[FacebookData]:
        """Buscar dados por termo no conteúdo.
        
        Args:
            search_term: Termo para busca no conteúdo
            task_id: ID da tarefa (opcional, para filtrar)
            limit: Limite de registros (opcional)
            
        Returns:
            Lista de dados que contêm o termo
        """
        query = self.db_session.query(FacebookData).filter(
            FacebookData.content.ilike(f'%{search_term}%')
        )
        
        if task_id:
            query = query.filter(FacebookData.task_id == task_id)
        
        query = query.order_by(desc(FacebookData.extracted_at))
        
        if limit:
            query = query.limit(limit)
            
        return query.all()
    
    def get_by_author(self, author: str, task_id: Optional[str] = None, 
                      limit: Optional[int] = None) -> List[FacebookData]:
        """Buscar dados por autor.
        
        Args:
            author: Nome do autor
            task_id: ID da tarefa (opcional, para filtrar)
            limit: Limite de registros (opcional)
            
        Returns:
            Lista de dados do autor especificado
        """
        # Buscar nos metadados JSON
        query = self.db_session.query(FacebookData).filter(
            FacebookData.metadata.ilike(f'%"author": "{author}"%')
        )
        
        if task_id:
            query = query.filter(FacebookData.task_id == task_id)
        
        query = query.order_by(desc(FacebookData.extracted_at))
        
        if limit:
            query = query.limit(limit)
            
        return query.all()
    
    def get_recent_data(self, hours: int = 24, limit: Optional[int] = None) -> List[FacebookData]:
        """Buscar dados extraídos recentemente.
        
        Args:
            hours: Número de horas para considerar como recente
            limit: Limite de registros (opcional)
            
        Returns:
            Lista de dados extraídos nas últimas horas
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        query = self.db_session.query(FacebookData).filter(
            FacebookData.extracted_at >= cutoff_time
        ).order_by(desc(FacebookData.extracted_at))
        
        if limit:
            query = query.limit(limit)
            
        return query.all()
    
    def get_statistics_by_task(self, task_id: str) -> Dict[str, Any]:
        """Obter estatísticas dos dados por tarefa.
        
        Args:
            task_id: ID da tarefa de scraping
            
        Returns:
            Dicionário com estatísticas dos dados
        """
        # Contar por tipo de dado
        type_counts = self.db_session.query(
            FacebookData.data_type,
            func.count(FacebookData.id).label('count')
        ).filter(
            FacebookData.task_id == task_id
        ).group_by(FacebookData.data_type).all()
        
        # Total de registros
        total = sum(count for _, count in type_counts)
        
        # Primeiro e último registro
        first_record = self.db_session.query(FacebookData).filter(
            FacebookData.task_id == task_id
        ).order_by(FacebookData.extracted_at).first()
        
        last_record = self.db_session.query(FacebookData).filter(
            FacebookData.task_id == task_id
        ).order_by(desc(FacebookData.extracted_at)).first()
        
        return {
            'total_records': total,
            'by_type': {data_type: count for data_type, count in type_counts},
            'first_extracted': first_record.extracted_at.isoformat() if first_record else None,
            'last_extracted': last_record.extracted_at.isoformat() if last_record else None
        }
    
    def get_data_for_export(self, task_id: str) -> List[FacebookData]:
        """Buscar dados formatados para exportação.
        
        Args:
            task_id: ID da tarefa de scraping
            
        Returns:
            Lista de dados ordenados para exportação
        """
        return self.db_session.query(FacebookData).filter(
            FacebookData.task_id == task_id
        ).order_by(
            FacebookData.data_type,
            FacebookData.extracted_at
        ).all()
    
    def delete_by_task_id(self, task_id: str) -> int:
        """Deletar todos os dados de uma tarefa.
        
        Args:
            task_id: ID da tarefa de scraping
            
        Returns:
            Número de registros deletados
        """
        deleted_count = self.db_session.query(FacebookData).filter(
            FacebookData.task_id == task_id
        ).delete()
        
        self.db_session.commit()
        return deleted_count
    
    def get_top_authors(self, task_id: Optional[str] = None, limit: int = 10) -> List[tuple]:
        """Buscar autores com mais conteúdo.
        
        Args:
            task_id: ID da tarefa (opcional, para filtrar)
            limit: Limite de registros
            
        Returns:
            Lista de tuplas (autor, contagem)
        """
        # Esta é uma implementação simplificada
        # Em produção, seria melhor ter um campo separado para autor
        query = self.db_session.query(FacebookData)
        
        if task_id:
            query = query.filter(FacebookData.task_id == task_id)
        
        data = query.all()
        
        # Contar autores dos metadados
        author_counts = {}
        for record in data:
            author = record.get_author()
            if author:
                author_counts[author] = author_counts.get(author, 0) + 1
        
        # Ordenar por contagem e retornar top N
        sorted_authors = sorted(author_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_authors[:limit]
    
    def get_data_by_date_range(self, start_date: datetime, end_date: datetime, 
                               task_id: Optional[str] = None) -> List[FacebookData]:
        """Buscar dados por intervalo de datas de extração.
        
        Args:
            start_date: Data inicial
            end_date: Data final
            task_id: ID da tarefa (opcional, para filtrar)
            
        Returns:
            Lista de dados no intervalo especificado
        """
        query = self.db_session.query(FacebookData).filter(
            and_(
                FacebookData.extracted_at >= start_date,
                FacebookData.extracted_at <= end_date
            )
        )
        
        if task_id:
            query = query.filter(FacebookData.task_id == task_id)
        
        return query.order_by(desc(FacebookData.extracted_at)).all()
    
    def cleanup_old_data(self, days: int = 90) -> int:
        """Limpar dados antigos.
        
        Args:
            days: Número de dias para considerar como antigos
            
        Returns:
            Número de registros removidos
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        deleted_count = self.db_session.query(FacebookData).filter(
            FacebookData.extracted_at <= cutoff_date
        ).delete()
        
        self.db_session.commit()
        return deleted_count