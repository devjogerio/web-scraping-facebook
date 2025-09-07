#!/usr/bin/env python3
"""
Facebook Scraper - Versão Final Otimizada

Versão definitiva da aplicação com interface Flet
que garante funcionamento em sistemas macOS.
"""

import flet as ft
import sqlite3
import os
import sys
import platform
from datetime import datetime
from pathlib import Path

# Configurações globais
APP_TITLE = "Facebook Scraper - Versão Final"
DB_PATH = "data/facebook_scraper.db"

def ensure_data_directory():
    """Garantir que o diretório de dados existe."""
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    return data_dir

def init_database():
    """Inicializar banco de dados SQLite."""
    ensure_data_directory()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Criar tabela de tarefas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scraping_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            data_types TEXT DEFAULT 'post,comment',
            max_items INTEGER DEFAULT 100,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            items_processed INTEGER DEFAULT 0,
            error_message TEXT
        )
    ''')
    
    # Criar tabela de dados extraídos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS facebook_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            data_type TEXT NOT NULL,
            content TEXT,
            author TEXT,
            timestamp TEXT,
            likes_count INTEGER DEFAULT 0,
            extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES scraping_tasks (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Banco de dados inicializado")

def get_tasks():
    """Obter lista de tarefas."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, name, url, status, items_processed, created_at 
        FROM scraping_tasks 
        ORDER BY created_at DESC 
        LIMIT 20
    ''')
    tasks = cursor.fetchall()
    conn.close()
    return tasks

