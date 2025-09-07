"""Controller para operações de scraping."""

import logging
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash


class ScrapingController:
    """Controller para operações de scraping."""
    
    def __init__(self, create_task_use_case, execute_scraping_use_case, 
                 task_repository, data_repository):
        """Inicializar controller de scraping."""
        self.create_task_use_case = create_task_use_case
        self.execute_scraping_use_case = execute_scraping_use_case
        self.task_repository = task_repository
        self.data_repository = data_repository
        self.logger = logging.getLogger(__name__)
        
        # Criar blueprint
        self.blueprint = Blueprint('scraping', __name__, url_prefix='/task')
        self._register_routes()
    
    def get_blueprint(self):
        """Obter blueprint do controller."""
        return self.blueprint
    
    def _register_routes(self):
        """Registrar rotas do controller."""
        self.blueprint.add_url_rule('/new', 'new_task', self.new_task, methods=['GET', 'POST'])
        self.blueprint.add_url_rule('/<task_id>', 'task_detail', self.task_detail)
        self.blueprint.add_url_rule('/<task_id>/start', 'start_task', self.start_task, methods=['POST'])
        self.blueprint.add_url_rule('/<task_id>/stop', 'stop_task', self.stop_task, methods=['POST'])
    
    def new_task(self):
        """Criar nova tarefa de scraping."""
        if request.method == 'GET':
            return render_template('scraping/new_task.html')
        
        try:
            task_data = {
                'name': request.form.get('name', '').strip(),
                'url': request.form.get('url', '').strip(),
                'data_types': request.form.getlist('data_types'),
                'max_items': int(request.form.get('max_items', 100))
            }
            
            task = self.create_task_use_case.execute(
                task_data['name'], 
                task_data['url'], 
                {
                    'data_types': task_data['data_types'], 
                    'max_items': task_data['max_items']
                }
            )
            flash('Tarefa criada com sucesso!', 'success')
            return redirect(url_for('scraping.task_detail', task_id=task.id))
            
        except Exception as e:
            self.logger.error(f"Erro ao criar tarefa: {str(e)}")
            flash('Erro ao criar tarefa.', 'error')
            return render_template('scraping/new_task.html')
    
    def task_detail(self, task_id):
        """Exibir detalhes de uma tarefa."""
        try:
            task = self.task_repository.get_by_id(task_id)
            if not task:
                flash('Tarefa não encontrada.', 'error')
                return redirect(url_for('dashboard.index'))
            
            extracted_data = self.data_repository.get_by_task_id(task_id)
            return render_template('scraping/task_detail.html', 
                                 task=task, 
                                 extracted_data=extracted_data)
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar tarefa {task_id}: {str(e)}")
            flash('Erro interno do servidor.', 'error')
            return redirect(url_for('dashboard.index'))
    
    def start_task(self, task_id):
        """Iniciar execução de uma tarefa."""
        try:
            task = self.task_repository.get_by_id(task_id)
            if not task:
                return jsonify({'error': 'Tarefa não encontrada'}), 404
            
            if task.status not in ['pending', 'failed']:
                return jsonify({'error': 'Tarefa não pode ser iniciada'}), 400
            
            # Simular início da tarefa
            task.status = 'running'
            self.task_repository.update(task)
            
            return jsonify({'success': True, 'message': 'Tarefa iniciada com sucesso'})
            
        except Exception as e:
            self.logger.error(f"Erro ao iniciar tarefa {task_id}: {str(e)}")
            return jsonify({'error': 'Erro interno do servidor'}), 500
    
    def stop_task(self, task_id):
        """Parar execução de uma tarefa."""
        try:
            task = self.task_repository.get_by_id(task_id)
            if not task:
                return jsonify({'error': 'Tarefa não encontrada'}), 404
            
            task.status = 'cancelled'
            self.task_repository.update(task)
            
            return jsonify({'success': True, 'message': 'Tarefa parada com sucesso'})
            
        except Exception as e:
            self.logger.error(f"Erro ao parar tarefa {task_id}: {str(e)}")
            return jsonify({'error': 'Erro interno do servidor'}), 500