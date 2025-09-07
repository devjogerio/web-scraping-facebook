#!/usr/bin/env python3
"""
Versão específica para macOS com configurações otimizadas.
"""

import flet as ft
import os
import sys
from datetime import datetime

def main(page: ft.Page):
    """Função principal otimizada para macOS."""
    print("🚀 Iniciando aplicação otimizada para macOS...")
    
    # Configurações específicas para macOS
    page.title = "Facebook Scraper - macOS"
    page.window_width = 900
    page.window_height = 600
    page.window_min_width = 600
    page.window_min_height = 400
    page.window_center = True
    page.window_resizable = True
    page.window_maximizable = True
    page.window_minimizable = True
    page.window_always_on_top = False
    page.window_focused = True
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO
    
    # Forçar foco na janela
    page.window_to_front = True
    
    print("✅ Configurações específicas para macOS aplicadas")
    
    # Interface simples mas funcional
    def show_message(message):
        """Mostrar mensagem na interface."""
        message_text.value = f"📝 {message} - {datetime.now().strftime('%H:%M:%S')}"
        page.update()
        print(f"📝 {message}")
    
    def test_button_click(e):
        """Testar funcionalidade do botão."""
        show_message("Botão funcionando perfeitamente!")
    
    def add_item_click(e):
        """Adicionar item à lista."""
        if input_field.value:
            items_list.controls.append(
                ft.ListTile(
                    leading=ft.Icon(ft.icons.TASK_ALT, color=ft.colors.BLUE),
                    title=ft.Text(input_field.value),
                    subtitle=ft.Text(f"Adicionado em {datetime.now().strftime('%H:%M:%S')}"),
                    trailing=ft.IconButton(
                        icon=ft.icons.DELETE,
                        on_click=lambda _: remove_item(input_field.value)
                    )
                )
            )
            show_message(f"Item '{input_field.value}' adicionado com sucesso")
            input_field.value = ""
            page.update()
        else:
            show_message("Digite algo no campo de texto primeiro")
    
    def remove_item(item_name):
        """Remover item da lista."""
        show_message(f"Item '{item_name}' removido")
        # Recarregar lista (implementação simplificada)
        page.update()
    
    # Componentes da interface
    title_text = ft.Text(
        "🚀 Facebook Scraper - Teste macOS",
        size=24,
        weight=ft.FontWeight.BOLD,
        color=ft.colors.BLUE_800
    )
    
    subtitle_text = ft.Text(
        "Versão otimizada para macOS - Testando funcionalidades",
        size=14,
        color=ft.colors.GREY_600
    )
    
    message_text = ft.Text(
        "🟢 Sistema inicializado com sucesso",
        size=12,
        color=ft.colors.GREEN
    )
    
    input_field = ft.TextField(
        label="Digite algo para testar",
        hint_text="Ex: Nova tarefa de scraping",
        width=400,
        on_submit=add_item_click
    )
    
    test_button = ft.ElevatedButton(
        "Testar Funcionalidade",
        icon=ft.icons.PLAY_ARROW,
        on_click=test_button_click,
        style=ft.ButtonStyle(
            color=ft.colors.WHITE,
            bgcolor=ft.colors.GREEN_600
        )
    )
    
    add_button = ft.ElevatedButton(
        "Adicionar Item",
        icon=ft.icons.ADD,
        on_click=add_item_click,
        style=ft.ButtonStyle(
            color=ft.colors.WHITE,
            bgcolor=ft.colors.BLUE_600
        )
    )
    
    items_list = ft.ListView(
        expand=True,
        spacing=5,
        padding=ft.padding.all(10)
    )
    
    # Adicionar alguns itens de exemplo
    items_list.controls.extend([
        ft.ListTile(
            leading=ft.Icon(ft.icons.INFO, color=ft.colors.BLUE),
            title=ft.Text("Interface carregada com sucesso"),
            subtitle=ft.Text("Sistema funcionando normalmente")
        ),
        ft.ListTile(
            leading=ft.Icon(ft.icons.CHECK_CIRCLE, color=ft.colors.GREEN),
            title=ft.Text("Configurações aplicadas"),
            subtitle=ft.Text("Otimizações para macOS ativas")
        ),
        ft.ListTile(
            leading=ft.Icon(ft.icons.DESKTOP_MAC, color=ft.colors.ORANGE),
            title=ft.Text("Compatibilidade macOS"),
            subtitle=ft.Text("Versão específica para sistema Apple")
        )
    ])
    
    # Construir layout principal
    page.add(
        ft.Column([
            # Cabeçalho
            ft.Container(
                content=ft.Column([
                    title_text,
                    subtitle_text,
                    ft.Divider(height=20, color=ft.colors.GREY_300)
                ]),
                padding=ft.padding.only(bottom=20)
            ),
            
            # Status
            ft.Container(
                content=message_text,
                padding=10,
                border_radius=5,
                bgcolor=ft.colors.GREY_50,
                border=ft.border.all(1, ft.colors.GREY_300)
            ),
            
            # Controles
            ft.Container(
                content=ft.Row([
                    input_field,
                    add_button,
                    test_button
                ], alignment=ft.MainAxisAlignment.START),
                padding=ft.padding.symmetric(vertical=20)
            ),
            
            # Lista de itens
            ft.Container(
                content=ft.Column([
                    ft.Text("Lista de Itens", size=16, weight=ft.FontWeight.BOLD),
                    ft.Container(
                        content=items_list,
                        height=250,
                        border_radius=10,
                        bgcolor=ft.colors.WHITE,
                        border=ft.border.all(1, ft.colors.GREY_300)
                    )
                ]),
                expand=True
            )
        ], expand=True)
    )
    
    print("✅ Interface construída")
    
    # Forçar atualização e foco
    page.update()
    
    print("✅ Página atualizada")
    print("🎯 Se você está vendo esta mensagem, a aplicação foi inicializada")
    print("🖥️  Uma janela deve ter sido aberta no seu macOS")
    
    # Mostrar mensagem de sucesso
    show_message("Interface carregada e funcionando!")

if __name__ == "__main__":
    print("="*60)
    print("🍎 FACEBOOK SCRAPER - VERSÃO MACOS")
    print("="*60)
    print(f"🐍 Python: {sys.version}")
    print(f"💻 Sistema: {os.name}")
    print(f"📁 Diretório: {os.getcwd()}")
    print("="*60)
    
    try:
        print("🚀 Iniciando aplicação Flet...")
        
        # Configurações específicas para macOS
        ft.app(
            target=main,
            view=ft.AppView.FLET_APP,
            port=0,
            web_renderer=ft.WebRenderer.HTML,
            route_url_strategy="hash"
        )
        
    except Exception as e:
        print(f"❌ ERRO CRÍTICO: {str(e)}")
        print("📋 Stack trace:")
        import traceback
        traceback.print_exc()
        print("\n💡 Possíveis soluções:")
        print("   1. Verificar se o Flet está instalado: pip install flet")
        print("   2. Verificar permissões do sistema")
        print("   3. Tentar executar como administrador")
        print("   4. Verificar se há conflitos com outros programas")
    
    print("\n🏁 Execução finalizada.")
    print("="*60)