#!/usr/bin/env python3
"""Script de teste para verificar se a interface Flet está funcionando.

Este script testa a funcionalidade básica da aplicação
e verifica se a janela está sendo exibida corretamente.
"""

import flet as ft
from flet_app.main import main


def test_basic_interface():
    """Testar interface básica do Flet."""
    def simple_app(page: ft.Page):
        page.title = "✅ Teste - Interface Funcionando!"
        page.window_width = 600
        page.window_height = 400
        page.window_center()
        
        def close_and_run_main(e):
            page.window_close()
            print("🚀 Agora execute: python -m flet_app.main")
        
        # Adicionar elementos de teste
        page.add(
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.icons.CHECK_CIRCLE, color=ft.colors.GREEN, size=64),
                    ft.Text(
                        "🎉 Interface Flet Funcionando!", 
                        size=24, 
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.Text(
                        "Se você está vendo esta janela, a interface está renderizando corretamente!",
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.Divider(),
                    ft.Text(
                        "✅ Teste de Interface: PASSOU",
                        color=ft.colors.GREEN,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.ElevatedButton(
                        "Fechar e Executar Aplicação Principal",
                        on_click=close_and_run_main,
                        style=ft.ButtonStyle(
                            color=ft.colors.WHITE,
                            bgcolor=ft.colors.BLUE
                        )
                    )
                ], 
                spacing=20,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                padding=ft.padding.all(30),
                alignment=ft.alignment.center
            )
        )
        
        page.update()
    
    print("🧪 Testando interface básica...")
    print("📋 Se uma janela abrir, a interface está funcionando!")
    ft.app(target=simple_app, view=ft.AppView.FLET_APP)


def test_main_app():
    """Testar aplicação principal diretamente."""
    print("🚀 Testando aplicação principal...")
    print("📋 Aguarde a janela do Facebook Scraper abrir...")
    ft.app(target=main, view=ft.AppView.FLET_APP)


if __name__ == "__main__":
    import sys
    
    print("🔍 Teste da Interface Flet - Facebook Scraper")
    print("=" * 50)
    print("📋 Opções de teste:")
    print("   1. Teste básico da interface")
    print("   2. Teste da aplicação principal")
    print()
    
    if len(sys.argv) > 1 and sys.argv[1] == "main":
        test_main_app()
    else:
        test_basic_interface()