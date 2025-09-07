#!/usr/bin/env python3
"""
Teste simples do Flet para verificar funcionamento básico.
"""

import flet as ft

def main(page: ft.Page):
    """Função principal de teste do Flet."""
    page.title = "Teste Flet - Facebook Scraper"
    page.window_width = 800
    page.window_height = 600
    page.window_center = True
    
    # Adicionar conteúdo simples
    page.add(
        ft.Column([
            ft.Text("🚀 Teste Flet Funcionando!", size=30, weight=ft.FontWeight.BOLD),
            ft.Text("Se você está vendo esta mensagem, o Flet está funcionando corretamente.", size=16),
            ft.ElevatedButton(
                "Clique aqui para testar",
                on_click=lambda _: page.add(ft.Text("✅ Botão funcionando!", color=ft.colors.GREEN))
            )
        ], 
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )
    
    page.update()
    print("✅ Interface Flet carregada com sucesso!")

if __name__ == "__main__":
    print("🔄 Iniciando teste simples do Flet...")
    ft.app(target=main, view=ft.AppView.FLET_APP)
    print("🏁 Teste finalizado.")