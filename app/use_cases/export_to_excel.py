"""Use case para exportar dados para Excel.

Este módulo implementa a lógica de negócio para exportação
dos dados extraídos para arquivos Excel formatados.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.models.scraping_task import ScrapingTask
from app.models.export_job import ExportJob
from app.repositories.scraping_task_repository import ScrapingTaskRepository
from app.repositories.facebook_data_repository import FacebookDataRepository
from app.repositories.export_job_repository import ExportJobRepository


class ExportToExcelUseCase:
    """Use case para exportar dados para Excel.
    
    Implementa a lógica de negócio para geração de arquivos Excel
    com os dados extraídos, incluindo formatação e organização.
    """
    
    def __init__(self, 
                 task_repository: ScrapingTaskRepository,
                 data_repository: FacebookDataRepository,
                 export_repository: ExportJobRepository,
                 excel_service):
        """Inicializar use case.
        
        Args:
            task_repository: Repositório de tarefas
            data_repository: Repositório de dados
            export_repository: Repositório de jobs de exportação
            excel_service: Serviço de geração de Excel
        """
        self.task_repository = task_repository
        self.data_repository = data_repository
        self.export_repository = export_repository
        self.excel_service = excel_service
        self.logger = logging.getLogger(__name__)
    
    def execute(self, task_id: str, export_options: Optional[Dict[str, Any]] = None) -> ExportJob:
        """Executar exportação para Excel.
        
        Args:
            task_id: ID da tarefa com dados para exportar
            export_options: Opções de exportação personalizadas
            
        Returns:
            Job de exportação criado
            
        Raises:
            ValueError: Se a tarefa não existe ou não tem dados
            RuntimeError: Se ocorre erro durante a exportação
        """
        # Buscar tarefa
        task = self.task_repository.get_by_id(task_id)
        if not task:
            raise ValueError(f"Tarefa {task_id} não encontrada")
        
        # Validar se tem dados para exportar
        self._validate_export_data(task)
        
        # Criar job de exportação
        export_job = self._create_export_job(task)
        
        try:
            # Marcar como processando
            export_job.start_processing()
            self.export_repository.update(export_job)
            
            self.logger.info(f"Iniciando exportação para tarefa {task_id}")
            
            # Executar exportação
            self._perform_export(task, export_job, export_options)
            
            # Marcar como concluída
            export_job.complete_export()
            self.export_repository.update(export_job)
            
            self.logger.info(f"Exportação concluída: {export_job.filename}")
            
            return export_job
            
        except Exception as e:
            # Marcar como falhada
            export_job.fail_export()
            self.export_repository.update(export_job)
            
            error_message = f"Erro na exportação: {str(e)}"
            self.logger.error(error_message)
            
            raise RuntimeError(error_message)
    
    def _validate_export_data(self, task: ScrapingTask) -> None:
        """Validar se a tarefa tem dados para exportar.
        
        Args:
            task: Tarefa a ser validada
            
        Raises:
            ValueError: Se não há dados para exportar
        """
        if not task.is_completed():
            raise ValueError("Tarefa deve estar concluída para exportar")
        
        data_count = len(self.data_repository.get_by_task_id(task.id, limit=1))
        if data_count == 0:
            raise ValueError("Não há dados extraídos para exportar")
    
    def _create_export_job(self, task: ScrapingTask) -> ExportJob:
        """Criar job de exportação.
        
        Args:
            task: Tarefa para exportação
            
        Returns:
            Job de exportação criado
        """
        # Gerar nome do arquivo
        filename = ExportJob.generate_filename(task.name, task.id)
        
        # Definir caminho do arquivo
        export_dir = self._ensure_export_directory()
        file_path = os.path.join(export_dir, filename)
        
        # Criar job
        export_job = ExportJob(
            task_id=task.id,
            filename=filename,
            file_path=file_path
        )
        
        return self.export_repository.create(export_job)
    
    def _ensure_export_directory(self) -> str:
        """Garantir que o diretório de exportação existe.
        
        Returns:
            Caminho do diretório de exportação
        """
        from config.config import Config
        
        export_dir = getattr(Config, 'EXPORT_DIR', 'exports')
        
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)
            self.logger.info(f"Diretório de exportação criado: {export_dir}")
        
        return export_dir
    
    def _perform_export(self, task: ScrapingTask, export_job: ExportJob, 
                       export_options: Optional[Dict[str, Any]]) -> None:
        """Executar o processo de exportação.
        
        Args:
            task: Tarefa com dados para exportar
            export_job: Job de exportação
            export_options: Opções de exportação
        """
        # Buscar todos os dados da tarefa
        all_data = self.data_repository.get_data_for_export(task.id)
        
        if not all_data:
            raise ValueError("Nenhum dado encontrado para exportação")
        
        # Organizar dados por tipo
        organized_data = self._organize_data_by_type(all_data)
        
        # Aplicar opções de exportação
        final_options = self._apply_export_options(export_options)
        
        # Gerar arquivo Excel
        self.excel_service.create_excel_file(
            file_path=export_job.file_path,
            task_info=task.to_dict(),
            organized_data=organized_data,
            options=final_options
        )
        
        # Verificar se arquivo foi criado
        if not os.path.exists(export_job.file_path):
            raise RuntimeError("Arquivo Excel não foi criado")
    
    def _organize_data_by_type(self, data_list: List) -> Dict[str, List[Dict[str, Any]]]:
        """Organizar dados por tipo para planilhas separadas.
        
        Args:
            data_list: Lista de dados extraídos
            
        Returns:
            Dados organizados por tipo
        """
        organized = {
            'posts': [],
            'comments': [],
            'profiles': [],
            'likes': [],
            'shares': [],
            'summary': []
        }
        
        # Separar por tipo
        for data in data_list:
            data_type = data.data_type
            excel_row = data.to_excel_row()
            
            if data_type in organized:
                organized[data_type].append(excel_row)
        
        # Criar resumo
        organized['summary'] = self._create_summary_data(organized)
        
        return organized
    
    def _create_summary_data(self, organized_data: Dict[str, List]) -> List[Dict[str, Any]]:
        """Criar dados de resumo para a planilha.
        
        Args:
            organized_data: Dados organizados por tipo
            
        Returns:
            Lista com dados de resumo
        """
        summary = []
        
        # Estatísticas por tipo
        for data_type, items in organized_data.items():
            if data_type != 'summary' and items:
                summary.append({
                    'Tipo de Dado': data_type.title(),
                    'Quantidade': len(items),
                    'Primeiro Item': items[0].get('Data/Hora', 'N/A') if items else 'N/A',
                    'Último Item': items[-1].get('Data/Hora', 'N/A') if items else 'N/A'
                })
        
        # Totais
        total_items = sum(len(items) for key, items in organized_data.items() 
                         if key != 'summary')
        
        summary.append({
            'Tipo de Dado': 'TOTAL',
            'Quantidade': total_items,
            'Primeiro Item': '',
            'Último Item': ''
        })
        
        return summary
    
    def _apply_export_options(self, export_options: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Aplicar opções de exportação com valores padrão.
        
        Args:
            export_options: Opções fornecidas pelo usuário
            
        Returns:
            Opções finais com padrões aplicados
        """
        default_options = {
            'include_metadata': True,
            'include_summary': True,
            'separate_sheets': True,
            'apply_formatting': True,
            'include_charts': False,
            'max_content_length': 1000,
            'date_format': 'dd/mm/yyyy hh:mm:ss',
            'auto_fit_columns': True,
            'freeze_header_row': True
        }
        
        if export_options:
            final_options = default_options.copy()
            final_options.update(export_options)
            return final_options
        
        return default_options
    
    def get_export_history(self, task_id: Optional[str] = None, 
                          limit: int = 50) -> List[ExportJob]:
        """Obter histórico de exportações.
        
        Args:
            task_id: ID da tarefa (opcional, para filtrar)
            limit: Limite de registros
            
        Returns:
            Lista de jobs de exportação
        """
        if task_id:
            return self.export_repository.get_by_task_id(task_id, limit)
        else:
            return self.export_repository.get_download_history(limit)
    
    def get_export_statistics(self) -> Dict[str, Any]:
        """Obter estatísticas de exportação.
        
        Returns:
            Estatísticas das exportações
        """
        return self.export_repository.get_statistics()
    
    def delete_export(self, export_id: str, delete_file: bool = True) -> bool:
        """Deletar exportação.
        
        Args:
            export_id: ID da exportação
            delete_file: Se deve deletar o arquivo físico
            
        Returns:
            True se deletada com sucesso
        """
        export_job = self.export_repository.get_by_id(export_id)
        if not export_job:
            return False
        
        try:
            # Deletar arquivo se solicitado
            if delete_file:
                export_job.delete_file()
            
            # Deletar registro
            self.export_repository.delete(export_id)
            
            self.logger.info(f"Exportação {export_id} deletada")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao deletar exportação {export_id}: {str(e)}")
            return False
    
    def cleanup_old_exports(self, days: int = 30) -> Dict[str, int]:
        """Limpar exportações antigas.
        
        Args:
            days: Número de dias para considerar como antigas
            
        Returns:
            Estatísticas da limpeza
        """
        # Limpar jobs antigos
        jobs_removed = self.export_repository.cleanup_old_jobs(days, delete_files=True)
        
        # Limpar arquivos órfãos
        orphaned_files = self.export_repository.cleanup_orphaned_files()
        
        self.logger.info(f"Limpeza concluída: {jobs_removed} jobs e {orphaned_files} arquivos órfãos removidos")
        
        return {
            'jobs_removed': jobs_removed,
            'orphaned_files_removed': orphaned_files,
            'total_cleaned': jobs_removed + orphaned_files
        }
    
    def validate_export_file(self, export_id: str) -> Dict[str, Any]:
        """Validar arquivo de exportação.
        
        Args:
            export_id: ID da exportação
            
        Returns:
            Resultado da validação
        """
        export_job = self.export_repository.get_by_id(export_id)
        if not export_job:
            return {'valid': False, 'error': 'Exportação não encontrada'}
        
        # Verificar se arquivo existe
        if not export_job.file_exists():
            return {'valid': False, 'error': 'Arquivo não encontrado'}
        
        # Verificar tamanho do arquivo
        try:
            file_size = os.path.getsize(export_job.file_path)
            if file_size == 0:
                return {'valid': False, 'error': 'Arquivo vazio'}
            
            # Verificar se é um arquivo Excel válido
            if not export_job.filename.endswith('.xlsx'):
                return {'valid': False, 'error': 'Formato de arquivo inválido'}
            
            return {
                'valid': True,
                'file_size': file_size,
                'file_path': export_job.file_path,
                'created_at': export_job.created_at
            }
            
        except Exception as e:
            return {'valid': False, 'error': f'Erro ao validar arquivo: {str(e)}'}