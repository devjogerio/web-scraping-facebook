#!/usr/bin/env python3
"""Teste simples do Flet para verificar funcionamento."""

import flet as ft

def main(page: ft.Page):
    """Função principal de teste."""
    page.title = "Teste Flet"
    page.window_width = 400
    page.window_height = 300
    
    def button_clicked(e):
        txt.value = "Flet está funcionando!"
        page.update()
    
    txt = ft.Text("Clique no botão para testar")
    btn = ft.ElevatedButton("Testar", on_click=button_clicked)
    
    page.add(txt, btn)

if __name__ == "__main__":
    print("Iniciando teste do Flet...")
    ft.app(target=main)
    print("Teste finalizado.")