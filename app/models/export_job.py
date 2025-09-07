"""Modelo de dados para jobs de exportação.

Este módulo define a entidade ExportJob que gerencia a exportação
dos dados extraídos para arquivos Excel.
"""

import uuid
import os
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, CheckConstraint
from app import db


class ExportJob(db.Model):
    """Modelo para jobs de exportação de dados.
    
    Gerencia a exportação dos dados extraídos para arquivos Excel,
    incluindo status, localização e metadados do arquivo.
    """
    
    __tablename__ = 'export_jobs'
    
    # Campos principais
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(
        String(36), 
        ForeignKey('scraping_tasks.id', ondelete='CASCADE'),
        nullable=False,
        comment='ID da tarefa de scraping'
    )
    filename = Column(String(255), nullable=False, comment='Nome do arquivo gerado')
    file_path = Column(String(500), nullable=False, comment='Caminho completo do arquivo')
    status = Column(
        String(20), 
        nullable=False, 
        default='pending',
        comment='Status da exportação'
    )
    file_size = Column(Integer, comment='Tamanho do arquivo em bytes')
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    # Relacionamentos serão definidos após importação de todos os modelos
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            status.in_(['pending', 'processing', 'completed', 'failed']),
            name='check_export_status_values'
        ),
    )
    
    def __init__(self, task_id: str, filename: str, file_path: str):
        """Inicializar novo job de exportação.
        
        Args:
            task_id: ID da tarefa de scraping
            filename: Nome do arquivo a ser gerado
            file_path: Caminho completo onde salvar o arquivo
        """
        self.task_id = task_id
        self.filename = filename
        self.file_path = file_path
        self.status = 'pending'
    
    def start_processing(self) -> None:
        """Marcar exportação como em processamento."""
        self.status = 'processing'
    
    def complete_export(self) -> None:
        """Marcar exportação como concluída.
        
        Calcula automaticamente o tamanho do arquivo se existir.
        """
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
        
        # Calcular tamanho do arquivo
        if os.path.exists(self.file_path):
            self.file_size = os.path.getsize(self.file_path)
    
    def fail_export(self) -> None:
        """Marcar exportação como falhada."""
        self.status = 'failed'
        self.completed_at = datetime.utcnow()
    
    def get_file_size_formatted(self) -> str:
        """Obter tamanho do arquivo formatado.
        
        Returns:
            Tamanho formatado (ex: '1.5 MB')
        """
        if not self.file_size:
            return 'N/A'
        
        # Converter bytes para unidades legíveis
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.file_size < 1024.0:
                return f'{self.file_size:.1f} {unit}'
            self.file_size /= 1024.0
        return f'{self.file_size:.1f} TB'
    
    def file_exists(self) -> bool:
        """Verificar se o arquivo existe no sistema.
        
        Returns:
            True se o arquivo existe
        """
        return os.path.exists(self.file_path)
    
    def get_file_extension(self) -> str:
        """Obter extensão do arquivo.
        
        Returns:
            Extensão do arquivo (ex: '.xlsx')
        """
        return os.path.splitext(self.filename)[1]
    
    def get_file_name_without_extension(self) -> str:
        """Obter nome do arquivo sem extensão.
        
        Returns:
            Nome do arquivo sem extensão
        """
        return os.path.splitext(self.filename)[0]
    
    def is_pending(self) -> bool:
        """Verificar se a exportação está pendente.
        
        Returns:
            True se está pendente
        """
        return self.status == 'pending'
    
    def is_processing(self) -> bool:
        """Verificar se a exportação está em processamento.
        
        Returns:
            True se está processando
        """
        return self.status == 'processing'
    
    def is_completed(self) -> bool:
        """Verificar se a exportação foi concluída.
        
        Returns:
            True se foi concluída
        """
        return self.status == 'completed'
    
    def is_failed(self) -> bool:
        """Verificar se a exportação falhou.
        
        Returns:
            True se falhou
        """
        return self.status == 'failed'
    
    def get_duration(self) -> Optional[float]:
        """Calcular duração da exportação em segundos.
        
        Returns:
            Duração em segundos ou None se não concluída
        """
        if not self.completed_at:
            return None
        
        return (self.completed_at - self.created_at).total_seconds()
    
    def get_download_url(self, base_url: str = '') -> str:
        """Gerar URL para download do arquivo.
        
        Args:
            base_url: URL base da aplicação
            
        Returns:
            URL completa para download
        """
        return f'{base_url}/download/{self.id}'
    
    def delete_file(self) -> bool:
        """Deletar arquivo do sistema de arquivos.
        
        Returns:
            True se deletado com sucesso
        """
        try:
            if self.file_exists():
                os.remove(self.file_path)
                return True
            return False
        except OSError:
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Converter modelo para dicionário.
        
        Returns:
            Dicionário com os dados da exportação
        """
        return {
            'id': self.id,
            'task_id': self.task_id,
            'filename': self.filename,
            'file_path': self.file_path,
            'status': self.status,
            'file_size': self.file_size,
            'file_size_formatted': self.get_file_size_formatted(),
            'file_exists': self.file_exists(),
            'file_extension': self.get_file_extension(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration': self.get_duration(),
            'download_url': self.get_download_url()
        }
    
    @classmethod
    def generate_filename(cls, task_name: str, task_id: str) -> str:
        """Gerar nome de arquivo baseado na tarefa.
        
        Args:
            task_name: Nome da tarefa
            task_id: ID da tarefa
            
        Returns:
            Nome do arquivo gerado
        """
        # Limpar nome da tarefa para uso em arquivo
        clean_name = ''.join(c for c in task_name if c.isalnum() or c in (' ', '-', '_')).strip()
        clean_name = clean_name.replace(' ', '_')
        
        # Adicionar timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        return f'{clean_name}_{task_id[:8]}_{timestamp}.xlsx'
    
    def __repr__(self) -> str:
        """Representação string do modelo."""
        return f'<ExportJob {self.id}: {self.filename} ({self.status})>'