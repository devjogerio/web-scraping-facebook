"""Aplicação principal - Facebook Scraper Flet.

Este módulo implementa a aplicação desktop principal
que integra todas as funcionalidades de scraping do Facebook.
"""

import flet as ft
import threading
import time
from typing import Optional, Dict, Any

from flet_app.config.database import init_database, get_database_session, close_database_session
from flet_app.config.logging_config import setup_logging, get_logger

from flet_app.repositories.scraping_task_repository import ScrapingTaskRepository
from flet_app.repositories.facebook_data_repository import FacebookDataRepository
from flet_app.repositories.export_job_repository import ExportJobRepository

from flet_app.services.scraping_service import ScrapingService
from flet_app.services.excel_service import ExcelService

from flet_app.use_cases.create_scraping_task import CreateScrapingTaskUseCase
from flet_app.use_cases.execute_scraping import ExecuteScrapingUseCase
from flet_app.use_cases.export_to_excel import ExportToExcelUseCase

from flet_app.views.dashboard_view import DashboardView
from flet_app.views.new_task_view import NewTaskView
from flet_app.views.task_detail_view import TaskDetailView


class FacebookScraperApp:
    """Aplicação principal do Facebook Scraper.
    
    Gerencia a interface principal, navegação entre views
    e integração com os use cases de negócio.
    """
    
    def __init__(self, page: ft.Page):
        """Inicializar aplicação.
        
        Args:
            page: Página principal do Flet
        """
        self.page = page
        self.logger = get_logger('FacebookScraperApp')
        
        # Configurar página
        self._setup_page()
        
        # Inicializar banco de dados
        self._init_database()
        
        # Inicializar repositórios
        self._init_repositories()
        
        # Inicializar serviços
        self._init_services()
        
        # Inicializar use cases
        self._init_use_cases()
        
        # Views
        self.current_view = None
        self.dashboard_view = None
        self.new_task_view = None
        self.task_detail_view = None
        
        # Timer para atualização automática
        self.update_timer = None
        self.auto_update_enabled = True
        
        # Inicializar interface
        self._init_ui()
    
    def _setup_page(self) -> None:
        """Configurar página principal."""
        # As configurações da página já foram definidas na função main
        # para garantir que sejam aplicadas antes da inicialização da aplicação
        pass
    
    def _init_database(self) -> None:
        """Inicializar banco de dados."""
        try:
            init_database()
            self.logger.info('Banco de dados inicializado com sucesso')
        except Exception as e:
            self.logger.error(f'Erro ao inicializar banco de dados: {str(e)}')
            self._show_error_dialog("Erro de Inicialização", f"Erro ao inicializar banco de dados: {str(e)}")
    
    def _init_repositories(self) -> None:
        """Inicializar repositórios."""
        self.db_session = get_database_session()
        
        self.task_repository = ScrapingTaskRepository(self.db_session)
        self.data_repository = FacebookDataRepository(self.db_session)
        self.export_repository = ExportJobRepository(self.db_session)
    
    def _init_services(self) -> None:
        """Inicializar serviços."""
        # Configuração padrão do scraping
        scraping_config = {
            'delay_min': 1,
            'delay_max': 3,
            'timeout': 30,
            'max_retries': 3,
            'headless': True
        }
        
        self.scraping_service = ScrapingService(scraping_config)
        self.excel_service = ExcelService()
    
    def _init_use_cases(self) -> None:
        """Inicializar use cases."""
        self.create_task_use_case = CreateScrapingTaskUseCase(self.task_repository)
        self.execute_scraping_use_case = ExecuteScrapingUseCase(
            self.task_repository,
            self.data_repository
        )
        self.export_use_case = ExportToExcelUseCase(
            self.task_repository,
            self.data_repository,
            self.export_repository,
            self.excel_service
        )
    
    def _init_ui(self) -> None:
        """Inicializar interface do usuário."""
        try:
            self.logger.info('Inicializando interface do usuário...')
            
            # Criar dashboard como view inicial
            self._show_dashboard()
            
            # Iniciar timer de atualização
            self._start_update_timer()
            
            self.logger.info('Interface inicializada com sucesso')
            
        except Exception as e:
            self.logger.error(f'Erro ao inicializar interface: {str(e)}')
            raise
    
    def _show_dashboard(self) -> None:
        """Exibir dashboard principal."""
        try:
            self.logger.info('Criando dashboard view...')
            
            self.dashboard_view = DashboardView(
                on_new_task=self._show_new_task,
                on_task_detail=self._show_task_detail,
                on_export_task=self._handle_export_task,
                on_start_task=self._handle_start_task,
                on_stop_task=self._handle_stop_task
            )
            
            self.logger.info('Dashboard view criado, definindo como view atual...')
            self._set_current_view(self.dashboard_view)
            
            self.logger.info('Atualizando dados do dashboard...')
            self._refresh_dashboard()
            
            self.logger.info('Dashboard exibido com sucesso')
            
        except Exception as e:
            self.logger.error(f'Erro ao exibir dashboard: {str(e)}')
            import traceback
            self.logger.error(f'Stack trace: {traceback.format_exc()}')
            self._show_error_dialog("Erro", f"Erro ao carregar dashboard: {str(e)}")
    
    def _show_new_task(self) -> None:
        """Exibir formulário de nova tarefa."""
        try:
            self.new_task_view = NewTaskView(
                on_create_task=self._handle_create_task,
                on_cancel=self._show_dashboard,
                on_validate_url=self._validate_url
            )
            
            self._set_current_view(self.new_task_view)
            
        except Exception as e:
            self.logger.error(f'Erro ao exibir nova tarefa: {str(e)}')
            self._show_error_dialog("Erro", f"Erro ao carregar formulário: {str(e)}")
    
    def _show_task_detail(self, task_id: str) -> None:
        """Exibir detalhes da tarefa.
        
        Args:
            task_id: ID da tarefa
        """
        try:
            self.task_detail_view = TaskDetailView(
                task_id=task_id,
                on_start_task=self._handle_start_task,
                on_stop_task=self._handle_stop_task,
                on_export_task=self._handle_export_task,
                on_back=self._show_dashboard
            )
            
            self._set_current_view(self.task_detail_view)
            self._refresh_task_detail(task_id)
            
        except Exception as e:
            self.logger.error(f'Erro ao exibir detalhes da tarefa: {str(e)}')
            self._show_error_dialog("Erro", f"Erro ao carregar detalhes: {str(e)}")
    
    def _set_current_view(self, view: ft.UserControl) -> None:
        """Definir view atual.
        
        Args:
            view: View a ser exibida
        """
        self.current_view = view
        self.page.controls.clear()
        self.page.add(view)
        self.page.update()
    
    def _handle_create_task(self, task_data: Dict[str, Any]) -> None:
        """Manipular criação de tarefa.
        
        Args:
            task_data: Dados da tarefa
        """
        try:
            self.new_task_view.show_loading("Criando tarefa...")
            
            # Criar tarefa
            task = self.create_task_use_case.execute(
                name=task_data['name'],
                url=task_data['url'],
                config=task_data['config']
            )
            
            self.logger.info(f'Tarefa criada com sucesso: {task.id}')
            
            # Mostrar mensagem de sucesso
            self._show_success_dialog(
                "Sucesso",
                f"Tarefa '{task.name}' criada com sucesso!",
                lambda: self._show_task_detail(task.id)
            )
            
        except Exception as e:
            self.logger.error(f'Erro ao criar tarefa: {str(e)}')
            self.new_task_view.hide_loading()
            self._show_error_dialog("Erro", f"Erro ao criar tarefa: {str(e)}")
    
    def _handle_start_task(self, task_id: str) -> None:
        """Manipular início de tarefa.
        
        Args:
            task_id: ID da tarefa
        """
        try:
            # Validar se pode executar
            can_execute, message = self.execute_scraping_use_case.validate_task_for_execution(task_id)
            
            if not can_execute:
                self._show_error_dialog("Não é possível executar", message)
                return
            
            # Callbacks de progresso
            def progress_callback(percentage: int, message: str) -> None:
                if self.task_detail_view and self.task_detail_view.task_id == task_id:
                    self.task_detail_view.add_log_message(f"[{percentage}%] {message}")
            
            def completion_callback(success: bool, message: str, items_count: int) -> None:
                if self.task_detail_view and self.task_detail_view.task_id == task_id:
                    level = "INFO" if success else "ERROR"
                    self.task_detail_view.add_log_message(message, level)
                
                if success:
                    self._show_success_dialog("Scraping Concluído", message)
                else:
                    self._show_error_dialog("Scraping Falhou", message)
            
            # Iniciar execução
            started = self.execute_scraping_use_case.execute_async(
                task_id=task_id,
                progress_callback=progress_callback,
                completion_callback=completion_callback
            )
            
            if started:
                self.logger.info(f'Execução iniciada para tarefa: {task_id}')
                if self.task_detail_view:
                    self.task_detail_view.add_log_message("Execução iniciada")
            else:
                self._show_error_dialog("Erro", "Não foi possível iniciar a execução")
                
        except Exception as e:
            self.logger.error(f'Erro ao iniciar tarefa: {str(e)}')
            self._show_error_dialog("Erro", f"Erro ao iniciar tarefa: {str(e)}")
    
    def _handle_stop_task(self, task_id: str) -> None:
        """Manipular parada de tarefa.
        
        Args:
            task_id: ID da tarefa
        """
        try:
            stopped = self.execute_scraping_use_case.stop_scraping(task_id)
            
            if stopped:
                self.logger.info(f'Parada solicitada para tarefa: {task_id}')
                if self.task_detail_view:
                    self.task_detail_view.add_log_message("Parada solicitada", "WARNING")
                self._show_success_dialog("Tarefa Parada", "A parada da tarefa foi solicitada")
            else:
                self._show_error_dialog("Erro", "Não foi possível parar a tarefa")
                
        except Exception as e:
            self.logger.error(f'Erro ao parar tarefa: {str(e)}')
            self._show_error_dialog("Erro", f"Erro ao parar tarefa: {str(e)}")
    
    def _handle_export_task(self, task_id: str) -> None:
        """Manipular exportação de tarefa.
        
        Args:
            task_id: ID da tarefa
        """
        try:
            # Validar se pode exportar
            can_export, message = self.export_use_case.validate_task_for_export(task_id)
            
            if not can_export:
                self._show_error_dialog("Não é possível exportar", message)
                return
            
            # Callbacks de progresso
            def progress_callback(percentage: int, message: str) -> None:
                if self.task_detail_view and self.task_detail_view.task_id == task_id:
                    self.task_detail_view.add_log_message(f"[Exportação {percentage}%] {message}")
            
            def completion_callback(success: bool, message: str, file_path: Optional[str]) -> None:
                if self.task_detail_view and self.task_detail_view.task_id == task_id:
                    level = "INFO" if success else "ERROR"
                    self.task_detail_view.add_log_message(message, level)
                
                if success:
                    self._show_success_dialog("Exportação Concluída", f"{message}\n\nArquivo salvo em: {file_path}")
                else:
                    self._show_error_dialog("Exportação Falhou", message)
            
            # Iniciar exportação
            started = self.export_use_case.export_task_data_async(
                task_id=task_id,
                progress_callback=progress_callback,
                completion_callback=completion_callback
            )
            
            if started:
                self.logger.info(f'Exportação iniciada para tarefa: {task_id}')
                if self.task_detail_view:
                    self.task_detail_view.add_log_message("Exportação iniciada")
            else:
                self._show_error_dialog("Erro", "Não foi possível iniciar a exportação")
                
        except Exception as e:
            self.logger.error(f'Erro ao exportar tarefa: {str(e)}')
            self._show_error_dialog("Erro", f"Erro ao exportar tarefa: {str(e)}")
    
    def _validate_url(self, url: str) -> tuple[bool, str]:
        """Validar URL.
        
        Args:
            url: URL a ser validada
            
        Returns:
            Tupla (é_válida, mensagem)
        """
        try:
            return self.create_task_use_case.validate_url_accessibility(url)
        except Exception as e:
            return False, f"Erro na validação: {str(e)}"
    
    def _refresh_dashboard(self) -> None:
        """Atualizar dados do dashboard."""
        try:
            if not self.dashboard_view:
                return
            
            # Buscar estatísticas
            stats = self.task_repository.get_statistics()
            self.dashboard_view.update_statistics(stats)
            
            # Buscar tarefas recentes
            recent_tasks = self.task_repository.get_recent_tasks(10)
            self.dashboard_view.update_tasks_list(recent_tasks)
            
        except Exception as e:
            self.logger.error(f'Erro ao atualizar dashboard: {str(e)}')
            if self.dashboard_view:
                self.dashboard_view.show_error(f"Erro ao carregar dados: {str(e)}")
    
    def _refresh_task_detail(self, task_id: str) -> None:
        """Atualizar detalhes da tarefa.
        
        Args:
            task_id: ID da tarefa
        """
        try:
            if not self.task_detail_view:
                return
            
            # Buscar dados da tarefa
            task = self.task_repository.get_by_id(task_id)
            if task:
                self.task_detail_view.update_task_data(task)
            
            # Buscar dados extraídos
            extracted_data = self.data_repository.get_by_task_id(task_id, limit=100)
            self.task_detail_view.update_extracted_data(extracted_data)
            
        except Exception as e:
            self.logger.error(f'Erro ao atualizar detalhes da tarefa: {str(e)}')
    
    def _start_update_timer(self) -> None:
        """Iniciar timer de atualização automática."""
        def update_loop():
            while self.auto_update_enabled:
                try:
                    if isinstance(self.current_view, DashboardView):
                        self._refresh_dashboard()
                    elif isinstance(self.current_view, TaskDetailView):
                        self._refresh_task_detail(self.current_view.task_id)
                    
                    time.sleep(5)  # Atualizar a cada 5 segundos
                    
                except Exception as e:
                    self.logger.error(f'Erro no timer de atualização: {str(e)}')
                    time.sleep(10)  # Aguardar mais tempo em caso de erro
        
        self.update_timer = threading.Thread(target=update_loop, daemon=True)
        self.update_timer.start()
    
    def _show_success_dialog(self, title: str, message: str, on_close: Optional[callable] = None) -> None:
        """Exibir diálogo de sucesso.
        
        Args:
            title: Título do diálogo
            message: Mensagem do diálogo
            on_close: Callback ao fechar
        """
        def close_dialog(e):
            dialog.open = False
            self.page.update()
            if on_close:
                on_close()
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(title),
            content=ft.Text(message),
            actions=[
                ft.TextButton("OK", on_click=close_dialog)
            ]
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _show_error_dialog(self, title: str, message: str) -> None:
        """Exibir diálogo de erro.
        
        Args:
            title: Título do diálogo
            message: Mensagem de erro
        """
        def close_dialog(e):
            dialog.open = False
            self.page.update()
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(title, color=ft.colors.RED_600),
            content=ft.Text(message),
            actions=[
                ft.TextButton("OK", on_click=close_dialog)
            ]
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def cleanup(self) -> None:
        """Limpar recursos da aplicação."""
        try:
            self.auto_update_enabled = False
            
            if self.db_session:
                close_database_session(self.db_session)
            
            self.logger.info('Aplicação finalizada')
            
        except Exception as e:
            self.logger.error(f'Erro durante limpeza: {str(e)}')


