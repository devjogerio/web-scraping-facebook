"""Modelo de dados para tarefas de scraping.

Este módulo define a entidade ScrapingTask que representa uma tarefa
de extração de dados do Facebook no sistema.
"""

import uuid
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, String, DateTime, Integer, Text, CheckConstraint
from app import db


class ScrapingTask(db.Model):
    """Modelo para tarefas de scraping do Facebook.
    
    Representa uma tarefa de extração de dados com todas as configurações
    necessárias para execução e monitoramento do progresso.
    """
    
    __tablename__ = 'scraping_tasks'
    
    # Campos principais
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, comment='Nome da tarefa')
    url = Column(Text, nullable=False, comment='URL do Facebook para scraping')
    status = Column(
        String(20), 
        nullable=False, 
        default='pending',
        comment='Status atual da tarefa'
    )
    config = Column(Text, comment='Configurações em JSON')
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Métricas de execução
    items_processed = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    
    # Relacionamentos serão definidos após importação de todos os modelos
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            status.in_(['pending', 'running', 'completed', 'failed', 'cancelled']),
            name='check_status_values'
        ),
    )
    
    def __init__(self, name: str, url: str, config: Optional[Dict[str, Any]] = None):
        """Inicializar nova tarefa de scraping.
        
        Args:
            name: Nome descritivo da tarefa
            url: URL do Facebook para fazer scraping
            config: Configurações específicas da tarefa
        """
        self.name = name
        self.url = url
        self.config = json.dumps(config) if config else None
        self.status = 'pending'
        self.items_processed = 0
    
    def get_config(self) -> Dict[str, Any]:
        """Obter configurações da tarefa como dicionário.
        
        Returns:
            Dict com as configurações da tarefa
        """
        if self.config:
            return json.loads(self.config)
        return {}
    
    def set_config(self, config: Dict[str, Any]) -> None:
        """Definir configurações da tarefa.
        
        Args:
            config: Dicionário com as configurações
        """
        self.config = json.dumps(config)
        self.updated_at = datetime.utcnow()
    
    def start_execution(self) -> None:
        """Marcar tarefa como iniciada."""
        self.status = 'running'
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def complete_execution(self) -> None:
        """Marcar tarefa como concluída."""
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def fail_execution(self, error_message: str) -> None:
        """Marcar tarefa como falhada.
        
        Args:
            error_message: Mensagem de erro detalhada
        """
        self.status = 'failed'
        self.error_message = error_message
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def cancel_execution(self) -> None:
        """Cancelar execução da tarefa."""
        self.status = 'cancelled'
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def increment_processed_items(self, count: int = 1) -> None:
        """Incrementar contador de itens processados.
        
        Args:
            count: Número de itens a incrementar
        """
        self.items_processed += count
        self.updated_at = datetime.utcnow()
    
    def get_duration(self) -> Optional[float]:
        """Calcular duração da execução em segundos.
        
        Returns:
            Duração em segundos ou None se não iniciada
        """
        if not self.started_at:
            return None
        
        end_time = self.completed_at or datetime.utcnow()
        return (end_time - self.started_at).total_seconds()
    
    def is_active(self) -> bool:
        """Verificar se a tarefa está ativa (executando).
        
        Returns:
            True se a tarefa está executando
        """
        return self.status == 'running'
    
    def is_completed(self) -> bool:
        """Verificar se a tarefa foi concluída.
        
        Returns:
            True se a tarefa foi concluída com sucesso
        """
        return self.status == 'completed'
    
    def is_failed(self) -> bool:
        """Verificar se a tarefa falhou.
        
        Returns:
            True se a tarefa falhou
        """
        return self.status == 'failed'
    
    def to_dict(self) -> Dict[str, Any]:
        """Converter modelo para dicionário.
        
        Returns:
            Dicionário com os dados da tarefa
        """
        return {
            'id': self.id,
            'name': self.name,
            'url': self.url,
            'status': self.status,
            'config': self.get_config(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'items_processed': self.items_processed,
            'error_message': self.error_message,
            'duration': self.get_duration()
        }
    
    def __repr__(self) -> str:
        """Representação string do modelo."""
        return f'<ScrapingTask {self.id}: {self.name} ({self.status})>'