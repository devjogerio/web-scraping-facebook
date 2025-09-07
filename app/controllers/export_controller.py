"""Controller para exportações.

Este módulo implementa as rotas e lógica de controle
para gerenciamento de exportações de dados.
"""

import os
import logging
from flask import Blueprint, render_template, request, jsonify, send_file, flash, redirect, url_for
from typing import Dict, Any

from app.use_cases.export_to_excel import ExportToExcelUseCase
from app.repositories.export_job_repository import ExportJobRepository
from app.repositories.scraping_task_repository import ScrapingTaskRepository


class ExportController:
    """Controller para exportações.
    
    Gerencia as rotas relacionadas à exportação de dados
    e download de arquivos Excel.
    """
    
    def __init__(self, 
                 export_use_case: ExportToExcelUseCase,
                 export_repository: ExportJobRepository,
                 task_repository: ScrapingTaskRepository):
        """Inicializar controller de exportação.
        
        Args:
            export_use_case: Use case para exportação
            export_repository: Repositório de exportações
            task_repository: Repositório de tarefas
        """
        self.export_use_case = export_use_case
        self.export_repository = export_repository
        self.task_repository = task_repository
        self.logger = logging.getLogger(__name__)
        
        # Criar blueprint
        self.blueprint = Blueprint('export', __name__)
        self._register_routes()
    
    def _register_routes(self) -> None:
        """Registrar rotas do blueprint."""
        self.blueprint.add_url_rule('/export/<task_id>', 'export_page', 
                                   self.export_page, methods=['GET', 'POST'])
        self.blueprint.add_url_rule('/download/<export_id>', 'download_file', 
                                   self.download_file, methods=['GET'])
        self.blueprint.add_url_rule('/api/export/create', 'api_create_export', 
                                   self.api_create_export, methods=['POST'])
        self.blueprint.add_url_rule('/api/export/<export_id>/status', 'api_export_status', 
                                   self.api_export_status, methods=['GET'])
        self.blueprint.add_url_rule('/api/export/history', 'api_export_history', 
                                   self.api_export_history, methods=['GET'])
    
    def export_page(self, task_id: str):
        """Página de exportação para uma tarefa.
        
        Args:
            task_id: ID da tarefa
            
        Returns:
            Template renderizado ou redirecionamento
        """
        try:
            # Buscar tarefa
            task = self.task_repository.get_by_id(task_id)
            if not task:
                flash('Tarefa não encontrada', 'error')
                return redirect(url_for('dashboard.dashboard'))
            
            if request.method == 'GET':
                # Obter histórico de exportações da tarefa
                export_history = self.export_repository.get_by_task_id(task_id)
                
                return render_template('export/export_page.html',
                                     task=task.to_dict(),
                                     export_history=[export.to_dict() for export in export_history])
            
            # POST - Criar nova exportação
            export_options = self._extract_export_options_from_form(request.form)
            
            # Criar exportação
            export_job = self.export_use_case.execute(task_id, export_options)
            
            flash(f'Exportação "{export_job.filename}" criada com sucesso!', 'success')
            return redirect(url_for('export.export_page', task_id=task_id))
            
        except ValueError as e:
            flash(str(e), 'error')
            return redirect(url_for('scraping.task_detail', task_id=task_id))
        
        except Exception as e:
            self.logger.error(f"Erro na exportação da tarefa {task_id}: {str(e)}")
            flash('Erro interno ao criar exportação', 'error')
            return redirect(url_for('scraping.task_detail', task_id=task_id))
    
    def download_file(self, export_id: str):
        """Download de arquivo de exportação.
        
        Args:
            export_id: ID da exportação
            
        Returns:
            Arquivo para download ou erro
        """
        try:
            # Buscar exportação
            export_job = self.export_repository.get_by_id(export_id)
            if not export_job:
                flash('Exportação não encontrada', 'error')
                return redirect(url_for('dashboard.dashboard'))
            
            # Verificar se arquivo existe
            if not export_job.file_exists():
                flash('Arquivo não encontrado no servidor', 'error')
                return redirect(url_for('dashboard.dashboard'))
            
            # Verificar se exportação foi concluída
            if not export_job.is_completed():
                flash('Exportação ainda não foi concluída', 'warning')
                return redirect(url_for('dashboard.dashboard'))
            
            # Enviar arquivo
            return send_file(
                export_job.file_path,
                as_attachment=True,
                download_name=export_job.filename,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            
        except Exception as e:
            self.logger.error(f"Erro no download da exportação {export_id}: {str(e)}")
            flash('Erro ao fazer download do arquivo', 'error')
            return redirect(url_for('dashboard.dashboard'))
    
    def api_create_export(self):
        """API para criar nova exportação.
        
        Returns:
            JSON com resultado
        """
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'Dados JSON são obrigatórios'
                }), 400
            
            task_id = data.get('task_id')
            if not task_id:
                return jsonify({
                    'success': False,
                    'error': 'task_id é obrigatório'
                }), 400
            
            export_options = data.get('options', {})
            
            # Criar exportação
            export_job = self.export_use_case.execute(task_id, export_options)
            
            return jsonify({
                'success': True,
                'message': 'Exportação criada com sucesso',
                'data': export_job.to_dict()
            })
            
        except ValueError as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400
        
        except Exception as e:
            self.logger.error(f"Erro na API de criação de exportação: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Erro interno do servidor'
            }), 500
    
    def api_export_status(self, export_id: str):
        """API para obter status da exportação.
        
        Args:
            export_id: ID da exportação
            
        Returns:
            JSON com status
        """
        try:
            export_job = self.export_repository.get_by_id(export_id)
            if not export_job:
                return jsonify({
                    'success': False,
                    'error': 'Exportação não encontrada'
                }), 404
            
            return jsonify({
                'success': True,
                'data': export_job.to_dict()
            })
            
        except Exception as e:
            self.logger.error(f"Erro ao obter status da exportação {export_id}: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Erro interno do servidor'
            }), 500
    
    def api_export_history(self):
        """API para obter histórico de exportações.
        
        Returns:
            JSON com histórico
        """
        try:
            # Parâmetros da query
            task_id = request.args.get('task_id')
            limit = request.args.get('limit', 50, type=int)
            
            # Obter histórico
            if task_id:
                exports = self.export_repository.get_by_task_id(task_id, limit)
            else:
                exports = self.export_repository.get_download_history(limit)
            
            return jsonify({
                'success': True,
                'data': [export.to_dict() for export in exports]
            })
            
        except Exception as e:
            self.logger.error(f"Erro ao obter histórico de exportações: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Erro interno do servidor'
            }), 500
    
    def _extract_export_options_from_form(self, form_data) -> Dict[str, Any]:
        """Extrair opções de exportação do formulário.
        
        Args:
            form_data: Dados do formulário
            
        Returns:
            Dicionário com opções
        """
        options = {}
        
        # Opções booleanas
        boolean_options = [
            'include_metadata', 'include_summary', 'separate_sheets',
            'apply_formatting', 'include_charts', 'auto_fit_columns',
            'freeze_header_row'
        ]
        
        for option in boolean_options:
            if form_data.get(option):
                options[option] = True
            else:
                options[option] = False
        
        # Limite de conteúdo
        max_content_length = form_data.get('max_content_length', type=int)
        if max_content_length and max_content_length > 0:
            options['max_content_length'] = max_content_length
        
        # Formato de data
        date_format = form_data.get('date_format')
        if date_format:
            options['date_format'] = date_format
        
        return options
    
    def get_blueprint(self) -> Blueprint:
        """Obter blueprint do controller.
        
        Returns:
            Blueprint configurado
        """
        return self.blueprint