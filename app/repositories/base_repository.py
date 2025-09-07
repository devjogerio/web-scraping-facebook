"""Repositório base com operações CRUD genéricas.

Este módulo define a classe base para todos os repositórios,
implementando operações comuns de acesso a dados.
"""

from typing import List, Optional, Type, TypeVar, Generic, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc, asc

# Type variable para tipagem genérica
T = TypeVar('T')


class BaseRepository(Generic[T]):
    """Repositório base com operações CRUD genéricas.
    
    Implementa padrão Repository para abstrair o acesso aos dados
    e fornecer interface consistente para todas as entidades.
    """
    
    def __init__(self, db_session: Session, model_class: Type[T]):
        """Inicializar repositório base.
        
        Args:
            db_session: Sessão do SQLAlchemy
            model_class: Classe do modelo SQLAlchemy
        """
        self.db_session = db_session
        self.model_class = model_class
    
    def create(self, entity: T) -> T:
        """Criar nova entidade no banco de dados.
        
        Args:
            entity: Instância da entidade a ser criada
            
        Returns:
            Entidade criada com ID atribuído
            
        Raises:
            SQLAlchemyError: Erro ao criar entidade
        """
        try:
            self.db_session.add(entity)
            self.db_session.commit()
            self.db_session.refresh(entity)
            return entity
        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise e
    
    def get_by_id(self, entity_id: str) -> Optional[T]:
        """Buscar entidade por ID.
        
        Args:
            entity_id: ID da entidade
            
        Returns:
            Entidade encontrada ou None
        """
        return self.db_session.query(self.model_class).filter(
            self.model_class.id == entity_id
        ).first()
    
    def get_all(self, limit: Optional[int] = None, offset: int = 0) -> List[T]:
        """Buscar todas as entidades.
        
        Args:
            limit: Limite de registros (opcional)
            offset: Número de registros para pular
            
        Returns:
            Lista de entidades
        """
        query = self.db_session.query(self.model_class)
        
        if offset > 0:
            query = query.offset(offset)
        
        if limit:
            query = query.limit(limit)
            
        return query.all()
    
    def update(self, entity: T) -> T:
        """Atualizar entidade existente.
        
        Args:
            entity: Entidade com dados atualizados
            
        Returns:
            Entidade atualizada
            
        Raises:
            SQLAlchemyError: Erro ao atualizar entidade
        """
        try:
            self.db_session.merge(entity)
            self.db_session.commit()
            return entity
        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise e
    
    def delete(self, entity_id: str) -> bool:
        """Deletar entidade por ID.
        
        Args:
            entity_id: ID da entidade a ser deletada
            
        Returns:
            True se deletada com sucesso
            
        Raises:
            SQLAlchemyError: Erro ao deletar entidade
        """
        try:
            entity = self.get_by_id(entity_id)
            if entity:
                self.db_session.delete(entity)
                self.db_session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise e
    
    def delete_entity(self, entity: T) -> bool:
        """Deletar entidade específica.
        
        Args:
            entity: Instância da entidade a ser deletada
            
        Returns:
            True se deletada com sucesso
            
        Raises:
            SQLAlchemyError: Erro ao deletar entidade
        """
        try:
            self.db_session.delete(entity)
            self.db_session.commit()
            return True
        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise e
    
    def count(self) -> int:
        """Contar total de entidades.
        
        Returns:
            Número total de entidades
        """
        return self.db_session.query(self.model_class).count()
    
    def exists(self, entity_id: str) -> bool:
        """Verificar se entidade existe.
        
        Args:
            entity_id: ID da entidade
            
        Returns:
            True se entidade existe
        """
        return self.db_session.query(self.model_class).filter(
            self.model_class.id == entity_id
        ).first() is not None
    
    def find_by_field(self, field_name: str, value: Any, 
                      limit: Optional[int] = None) -> List[T]:
        """Buscar entidades por campo específico.
        
        Args:
            field_name: Nome do campo
            value: Valor a ser buscado
            limit: Limite de registros (opcional)
            
        Returns:
            Lista de entidades encontradas
        """
        query = self.db_session.query(self.model_class).filter(
            getattr(self.model_class, field_name) == value
        )
        
        if limit:
            query = query.limit(limit)
            
        return query.all()
    
    def find_by_fields(self, filters: Dict[str, Any], 
                       limit: Optional[int] = None) -> List[T]:
        """Buscar entidades por múltiplos campos.
        
        Args:
            filters: Dicionário com campo: valor
            limit: Limite de registros (opcional)
            
        Returns:
            Lista de entidades encontradas
        """
        query = self.db_session.query(self.model_class)
        
        for field_name, value in filters.items():
            query = query.filter(getattr(self.model_class, field_name) == value)
        
        if limit:
            query = query.limit(limit)
            
        return query.all()
    
    def get_ordered(self, order_by: str, ascending: bool = True, 
                    limit: Optional[int] = None) -> List[T]:
        """Buscar entidades ordenadas.
        
        Args:
            order_by: Campo para ordenação
            ascending: True para ordem crescente
            limit: Limite de registros (opcional)
            
        Returns:
            Lista de entidades ordenadas
        """
        query = self.db_session.query(self.model_class)
        
        order_field = getattr(self.model_class, order_by)
        if ascending:
            query = query.order_by(asc(order_field))
        else:
            query = query.order_by(desc(order_field))
        
        if limit:
            query = query.limit(limit)
            
        return query.all()
    
    def bulk_create(self, entities: List[T]) -> List[T]:
        """Criar múltiplas entidades em lote.
        
        Args:
            entities: Lista de entidades a serem criadas
            
        Returns:
            Lista de entidades criadas
            
        Raises:
            SQLAlchemyError: Erro ao criar entidades
        """
        try:
            self.db_session.add_all(entities)
            self.db_session.commit()
            for entity in entities:
                self.db_session.refresh(entity)
            return entities
        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise e
    
    def bulk_delete(self, entity_ids: List[str]) -> int:
        """Deletar múltiplas entidades por IDs.
        
        Args:
            entity_ids: Lista de IDs das entidades
            
        Returns:
            Número de entidades deletadas
            
        Raises:
            SQLAlchemyError: Erro ao deletar entidades
        """
        try:
            deleted_count = self.db_session.query(self.model_class).filter(
                self.model_class.id.in_(entity_ids)
            ).delete(synchronize_session=False)
            
            self.db_session.commit()
            return deleted_count
        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise e