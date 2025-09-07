"""View de detalhes da tarefa - Versão Flet.

Este módulo implementa a interface para visualização detalhada
de tarefas com monitoramento em tempo real e logs.
"""

import flet as ft
from typing import Optional, Callable, Dict, Any, List
from datetime import datetime

from flet_app.models.scraping_task import ScrapingTask
from flet_app.models.facebook_data import FacebookData
from flet_app.config.logging_config import get_logger


class TaskDetailView(ft.UserControl):
    """View de detalhes da tarefa.
    
    Exibe informações detalhadas da tarefa, progresso em tempo real,
    logs de execução e dados extraídos.
    """
    
    def __init__(self, 
                 task_id: str,
                 on_start_task: Optional[Callable[[str], None]] = None,
                 on_stop_task: Optional[Callable[[str], None]] = None,
                 on_export_task: Optional[Callable[[str], None]] = None,
                 on_back: Optional[Callable[[], None]] = None):
        """Inicializar view de detalhes.
        
        Args:
            task_id: ID da tarefa
            on_start_task: Callback para iniciar tarefa
            on_stop_task: Callback para parar tarefa
            on_export_task: Callback para exportar tarefa
            on_back: Callback para voltar
        """
        super().__init__()
        self.logger = get_logger('TaskDetailView')
        
        self.task_id = task_id
        self.on_start_task = on_start_task
        self.on_stop_task = on_stop_task
        self.on_export_task = on_export_task
        self.on_back = on_back
        
        # Dados da tarefa
        self.task_data = None
        self.extracted_data = []
        
        # Componentes principais
        self.task_info_section = ft.Container()
        self.progress_section = ft.Container()
        self.logs_section = ft.Container()
        self.data_section = ft.Container()
        
        # Componentes de progresso
        self.progress_bar = ft.ProgressBar(
            width=400,
            height=8,
            color=ft.colors.BLUE_600,
            bgcolor=ft.colors.GREY_300
        )
        
        self.progress_text = ft.Text(
            "0%",
            size=14,
            weight=ft.FontWeight.BOLD
        )
        
        self.status_chip = ft.Chip(
            label=ft.Text("Carregando..."),
            bgcolor=ft.colors.GREY_300
        )
        
        # Lista de logs
        self.logs_list = ft.ListView(
            height=200,
            spacing=5,
            padding=ft.padding.all(10)
        )
        
        # Lista de dados extraídos
        self.data_list = ft.ListView(
            height=300,
            spacing=5,
            padding=ft.padding.all(10)
        )
        
        # Botões de ação
        self.action_buttons = ft.Row(spacing=10)
    
    def build(self):
        """Construir interface de detalhes."""
        return ft.Container(
            content=ft.Column([
                # Cabeçalho
                self._build_header(),
                
                # Informações da tarefa
                self._build_task_info_section(),
                
                # Progresso
                self._build_progress_section(),
                
                # Abas de conteúdo
                self._build_tabs_section()
            ], scroll=ft.ScrollMode.AUTO),
            padding=ft.padding.all(20),
            expand=True
        )
    
    def _build_header(self) -> ft.Container:
        """Construir cabeçalho."""
        return ft.Container(
            content=ft.Row([
                ft.IconButton(
                    icon=ft.icons.ARROW_BACK,
                    tooltip="Voltar",
                    on_click=lambda _: self._handle_back()
                ),
                ft.Column([
                    ft.Text(
                        "Detalhes da Tarefa",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.BLUE_800
                    ),
                    ft.Text(
                        f"ID: {self.task_id}",
                        size=12,
                        color=ft.colors.GREY_600
                    )
                ], expand=True),
                
                self.action_buttons
            ]),
            padding=ft.padding.only(bottom=20)
        )
    
    def _build_task_info_section(self) -> ft.Container:
        """Construir seção de informações da tarefa."""
        self.task_info_section = ft.Container(
            content=ft.Column([
                ft.Text(
                    "Informações da Tarefa",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.GREY_800
                ),
                
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text("Nome:", weight=ft.FontWeight.BOLD, width=120),
                                ft.Text("Carregando...", expand=True)
                            ]),
                            ft.Row([
                                ft.Text("URL:", weight=ft.FontWeight.BOLD, width=120),
                                ft.Text("Carregando...", expand=True)
                            ]),
                            ft.Row([
                                ft.Text("Status:", weight=ft.FontWeight.BOLD, width=120),
                                self.status_chip
                            ]),
                            ft.Row([
                                ft.Text("Criado em:", weight=ft.FontWeight.BOLD, width=120),
                                ft.Text("Carregando...", expand=True)
                            ]),
                            ft.Row([
                                ft.Text("Itens processados:", weight=ft.FontWeight.BOLD, width=120),
                                ft.Text("0", expand=True)
                            ])
                        ], spacing=10),
                        padding=ft.padding.all(15)
                    )
                )
            ]),
            padding=ft.padding.only(bottom=20)
        )
        
        return self.task_info_section
    
    def _build_progress_section(self) -> ft.Container:
        """Construir seção de progresso."""
        self.progress_section = ft.Container(
            content=ft.Column([
                ft.Text(
                    "Progresso",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.GREY_800
                ),
                
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Row([
                                self.progress_bar,
                                self.progress_text
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            
                            ft.Text(
                                "Aguardando início da tarefa...",
                                size=12,
                                color=ft.colors.GREY_600,
                                italic=True
                            )
                        ], spacing=10),
                        padding=ft.padding.all(15)
                    )
                )
            ]),
            padding=ft.padding.only(bottom=20)
        )
        
        return self.progress_section
    
    def _build_tabs_section(self) -> ft.Container:
        """Construir seção de abas."""
        return ft.Container(
            content=ft.Tabs(
                selected_index=0,
                tabs=[
                    ft.Tab(
                        text="Logs de Execução",
                        icon=ft.icons.LIST_ALT,
                        content=self._build_logs_tab()
                    ),
                    ft.Tab(
                        text="Dados Extraídos",
                        icon=ft.icons.DATA_OBJECT,
                        content=self._build_data_tab()
                    ),
                    ft.Tab(
                        text="Configurações",
                        icon=ft.icons.SETTINGS,
                        content=self._build_config_tab()
                    )
                ]
            ),
            expand=True
        )
    
    def _build_logs_tab(self) -> ft.Container:
        """Construir aba de logs."""
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(
                        "Logs de Execução",
                        size=16,
                        weight=ft.FontWeight.BOLD
                    ),
                    ft.IconButton(
                        icon=ft.icons.REFRESH,
                        tooltip="Atualizar logs",
                        on_click=lambda _: self._refresh_logs()
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                ft.Container(
                    content=self.logs_list,
                    border_radius=8,
                    bgcolor=ft.colors.GREY_50,
                    border=ft.border.all(1, ft.colors.GREY_300)
                )
            ]),
            padding=ft.padding.all(10)
        )
    
    def _build_data_tab(self) -> ft.Container:
        """Construir aba de dados extraídos."""
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(
                        "Dados Extraídos",
                        size=16,
                        weight=ft.FontWeight.BOLD
                    ),
                    ft.Row([
                        ft.IconButton(
                            icon=ft.icons.REFRESH,
                            tooltip="Atualizar dados",
                            on_click=lambda _: self._refresh_data()
                        ),
                        ft.IconButton(
                            icon=ft.icons.DOWNLOAD,
                            tooltip="Exportar dados",
                            on_click=lambda _: self._handle_export_task()
                        )
                    ])
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                ft.Container(
                    content=self.data_list,
                    border_radius=8,
                    bgcolor=ft.colors.GREY_50,
                    border=ft.border.all(1, ft.colors.GREY_300)
                )
            ]),
            padding=ft.padding.all(10)
        )
    
    def _build_config_tab(self) -> ft.Container:
        """Construir aba de configurações."""
        return ft.Container(
            content=ft.Column([
                ft.Text(
                    "Configurações da Tarefa",
                    size=16,
                    weight=ft.FontWeight.BOLD
                ),
                
                ft.Card(
                    content=ft.Container(
                        content=ft.Text(
                            "Carregando configurações...",
                            color=ft.colors.GREY_600
                        ),
                        padding=ft.padding.all(15)
                    )
                )
            ]),
            padding=ft.padding.all(10)
        )
    
    def update_task_data(self, task: ScrapingTask) -> None:
        """Atualizar dados da tarefa.
        
        Args:
            task: Dados da tarefa
        """
        try:
            self.task_data = task
            
            # Atualizar informações básicas
            info_card = self.task_info_section.content.controls[1].content.content
            
            info_card.controls[0].controls[1].value = task.name
            info_card.controls[1].controls[1].value = task.url
            info_card.controls[3].controls[1].value = task.created_at.strftime('%d/%m/%Y %H:%M:%S') if task.created_at else 'N/A'
            info_card.controls[4].controls[1].value = str(task.items_processed)
            
            # Atualizar status
            self._update_status_chip(task.status)
            
            # Atualizar progresso
            self._update_progress(task)
            
            # Atualizar botões de ação
            self._update_action_buttons(task)
            
            # Atualizar configurações
            self._update_config_tab(task)
            
            self.update()
            
        except Exception as e:
            self.logger.error(f'Erro ao atualizar dados da tarefa: {str(e)}')
    
    def _update_status_chip(self, status: str) -> None:
        """Atualizar chip de status."""
        status_config = {
            'pending': {'text': 'Pendente', 'color': ft.colors.GREY_600},
            'running': {'text': 'Executando', 'color': ft.colors.GREEN_600},
            'completed': {'text': 'Concluída', 'color': ft.colors.BLUE_600},
            'failed': {'text': 'Falhada', 'color': ft.colors.RED_600},
            'cancelled': {'text': 'Cancelada', 'color': ft.colors.ORANGE_600}
        }
        
        config = status_config.get(status, {'text': status, 'color': ft.colors.GREY_600})
        
        self.status_chip.label.value = config['text']
        self.status_chip.bgcolor = config['color']
    
    def _update_progress(self, task: ScrapingTask) -> None:
        """Atualizar barra de progresso."""
        progress_percentage = task.get_progress_percentage()
        
        self.progress_bar.value = progress_percentage / 100
        self.progress_text.value = f"{progress_percentage}%"
        
        # Atualizar mensagem de progresso
        progress_card = self.progress_section.content.controls[1].content.content
        progress_message = progress_card.controls[1]
        
        if task.status == 'pending':
            progress_message.value = "Aguardando início da tarefa..."
        elif task.status == 'running':
            progress_message.value = f"Processando... {task.items_processed} itens extraídos"
        elif task.status == 'completed':
            progress_message.value = f"Tarefa concluída! {task.items_processed} itens extraídos"
        elif task.status == 'failed':
            progress_message.value = f"Tarefa falhou: {task.error_message or 'Erro desconhecido'}"
        elif task.status == 'cancelled':
            progress_message.value = "Tarefa cancelada pelo usuário"
    
    def _update_action_buttons(self, task: ScrapingTask) -> None:
        """Atualizar botões de ação."""
        self.action_buttons.controls.clear()
        
        if task.status in ['pending', 'failed']:
            self.action_buttons.controls.append(
                ft.ElevatedButton(
                    "Iniciar",
                    icon=ft.icons.PLAY_ARROW,
                    on_click=lambda _: self._handle_start_task(),
                    style=ft.ButtonStyle(
                        color=ft.colors.WHITE,
                        bgcolor=ft.colors.GREEN_600
                    )
                )
            )
        
        if task.status == 'running':
            self.action_buttons.controls.append(
                ft.ElevatedButton(
                    "Parar",
                    icon=ft.icons.STOP,
                    on_click=lambda _: self._handle_stop_task(),
                    style=ft.ButtonStyle(
                        color=ft.colors.WHITE,
                        bgcolor=ft.colors.RED_600
                    )
                )
            )
        
        if task.status == 'completed':
            self.action_buttons.controls.append(
                ft.ElevatedButton(
                    "Exportar",
                    icon=ft.icons.DOWNLOAD,
                    on_click=lambda _: self._handle_export_task(),
                    style=ft.ButtonStyle(
                        color=ft.colors.WHITE,
                        bgcolor=ft.colors.BLUE_600
                    )
                )
            )
    
    def _update_config_tab(self, task: ScrapingTask) -> None:
        """Atualizar aba de configurações."""
        try:
            config = task.get_config()
            
            config_text = []
            config_text.append(f"Tipos de dados: {', '.join(config.get('data_types', []))}")
            config_text.append(f"Máximo de itens: {config.get('max_items', 'N/A')}")
            config_text.append(f"Delay mínimo: {config.get('delay_min', 'N/A')}s")
            config_text.append(f"Delay máximo: {config.get('delay_max', 'N/A')}s")
            config_text.append(f"Modo headless: {'Sim' if config.get('headless', True) else 'Não'}")
            
            # Encontrar aba de configurações e atualizar
            tabs_container = self.controls[0].content.controls[3].content
            config_tab = tabs_container.tabs[2].content
            config_card = config_tab.content.controls[1].content.content
            
            config_card.value = "\n".join(config_text)
            
        except Exception as e:
            self.logger.error(f'Erro ao atualizar configurações: {str(e)}')
    
    def update_extracted_data(self, data: List[FacebookData]) -> None:
        """Atualizar dados extraídos.
        
        Args:
            data: Lista de dados extraídos
        """
        try:
            self.extracted_data = data
            
            self.data_list.controls.clear()
            
            if not data:
                self.data_list.controls.append(
                    ft.Container(
                        content=ft.Text(
                            "Nenhum dado extraído ainda",
                            color=ft.colors.GREY_600,
                            text_align=ft.TextAlign.CENTER
                        ),
                        alignment=ft.alignment.center,
                        padding=ft.padding.all(20)
                    )
                )
            else:
                for item in data[:50]:  # Limitar a 50 itens para performance
                    self.data_list.controls.append(self._create_data_item(item))
                
                if len(data) > 50:
                    self.data_list.controls.append(
                        ft.Container(
                            content=ft.Text(
                                f"... e mais {len(data) - 50} itens",
                                color=ft.colors.GREY_600,
                                text_align=ft.TextAlign.CENTER,
                                italic=True
                            ),
                            alignment=ft.alignment.center,
                            padding=ft.padding.all(10)
                        )
                    )
            
            self.update()
            
        except Exception as e:
            self.logger.error(f'Erro ao atualizar dados extraídos: {str(e)}')
    
    def _create_data_item(self, data: FacebookData) -> ft.Container:
        """Criar item de dados extraídos."""
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Chip(
                        label=ft.Text(data.data_type.title()),
                        bgcolor=ft.colors.BLUE_100
                    ),
                    ft.Text(
                        data.extracted_at.strftime('%d/%m/%Y %H:%M:%S') if data.extracted_at else 'N/A',
                        size=12,
                        color=ft.colors.GREY_600
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                ft.Text(
                    data.get_content_preview(200),
                    size=12,
                    color=ft.colors.GREY_800
                ),
                
                ft.Row([
                    ft.Text(f"Autor: {data.get_author() or 'N/A'}", size=10, color=ft.colors.GREY_600),
                    ft.Text(f"Curtidas: {data.get_likes_count()}", size=10, color=ft.colors.GREY_600),
                    ft.Text(f"Comentários: {data.get_comments_count()}", size=10, color=ft.colors.GREY_600)
                ])
            ], spacing=5),
            padding=ft.padding.all(10),
            margin=ft.margin.only(bottom=5),
            border_radius=5,
            bgcolor=ft.colors.WHITE,
            border=ft.border.all(1, ft.colors.GREY_300)
        )
    
    def add_log_message(self, message: str, level: str = "INFO") -> None:
        """Adicionar mensagem de log.
        
        Args:
            message: Mensagem do log
            level: Nível do log (INFO, WARNING, ERROR)
        """
        try:
            # Cores por nível
            level_colors = {
                'INFO': ft.colors.BLUE_600,
                'WARNING': ft.colors.ORANGE_600,
                'ERROR': ft.colors.RED_600
            }
            
            color = level_colors.get(level, ft.colors.GREY_600)
            
            log_item = ft.Container(
                content=ft.Row([
                    ft.Text(
                        datetime.now().strftime('%H:%M:%S'),
                        size=10,
                        color=ft.colors.GREY_600,
                        width=60
                    ),
                    ft.Text(
                        level,
                        size=10,
                        color=color,
                        weight=ft.FontWeight.BOLD,
                        width=60
                    ),
                    ft.Text(
                        message,
                        size=12,
                        color=ft.colors.GREY_800,
                        expand=True
                    )
                ]),
                padding=ft.padding.symmetric(vertical=2, horizontal=5),
                border_radius=3,
                bgcolor=ft.colors.WHITE
            )
            
            self.logs_list.controls.append(log_item)
            
            # Manter apenas os últimos 100 logs
            if len(self.logs_list.controls) > 100:
                self.logs_list.controls.pop(0)
            
            # Scroll para o final
            if hasattr(self.logs_list, 'scroll_to'):
                self.logs_list.scroll_to(offset=-1, duration=100)
            
            self.update()
            
        except Exception as e:
            self.logger.error(f'Erro ao adicionar log: {str(e)}')
    
    def _handle_start_task(self) -> None:
        """Manipular início da tarefa."""
        if self.on_start_task:
            self.on_start_task(self.task_id)
    
    def _handle_stop_task(self) -> None:
        """Manipular parada da tarefa."""
        if self.on_stop_task:
            self.on_stop_task(self.task_id)
    
    def _handle_export_task(self) -> None:
        """Manipular exportação da tarefa."""
        if self.on_export_task:
            self.on_export_task(self.task_id)
    
    def _handle_back(self) -> None:
        """Manipular volta ao dashboard."""
        if self.on_back:
            self.on_back()
    
    def _refresh_logs(self) -> None:
        """Atualizar logs."""
        # Implementado pelo controlador principal
        pass
    
    def _refresh_data(self) -> None:
        """Atualizar dados extraídos."""
        # Implementado pelo controlador principal
        pass