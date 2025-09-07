"""View do Dashboard principal - Versão Flet.

Este módulo implementa a interface principal da aplicação
com estatísticas, lista de tarefas e navegação.
"""

import flet as ft
from typing import Optional, Callable, List, Dict, Any
from datetime import datetime

from flet_app.models.scraping_task import ScrapingTask
from flet_app.config.logging_config import get_logger


class DashboardView(ft.UserControl):
    """View principal do dashboard.
    
    Exibe estatísticas, lista de tarefas e permite navegação
    para outras funcionalidades da aplicação.
    """
    
    def __init__(self, 
                 on_new_task: Optional[Callable[[], None]] = None,
                 on_task_detail: Optional[Callable[[str], None]] = None,
                 on_export_task: Optional[Callable[[str], None]] = None,
                 on_start_task: Optional[Callable[[str], None]] = None,
                 on_stop_task: Optional[Callable[[str], None]] = None):
        """Inicializar view do dashboard.
        
        Args:
            on_new_task: Callback para criar nova tarefa
            on_task_detail: Callback para ver detalhes da tarefa
            on_export_task: Callback para exportar tarefa
            on_start_task: Callback para iniciar tarefa
            on_stop_task: Callback para parar tarefa
        """
        super().__init__()
        self.logger = get_logger('DashboardView')
        
        # Callbacks
        self.on_new_task = on_new_task
        self.on_task_detail = on_task_detail
        self.on_export_task = on_export_task
        self.on_start_task = on_start_task
        self.on_stop_task = on_stop_task
        
        # Componentes
        self.stats_cards = []
        self.tasks_list = ft.ListView(
            expand=True,
            spacing=10,
            padding=ft.padding.all(10)
        )
        
        # Dados
        self.tasks_data = []
        self.statistics = {}
    
    def build(self):
        """Construir interface do dashboard."""
        return ft.Container(
            content=ft.Column([
                # Cabeçalho
                self._build_header(),
                
                # Estatísticas
                self._build_statistics_section(),
                
                # Lista de tarefas
                self._build_tasks_section()
            ]),
            padding=ft.padding.all(20),
            expand=True
        )
    
    def _build_header(self) -> ft.Container:
        """Construir cabeçalho do dashboard."""
        return ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text(
                        "Dashboard - Facebook Scraper",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.BLUE_800
                    ),
                    ft.Text(
                        f"Atualizado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
                        size=14,
                        color=ft.colors.GREY_600
                    )
                ], expand=True),
                
                ft.ElevatedButton(
                    "Nova Tarefa",
                    icon=ft.icons.ADD,
                    on_click=lambda _: self._handle_new_task(),
                    style=ft.ButtonStyle(
                        color=ft.colors.WHITE,
                        bgcolor=ft.colors.BLUE_600
                    )
                )
            ]),
            padding=ft.padding.only(bottom=20)
        )
    
    def _build_statistics_section(self) -> ft.Container:
        """Construir seção de estatísticas."""
        self.stats_cards = [
            self._create_stat_card("Total de Tarefas", "0", ft.icons.TASK_ALT, ft.colors.BLUE_600),
            self._create_stat_card("Em Execução", "0", ft.icons.PLAY_CIRCLE, ft.colors.GREEN_600),
            self._create_stat_card("Concluídas", "0", ft.icons.CHECK_CIRCLE, ft.colors.ORANGE_600),
            self._create_stat_card("Falhadas", "0", ft.icons.ERROR, ft.colors.RED_600)
        ]
        
        return ft.Container(
            content=ft.Column([
                ft.Text(
                    "Estatísticas",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.GREY_800
                ),
                ft.Row(
                    self.stats_cards,
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                )
            ]),
            padding=ft.padding.only(bottom=30)
        )
    
    def _create_stat_card(self, title: str, value: str, icon: str, color: str) -> ft.Container:
        """Criar card de estatística.
        
        Args:
            title: Título da estatística
            value: Valor da estatística
            icon: Ícone da estatística
            color: Cor do card
            
        Returns:
            Container com o card
        """
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(icon, color=color, size=30),
                    ft.Column([
                        ft.Text(
                            value,
                            size=24,
                            weight=ft.FontWeight.BOLD,
                            color=color
                        ),
                        ft.Text(
                            title,
                            size=12,
                            color=ft.colors.GREY_600
                        )
                    ], spacing=0)
                ], alignment=ft.MainAxisAlignment.START)
            ]),
            padding=ft.padding.all(15),
            border_radius=10,
            bgcolor=ft.colors.WHITE,
            border=ft.border.all(1, ft.colors.GREY_300),
            width=200
        )
    
    def _build_tasks_section(self) -> ft.Container:
        """Construir seção de tarefas."""
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(
                        "Tarefas Recentes",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.GREY_800
                    ),
                    ft.IconButton(
                        icon=ft.icons.REFRESH,
                        tooltip="Atualizar lista",
                        on_click=lambda _: self._handle_refresh()
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                ft.Container(
                    content=self.tasks_list,
                    height=400,
                    border_radius=10,
                    bgcolor=ft.colors.WHITE,
                    border=ft.border.all(1, ft.colors.GREY_300)
                )
            ]),
            expand=True
        )
    
    def _create_task_card(self, task: ScrapingTask) -> ft.Container:
        """Criar card de tarefa.
        
        Args:
            task: Dados da tarefa
            
        Returns:
            Container com o card da tarefa
        """
        # Determinar cor do status
        status_colors = {
            'pending': ft.colors.GREY_600,
            'running': ft.colors.GREEN_600,
            'completed': ft.colors.BLUE_600,
            'failed': ft.colors.RED_600,
            'cancelled': ft.colors.ORANGE_600
        }
        
        status_color = status_colors.get(task.status, ft.colors.GREY_600)
        
        # Determinar ícone do status
        status_icons = {
            'pending': ft.icons.SCHEDULE,
            'running': ft.icons.PLAY_CIRCLE,
            'completed': ft.icons.CHECK_CIRCLE,
            'failed': ft.icons.ERROR,
            'cancelled': ft.icons.CANCEL
        }
        
        status_icon = status_icons.get(task.status, ft.icons.HELP)
        
        # Botões de ação
        action_buttons = []
        
        if task.status in ['pending', 'failed']:
            action_buttons.append(
                ft.IconButton(
                    icon=ft.icons.PLAY_ARROW,
                    tooltip="Iniciar tarefa",
                    on_click=lambda _, task_id=task.id: self._handle_start_task(task_id)
                )
            )
        
        if task.status == 'running':
            action_buttons.append(
                ft.IconButton(
                    icon=ft.icons.STOP,
                    tooltip="Parar tarefa",
                    on_click=lambda _, task_id=task.id: self._handle_stop_task(task_id)
                )
            )
        
        if task.status == 'completed':
            action_buttons.append(
                ft.IconButton(
                    icon=ft.icons.DOWNLOAD,
                    tooltip="Exportar dados",
                    on_click=lambda _, task_id=task.id: self._handle_export_task(task_id)
                )
            )
        
        action_buttons.append(
            ft.IconButton(
                icon=ft.icons.VISIBILITY,
                tooltip="Ver detalhes",
                on_click=lambda _, task_id=task.id: self._handle_task_detail(task_id)
            )
        )
        
        return ft.Container(
            content=ft.Row([
                # Informações da tarefa
                ft.Column([
                    ft.Row([
                        ft.Icon(status_icon, color=status_color, size=20),
                        ft.Text(
                            task.name,
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            color=ft.colors.GREY_800
                        )
                    ]),
                    ft.Text(
                        task.url[:60] + "..." if len(task.url) > 60 else task.url,
                        size=12,
                        color=ft.colors.GREY_600
                    ),
                    ft.Row([
                        ft.Text(
                            f"Status: {task.status.title()}",
                            size=12,
                            color=status_color,
                            weight=ft.FontWeight.BOLD
                        ),
                        ft.Text(
                            f"Itens: {task.items_processed}",
                            size=12,
                            color=ft.colors.GREY_600
                        ),
                        ft.Text(
                            f"Criado: {task.created_at.strftime('%d/%m/%Y %H:%M') if task.created_at else 'N/A'}",
                            size=12,
                            color=ft.colors.GREY_600
                        )
                    ])
                ], expand=True, spacing=5),
                
                # Barra de progresso (se em execução)
                ft.Column([
                    ft.ProgressBar(
                        value=task.get_progress_percentage() / 100,
                        width=100,
                        height=4,
                        color=ft.colors.BLUE_600,
                        bgcolor=ft.colors.GREY_300
                    ) if task.status == 'running' else ft.Container(width=100),
                    
                    ft.Row(action_buttons, spacing=5)
                ], horizontal_alignment=ft.CrossAxisAlignment.END)
            ]),
            padding=ft.padding.all(15),
            margin=ft.margin.only(bottom=10),
            border_radius=8,
            bgcolor=ft.colors.WHITE,
            border=ft.border.all(1, ft.colors.GREY_300)
        )
    
    def update_statistics(self, stats: Dict[str, Any]) -> None:
        """Atualizar estatísticas do dashboard.
        
        Args:
            stats: Dicionário com estatísticas
        """
        try:
            self.statistics = stats
            
            # Atualizar cards de estatísticas
            if len(self.stats_cards) >= 4:
                # Total de tarefas
                self.stats_cards[0].content.controls[0].controls[1].controls[0].value = str(stats.get('total', 0))
                
                # Em execução
                self.stats_cards[1].content.controls[0].controls[1].controls[0].value = str(stats.get('running', 0))
                
                # Concluídas
                self.stats_cards[2].content.controls[0].controls[1].controls[0].value = str(stats.get('completed', 0))
                
                # Falhadas
                self.stats_cards[3].content.controls[0].controls[1].controls[0].value = str(stats.get('failed', 0))
            
            self.update()
            
        except Exception as e:
            self.logger.error(f'Erro ao atualizar estatísticas: {str(e)}')
    
    def update_tasks_list(self, tasks: List[ScrapingTask]) -> None:
        """Atualizar lista de tarefas.
        
        Args:
            tasks: Lista de tarefas
        """
        try:
            self.tasks_data = tasks
            
            # Limpar lista atual
            self.tasks_list.controls.clear()
            
            if not tasks:
                # Exibir mensagem quando não há tarefas
                self.tasks_list.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.icons.INBOX, size=64, color=ft.colors.GREY_400),
                            ft.Text(
                                "Nenhuma tarefa encontrada",
                                size=16,
                                color=ft.colors.GREY_600,
                                text_align=ft.TextAlign.CENTER
                            ),
                            ft.Text(
                                "Clique em 'Nova Tarefa' para começar",
                                size=12,
                                color=ft.colors.GREY_500,
                                text_align=ft.TextAlign.CENTER
                            )
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=ft.padding.all(40),
                        alignment=ft.alignment.center
                    )
                )
            else:
                # Adicionar cards das tarefas
                for task in tasks:
                    self.tasks_list.controls.append(self._create_task_card(task))
            
            self.update()
            
        except Exception as e:
            self.logger.error(f'Erro ao atualizar lista de tarefas: {str(e)}')
    
    def show_loading(self, message: str = "Carregando...") -> None:
        """Exibir indicador de carregamento.
        
        Args:
            message: Mensagem de carregamento
        """
        self.tasks_list.controls.clear()
        self.tasks_list.controls.append(
            ft.Container(
                content=ft.Column([
                    ft.ProgressRing(),
                    ft.Text(
                        message,
                        size=14,
                        color=ft.colors.GREY_600,
                        text_align=ft.TextAlign.CENTER
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.padding.all(40),
                alignment=ft.alignment.center
            )
        )
        self.update()
    
    def show_error(self, error_message: str) -> None:
        """Exibir mensagem de erro.
        
        Args:
            error_message: Mensagem de erro
        """
        self.tasks_list.controls.clear()
        self.tasks_list.controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.icons.ERROR, size=64, color=ft.colors.RED_400),
                    ft.Text(
                        "Erro ao carregar dados",
                        size=16,
                        color=ft.colors.RED_600,
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.Text(
                        error_message,
                        size=12,
                        color=ft.colors.GREY_600,
                        text_align=ft.TextAlign.CENTER
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.padding.all(40),
                alignment=ft.alignment.center
            )
        )
        self.update()
    
    def _handle_new_task(self) -> None:
        """Manipular clique em nova tarefa."""
        if self.on_new_task:
            self.on_new_task()
    
    def _handle_task_detail(self, task_id: str) -> None:
        """Manipular clique em detalhes da tarefa."""
        if self.on_task_detail:
            self.on_task_detail(task_id)
    
    def _handle_export_task(self, task_id: str) -> None:
        """Manipular clique em exportar tarefa."""
        if self.on_export_task:
            self.on_export_task(task_id)
    
    def _handle_start_task(self, task_id: str) -> None:
        """Manipular clique em iniciar tarefa."""
        if self.on_start_task:
            self.on_start_task(task_id)
    
    def _handle_stop_task(self, task_id: str) -> None:
        """Manipular clique em parar tarefa."""
        if self.on_stop_task:
            self.on_stop_task(task_id)
    
    def _handle_refresh(self) -> None:
        """Manipular clique em atualizar."""
        # Callback será implementado pelo controlador principal
        pass