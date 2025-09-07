"""Modelo de dados para jobs de exportação - Versão Flet.

Este módulo define a entidade ExportJob que gerencia
os processos de exportação de dados para Excel.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, CheckConstraint
from flet_app.config.database import Base


class ExportJob(Base):
    """Modelo para jobs de exportação.
    
    Representa um processo de exportação de dados
    extraídos para arquivo Excel.
    """
    
    __tablename__ = 'export_jobs'
    
    # Campos principais
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String(36), ForeignKey('scraping_tasks.id', ondelete='CASCADE'), nullable=False)
    filename = Column(String(255), nullable=False, comment='Nome do arquivo gerado')
    file_path = Column(String(500), nullable=False, comment='Caminho completo do arquivo')
    status = Column(
        String(20), 
        nullable=False, 
        default='pending',
        comment='Status do job de exportação'
    )
    file_size = Column(Integer, nullable=True, comment='Tamanho do arquivo em bytes')
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            status.in_(['pending', 'processing', 'completed', 'failed']),
            name='check_export_status_values'
        ),
    )
    
    def __init__(self, task_id: str, filename: str, file_path: str):
        """Inicializar job de exportação.
        
        Args:
            task_id: ID da tarefa de scraping
            filename: Nome do arquivo
            file_path: Caminho completo do arquivo
        """
        self.task_id = task_id
        self.filename = filename
        self.file_path = file_path
        self.status = 'pending'
    
    def start_processing(self) -> None:
        """Marcar job como em processamento."""
        self.status = 'processing'
    
    def complete_processing(self, file_size: int) -> None:
        """Marcar job como concluído.
        
        Args:
            file_size: Tamanho do arquivo gerado em bytes
        """
        self.status = 'completed'
        self.file_size = file_size
        self.completed_at = datetime.utcnow()
    
    def fail_processing(self) -> None:
        """Marcar job como falhado."""
        self.status = 'failed'
        self.completed_at = datetime.utcnow()
    
    def is_completed(self) -> bool:
        """Verificar se o job foi concluído.
        
        Returns:
            True se o job foi concluído com sucesso
        """
        return self.status == 'completed'
    
    def is_failed(self) -> bool:
        """Verificar se o job falhou.
        
        Returns:
            True se o job falhou
        """
        return self.status == 'failed'
    
    def is_processing(self) -> bool:
        """Verificar se o job está em processamento.
        
        Returns:
            True se o job está sendo processado
        """
        return self.status == 'processing'
    
    def get_file_size_formatted(self) -> str:
        """Obter tamanho do arquivo formatado.
        
        Returns:
            Tamanho formatado (ex: "1.5 MB")
        """
        if not self.file_size:
            return 'N/A'
        
        # Converter bytes para unidades maiores
        if self.file_size < 1024:
            return f'{self.file_size} B'
        elif self.file_size < 1024 * 1024:
            return f'{self.file_size / 1024:.1f} KB'
        elif self.file_size < 1024 * 1024 * 1024:
            return f'{self.file_size / (1024 * 1024):.1f} MB'
        else:
            return f'{self.file_size / (1024 * 1024 * 1024):.1f} GB'
    
    def get_duration(self) -> Optional[float]:
        """Calcular duração do processamento em segundos.
        
        Returns:
            Duração em segundos ou None se não concluído
        """
        if not self.completed_at:
            return None
        
        return (self.completed_at - self.created_at).total_seconds()
    
    def get_status_display(self) -> str:
        """Obter status formatado para exibição.
        
        Returns:
            Status formatado em português
        """
        status_map = {
            'pending': 'Pendente',
            'processing': 'Processando',
            'completed': 'Concluído',
            'failed': 'Falhou'
        }
        return status_map.get(self.status, self.status)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converter modelo para dicionário.
        
        Returns:
            Dicionário com os dados do job
        """
        return {
            'id': self.id,
            'task_id': self.task_id,
            'filename': self.filename,
            'file_path': self.file_path,
            'status': self.status,
            'status_display': self.get_status_display(),
            'file_size': self.file_size,
            'file_size_formatted': self.get_file_size_formatted(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration': self.get_duration()
        }
    
    def __repr__(self) -> str:
        """Representação string do modelo."""
        return f'<ExportJob {self.id}: {self.filename} ({self.status})>'