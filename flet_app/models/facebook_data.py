"""Modelo de dados para informações extraídas do Facebook - Versão Flet.

Este módulo define a entidade FacebookData que armazena
os dados extraídos durante o processo de scraping.
"""

import uuid
import json
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from flet_app.config.database import Base


class FacebookData(Base):
    """Modelo para dados extraídos do Facebook.
    
    Armazena informações extraídas como posts, comentários,
    informações de perfil, etc.
    """
    
    __tablename__ = 'facebook_data'
    
    # Campos principais
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String(36), ForeignKey('scraping_tasks.id', ondelete='CASCADE'), nullable=False)
    data_type = Column(String(50), nullable=False, comment='Tipo de dado (post, comment, profile, etc.)')
    content = Column(Text, comment='Conteúdo extraído')
    meta_data = Column(Text, comment='Metadados em JSON')
    extracted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    source_url = Column(Text, comment='URL de origem dos dados')
    
    def __init__(self, task_id: str, data_type: str, content: str = '', 
                 metadata: Optional[Dict[str, Any]] = None, source_url: str = ''):
        """Inicializar dados do Facebook.
        
        Args:
            task_id: ID da tarefa de scraping
            data_type: Tipo de dado (post, comment, profile, like, share)
            content: Conteúdo extraído
            metadata: Metadados adicionais
            source_url: URL de origem
        """
        self.task_id = task_id
        self.data_type = data_type
        self.content = content or ''
        self.meta_data = json.dumps(metadata) if metadata else None
        self.source_url = source_url
    
    def get_metadata(self) -> Dict[str, Any]:
        """Obter metadados como dicionário.
        
        Returns:
            Dict com os metadados
        """
        if self.meta_data:
            try:
                return json.loads(self.meta_data)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_metadata(self, metadata: Dict[str, Any]) -> None:
        """Definir metadados.
        
        Args:
            metadata: Dicionário com os metadados
        """
        self.meta_data = json.dumps(metadata)
    
    def get_author(self) -> str:
        """Obter autor dos dados.
        
        Returns:
            Nome do autor ou string vazia
        """
        metadata = self.get_metadata()
        return metadata.get('author', '')
    
    def get_timestamp(self) -> str:
        """Obter timestamp dos dados.
        
        Returns:
            Timestamp ou string vazia
        """
        metadata = self.get_metadata()
        return metadata.get('timestamp', '')
    
    def get_likes_count(self) -> int:
        """Obter número de curtidas.
        
        Returns:
            Número de curtidas
        """
        metadata = self.get_metadata()
        return metadata.get('likes_count', 0)
    
    def get_comments_count(self) -> int:
        """Obter número de comentários.
        
        Returns:
            Número de comentários
        """
        metadata = self.get_metadata()
        return metadata.get('comments_count', 0)
    
    def get_shares_count(self) -> int:
        """Obter número de compartilhamentos.
        
        Returns:
            Número de compartilhamentos
        """
        metadata = self.get_metadata()
        return metadata.get('shares_count', 0)
    
    def get_content_preview(self, max_length: int = 100) -> str:
        """Obter prévia do conteúdo.
        
        Args:
            max_length: Comprimento máximo da prévia
            
        Returns:
            Prévia do conteúdo
        """
        if not self.content:
            return ''
        
        if len(self.content) <= max_length:
            return self.content
        
        return self.content[:max_length] + '...'
    
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
            'shares_count': self.get_shares_count(),
            'content_preview': self.get_content_preview()
        }
    
    def to_excel_row(self) -> Dict[str, Any]:
        """Converter para linha de Excel.
        
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
        preview = self.get_content_preview(50)
        return f'<FacebookData {self.id}: {self.data_type} - {preview}>'