#!/usr/bin/env python3
"""
Versão simplificada da aplicação Flet para garantir funcionamento.
"""

import flet as ft
import sqlite3
import os
from datetime import datetime

def create_simple_database():
    """Criar banco de dados simples."""
    if not os.path.exists('data'):
        os.makedirs('data')
    
    conn = sqlite3.connect('data/facebook_scraper.db')
    cursor = conn.cursor()
    
    # Criar tabela simples de tarefas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Banco de dados criado com sucesso")

def get_tasks():
    """Obter lista de tarefas."""
    conn = sqlite3.connect('data/facebook_scraper.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tasks ORDER BY created_at DESC LIMIT 10')
    tasks = cursor.fetchall()
    conn.close()
    return tasks

def add_task(name, url):
    """Adicionar nova tarefa."""
    conn = sqlite3.connect('data/facebook_scraper.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO tasks (name, url) VALUES (?, ?)', (name, url))
    conn.commit()
    conn.close()
    print(f"✅ Tarefa '{name}' adicionada com sucesso")

def main(page: ft.Page):
    """Função principal simplificada."""
    print("🚀 Iniciando aplicação simplificada...")
    
    # Configurações da página
    page.title = "Facebook Scraper - Versão Simplificada"
    page.window_width = 1000
    page.window_height = 700
    page.window_center = True
    page.window_resizable = True
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    
    print("✅ Configurações da página definidas")
    
    # Criar banco de dados
    create_simple_database()
    
    # Componentes da interface
    task_name = ft.TextField(
        label="Nome da Tarefa",
        hint_text="Digite o nome da tarefa",
        width=300
    )
    
    task_url = ft.TextField(
        label="URL do Facebook",
        hint_text="https://facebook.com/...",
        width=400
    )
    
    tasks_list = ft.ListView(
        expand=True,
        spacing=10,
        padding=ft.padding.all(10)
    )
    
    status_text = ft.Text(
        "Pronto para uso",
        size=14,
        color=ft.colors.GREEN
    )
    
    def refresh_tasks():
        """Atualizar lista de tarefas."""
        tasks_list.controls.clear()
        tasks = get_tasks()
        
        if not tasks:
            tasks_list.controls.append(
                ft.Container(
                    content=ft.Text(
                        "Nenhuma tarefa encontrada. Adicione uma nova tarefa acima.",
                        size=16,
                        text_align=ft.TextAlign.CENTER,
                        color=ft.colors.GREY_600
                    ),
                    padding=20,
                    alignment=ft.alignment.center
                )
            )
        else:
            for task in tasks:
                task_id, name, url, status, created_at = task
                
                # Determinar cor do status
                status_color = {
                    'pending': ft.colors.ORANGE,
                    'running': ft.colors.BLUE,
                    'completed': ft.colors.GREEN,
                    'failed': ft.colors.RED
                }.get(status, ft.colors.GREY)
                
                tasks_list.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Text(name, size=16, weight=ft.FontWeight.BOLD),
                                ft.Text(url[:50] + "..." if len(url) > 50 else url, size=12, color=ft.colors.GREY_600),
                                ft.Text(f"Criado: {created_at}", size=10, color=ft.colors.GREY_500)
                            ], expand=True),
                            ft.Container(
                                content=ft.Text(status.upper(), color=ft.colors.WHITE, size=12, weight=ft.FontWeight.BOLD),
                                bgcolor=status_color,
                                padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                border_radius=15
                            )
                        ]),
                        padding=15,
                        border_radius=10,
                        bgcolor=ft.colors.WHITE,
                        border=ft.border.all(1, ft.colors.GREY_300)
                    )
                )
        
        page.update()
        print(f"✅ Lista atualizada com {len(tasks)} tarefas")
    
    def add_new_task(e):
        """Adicionar nova tarefa."""
        if not task_name.value or not task_url.value:
            status_text.value = "❌ Preencha todos os campos"
            status_text.color = ft.colors.RED
            page.update()
            return
        
        try:
            add_task(task_name.value, task_url.value)
            task_name.value = ""
            task_url.value = ""
            status_text.value = f"✅ Tarefa adicionada com sucesso"
            status_text.color = ft.colors.GREEN
            refresh_tasks()
        except Exception as ex:
            status_text.value = f"❌ Erro: {str(ex)}"
            status_text.color = ft.colors.RED
        
        page.update()
    
    # Construir interface
    page.add(
        ft.Column([
            # Cabeçalho
            ft.Container(
                content=ft.Row([
                    ft.Text(
                        "🚀 Facebook Scraper",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.BLUE_800
                    ),
                    ft.Text(
                        f"Versão Simplificada - {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                        size=12,
                        color=ft.colors.GREY_600
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=ft.padding.only(bottom=20)
            ),
            
            # Formulário de nova tarefa
            ft.Container(
                content=ft.Column([
                    ft.Text("Nova Tarefa", size=18, weight=ft.FontWeight.BOLD),
                    ft.Row([
                        task_name,
                        task_url,
                        ft.ElevatedButton(
                            "Adicionar",
                            icon=ft.icons.ADD,
                            on_click=add_new_task,
                            style=ft.ButtonStyle(
                                color=ft.colors.WHITE,
                                bgcolor=ft.colors.BLUE_600
                            )
                        )
                    ], alignment=ft.MainAxisAlignment.START),
                    status_text
                ]),
                padding=20,
                border_radius=10,
                bgcolor=ft.colors.GREY_50,
                border=ft.border.all(1, ft.colors.GREY_300),
                margin=ft.margin.only(bottom=20)
            ),
            
            # Lista de tarefas
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("Tarefas", size=18, weight=ft.FontWeight.BOLD),
                        ft.IconButton(
                            icon=ft.icons.REFRESH,
                            tooltip="Atualizar lista",
                            on_click=lambda _: refresh_tasks()
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Container(
                        content=tasks_list,
                        height=300,
                        border_radius=10,
                        bgcolor=ft.colors.GREY_50,
                        border=ft.border.all(1, ft.colors.GREY_300)
                    )
                ]),
                expand=True
            )
        ], expand=True)
    )
    
    # Carregar tarefas iniciais
    refresh_tasks()
    
    print("✅ Interface construída com sucesso")
    page.update()
    print("✅ Página atualizada - interface deve estar visível")

if __name__ == "__main__":
    print("🔄 Iniciando Facebook Scraper Simplificado...")
    try:
        ft.app(
            target=main,
            view=ft.AppView.FLET_APP,
            port=0
        )
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()
    print("🏁 Aplicação finalizada.")