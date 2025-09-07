"""Controller do dashboard principal.

Este módulo implementa as rotas e lógica de controle
para o dashboard da aplicação.
"""

import logging
from flask import Blueprint, render_template, jsonify, request
from typing import Dict, Any

from app.repositories.scraping_task_repository import ScrapingTaskRepository
from app.repositories.facebook_data_repository import FacebookDataRepository
from app.repositories.export_job_repository import ExportJobRepository


class DashboardController:
    """Controller para o dashboard principal.
    
    Gerencia as rotas relacionadas ao painel de controle
    e estatísticas da aplicação.
    """
    
    def __init__(self, task_repository: ScrapingTaskRepository,
                 data_repository: FacebookDataRepository,
                 export_repository: ExportJobRepository):
        """Inicializar controller do dashboard.
        
        Args:
            task_repository: Repositório de tarefas
            data_repository: Repositório de dados
            export_repository: Repositório de exportações
        """
        self.task_repository = task_repository
        self.data_repository = data_repository
        self.export_repository = export_repository
        self.logger = logging.getLogger(__name__)
        
        # Criar blueprint
        self.blueprint = Blueprint('dashboard', __name__)
        self._register_routes()
    
    def _register_routes(self) -> None:
        """Registrar rotas do blueprint."""
        self.blueprint.add_url_rule('/', 'index', self.index, methods=['GET'])
        self.blueprint.add_url_rule('/dashboard', 'dashboard', self.dashboard, methods=['GET'])
        self.blueprint.add_url_rule('/api/dashboard/stats', 'api_stats', self.api_stats, methods=['GET'])
        self.blueprint.add_url_rule('/api/dashboard/recent-activity', 'api_recent_activity', 
                                   self.api_recent_activity, methods=['GET'])
    
    def index(self):
        """Página inicial - redireciona para dashboard.
        
        Returns:
            Template renderizado ou redirecionamento
        """
        try:
            # Obter estatísticas básicas
            stats = self._get_dashboard_stats()
            
            # Obter tarefas recentes
            recent_tasks = self.task_repository.get_recent_tasks(days=7, limit=5)
            
            return render_template('dashboard/index.html', 
                                 stats=stats,
                                 recent_tasks=[task.to_dict() for task in recent_tasks])
            
        except Exception as e:
            self.logger.error(f"Erro na página inicial: {str(e)}")
            return render_template('error.html', 
                                 error="Erro ao carregar dashboard"), 500
    
    def dashboard(self):
        """Página do dashboard completo.
        
        Returns:
            Template renderizado
        """
        try:
            # Obter estatísticas completas
            stats = self._get_dashboard_stats()
            
            # Obter tarefas por status
            pending_tasks = self.task_repository.get_pending_tasks(limit=10)
            active_tasks = self.task_repository.get_active_tasks()
            completed_tasks = self.task_repository.get_completed_tasks(limit=10)
            failed_tasks = self.task_repository.get_failed_tasks(limit=5)
            
            # Obter exportações recentes
            recent_exports = self.export_repository.get_recent_exports(days=7, limit=5)
            
            return render_template('dashboard/dashboard.html',
                                 stats=stats,
                                 pending_tasks=[task.to_dict() for task in pending_tasks],
                                 active_tasks=[task.to_dict() for task in active_tasks],
                                 completed_tasks=[task.to_dict() for task in completed_tasks],
                                 failed_tasks=[task.to_dict() for task in failed_tasks],
                                 recent_exports=[export.to_dict() for export in recent_exports])
            
        except Exception as e:
            self.logger.error(f"Erro no dashboard: {str(e)}")
            return render_template('error.html', 
                                 error="Erro ao carregar dashboard completo"), 500
    
    def api_stats(self):
        """API para obter estatísticas do dashboard.
        
        Returns:
            JSON com estatísticas
        """
        try:
            stats = self._get_dashboard_stats()
            return jsonify({
                'success': True,
                'data': stats
            })
            
        except Exception as e:
            self.logger.error(f"Erro na API de estatísticas: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    def api_recent_activity(self):
        """API para obter atividade recente.
        
        Returns:
            JSON com atividade recente
        """
        try:
            # Parâmetros da query
            limit = request.args.get('limit', 10, type=int)
            days = request.args.get('days', 7, type=int)
            
            # Obter atividades recentes
            recent_tasks = self.task_repository.get_recent_tasks(days=days, limit=limit)
            recent_exports = self.export_repository.get_recent_exports(days=days, limit=limit)
            
            # Combinar e ordenar por data
            activities = []
            
            for task in recent_tasks:
                activities.append({
                    'type': 'task',
                    'id': task.id,
                    'title': task.name,
                    'status': task.status,
                    'created_at': task.created_at.isoformat() if task.created_at else None,
                    'url': f'/task/{task.id}'
                })
            
            for export in recent_exports:
                activities.append({
                    'type': 'export',
                    'id': export.id,
                    'title': export.filename,
                    'status': export.status,
                    'created_at': export.created_at.isoformat() if export.created_at else None,
                    'url': f'/export/{export.id}'
                })
            
            # Ordenar por data (mais recente primeiro)
            activities.sort(key=lambda x: x['created_at'] or '', reverse=True)
            
            return jsonify({
                'success': True,
                'data': activities[:limit]
            })
            
        except Exception as e:
            self.logger.error(f"Erro na API de atividade recente: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    def _get_dashboard_stats(self) -> Dict[str, Any]:
        """Obter estatísticas para o dashboard.
        
        Returns:
            Dicionário com estatísticas
        """
        try:
            # Estatísticas de tarefas
            task_stats = self.task_repository.get_statistics()
            
            # Estatísticas de dados
            total_data = self.data_repository.count()
            
            # Estatísticas de exportações
            export_stats = self.export_repository.get_statistics()
            
            # Tarefas mais produtivas
            top_tasks = self.task_repository.get_most_processed_tasks(limit=5)
            
            return {
                'tasks': {
                    'total': task_stats['total'],
                    'pending': task_stats['pending'],
                    'running': task_stats['running'],
                    'completed': task_stats['completed'],
                    'failed': task_stats['failed'],
                    'success_rate': task_stats['success_rate']
                },
                'data': {
                    'total_extracted': total_data,
                    'avg_per_task': total_data / task_stats['total'] if task_stats['total'] > 0 else 0
                },
                'exports': {
                    'total': export_stats['total'],
                    'completed': export_stats['completed'],
                    'total_size_mb': export_stats['total_file_size_mb'],
                    'avg_duration': export_stats['average_duration_seconds']
                },
                'top_tasks': [
                    {
                        'name': task.name,
                        'items_processed': task.items_processed,
                        'status': task.status
                    } for task in top_tasks
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao obter estatísticas: {str(e)}")
            return {
                'tasks': {'total': 0, 'pending': 0, 'running': 0, 'completed': 0, 'failed': 0, 'success_rate': 0},
                'data': {'total_extracted': 0, 'avg_per_task': 0},
                'exports': {'total': 0, 'completed': 0, 'total_size_mb': 0, 'avg_duration': 0},
                'top_tasks': []
            }
    
    def get_blueprint(self) -> Blueprint:
        """Obter blueprint do controller.
        
        Returns:
            Blueprint configurado
        """
        return self.blueprint