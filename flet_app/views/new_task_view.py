"""View do formulário de nova tarefa - Versão Flet.

Este módulo implementa a interface para criação de novas
tarefas de scraping com validação em tempo real.
"""

import flet as ft
from typing import Optional, Callable, Dict, Any, List

from flet_app.config.logging_config import get_logger


class NewTaskView(ft.UserControl):
    """View do formulário de nova tarefa.
    
    Permite criar novas tarefas de scraping com configurações
    personalizadas e validação em tempo real.
    """
    
    def __init__(self, 
                 on_create_task: Optional[Callable[[Dict[str, Any]], None]] = None,
                 on_cancel: Optional[Callable[[], None]] = None,
                 on_validate_url: Optional[Callable[[str], tuple[bool, str]]] = None):
        """Inicializar view de nova tarefa.
        
        Args:
            on_create_task: Callback para criar tarefa
            on_cancel: Callback para cancelar criação
            on_validate_url: Callback para validar URL
        """
        super().__init__()
        self.logger = get_logger('NewTaskView')
        
        # Callbacks
        self.on_create_task = on_create_task
        self.on_cancel = on_cancel
        self.on_validate_url = on_validate_url
        
        # Campos do formulário
        self.name_field = ft.TextField(
            label="Nome da Tarefa",
            hint_text="Digite um nome descritivo para a tarefa",
            on_change=self._validate_form,
            autofocus=True
        )
        
        self.url_field = ft.TextField(
            label="URL do Facebook",
            hint_text="https://www.facebook.com/pagina-exemplo",
            on_change=self._validate_form,
            on_blur=self._validate_url
        )
        
        # Checkboxes para tipos de dados
        self.data_types_checkboxes = {
            'post': ft.Checkbox(label="Posts", value=True),
            'comment': ft.Checkbox(label="Comentários", value=True),
            'profile': ft.Checkbox(label="Informações de Perfil", value=False),
            'like': ft.Checkbox(label="Curtidas", value=False),
            'share': ft.Checkbox(label="Compartilhamentos", value=False)
        }
        
        # Campo de limite de itens
        self.max_items_field = ft.TextField(
            label="Máximo de Itens",
            hint_text="100",
            value="100",
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=self._validate_form
        )
        
        # Configurações avançadas
        self.delay_min_field = ft.TextField(
            label="Delay Mínimo (segundos)",
            hint_text="1",
            value="1",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=150
        )
        
        self.delay_max_field = ft.TextField(
            label="Delay Máximo (segundos)",
            hint_text="3",
            value="3",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=150
        )
        
        self.headless_checkbox = ft.Checkbox(
            label="Executar em modo headless (sem interface gráfica)",
            value=True
        )
        
        # Botões
        self.create_button = ft.ElevatedButton(
            "Criar Tarefa",
            icon=ft.icons.ADD_TASK,
            on_click=self._handle_create_task,
            disabled=True,
            style=ft.ButtonStyle(
                color=ft.colors.WHITE,
                bgcolor=ft.colors.BLUE_600
            )
        )
        
        self.cancel_button = ft.TextButton(
            "Cancelar",
            on_click=self._handle_cancel
        )
        
        # Mensagens de validação
        self.validation_messages = ft.Column(spacing=5)
        
        # Seção de configurações avançadas (inicialmente oculta)
        self.advanced_section_visible = False
        self.advanced_toggle = ft.TextButton(
            "Mostrar Configurações Avançadas",
            icon=ft.icons.EXPAND_MORE,
            on_click=self._toggle_advanced_section
        )
    
    def build(self):
        """Construir interface do formulário."""
        return ft.Container(
            content=ft.Column([
                # Cabeçalho
                self._build_header(),
                
                # Formulário principal
                self._build_main_form(),
                
                # Configurações avançadas
                self._build_advanced_section(),
                
                # Mensagens de validação
                self.validation_messages,
                
                # Botões
                self._build_buttons_section()
            ], scroll=ft.ScrollMode.AUTO),
            padding=ft.padding.all(20),
            expand=True
        )
    
    def _build_header(self) -> ft.Container:
        """Construir cabeçalho do formulário."""
        return ft.Container(
            content=ft.Column([
                ft.Text(
                    "Nova Tarefa de Scraping",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.BLUE_800
                ),
                ft.Text(
                    "Configure uma nova tarefa para extrair dados do Facebook",
                    size=14,
                    color=ft.colors.GREY_600
                )
            ]),
            padding=ft.padding.only(bottom=20)
        )
    
    def _build_main_form(self) -> ft.Container:
        """Construir formulário principal."""
        return ft.Container(
            content=ft.Column([
                # Informações básicas
                ft.Text(
                    "Informações Básicas",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.GREY_800
                ),
                
                self.name_field,
                self.url_field,
                
                # Tipos de dados
                ft.Text(
                    "Tipos de Dados para Extrair",
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.GREY_800
                ),
                
                ft.Row([
                    ft.Column([
                        self.data_types_checkboxes['post'],
                        self.data_types_checkboxes['comment']
                    ]),
                    ft.Column([
                        self.data_types_checkboxes['profile'],
                        self.data_types_checkboxes['like']
                    ]),
                    ft.Column([
                        self.data_types_checkboxes['share']
                    ])
                ]),
                
                # Limite de itens
                self.max_items_field
            ], spacing=15),
            padding=ft.padding.only(bottom=20)
        )
    
    def _build_advanced_section(self) -> ft.Container:
        """Construir seção de configurações avançadas."""
        advanced_content = ft.Column([
            ft.Text(
                "Configurações Avançadas",
                size=16,
                weight=ft.FontWeight.BOLD,
                color=ft.colors.GREY_800
            ),
            
            ft.Row([
                self.delay_min_field,
                self.delay_max_field
            ], spacing=20),
            
            self.headless_checkbox,
            
            ft.Text(
                "Nota: Delays maiores reduzem o risco de bloqueio, mas tornam o processo mais lento.",
                size=12,
                color=ft.colors.GREY_600,
                italic=True
            )
        ], spacing=10, visible=self.advanced_section_visible)
        
        return ft.Container(
            content=ft.Column([
                self.advanced_toggle,
                advanced_content
            ]),
            padding=ft.padding.only(bottom=20)
        )
    
    def _build_buttons_section(self) -> ft.Container:
        """Construir seção de botões."""
        return ft.Container(
            content=ft.Row([
                self.cancel_button,
                self.create_button
            ], alignment=ft.MainAxisAlignment.END, spacing=10),
            padding=ft.padding.only(top=20)
        )
    
    def _toggle_advanced_section(self, e) -> None:
        """Alternar visibilidade da seção avançada."""
        self.advanced_section_visible = not self.advanced_section_visible
        
        # Atualizar visibilidade
        advanced_content = self.controls[0].content.controls[2].content.controls[1]
        advanced_content.visible = self.advanced_section_visible
        
        # Atualizar texto e ícone do botão
        if self.advanced_section_visible:
            self.advanced_toggle.text = "Ocultar Configurações Avançadas"
            self.advanced_toggle.icon = ft.icons.EXPAND_LESS
        else:
            self.advanced_toggle.text = "Mostrar Configurações Avançadas"
            self.advanced_toggle.icon = ft.icons.EXPAND_MORE
        
        self.update()
    
    def _validate_form(self, e=None) -> None:
        """Validar formulário em tempo real."""
        try:
            errors = []
            
            # Validar nome
            name = self.name_field.value or ""
            if len(name.strip()) < 3:
                errors.append("Nome deve ter pelo menos 3 caracteres")
            elif len(name.strip()) > 255:
                errors.append("Nome deve ter no máximo 255 caracteres")
            
            # Validar URL
            url = self.url_field.value or ""
            if not url.strip():
                errors.append("URL é obrigatória")
            elif not self._is_facebook_url(url):
                errors.append("URL deve ser do Facebook")
            
            # Validar tipos de dados
            selected_types = [key for key, checkbox in self.data_types_checkboxes.items() if checkbox.value]
            if not selected_types:
                errors.append("Selecione pelo menos um tipo de dado")
            
            # Validar limite de itens
            try:
                max_items = int(self.max_items_field.value or "0")
                if max_items <= 0:
                    errors.append("Máximo de itens deve ser maior que zero")
                elif max_items > 10000:
                    errors.append("Máximo de itens não pode ser maior que 10.000")
            except ValueError:
                errors.append("Máximo de itens deve ser um número válido")
            
            # Atualizar mensagens de validação
            self._update_validation_messages(errors)
            
            # Habilitar/desabilitar botão de criar
            self.create_button.disabled = len(errors) > 0
            self.update()
            
        except Exception as ex:
            self.logger.error(f'Erro na validação do formulário: {str(ex)}')
    
    def _validate_url(self, e) -> None:
        """Validar URL quando o campo perde o foco."""
        if self.on_validate_url and self.url_field.value:
            try:
                is_valid, message = self.on_validate_url(self.url_field.value)
                
                if not is_valid:
                    self._show_url_validation_error(message)
                else:
                    self._clear_url_validation_error()
                    
            except Exception as ex:
                self.logger.error(f'Erro na validação da URL: {str(ex)}')
    
    def _is_facebook_url(self, url: str) -> bool:
        """Verificar se é uma URL do Facebook."""
        facebook_domains = [
            'facebook.com',
            'www.facebook.com',
            'm.facebook.com',
            'mobile.facebook.com'
        ]
        
        url_lower = url.lower()
        return any(domain in url_lower for domain in facebook_domains)
    
    def _update_validation_messages(self, errors: List[str]) -> None:
        """Atualizar mensagens de validação."""
        self.validation_messages.controls.clear()
        
        for error in errors:
            self.validation_messages.controls.append(
                ft.Row([
                    ft.Icon(ft.icons.ERROR, color=ft.colors.RED_600, size=16),
                    ft.Text(
                        error,
                        color=ft.colors.RED_600,
                        size=12
                    )
                ])
            )
    
    def _show_url_validation_error(self, message: str) -> None:
        """Exibir erro de validação da URL."""
        self.url_field.error_text = message
        self.update()
    
    def _clear_url_validation_error(self) -> None:
        """Limpar erro de validação da URL."""
        self.url_field.error_text = None
        self.update()
    
    def _handle_create_task(self, e) -> None:
        """Manipular criação da tarefa."""
        try:
            if self.on_create_task:
                # Coletar dados do formulário
                task_data = self._collect_form_data()
                self.on_create_task(task_data)
                
        except Exception as ex:
            self.logger.error(f'Erro ao criar tarefa: {str(ex)}')
            self._show_error(f'Erro ao criar tarefa: {str(ex)}')
    
    def _handle_cancel(self, e) -> None:
        """Manipular cancelamento."""
        if self.on_cancel:
            self.on_cancel()
    
    def _collect_form_data(self) -> Dict[str, Any]:
        """Coletar dados do formulário."""
        # Tipos de dados selecionados
        selected_types = [key for key, checkbox in self.data_types_checkboxes.items() if checkbox.value]
        
        # Configurações avançadas
        delay_min = float(self.delay_min_field.value or "1")
        delay_max = float(self.delay_max_field.value or "3")
        
        return {
            'name': self.name_field.value.strip(),
            'url': self.url_field.value.strip(),
            'config': {
                'data_types': selected_types,
                'max_items': int(self.max_items_field.value or "100"),
                'delay_min': delay_min,
                'delay_max': delay_max,
                'headless': self.headless_checkbox.value,
                'include_reactions': True,
                'include_shares': True,
                'extract_links': False,
                'extract_images': False
            }
        }
    
    def _show_error(self, message: str) -> None:
        """Exibir mensagem de erro."""
        # Adicionar mensagem de erro à lista de validação
        self.validation_messages.controls.append(
            ft.Row([
                ft.Icon(ft.icons.ERROR, color=ft.colors.RED_600, size=16),
                ft.Text(
                    message,
                    color=ft.colors.RED_600,
                    size=12
                )
            ])
        )
        self.update()
    
    def clear_form(self) -> None:
        """Limpar formulário."""
        self.name_field.value = ""
        self.url_field.value = ""
        self.max_items_field.value = "100"
        self.delay_min_field.value = "1"
        self.delay_max_field.value = "3"
        
        # Resetar checkboxes
        self.data_types_checkboxes['post'].value = True
        self.data_types_checkboxes['comment'].value = True
        self.data_types_checkboxes['profile'].value = False
        self.data_types_checkboxes['like'].value = False
        self.data_types_checkboxes['share'].value = False
        
        self.headless_checkbox.value = True
        
        # Limpar mensagens de validação
        self.validation_messages.controls.clear()
        
        # Desabilitar botão de criar
        self.create_button.disabled = True
        
        self.update()
    
    def set_suggested_name(self, name: str) -> None:
        """Definir nome sugerido."""
        self.name_field.value = name
        self._validate_form()
    
    def show_loading(self, message: str = "Criando tarefa...") -> None:
        """Exibir indicador de carregamento."""
        self.create_button.disabled = True
        self.create_button.text = message
        self.update()
    
    def hide_loading(self) -> None:
        """Ocultar indicador de carregamento."""
        self.create_button.text = "Criar Tarefa"
        self._validate_form()  # Revalidar para habilitar/desabilitar botão