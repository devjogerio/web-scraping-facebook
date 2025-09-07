"""Repositório para jobs de exportação - Versão Flet.

Este módulo implementa operações específicas de banco de dados
para o modelo ExportJob.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from flet_app.models.export_job import ExportJob
from flet_app.repositories.base_repository import BaseRepository


class ExportJobRepository(BaseRepository[ExportJob]):
    """Repositório para operações com jobs de exportação.
    
    Implementa operações específicas para gerenciar jobs
    de exportação de dados para Excel.
    """
    
    def __init__(self, db_session: Session):
        """Inicializar repositório de jobs de exportação.
        
        Args:
            db_session: Sessão do banco de dados
        """
        super().__init__(ExportJob, db_session)
    
    def get_by_task_id(self, task_id: str, limit: Optional[int] = None) -> List[ExportJob]:
        """Buscar jobs de exportação por ID da tarefa.
        
        Args:
            task_id: ID da tarefa de scraping
            limit: Limite de resultados
            
        Returns:
            Lista de jobs de exportação da tarefa
        """
        try:
            query = self.db_session.query(ExportJob)
            query = query.filter(ExportJob.task_id == task_id)
            query = query.order_by(desc(ExportJob.created_at))
            
            if limit:
                query = query.limit(limit)
            
            results = query.all()
            self.logger.debug(f'Encontrados {len(results)} jobs de exportação para tarefa {task_id}')
            return results
        except Exception as e:
            self.logger.error(f'Erro ao buscar jobs de exportação da tarefa {task_id}: {str(e)}')
            return []
    
    def get_by_status(self, status: str, limit: Optional[int] = None) -> List[ExportJob]:
        """Buscar jobs por status.
        
        Args:
            status: Status dos jobs (pending, processing, completed, failed)
            limit: Limite de resultados
            
        Returns:
            Lista de jobs com o status especificado
        """
        try:
            query = self.db_session.query(ExportJob).filter(ExportJob.status == status)
            query = query.order_by(desc(ExportJob.created_at))
            
            if limit:
                query = query.limit(limit)
            
            results = query.all()
            self.logger.debug(f'Encontrados {len(results)} jobs com status {status}')
            return results
        except Exception as e:
            self.logger.error(f'Erro ao buscar jobs por status {status}: {str(e)}')
            return []
    
    def get_pending_jobs(self) -> List[ExportJob]:
        """Buscar jobs pendentes.
        
        Returns:
            Lista de jobs pendentes
        """
        return self.get_by_status('pending')
    
    def get_processing_jobs(self) -> List[ExportJob]:
        """Buscar jobs em processamento.
        
        Returns:
            Lista de jobs em processamento
        """
        return self.get_by_status('processing')
    
    def get_completed_jobs(self, limit: Optional[int] = 10) -> List[ExportJob]:
        """Buscar jobs concluídos.
        
        Args:
            limit: Limite de resultados
            
        Returns:
            Lista de jobs concluídos
        """
        return self.get_by_status('completed', limit)
    
    def get_failed_jobs(self, limit: Optional[int] = 10) -> List[ExportJob]:
        """Buscar jobs que falharam.
        
        Args:
            limit: Limite de resultados
            
        Returns:
            Lista de jobs que falharam
        """
        return self.get_by_status('failed', limit)
    
    def get_recent_jobs(self, limit: int = 10) -> List[ExportJob]:
        """Buscar jobs mais recentes.
        
        Args:
            limit: Número máximo de jobs
            
        Returns:
            Lista dos jobs mais recentes
        """
        try:
            query = self.db_session.query(ExportJob)
            query = query.order_by(desc(ExportJob.created_at))
            query = query.limit(limit)
            
            results = query.all()
            self.logger.debug(f'Encontrados {len(results)} jobs recentes')
            return results
        except Exception as e:
            self.logger.error(f'Erro ao buscar jobs recentes: {str(e)}')
            return []
    
    def get_latest_export_for_task(self, task_id: str) -> Optional[ExportJob]:
        """Buscar a exportação mais recente de uma tarefa.
        
        Args:
            task_id: ID da tarefa
            
        Returns:
            Job de exportação mais recente ou None
        """
        try:
            job = (
                self.db_session.query(ExportJob)
                .filter(ExportJob.task_id == task_id)
                .order_by(desc(ExportJob.created_at))
                .first()
            )
            
            if job:
                self.logger.debug(f'Encontrada exportação mais recente para tarefa {task_id}: {job.id}')
            else:
                self.logger.debug(f'Nenhuma exportação encontrada para tarefa {task_id}')
            
            return job
        except Exception as e:
            self.logger.error(f'Erro ao buscar exportação mais recente da tarefa {task_id}: {str(e)}')
            return None
    
    def get_successful_exports_for_task(self, task_id: str) -> List[ExportJob]:
        """Buscar exportações bem-sucedidas de uma tarefa.
        
        Args:
            task_id: ID da tarefa
            
        Returns:
            Lista de exportações concluídas com sucesso
        """
        try:
            query = self.db_session.query(ExportJob)
            query = query.filter(
                ExportJob.task_id == task_id,
                ExportJob.status == 'completed'
            )
            query = query.order_by(desc(ExportJob.created_at))
            
            results = query.all()
            self.logger.debug(f'Encontradas {len(results)} exportações bem-sucedidas para tarefa {task_id}')
            return results
        except Exception as e:
            self.logger.error(f'Erro ao buscar exportações bem-sucedidas da tarefa {task_id}: {str(e)}')
            return []
    
    def search_by_filename(self, filename: str) -> List[ExportJob]:
        """Buscar jobs por nome de arquivo.
        
        Args:
            filename: Nome do arquivo ou parte dele
            
        Returns:
            Lista de jobs que contêm o nome especificado
        """
        try:
            query = self.db_session.query(ExportJob)
            query = query.filter(ExportJob.filename.ilike(f'%{filename}%'))
            query = query.order_by(desc(ExportJob.created_at))
            
            results = query.all()
            self.logger.debug(f'Encontrados {len(results)} jobs com filename contendo "{filename}"')
            return results
        except Exception as e:
            self.logger.error(f'Erro ao buscar jobs por filename "{filename}": {str(e)}')
            return []
    
    def get_export_statistics(self) -> dict:
        """Obter estatísticas dos jobs de exportação.
        
        Returns:
            Dicionário com estatísticas dos jobs
        """
        try:
            stats = {
                'total': self.count(),
                'pending': len(self.get_by_status('pending')),
                'processing': len(self.get_by_status('processing')),
                'completed': len(self.get_by_status('completed')),
                'failed': len(self.get_by_status('failed'))
            }
            
            # Calcular tamanho total dos arquivos
            completed_jobs = self.get_by_status('completed')
            total_size = sum(job.file_size or 0 for job in completed_jobs)
            stats['total_file_size'] = total_size
            
            self.logger.debug(f'Estatísticas dos jobs de exportação: {stats}')
            return stats
        except Exception as e:
            self.logger.error(f'Erro ao obter estatísticas dos jobs: {str(e)}')
            return {
                'total': 0,
                'pending': 0,
                'processing': 0,
                'completed': 0,
                'failed': 0,
                'total_file_size': 0
            }
    
    def update_job_status(self, job_id: str, status: str, file_size: Optional[int] = None) -> bool:
        """Atualizar status de um job.
        
        Args:
            job_id: ID do job
            status: Novo status
            file_size: Tamanho do arquivo (para jobs concluídos)
            
        Returns:
            True se atualizado com sucesso
        """
        try:
            job = self.get_by_id(job_id)
            if not job:
                self.logger.warning(f'Job não encontrado para atualização: {job_id}')
                return False
            
            if status == 'processing':
                job.start_processing()
            elif status == 'completed':
                job.complete_processing(file_size or 0)
            elif status == 'failed':
                job.fail_processing()
            else:
                job.status = status
            
            self.update(job)
            return True
        except Exception as e:
            self.logger.error(f'Erro ao atualizar status do job {job_id}: {str(e)}')
            return False
    
    def cleanup_old_failed_jobs(self, days: int = 7) -> int:
        """Limpar jobs falhados antigos.
        
        Args:
            days: Número de dias para considerar como antigo
            
        Returns:
            Número de jobs removidos
        """
        try:
            from datetime import datetime, timedelta
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            deleted_count = (
                self.db_session.query(ExportJob)
                .filter(
                    ExportJob.status == 'failed',
                    ExportJob.created_at < cutoff_date
                )
                .delete()
            )
            
            self.db_session.commit()
            self.logger.info(f'Removidos {deleted_count} jobs falhados antigos')
            return deleted_count
        except Exception as e:
            self.db_session.rollback()
            self.logger.error(f'Erro ao limpar jobs falhados antigos: {str(e)}')
            return 0