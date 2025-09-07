#!/usr/bin/env python3
"""
Script de diagnóstico completo para identificar problemas com Flet.
"""

import sys
import os
import subprocess
import platform
from datetime import datetime

def print_header(title):
    """Imprimir cabeçalho formatado."""
    print("\n" + "="*60)
    print(f"🔍 {title}")
    print("="*60)

def check_system_info():
    """Verificar informações do sistema."""
    print_header("INFORMAÇÕES DO SISTEMA")
    print(f"🖥️  Sistema Operacional: {platform.system()} {platform.release()}")
    print(f"🏗️  Arquitetura: {platform.machine()}")
    print(f"🐍 Python: {sys.version}")
    print(f"📁 Diretório atual: {os.getcwd()}")
    print(f"🕐 Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    # Verificar variáveis de ambiente importantes
    print("\n🌍 Variáveis de ambiente relevantes:")
    env_vars = ['DISPLAY', 'WAYLAND_DISPLAY', 'XDG_SESSION_TYPE', 'DESKTOP_SESSION']
    for var in env_vars:
        value = os.environ.get(var, 'Não definida')
        print(f"   {var}: {value}")

def check_python_packages():
    """Verificar pacotes Python instalados."""
    print_header("PACOTES PYTHON")
    
    packages_to_check = ['flet', 'flet-core', 'flet-runtime']
    
    for package in packages_to_check:
        try:
            result = subprocess.run([sys.executable, '-m', 'pip', 'show', package], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                version_line = [line for line in lines if line.startswith('Version:')]
                if version_line:
                    version = version_line[0].split(': ')[1]
                    print(f"✅ {package}: {version}")
                else:
                    print(f"⚠️  {package}: Instalado (versão não detectada)")
            else:
                print(f"❌ {package}: Não instalado")
        except Exception as e:
            print(f"❌ Erro ao verificar {package}: {str(e)}")

def test_flet_import():
    """Testar importação do Flet."""
    print_header("TESTE DE IMPORTAÇÃO")
    
    try:
        import flet as ft
        print("✅ Importação do Flet: Sucesso")
        print(f"📦 Versão do Flet: {ft.__version__ if hasattr(ft, '__version__') else 'Não disponível'}")
        
        # Testar componentes básicos
        try:
            text = ft.Text("Teste")
            print("✅ Criação de componente Text: Sucesso")
        except Exception as e:
            print(f"❌ Criação de componente Text: {str(e)}")
        
        try:
            button = ft.ElevatedButton("Teste")
            print("✅ Criação de componente Button: Sucesso")
        except Exception as e:
            print(f"❌ Criação de componente Button: {str(e)}")
            
    except ImportError as e:
        print(f"❌ Erro na importação do Flet: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")
        return False
    
    return True

def test_simple_app():
    """Testar aplicação Flet simples."""
    print_header("TESTE DE APLICAÇÃO SIMPLES")
    
    try:
        import flet as ft
        
        def test_main(page: ft.Page):
            print("🚀 Função main chamada")
            page.title = "Teste Diagnóstico"
            page.window_width = 400
            page.window_height = 300
            page.window_center = True
            
            page.add(
                ft.Column([
                    ft.Text("🎉 Teste Funcionando!", size=20),
                    ft.Text("Se você vê esta janela, o Flet está OK"),
                    ft.ElevatedButton(
                        "Fechar",
                        on_click=lambda _: page.window_close()
                    )
                ], alignment=ft.MainAxisAlignment.CENTER)
            )
            
            page.update()
            print("✅ Interface criada com sucesso")
            
            # Aguardar um pouco e fechar automaticamente
            import threading
            import time
            
            def auto_close():
                time.sleep(5)
                try:
                    page.window_close()
                    print("🔄 Janela fechada automaticamente")
                except:
                    pass
            
            threading.Thread(target=auto_close, daemon=True).start()
        
        print("🔄 Iniciando aplicação de teste...")
        print("⏰ A janela será fechada automaticamente em 5 segundos")
        
        ft.app(
            target=test_main,
            view=ft.AppView.FLET_APP,
            port=0
        )
        
        print("✅ Teste de aplicação concluído")
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de aplicação: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def check_display_issues():
    """Verificar possíveis problemas de display."""
    print_header("DIAGNÓSTICO DE DISPLAY")
    
    # Verificar se estamos em um ambiente headless
    if os.environ.get('DISPLAY') is None and platform.system() == 'Linux':
        print("⚠️  Variável DISPLAY não definida (ambiente pode ser headless)")
    else:
        print("✅ Variável DISPLAY OK ou sistema não-Linux")
    
    # Verificar se estamos em SSH
    if os.environ.get('SSH_CLIENT') or os.environ.get('SSH_TTY'):
        print("⚠️  Conexão SSH detectada - pode afetar exibição de janelas")
    else:
        print("✅ Não está em sessão SSH")
    
    # Verificar macOS específico
    if platform.system() == 'Darwin':
        print("🍎 Sistema macOS detectado")
        print("💡 Dicas para macOS:")
        print("   - Verificar permissões de acessibilidade")
        print("   - Verificar se o Python tem permissão para controlar o computador")
        print("   - Tentar executar a partir do Terminal nativo (não IDE)")

def main():
    """Função principal do diagnóstico."""
    print("🔍 DIAGNÓSTICO COMPLETO DO FLET")
    print(f"Iniciado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    # Executar todos os testes
    check_system_info()
    check_python_packages()
    
    if test_flet_import():
        check_display_issues()
        
        print("\n" + "="*60)
        print("🎯 TESTE FINAL - APLICAÇÃO SIMPLES")
        print("="*60)
        print("⚠️  ATENÇÃO: Uma janela será aberta por 5 segundos")
        print("📋 Observe se a janela aparece na sua tela")
        
        input("\n🔄 Pressione ENTER para iniciar o teste final...")
        
        success = test_simple_app()
        
        print("\n" + "="*60)
        print("📊 RESULTADO FINAL")
        print("="*60)
        
        if success:
            print("✅ DIAGNÓSTICO: Flet está funcionando corretamente")
            print("💡 Se você não viu a janela, pode ser um problema de:")
            print("   1. Configurações de display do sistema")
            print("   2. Permissões de segurança (especialmente no macOS)")
            print("   3. Ambiente de execução (SSH, Docker, etc.)")
        else:
            print("❌ DIAGNÓSTICO: Problemas detectados com o Flet")
            print("💡 Soluções sugeridas:")
            print("   1. Reinstalar Flet: pip uninstall flet && pip install flet")
            print("   2. Verificar dependências do sistema")
            print("   3. Tentar em um ambiente Python limpo")
    
    print("\n🏁 Diagnóstico concluído.")

if __name__ == "__main__":
    main()