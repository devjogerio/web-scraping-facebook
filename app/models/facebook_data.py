"""Modelo de dados para informações extraídas do Facebook.

Este módulo define a entidade FacebookData que armazena os dados
extraídos durante o processo de scraping.
"""

import uuid
import json
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, CheckConstraint
from app import db


class FacebookData(db.Model):
    """Modelo para dados extraídos do Facebook.
    
    Armazena informações específicas extraídas durante o scraping,
    incluindo posts, comentários, curtidas e informações de perfil.
    """
    
    __tablename__ = 'facebook_data'
    
    # Campos principais
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(
        String(36), 
        ForeignKey('scraping_tasks.id', ondelete='CASCADE'),
        nullable=False,
        comment='ID da tarefa de scraping'
    )
    data_type = Column(
        String(50), 
        nullable=False,
        comment='Tipo de dado extraído'
    )
    content = Column(Text, comment='Conteúdo principal extraído')
    meta_data = Column(Text, comment='Metadados em JSON')
    extracted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    source_url = Column(Text, comment='URL de origem dos dados')
    
    # Relacionamentos serão definidos após importação de todos os modelos
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            data_type.in_(['post', 'comment', 'profile', 'like', 'share']),
            name='check_data_type_values'
        ),
    )
    
    def __init__(self, task_id: str, data_type: str, content: str, 
                 metadata: Optional[Dict[str, Any]] = None, source_url: Optional[str] = None):
        """Inicializar novo registro de dados do Facebook.
        
        Args:
            task_id: ID da tarefa de scraping
            data_type: Tipo de dado (post, comment, profile, like, share)
            content: Conteúdo principal extraído
            metadata: Metadados adicionais
            source_url: URL de origem dos dados
        """
        self.task_id = task_id
        self.data_type = data_type
        self.content = content
        self.meta_data = json.dumps(metadata) if metadata else None
        self.source_url = source_url
    
    def get_metadata(self) -> Dict[str, Any]:
        """Obter metadados como dicionário.
        
        Returns:
            Dict com os metadados ou dict vazio
        """
        if self.meta_data:
            return json.loads(self.meta_data)
        return {}
    
    def set_metadata(self, metadata: Dict[str, Any]) -> None:
        """Definir metadados.
        
        Args:
            metadata: Dicionário com os metadados
        """
        self.meta_data = json.dumps(metadata)
    
    def add_metadata_field(self, key: str, value: Any) -> None:
        """Adicionar campo aos metadados.
        
        Args:
            key: Chave do campo
            value: Valor do campo
        """
        current_metadata = self.get_metadata()
        current_metadata[key] = value
        self.set_metadata(current_metadata)
    
    def get_metadata_field(self, key: str, default: Any = None) -> Any:
        """Obter campo específico dos metadados.
        
        Args:
            key: Chave do campo
            default: Valor padrão se não encontrado
            
        Returns:
            Valor do campo ou valor padrão
        """
        metadata = self.get_metadata()
        return metadata.get(key, default)
    
    def is_post(self) -> bool:
        """Verificar se é um post.
        
        Returns:
            True se for um post
        """
        return self.data_type == 'post'
    
    def is_comment(self) -> bool:
        """Verificar se é um comentário.
        
        Returns:
            True se for um comentário
        """
        return self.data_type == 'comment'
    
    def is_profile(self) -> bool:
        """Verificar se são dados de perfil.
        
        Returns:
            True se forem dados de perfil
        """
        return self.data_type == 'profile'
    
    def get_author(self) -> Optional[str]:
        """Obter autor do conteúdo dos metadados.
        
        Returns:
            Nome do autor ou None
        """
        return self.get_metadata_field('author')
    
    def get_timestamp(self) -> Optional[str]:
        """Obter timestamp do conteúdo dos metadados.
        
        Returns:
            Timestamp ou None
        """
        return self.get_metadata_field('timestamp')
    
    def get_likes_count(self) -> int:
        """Obter número de curtidas dos metadados.
        
        Returns:
            Número de curtidas
        """
        return self.get_metadata_field('likes_count', 0)
    
    def get_comments_count(self) -> int:
        """Obter número de comentários dos metadados.
        
        Returns:
            Número de comentários
        """
        return self.get_metadata_field('comments_count', 0)
    
    def get_shares_count(self) -> int:
        """Obter número de compartilhamentos dos metadados.
        
        Returns:
            Número de compartilhamentos
        """
        return self.get_metadata_field('shares_count', 0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converter modelo para dicionário.
        
        Returns:
            Dicionário com os dados
        """
        return {
            'id': self.id,
            'task_id': self.task_id,
            'data_type': self.data_type,
            'content': self.content,
            'metadata': self.get_metadata(),
            'extracted_at': self.extracted_at.isoformat() if self.extracted_at else None,
            'source_url': self.source_url,
            'author': self.get_author(),
            'timestamp': self.get_timestamp(),
            'likes_count': self.get_likes_count(),
            'comments_count': self.get_comments_count(),
            'shares_count': self.get_shares_count()
        }
    
    def to_excel_row(self) -> Dict[str, Any]:
        """Converter para formato de linha do Excel.
        
        Returns:
            Dicionário formatado para exportação Excel
        """
        return {
            'ID': self.id,
            'Tipo': self.data_type.title(),
            'Conteúdo': self.content,
            'Autor': self.get_author(),
            'Data/Hora': self.get_timestamp(),
            'Curtidas': self.get_likes_count(),
            'Comentários': self.get_comments_count(),
            'Compartilhamentos': self.get_shares_count(),
            'URL Origem': self.source_url,
            'Extraído em': self.extracted_at.strftime('%d/%m/%Y %H:%M:%S') if self.extracted_at else ''
        }
    
    def __repr__(self) -> str:
        """Representação string do modelo."""
        content_preview = self.content[:50] + '...' if self.content and len(self.content) > 50 else self.content
        return f'<FacebookData {self.id}: {self.data_type} - {content_preview}>'