def main(page: ft.Page):
    """Função principal da aplicação.
    
    Args:
        page: Página principal do Flet
    """
    try:
        # Configurar logging
        setup_logging('INFO')
        logger = get_logger('main')
        logger.info('Iniciando aplicação Flet...')
        
        # Configurações específicas para macOS
        page.title = "Facebook Scraper"
        page.window_width = 1200
        page.window_height = 800
        page.window_min_width = 800
        page.window_min_height = 600
        page.window_center = True
        page.window_resizable = True
        page.window_maximizable = True
        page.window_minimizable = True
        page.theme_mode = ft.ThemeMode.LIGHT
        page.padding = 0
        page.scroll = ft.ScrollMode.AUTO
        
        # Configurar tema
        page.theme = ft.Theme(
            color_scheme_seed=ft.colors.BLUE,
            use_material3=True
        )
        
        logger.info('Configurações da página definidas')
        
        # Criar e inicializar aplicação
        app = FacebookScraperApp(page)
        logger.info('Aplicação inicializada com sucesso')
        
        # Configurar cleanup ao fechar
        def on_window_event(e):
            if e.data == "close":
                logger.info('Fechando aplicação...')
                app.cleanup()
        
        page.window_prevent_close = True
        page.on_window_event = on_window_event
        
        # Forçar atualização da página
        page.update()
        logger.info('Página atualizada - interface deve estar visível')
        
    except Exception as e:
        print(f"❌ Erro crítico na inicialização: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Criar interface de erro simples
        page.add(
            ft.Container(
                content=ft.Column([
                    ft.Text("❌ Erro na Aplicação", size=24, color=ft.colors.RED),
                    ft.Text(f"Erro: {str(e)}", size=14),
                    ft.ElevatedButton("Fechar", on_click=lambda _: page.window_close())
                ], alignment=ft.MainAxisAlignment.CENTER),
                padding=50,
                alignment=ft.alignment.center
            )
        )
        page.update()


if __name__ == "__main__":
    print("="*60)
    print("🚀 FACEBOOK SCRAPER - APLICAÇÃO FLET")
    print("="*60)
    print(f"🐍 Python: {sys.version.split()[0]}")
    print(f"💻 Sistema: {platform.system()} {platform.release()}")
    print(f"📁 Diretório: {os.getcwd()}")
    print("="*60)
    
    try:
        print("🔄 Iniciando aplicação Flet...")
        print("⚠️  IMPORTANTE: Uma janela desktop será aberta")
        print("📋 Se a janela não aparecer, verifique:")
        print("   1. Permissões de acessibilidade no macOS")
        print("   2. Se o Python tem permissão para controlar o computador")
        print("   3. Execute a partir do Terminal nativo (não IDE)")
        print("\n🚀 Iniciando interface...")
        
        # Importar módulos necessários
        import platform
        import sys
        import os
        
        ft.app(
            target=main,
            view=ft.AppView.FLET_APP,
            port=0,
            web_renderer=ft.WebRenderer.HTML,
            route_url_strategy="hash"
        )
        
        print("✅ Aplicação executada com sucesso")
        
    except KeyboardInterrupt:
        print("\n🛑 Aplicação interrompida pelo usuário")
    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO: {str(e)}")
        print("\n📋 Stack trace completo:")
        import traceback
        traceback.print_exc()
        
        print("\n💡 SOLUÇÕES SUGERIDAS:")
        print("   1. Verificar se o Flet está instalado: pip install flet")
        print("   2. Verificar permissões do sistema (especialmente macOS)")
        print("   3. Tentar executar como administrador")
        print("   4. Verificar se há conflitos com outros programas")
        print("   5. Executar o diagnóstico: python diagnostico_flet.py")
    
    print("\n🏁 Execução finalizada.")
    print("="*60)