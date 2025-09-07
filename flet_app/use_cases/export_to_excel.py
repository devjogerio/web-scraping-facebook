"""Use case para exportação para Excel - Versão Flet.

Este módulo implementa a lógica de negócio para exportação
de dados extraídos para arquivos Excel.
"""

import threading
from typing import Optional, Callable, Dict, Any
from datetime import datetime

from flet_app.models.scraping_task import ScrapingTask
from flet_app.models.export_job import ExportJob
from flet_app.repositories.scraping_task_repository import ScrapingTaskRepository
from flet_app.repositories.facebook_data_repository import FacebookDataRepository
from flet_app.repositories.export_job_repository import ExportJobRepository
from flet_app.services.excel_service import ExcelService
from flet_app.config.logging_config import get_logger


class ExportToExcelUseCase:
    """Use case para exportação para Excel.
    
    Implementa a lógica de negócio para exportação de dados
    extraídos para arquivos Excel formatados.
    """
    
    def __init__(self, task_repository: ScrapingTaskRepository,
                 data_repository: FacebookDataRepository,
                 export_repository: ExportJobRepository,
                 excel_service: ExcelService):
        """Inicializar use case.
        
        Args:
            task_repository: Repositório de tarefas
            data_repository: Repositório de dados
            export_repository: Repositório de jobs de exportação
            excel_service: Serviço de exportação Excel
        """
        self.task_repository = task_repository
        self.data_repository = data_repository
        self.export_repository = export_repository
        self.excel_service = excel_service
        self.logger = get_logger('ExportToExcelUseCase')
        self.active_exports = {}
    
    def export_task_data_async(self, task_id: str,
                              progress_callback: Optional[Callable[[int, str], None]] = None,
                              completion_callback: Optional[Callable[[bool, str, Optional[str]], None]] = None) -> bool:
        """Exportar dados de uma tarefa de forma assíncrona.
        
        Args:
            task_id: ID da tarefa
            progress_callback: Callback para progresso (percentual, mensagem)
            completion_callback: Callback para conclusão (sucesso, mensagem, caminho_arquivo)
            
        Returns:
            True se a exportação foi iniciada com sucesso
        """
        try:
            # Verificar se a tarefa existe
            task = self.task_repository.get_by_id(task_id)
            if not task:
                self.logger.error(f'Tarefa não encontrada: {task_id}')
                if completion_callback:
                    completion_callback(False, 'Tarefa não encontrada', None)
                return False
            
            # Verificar se já existe exportação em andamento
            if task_id in self.active_exports:
                self.logger.warning(f'Exportação já em andamento para tarefa: {task_id}')
                if completion_callback:
                    completion_callback(False, 'Exportação já em andamento', None)
                return False
            
            # Verificar se há dados para exportar
            data_count = len(self.data_repository.get_by_task_id(task_id, limit=1))
            if data_count == 0:
                self.logger.warning(f'Nenhum dado encontrado para exportação: {task_id}')
                if completion_callback:
                    completion_callback(False, 'Nenhum dado encontrado para exportação', None)
                return False
            
            # Criar thread para exportação
            thread = threading.Thread(
                target=self._export_thread,
                args=(task, progress_callback, completion_callback),
                daemon=True
            )
            
            # Registrar exportação ativa
            self.active_exports[task_id] = thread
            
            # Iniciar exportação
            thread.start()
            
            self.logger.info(f'Exportação iniciada para tarefa: {task_id}')
            return True
            
        except Exception as e:
            self.logger.error(f'Erro ao iniciar exportação: {str(e)}')
            if completion_callback:
                completion_callback(False, f'Erro interno: {str(e)}', None)
            return False
    
    def _export_thread(self, task: ScrapingTask,
                      progress_callback: Optional[Callable[[int, str], None]],
                      completion_callback: Optional[Callable[[bool, str, Optional[str]], None]]) -> None:
        """Thread de execução da exportação.
        
        Args:
            task: Tarefa a ser exportada
            progress_callback: Callback de progresso
            completion_callback: Callback de conclusão
        """
        export_job = None
        
        try:
            if progress_callback:
                progress_callback(0, 'Preparando exportação...')
            
            # Gerar nome do arquivo
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'{task.name}_{timestamp}.xlsx'
            file_path = f'exports/{filename}'
            
            # Criar job de exportação
            export_job = ExportJob(
                task_id=task.id,
                filename=filename,
                file_path=file_path
            )
            export_job = self.export_repository.create(export_job)
            
            # Marcar job como em processamento
            self.export_repository.update_job_status(export_job.id, 'processing')
            
            if progress_callback:
                progress_callback(10, 'Carregando dados...')
            
            # Buscar todos os dados da tarefa
            data_list = self.data_repository.get_data_for_export(task.id)
            
            if not data_list:
                raise Exception('Nenhum dado encontrado para exportação')
            
            if progress_callback:
                progress_callback(30, f'Exportando {len(data_list)} itens...')
            
            # Obter configurações da tarefa
            task_config = task.get_config()
            task_config['url'] = task.url
            
            # Executar exportação
            filename, full_path, file_size = self.excel_service.export_task_data(
                task_name=task.name,
                data_list=data_list,
                task_config=task_config
            )
            
            if progress_callback:
                progress_callback(90, 'Finalizando exportação...')
            
            # Atualizar job como concluído
            export_job.file_path = full_path
            export_job.filename = filename
            self.export_repository.update_job_status(export_job.id, 'completed', file_size)
            
            if progress_callback:
                progress_callback(100, 'Exportação concluída!')
            
            success_message = f'Arquivo exportado com sucesso: {filename}'
            self.logger.info(f'Exportação concluída para tarefa {task.id}: {filename}')
            
            if completion_callback:
                completion_callback(True, success_message, full_path)
            
        except Exception as e:
            error_message = f'Erro durante exportação: {str(e)}'
            self.logger.error(f'Erro na exportação da tarefa {task.id}: {str(e)}')
            
            # Marcar job como falhado
            if export_job:
                self.export_repository.update_job_status(export_job.id, 'failed')
            
            if completion_callback:
                completion_callback(False, error_message, None)
        
        finally:
            # Limpar exportação ativa
            self.active_exports.pop(task.id, None)
    
    def get_export_history(self, task_id: Optional[str] = None, limit: int = 10) -> list[ExportJob]:
        """Obter histórico de exportações.
        
        Args:
            task_id: ID da tarefa (opcional)
            limit: Limite de resultados
            
        Returns:
            Lista de jobs de exportação
        """
        try:
            if task_id:
                return self.export_repository.get_by_task_id(task_id, limit)
            else:
                return self.export_repository.get_recent_jobs(limit)
        except Exception as e:
            self.logger.error(f'Erro ao obter histórico de exportações: {str(e)}')
            return []
    
    def get_latest_export_for_task(self, task_id: str) -> Optional[ExportJob]:
        """Obter a exportação mais recente de uma tarefa.
        
        Args:
            task_id: ID da tarefa
            
        Returns:
            Job de exportação mais recente ou None
        """
        try:
            return self.export_repository.get_latest_export_for_task(task_id)
        except Exception as e:
            self.logger.error(f'Erro ao obter exportação mais recente: {str(e)}')
            return None
    
    def is_export_running(self, task_id: str) -> bool:
        """Verificar se uma exportação está em andamento.
        
        Args:
            task_id: ID da tarefa
            
        Returns:
            True se a exportação está em andamento
        """
        return task_id in self.active_exports and self.active_exports[task_id].is_alive()
    
    def get_running_exports(self) -> list[str]:
        """Obter lista de exportações em andamento.
        
        Returns:
            Lista de IDs das tarefas com exportação em andamento
        """
        running_exports = []
        
        # Limpar threads mortas
        dead_threads = []
        for task_id, thread in self.active_exports.items():
            if thread.is_alive():
                running_exports.append(task_id)
            else:
                dead_threads.append(task_id)
        
        # Remover threads mortas
        for task_id in dead_threads:
            self.active_exports.pop(task_id, None)
        
        return running_exports
    
    def validate_task_for_export(self, task_id: str) -> tuple[bool, str]:
        """Validar se uma tarefa pode ser exportada.
        
        Args:
            task_id: ID da tarefa
            
        Returns:
            Tupla (pode_exportar, mensagem)
        """
        try:
            # Verificar se a tarefa existe
            task = self.task_repository.get_by_id(task_id)
            if not task:
                return False, 'Tarefa não encontrada'
            
            # Verificar se já está exportando
            if self.is_export_running(task_id):
                return False, 'Exportação já em andamento'
            
            # Verificar se há dados para exportar
            data_count = len(self.data_repository.get_by_task_id(task_id, limit=1))
            if data_count == 0:
                return False, 'Nenhum dado encontrado para exportação'
            
            # Verificar diretório de exportação
            if not self.excel_service.validate_export_directory():
                return False, 'Diretório de exportação não acessível'
            
            return True, 'Tarefa pode ser exportada'
            
        except Exception as e:
            self.logger.error(f'Erro ao validar tarefa para exportação {task_id}: {str(e)}')
            return False, f'Erro interno: {str(e)}'
    
    def get_export_statistics(self) -> Dict[str, Any]:
        """Obter estatísticas de exportação.
        
        Returns:
            Dicionário com estatísticas
        """
        try:
            running_exports = self.get_running_exports()
            export_stats = self.export_repository.get_export_statistics()
            
            return {
                'running_exports_count': len(running_exports),
                'running_export_task_ids': running_exports,
                'export_statistics': export_stats,
                'export_directory': self.excel_service.get_export_directory()
            }
            
        except Exception as e:
            self.logger.error(f'Erro ao obter estatísticas de exportação: {str(e)}')
            return {
                'error': f'Erro interno: {str(e)}',
                'running_exports_count': 0,
                'running_export_task_ids': []
            }
    
    def cleanup_old_exports(self, days: int = 30) -> int:
        """Limpar exportações antigas.
        
        Args:
            days: Número de dias para considerar como antigo
            
        Returns:
            Número de exportações removidas
        """
        try:
            # Limpar jobs falhados antigos do banco
            cleaned_jobs = self.export_repository.cleanup_old_failed_jobs(days)
            
            # Limpar threads mortas
            dead_threads = []
            for task_id, thread in self.active_exports.items():
                if not thread.is_alive():
                    dead_threads.append(task_id)
            
            for task_id in dead_threads:
                self.active_exports.pop(task_id, None)
            
            total_cleaned = cleaned_jobs + len(dead_threads)
            
            if total_cleaned > 0:
                self.logger.info(f'Limpeza de exportações concluída: {total_cleaned} itens removidos')
            
            return total_cleaned
            
        except Exception as e:
            self.logger.error(f'Erro durante limpeza de exportações: {str(e)}')
            return 0
    
    def get_exported_files_list(self) -> list[Dict[str, Any]]:
        """Obter lista de arquivos exportados.
        
        Returns:
            Lista de informações dos arquivos exportados
        """
        try:
            return self.excel_service.list_exported_files()
        except Exception as e:
            self.logger.error(f'Erro ao listar arquivos exportados: {str(e)}')
            return []
    
    def create_sample_export(self) -> tuple[bool, str, Optional[str]]:
        """Criar arquivo de exemplo para demonstração.
        
        Returns:
            Tupla (sucesso, mensagem, caminho_arquivo)
        """
        try:
            file_path = self.excel_service.create_template_file('exemplo_exportacao.xlsx')
            
            success_message = 'Arquivo de exemplo criado com sucesso'
            self.logger.info(f'Arquivo de exemplo criado: {file_path}')
            
            return True, success_message, file_path
            
        except Exception as e:
            error_message = f'Erro ao criar arquivo de exemplo: {str(e)}'
            self.logger.error(error_message)
            return False, error_message, None
    
    def get_task_export_summary(self, task_id: str) -> Dict[str, Any]:
        """Obter resumo de exportações de uma tarefa.
        
        Args:
            task_id: ID da tarefa
            
        Returns:
            Dicionário com resumo das exportações
        """
        try:
            task = self.task_repository.get_by_id(task_id)
            if not task:
                return {'error': 'Tarefa não encontrada'}
            
            exports = self.export_repository.get_by_task_id(task_id)
            successful_exports = self.export_repository.get_successful_exports_for_task(task_id)
            latest_export = self.export_repository.get_latest_export_for_task(task_id)
            data_count = len(self.data_repository.get_by_task_id(task_id, limit=1))
            
            return {
                'task_id': task_id,
                'task_name': task.name,
                'data_available': data_count > 0,
                'data_count': data_count,
                'total_exports': len(exports),
                'successful_exports': len(successful_exports),
                'latest_export': latest_export.to_dict() if latest_export else None,
                'is_export_running': self.is_export_running(task_id),
                'can_export': self.validate_task_for_export(task_id)[0]
            }
            
        except Exception as e:
            self.logger.error(f'Erro ao obter resumo de exportações da tarefa {task_id}: {str(e)}')
            return {'error': f'Erro interno: {str(e)}'}