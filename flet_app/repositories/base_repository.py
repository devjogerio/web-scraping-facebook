"""Repositório base para operações comuns de banco de dados - Versão Flet.

Este módulo define a classe base que implementa operações
CRUD genéricas para todos os repositórios da aplicação.
"""

from typing import List, Optional, Type, TypeVar, Generic
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from flet_app.config.database import Base
from flet_app.config.logging_config import get_logger

# Type variable para o modelo
ModelType = TypeVar('ModelType', bound=Base)


class BaseRepository(Generic[ModelType]):
    """Repositório base com operações CRUD genéricas.
    
    Implementa operações comuns de Create, Read, Update, Delete
    que podem ser reutilizadas por repositórios específicos.
    """
    
    def __init__(self, model: Type[ModelType], db_session: Session):
        """Inicializar repositório base.
        
        Args:
            model: Classe do modelo SQLAlchemy
            db_session: Sessão do banco de dados
        """
        self.model = model
        self.db_session = db_session
        self.logger = get_logger(self.__class__.__name__)
    
    def create(self, obj: ModelType) -> ModelType:
        """Criar novo registro no banco de dados.
        
        Args:
            obj: Instância do modelo a ser criada
            
        Returns:
            Instância criada com ID atribuído
            
        Raises:
            SQLAlchemyError: Se houver erro na operação
        """
        try:
            self.db_session.add(obj)
            self.db_session.commit()
            self.db_session.refresh(obj)
            self.logger.info(f'Registro criado: {obj}')
            return obj
        except SQLAlchemyError as e:
            self.db_session.rollback()
            self.logger.error(f'Erro ao criar registro: {str(e)}')
            raise
    
    def get_by_id(self, obj_id: str) -> Optional[ModelType]:
        """Buscar registro por ID.
        
        Args:
            obj_id: ID do registro
            
        Returns:
            Instância encontrada ou None
        """
        try:
            obj = self.db_session.query(self.model).filter(self.model.id == obj_id).first()
            if obj:
                self.logger.debug(f'Registro encontrado: {obj_id}')
            else:
                self.logger.debug(f'Registro não encontrado: {obj_id}')
            return obj
        except SQLAlchemyError as e:
            self.logger.error(f'Erro ao buscar registro por ID {obj_id}: {str(e)}')
            return None
    
    def get_all(self, limit: Optional[int] = None, offset: int = 0) -> List[ModelType]:
        """Buscar todos os registros.
        
        Args:
            limit: Limite de registros (opcional)
            offset: Número de registros para pular
            
        Returns:
            Lista de registros
        """
        try:
            query = self.db_session.query(self.model)
            
            if offset > 0:
                query = query.offset(offset)
            
            if limit:
                query = query.limit(limit)
            
            results = query.all()
            self.logger.debug(f'Encontrados {len(results)} registros')
            return results
        except SQLAlchemyError as e:
            self.logger.error(f'Erro ao buscar todos os registros: {str(e)}')
            return []
    
    def update(self, obj: ModelType) -> ModelType:
        """Atualizar registro existente.
        
        Args:
            obj: Instância do modelo a ser atualizada
            
        Returns:
            Instância atualizada
            
        Raises:
            SQLAlchemyError: Se houver erro na operação
        """
        try:
            self.db_session.merge(obj)
            self.db_session.commit()
            self.db_session.refresh(obj)
            self.logger.info(f'Registro atualizado: {obj}')
            return obj
        except SQLAlchemyError as e:
            self.db_session.rollback()
            self.logger.error(f'Erro ao atualizar registro: {str(e)}')
            raise
    
    def delete(self, obj_id: str) -> bool:
        """Deletar registro por ID.
        
        Args:
            obj_id: ID do registro a ser deletado
            
        Returns:
            True se deletado com sucesso, False caso contrário
        """
        try:
            obj = self.get_by_id(obj_id)
            if obj:
                self.db_session.delete(obj)
                self.db_session.commit()
                self.logger.info(f'Registro deletado: {obj_id}')
                return True
            else:
                self.logger.warning(f'Tentativa de deletar registro inexistente: {obj_id}')
                return False
        except SQLAlchemyError as e:
            self.db_session.rollback()
            self.logger.error(f'Erro ao deletar registro {obj_id}: {str(e)}')
            return False
    
    def count(self) -> int:
        """Contar total de registros.
        
        Returns:
            Número total de registros
        """
        try:
            count = self.db_session.query(self.model).count()
            self.logger.debug(f'Total de registros: {count}')
            return count
        except SQLAlchemyError as e:
            self.logger.error(f'Erro ao contar registros: {str(e)}')
            return 0
    
    def exists(self, obj_id: str) -> bool:
        """Verificar se registro existe.
        
        Args:
            obj_id: ID do registro
            
        Returns:
            True se existe, False caso contrário
        """
        try:
            exists = self.db_session.query(self.model).filter(self.model.id == obj_id).first() is not None
            self.logger.debug(f'Registro {obj_id} existe: {exists}')
            return exists
        except SQLAlchemyError as e:
            self.logger.error(f'Erro ao verificar existência do registro {obj_id}: {str(e)}')
            return False
    
    def bulk_create(self, objects: List[ModelType]) -> List[ModelType]:
        """Criar múltiplos registros em lote.
        
        Args:
            objects: Lista de instâncias a serem criadas
            
        Returns:
            Lista de instâncias criadas
            
        Raises:
            SQLAlchemyError: Se houver erro na operação
        """
        try:
            self.db_session.add_all(objects)
            self.db_session.commit()
            
            # Refresh all objects
            for obj in objects:
                self.db_session.refresh(obj)
            
            self.logger.info(f'{len(objects)} registros criados em lote')
            return objects
        except SQLAlchemyError as e:
            self.db_session.rollback()
            self.logger.error(f'Erro ao criar registros em lote: {str(e)}')
            raise
    
    def close_session(self) -> None:
        """Fechar sessão do banco de dados."""
        try:
            self.db_session.close()
            self.logger.debug('Sessão do banco de dados fechada')
        except Exception as e:
            self.logger.error(f'Erro ao fechar sessão: {str(e)}')