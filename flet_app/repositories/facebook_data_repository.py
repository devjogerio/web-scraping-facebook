"""Repositório para dados do Facebook - Versão Flet.

Este módulo implementa operações específicas de banco de dados
para o modelo FacebookData.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from flet_app.models.facebook_data import FacebookData
from flet_app.repositories.base_repository import BaseRepository


class FacebookDataRepository(BaseRepository[FacebookData]):
    """Repositório para operações com dados do Facebook.
    
    Implementa operações específicas para gerenciar dados
    extraídos do Facebook.
    """
    
    def __init__(self, db_session: Session):
        """Inicializar repositório de dados do Facebook.
        
        Args:
            db_session: Sessão do banco de dados
        """
        super().__init__(FacebookData, db_session)
    
    def get_by_task_id(self, task_id: str, limit: Optional[int] = None) -> List[FacebookData]:
        """Buscar dados por ID da tarefa.
        
        Args:
            task_id: ID da tarefa de scraping
            limit: Limite de resultados
            
        Returns:
            Lista de dados extraídos da tarefa
        """
        try:
            query = self.db_session.query(FacebookData)
            query = query.filter(FacebookData.task_id == task_id)
            query = query.order_by(desc(FacebookData.extracted_at))
            
            if limit:
                query = query.limit(limit)
            
            results = query.all()
            self.logger.debug(f'Encontrados {len(results)} dados para tarefa {task_id}')
            return results
        except Exception as e:
            self.logger.error(f'Erro ao buscar dados da tarefa {task_id}: {str(e)}')
            return []
    
    def get_by_data_type(self, data_type: str, task_id: Optional[str] = None, 
                        limit: Optional[int] = None) -> List[FacebookData]:
        """Buscar dados por tipo.
        
        Args:
            data_type: Tipo de dado (post, comment, profile, like, share)
            task_id: ID da tarefa (opcional)
            limit: Limite de resultados
            
        Returns:
            Lista de dados do tipo especificado
        """
        try:
            query = self.db_session.query(FacebookData)
            query = query.filter(FacebookData.data_type == data_type)
            
            if task_id:
                query = query.filter(FacebookData.task_id == task_id)
            
            query = query.order_by(desc(FacebookData.extracted_at))
            
            if limit:
                query = query.limit(limit)
            
            results = query.all()
            self.logger.debug(f'Encontrados {len(results)} dados do tipo {data_type}')
            return results
        except Exception as e:
            self.logger.error(f'Erro ao buscar dados do tipo {data_type}: {str(e)}')
            return []
    
    def get_posts_by_task(self, task_id: str, limit: Optional[int] = None) -> List[FacebookData]:
        """Buscar posts de uma tarefa.
        
        Args:
            task_id: ID da tarefa
            limit: Limite de resultados
            
        Returns:
            Lista de posts extraídos
        """
        return self.get_by_data_type('post', task_id, limit)
    
    def get_comments_by_task(self, task_id: str, limit: Optional[int] = None) -> List[FacebookData]:
        """Buscar comentários de uma tarefa.
        
        Args:
            task_id: ID da tarefa
            limit: Limite de resultados
            
        Returns:
            Lista de comentários extraídos
        """
        return self.get_by_data_type('comment', task_id, limit)
    
    def get_profile_data_by_task(self, task_id: str) -> List[FacebookData]:
        """Buscar dados de perfil de uma tarefa.
        
        Args:
            task_id: ID da tarefa
            
        Returns:
            Lista de dados de perfil extraídos
        """
        return self.get_by_data_type('profile', task_id)
    
    def search_content(self, search_term: str, task_id: Optional[str] = None, 
                      limit: Optional[int] = None) -> List[FacebookData]:
        """Buscar dados por conteúdo.
        
        Args:
            search_term: Termo de busca
            task_id: ID da tarefa (opcional)
            limit: Limite de resultados
            
        Returns:
            Lista de dados que contêm o termo de busca
        """
        try:
            query = self.db_session.query(FacebookData)
            query = query.filter(FacebookData.content.ilike(f'%{search_term}%'))
            
            if task_id:
                query = query.filter(FacebookData.task_id == task_id)
            
            query = query.order_by(desc(FacebookData.extracted_at))
            
            if limit:
                query = query.limit(limit)
            
            results = query.all()
            self.logger.debug(f'Encontrados {len(results)} dados contendo "{search_term}"')
            return results
        except Exception as e:
            self.logger.error(f'Erro ao buscar dados por conteúdo "{search_term}": {str(e)}')
            return []
    
    def get_data_statistics(self, task_id: Optional[str] = None) -> Dict[str, Any]:
        """Obter estatísticas dos dados extraídos.
        
        Args:
            task_id: ID da tarefa (opcional)
            
        Returns:
            Dicionário com estatísticas dos dados
        """
        try:
            query = self.db_session.query(FacebookData)
            
            if task_id:
                query = query.filter(FacebookData.task_id == task_id)
            
            # Contar por tipo de dado
            type_counts = (
                query.with_entities(FacebookData.data_type, func.count(FacebookData.id))
                .group_by(FacebookData.data_type)
                .all()
            )
            
            stats = {
                'total': query.count(),
                'by_type': {data_type: count for data_type, count in type_counts}
            }
            
            # Adicionar tipos que podem não existir
            for data_type in ['post', 'comment', 'profile', 'like', 'share']:
                if data_type not in stats['by_type']:
                    stats['by_type'][data_type] = 0
            
            self.logger.debug(f'Estatísticas dos dados: {stats}')
            return stats
        except Exception as e:
            self.logger.error(f'Erro ao obter estatísticas dos dados: {str(e)}')
            return {
                'total': 0,
                'by_type': {
                    'post': 0,
                    'comment': 0,
                    'profile': 0,
                    'like': 0,
                    'share': 0
                }
            }
    
    def get_recent_data(self, limit: int = 10, task_id: Optional[str] = None) -> List[FacebookData]:
        """Buscar dados mais recentes.
        
        Args:
            limit: Número máximo de dados
            task_id: ID da tarefa (opcional)
            
        Returns:
            Lista dos dados mais recentes
        """
        try:
            query = self.db_session.query(FacebookData)
            
            if task_id:
                query = query.filter(FacebookData.task_id == task_id)
            
            query = query.order_by(desc(FacebookData.extracted_at))
            query = query.limit(limit)
            
            results = query.all()
            self.logger.debug(f'Encontrados {len(results)} dados recentes')
            return results
        except Exception as e:
            self.logger.error(f'Erro ao buscar dados recentes: {str(e)}')
            return []
    
    def get_data_for_export(self, task_id: str) -> List[FacebookData]:
        """Buscar todos os dados de uma tarefa para exportação.
        
        Args:
            task_id: ID da tarefa
            
        Returns:
            Lista completa de dados para exportação
        """
        try:
            query = self.db_session.query(FacebookData)
            query = query.filter(FacebookData.task_id == task_id)
            query = query.order_by(FacebookData.data_type, desc(FacebookData.extracted_at))
            
            results = query.all()
            self.logger.info(f'Preparados {len(results)} dados para exportação da tarefa {task_id}')
            return results
        except Exception as e:
            self.logger.error(f'Erro ao buscar dados para exportação da tarefa {task_id}: {str(e)}')
            return []
    
    def delete_by_task_id(self, task_id: str) -> bool:
        """Deletar todos os dados de uma tarefa.
        
        Args:
            task_id: ID da tarefa
            
        Returns:
            True se deletado com sucesso
        """
        try:
            deleted_count = (
                self.db_session.query(FacebookData)
                .filter(FacebookData.task_id == task_id)
                .delete()
            )
            
            self.db_session.commit()
            self.logger.info(f'Deletados {deleted_count} dados da tarefa {task_id}')
            return True
        except Exception as e:
            self.db_session.rollback()
            self.logger.error(f'Erro ao deletar dados da tarefa {task_id}: {str(e)}')
            return False
    
    def get_authors_by_task(self, task_id: str) -> List[str]:
        """Obter lista de autores únicos de uma tarefa.
        
        Args:
            task_id: ID da tarefa
            
        Returns:
            Lista de autores únicos
        """
        try:
            # Buscar metadados que contêm informações de autor
            data_list = self.get_by_task_id(task_id)
            authors = set()
            
            for data in data_list:
                author = data.get_author()
                if author:
                    authors.add(author)
            
            author_list = list(authors)
            self.logger.debug(f'Encontrados {len(author_list)} autores únicos na tarefa {task_id}')
            return author_list
        except Exception as e:
            self.logger.error(f'Erro ao buscar autores da tarefa {task_id}: {str(e)}')
            return []