def add_task(name, url, data_types="post,comment", max_items=100):
    """Adicionar nova tarefa."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO scraping_tasks (name, url, data_types, max_items) 
        VALUES (?, ?, ?, ?)
    ''', (name, url, data_types, max_items))
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return task_id

def update_task_status(task_id, status, error_message=None):
    """Atualizar status da tarefa."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE scraping_tasks 
        SET status = ?, error_message = ?, updated_at = CURRENT_TIMESTAMP 
        WHERE id = ?
    ''', (status, error_message, task_id))
    conn.commit()
    conn.close()

def get_statistics():
    """Obter estatísticas das tarefas."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    stats = {}
    
    # Total de tarefas
    cursor.execute('SELECT COUNT(*) FROM scraping_tasks')
    stats['total'] = cursor.fetchone()[0]
    
    # Por status
    for status in ['pending', 'running', 'completed', 'failed']:
        cursor.execute('SELECT COUNT(*) FROM scraping_tasks WHERE status = ?', (status,))
        stats[status] = cursor.fetchone()[0]
    
    # Total de dados extraídos
    cursor.execute('SELECT COUNT(*) FROM facebook_data')
    stats['total_data'] = cursor.fetchone()[0]
    
    conn.close()
    return stats

def main(page: ft.Page):
    """Função principal da aplicação."""
    print("🚀 Iniciando Facebook Scraper Final...")
    
    # Configurações da página
    page.title = APP_TITLE
    page.window_width = 1100
    page.window_height = 750
    page.window_min_width = 800
    page.window_min_height = 600
    page.window_center = True
    page.window_resizable = True
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO
    
    # Configurar tema
    page.theme = ft.Theme(
        color_scheme_seed=ft.colors.BLUE,
        use_material3=True
    )
    
    print("✅ Configurações da página aplicadas")
    
    # Inicializar banco de dados
    init_database()
    
    # Componentes da interface
    status_text = ft.Text(
        "🟢 Sistema inicializado com sucesso",
        size=14,
        color=ft.colors.GREEN
    )
    
    # Campos do formulário
    task_name_field = ft.TextField(
        label="Nome da Tarefa",
        hint_text="Ex: Scraping Página Facebook",
        width=300,
        value=""
    )
    
    task_url_field = ft.TextField(
        label="URL do Facebook",
        hint_text="https://facebook.com/...",
        width=400,
        value=""
    )
    
    max_items_field = ft.TextField(
        label="Máximo de Itens",
        hint_text="100",
        width=150,
        value="100"
    )
    
    # Lista de tarefas
    tasks_list = ft.ListView(
        expand=True,
        spacing=10,
        padding=ft.padding.all(10)
    )
    
    # Cards de estatísticas
    stats_cards = ft.Row([
        ft.Container(
            content=ft.Column([
                ft.Text("0", size=24, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE),
                ft.Text("Total", size=12, color=ft.colors.GREY_600)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=15,
            border_radius=10,
            bgcolor=ft.colors.WHITE,
            border=ft.border.all(1, ft.colors.GREY_300),
            width=120
        ),
        ft.Container(
            content=ft.Column([
                ft.Text("0", size=24, weight=ft.FontWeight.BOLD, color=ft.colors.GREEN),
                ft.Text("Concluídas", size=12, color=ft.colors.GREY_600)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=15,
            border_radius=10,
            bgcolor=ft.colors.WHITE,
            border=ft.border.all(1, ft.colors.GREY_300),
            width=120
        ),
        ft.Container(
            content=ft.Column([
                ft.Text("0", size=24, weight=ft.FontWeight.BOLD, color=ft.colors.ORANGE),
                ft.Text("Pendentes", size=12, color=ft.colors.GREY_600)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=15,
            border_radius=10,
            bgcolor=ft.colors.WHITE,
            border=ft.border.all(1, ft.colors.GREY_300),
            width=120
        ),
        ft.Container(
            content=ft.Column([
                ft.Text("0", size=24, weight=ft.FontWeight.BOLD, color=ft.colors.RED),
                ft.Text("Falhadas", size=12, color=ft.colors.GREY_600)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=15,
            border_radius=10,
            bgcolor=ft.colors.WHITE,
            border=ft.border.all(1, ft.colors.GREY_300),
            width=120
        )
    ], alignment=ft.MainAxisAlignment.SPACE_AROUND)
    
    def update_statistics():
        """Atualizar estatísticas na interface."""
        try:
            stats = get_statistics()
            
            # Atualizar cards
            stats_cards.controls[0].content.controls[0].value = str(stats.get('total', 0))
            stats_cards.controls[1].content.controls[0].value = str(stats.get('completed', 0))
            stats_cards.controls[2].content.controls[0].value = str(stats.get('pending', 0))
            stats_cards.controls[3].content.controls[0].value = str(stats.get('failed', 0))
            
            page.update()
        except Exception as e:
            print(f"Erro ao atualizar estatísticas: {e}")
    
    def refresh_tasks():
        """Atualizar lista de tarefas."""
        try:
            tasks_list.controls.clear()
            tasks = get_tasks()
            
            if not tasks:
                tasks_list.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.icons.INBOX, size=48, color=ft.colors.GREY_400),
                            ft.Text(
                                "Nenhuma tarefa encontrada",
                                size=16,
                                color=ft.colors.GREY_600,
                                text_align=ft.TextAlign.CENTER
                            ),
                            ft.Text(
                                "Adicione uma nova tarefa usando o formulário acima",
                                size=12,
                                color=ft.colors.GREY_500,
                                text_align=ft.TextAlign.CENTER
                            )
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=30,
                        alignment=ft.alignment.center
                    )
                )
            else:
                for task in tasks:
                    task_id, name, url, status, items_processed, created_at = task
                    
                    # Cores por status
                    status_colors = {
                        'pending': ft.colors.ORANGE,
                        'running': ft.colors.BLUE,
                        'completed': ft.colors.GREEN,
                        'failed': ft.colors.RED
                    }
                    
                    status_color = status_colors.get(status, ft.colors.GREY)
                    
                    tasks_list.controls.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Column([
                                    ft.Text(name, size=16, weight=ft.FontWeight.BOLD),
                                    ft.Text(
                                        url[:60] + "..." if len(url) > 60 else url,
                                        size=12,
                                        color=ft.colors.GREY_600
                                    ),
                                    ft.Text(
                                        f"Criado: {created_at} | Itens: {items_processed}",
                                        size=10,
                                        color=ft.colors.GREY_500
                                    )
                                ], expand=True),
                                ft.Container(
                                    content=ft.Text(
                                        status.upper(),
                                        color=ft.colors.WHITE,
                                        size=12,
                                        weight=ft.FontWeight.BOLD
                                    ),
                                    bgcolor=status_color,
                                    padding=ft.padding.symmetric(horizontal=12, vertical=6),
                                    border_radius=15
                                )
                            ]),
                            padding=15,
                            margin=ft.margin.only(bottom=8),
                            border_radius=8,
                            bgcolor=ft.colors.WHITE,
                            border=ft.border.all(1, ft.colors.GREY_300)
                        )
                    )
            
            update_statistics()
            page.update()
            
        except Exception as e:
            status_text.value = f"❌ Erro ao carregar tarefas: {str(e)}"
            status_text.color = ft.colors.RED
            page.update()
    
    def add_new_task(e):
        """Adicionar nova tarefa."""
        try:
            name = task_name_field.value.strip()
            url = task_url_field.value.strip()
            max_items = int(max_items_field.value or "100")
            
            if not name or not url:
                status_text.value = "❌ Preencha o nome e URL da tarefa"
                status_text.color = ft.colors.RED
                page.update()
                return
            
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            task_id = add_task(name, url, "post,comment", max_items)
            
            # Limpar campos
            task_name_field.value = ""
            task_url_field.value = ""
            max_items_field.value = "100"
            
            status_text.value = f"✅ Tarefa '{name}' adicionada com sucesso (ID: {task_id})"
            status_text.color = ft.colors.GREEN
            
            refresh_tasks()
            
        except ValueError:
            status_text.value = "❌ Número máximo de itens deve ser um número válido"
            status_text.color = ft.colors.RED
            page.update()
        except Exception as e:
            status_text.value = f"❌ Erro ao adicionar tarefa: {str(e)}"
            status_text.color = ft.colors.RED
            page.update()
    
    def simulate_scraping(e):
        """Simular execução de scraping (demonstração)."""
        try:
            tasks = get_tasks()
            pending_tasks = [t for t in tasks if t[3] == 'pending']
            
            if not pending_tasks:
                status_text.value = "⚠️ Nenhuma tarefa pendente para executar"
                status_text.color = ft.colors.ORANGE
                page.update()
                return
            
            # Simular execução da primeira tarefa pendente
            task = pending_tasks[0]
            task_id = task[0]
            
            update_task_status(task_id, 'running')
            status_text.value = f"🔄 Simulando execução da tarefa '{task[1]}'..."
            status_text.color = ft.colors.BLUE
            refresh_tasks()
            
            # Simular conclusão após alguns segundos
            import threading
            import time
            
            def complete_task():
                time.sleep(3)
                update_task_status(task_id, 'completed')
                status_text.value = f"✅ Tarefa '{task[1]}' concluída com sucesso!"
                status_text.color = ft.colors.GREEN
                refresh_tasks()
            
            threading.Thread(target=complete_task, daemon=True).start()
            
        except Exception as e:
            status_text.value = f"❌ Erro na simulação: {str(e)}"
            status_text.color = ft.colors.RED
            page.update()
    
    # Construir interface
    page.add(
        ft.Column([
            # Cabeçalho
            ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Text(
                            "🚀 Facebook Scraper",
                            size=28,
                            weight=ft.FontWeight.BOLD,
                            color=ft.colors.BLUE_800
                        ),
                        ft.Text(
                            f"Versão Final - {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                            size=12,
                            color=ft.colors.GREY_600
                        )
                    ], expand=True),
                    ft.ElevatedButton(
                        "Simular Scraping",
                        icon=ft.icons.PLAY_ARROW,
                        on_click=simulate_scraping,
                        style=ft.ButtonStyle(
                            color=ft.colors.WHITE,
                            bgcolor=ft.colors.GREEN_600
                        )
                    )
                ]),
                padding=ft.padding.only(bottom=20)
            ),
            
            # Estatísticas
            ft.Container(
                content=ft.Column([
                    ft.Text("Estatísticas", size=18, weight=ft.FontWeight.BOLD),
                    stats_cards
                ]),
                padding=ft.padding.only(bottom=20)
            ),
            
            # Formulário
            ft.Container(
                content=ft.Column([
                    ft.Text("Nova Tarefa de Scraping", size=18, weight=ft.FontWeight.BOLD),
                    ft.Row([
                        task_name_field,
                        task_url_field,
                        max_items_field,
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
                        ft.Text("Tarefas de Scraping", size=18, weight=ft.FontWeight.BOLD),
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
    
    # Carregar dados iniciais
    refresh_tasks()
    
    print("✅ Interface construída com sucesso")
    print("🎯 Aplicação pronta para uso!")
    
    # Atualizar página
    page.update()

if __name__ == "__main__":
    print("="*60)
    print("🚀 FACEBOOK SCRAPER - VERSÃO FINAL")
    print("="*60)
    print(f"🐍 Python: {sys.version.split()[0]}")
    print(f"💻 Sistema: {platform.system()} {platform.release()}")
    print(f"📁 Diretório: {os.getcwd()}")
    print(f"🕐 Iniciado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("="*60)
    
    try:
        print("\n🔄 Iniciando aplicação Flet...")
        print("⚠️  IMPORTANTE: Uma janela desktop será aberta automaticamente")
        print("📋 Funcionalidades disponíveis:")
        print("   ✅ Adicionar tarefas de scraping")
        print("   ✅ Visualizar estatísticas em tempo real")
        print("   ✅ Simular execução de scraping")
        print("   ✅ Interface responsiva e moderna")
        
        print("\n🚀 Abrindo interface...")
        
        ft.app(
            target=main,
            view=ft.AppView.FLET_APP,
            port=0,
            web_renderer=ft.WebRenderer.HTML
        )
        
        print("\n✅ Aplicação executada com sucesso")
        
    except KeyboardInterrupt:
        print("\n🛑 Aplicação interrompida pelo usuário")
    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO: {str(e)}")
        print("\n📋 Stack trace:")
        import traceback
        traceback.print_exc()
        
        print("\n💡 SOLUÇÕES:")
        print("   1. Verificar permissões do sistema (macOS)")
        print("   2. Executar a partir do Terminal nativo")
        print("   3. Reinstalar Flet: pip install --upgrade flet")
        print("   4. Executar diagnóstico: python diagnostico_flet.py")
    
    print("\n🏁 Execução finalizada.")
    print("="*60)