"""Repositório para jobs de exportação.

Este módulo implementa operações específicas de acesso a dados
para a entidade ExportJob.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func
from datetime import datetime, timedelta

from .base_repository import BaseRepository
from app.models.export_job import ExportJob


class ExportJobRepository(BaseRepository[ExportJob]):
    """Repositório para operações com jobs de exportação.
    
    Implementa operações específicas para gerenciar jobs de exportação,
    incluindo busca por status, tarefa e limpeza de arquivos.
    """
    
    def __init__(self, db_session: Session):
        """Inicializar repositório de jobs de exportação.
        
        Args:
            db_session: Sessão do SQLAlchemy
        """
        super().__init__(db_session, ExportJob)
    
    def get_by_task_id(self, task_id: str, limit: Optional[int] = None) -> List[ExportJob]:
        """Buscar jobs por ID da tarefa.
        
        Args:
            task_id: ID da tarefa de scraping
            limit: Limite de registros (opcional)
            
        Returns:
            Lista de jobs da tarefa especificada
        """
        query = self.db_session.query(ExportJob).filter(
            ExportJob.task_id == task_id
        ).order_by(desc(ExportJob.created_at))
        
        if limit:
            query = query.limit(limit)
            
        return query.all()
    
    def get_by_status(self, status: str, limit: Optional[int] = None) -> List[ExportJob]:
        """Buscar jobs por status.
        
        Args:
            status: Status dos jobs (pending, processing, completed, failed)
            limit: Limite de registros (opcional)
            
        Returns:
            Lista de jobs com o status especificado
        """
        query = self.db_session.query(ExportJob).filter(
            ExportJob.status == status
        ).order_by(desc(ExportJob.created_at))
        
        if limit:
            query = query.limit(limit)
            
        return query.all()
    
    def get_pending_jobs(self, limit: Optional[int] = None) -> List[ExportJob]:
        """Buscar jobs pendentes.
        
        Args:
            limit: Limite de registros (opcional)
            
        Returns:
            Lista de jobs pendentes
        """
        return self.get_by_status('pending', limit)
    
    def get_processing_jobs(self) -> List[ExportJob]:
        """Buscar jobs em processamento.
        
        Returns:
            Lista de jobs em processamento
        """
        return self.get_by_status('processing')
    
    def get_completed_jobs(self, limit: Optional[int] = None) -> List[ExportJob]:
        """Buscar jobs concluídos.
        
        Args:
            limit: Limite de registros (opcional)
            
        Returns:
            Lista de jobs concluídos
        """
        return self.get_by_status('completed', limit)
    
    def get_failed_jobs(self, limit: Optional[int] = None) -> List[ExportJob]:
        """Buscar jobs que falharam.
        
        Args:
            limit: Limite de registros (opcional)
            
        Returns:
            Lista de jobs que falharam
        """
        return self.get_by_status('failed', limit)
    
    def get_recent_exports(self, days: int = 7, limit: Optional[int] = None) -> List[ExportJob]:
        """Buscar exportações recentes.
        
        Args:
            days: Número de dias para considerar como recente
            limit: Limite de registros (opcional)
            
        Returns:
            Lista de jobs criados nos últimos dias
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = self.db_session.query(ExportJob).filter(
            ExportJob.created_at >= cutoff_date
        ).order_by(desc(ExportJob.created_at))
        
        if limit:
            query = query.limit(limit)
            
        return query.all()
    
    def get_by_filename(self, filename: str) -> Optional[ExportJob]:
        """Buscar job por nome do arquivo.
        
        Args:
            filename: Nome do arquivo
            
        Returns:
            Job encontrado ou None
        """
        return self.db_session.query(ExportJob).filter(
            ExportJob.filename == filename
        ).first()
    
    def search_by_filename_pattern(self, pattern: str, 
                                   limit: Optional[int] = None) -> List[ExportJob]:
        """Buscar jobs por padrão no nome do arquivo.
        
        Args:
            pattern: Padrão para busca no nome do arquivo
            limit: Limite de registros (opcional)
            
        Returns:
            Lista de jobs que correspondem ao padrão
        """
        query = self.db_session.query(ExportJob).filter(
            ExportJob.filename.ilike(f'%{pattern}%')
        ).order_by(desc(ExportJob.created_at))
        
        if limit:
            query = query.limit(limit)
            
        return query.all()
    
    def get_large_files(self, min_size_mb: float = 10, 
                        limit: Optional[int] = None) -> List[ExportJob]:
        """Buscar arquivos grandes.
        
        Args:
            min_size_mb: Tamanho mínimo em MB
            limit: Limite de registros (opcional)
            
        Returns:
            Lista de jobs com arquivos grandes
        """
        min_size_bytes = int(min_size_mb * 1024 * 1024)
        
        query = self.db_session.query(ExportJob).filter(
            ExportJob.file_size >= min_size_bytes
        ).order_by(desc(ExportJob.file_size))
        
        if limit:
            query = query.limit(limit)
            
        return query.all()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obter estatísticas dos jobs de exportação.
        
        Returns:
            Dicionário com estatísticas dos jobs
        """
        total = self.count()
        pending = len(self.get_by_status('pending'))
        processing = len(self.get_by_status('processing'))
        completed = len(self.get_by_status('completed'))
        failed = len(self.get_by_status('failed'))
        
        # Calcular tamanho total dos arquivos
        total_size = self.db_session.query(
            func.sum(ExportJob.file_size)
        ).filter(
            ExportJob.status == 'completed'
        ).scalar() or 0
        
        # Calcular tempo médio de processamento
        completed_jobs = self.get_completed_jobs()
        avg_duration = 0
        if completed_jobs:
            durations = [job.get_duration() for job in completed_jobs if job.get_duration()]
            if durations:
                avg_duration = sum(durations) / len(durations)
        
        return {
            'total': total,
            'pending': pending,
            'processing': processing,
            'completed': completed,
            'failed': failed,
            'success_rate': (completed / total * 100) if total > 0 else 0,
            'total_file_size_bytes': total_size,
            'total_file_size_mb': total_size / (1024 * 1024) if total_size else 0,
            'average_duration_seconds': avg_duration
        }
    
    def get_jobs_by_date_range(self, start_date: datetime, 
                               end_date: datetime) -> List[ExportJob]:
        """Buscar jobs por intervalo de datas.
        
        Args:
            start_date: Data inicial
            end_date: Data final
            
        Returns:
            Lista de jobs no intervalo especificado
        """
        return self.db_session.query(ExportJob).filter(
            and_(
                ExportJob.created_at >= start_date,
                ExportJob.created_at <= end_date
            )
        ).order_by(desc(ExportJob.created_at)).all()
    
    def get_long_processing_jobs(self, hours: int = 1) -> List[ExportJob]:
        """Buscar jobs processando há muito tempo.
        
        Args:
            hours: Número de horas para considerar como longo processamento
            
        Returns:
            Lista de jobs processando há mais tempo que o especificado
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        return self.db_session.query(ExportJob).filter(
            and_(
                ExportJob.status == 'processing',
                ExportJob.created_at <= cutoff_time
            )
        ).all()
    
    def cleanup_old_jobs(self, days: int = 30, delete_files: bool = True) -> int:
        """Limpar jobs antigos.
        
        Args:
            days: Número de dias para considerar como antigos
            delete_files: Se deve deletar os arquivos físicos
            
        Returns:
            Número de jobs removidos
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        old_jobs = self.db_session.query(ExportJob).filter(
            and_(
                ExportJob.created_at <= cutoff_date,
                ExportJob.status.in_(['completed', 'failed'])
            )
        ).all()
        
        removed_count = 0
        for job in old_jobs:
            if delete_files:
                job.delete_file()
            
            self.delete_entity(job)
            removed_count += 1
        
        return removed_count
    
    def cleanup_orphaned_files(self) -> int:
        """Limpar arquivos órfãos (sem registro no banco).
        
        Returns:
            Número de arquivos removidos
        """
        import os
        from config.config import Config
        
        export_dir = Config.EXPORT_DIR
        if not os.path.exists(export_dir):
            return 0
        
        # Obter todos os caminhos de arquivo do banco
        db_files = set(
            job.file_path for job in self.get_all() 
            if job.file_path
        )
        
        # Verificar arquivos no diretório
        removed_count = 0
        for filename in os.listdir(export_dir):
            file_path = os.path.join(export_dir, filename)
            
            # Se o arquivo não está no banco, remover
            if file_path not in db_files and os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                    removed_count += 1
                except OSError:
                    pass  # Ignorar erros de remoção
        
        return removed_count
    
    def get_download_history(self, limit: int = 50) -> List[ExportJob]:
        """Obter histórico de downloads.
        
        Args:
            limit: Limite de registros
            
        Returns:
            Lista dos jobs mais recentes para histórico
        """
        return self.db_session.query(ExportJob).filter(
            ExportJob.status == 'completed'
        ).order_by(desc(ExportJob.completed_at)).limit(limit).all()
    
    def get_jobs_with_missing_files(self) -> List[ExportJob]:
        """Buscar jobs cujos arquivos não existem mais.
        
        Returns:
            Lista de jobs com arquivos faltando
        """
        completed_jobs = self.get_completed_jobs()
        missing_files = []
        
        for job in completed_jobs:
            if not job.file_exists():
                missing_files.append(job)
        
        return missing_files
    
    def mark_missing_files_as_failed(self) -> int:
        """Marcar jobs com arquivos faltando como falhados.
        
        Returns:
            Número de jobs marcados como falhados
        """
        missing_jobs = self.get_jobs_with_missing_files()
        
        updated_count = 0
        for job in missing_jobs:
            job.fail_export()
            self.update(job)
            updated_count += 1
        
        return updated_count