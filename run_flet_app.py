#!/usr/bin/env python3
"""
Script de inicialização otimizado da aplicação Flet.

Este script realiza verificações completas e inicia a aplicação
Facebook Scraper com interface desktop Flet de forma robusta.
"""

import os
import sys
import platform
import subprocess
from pathlib import Path
from datetime import datetime

# Adicionar diretório do projeto ao path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def print_header(title):
    """Imprimir cabeçalho formatado."""
    print("\n" + "="*60)
    print(f"🚀 {title}")
    print("="*60)

def check_system_compatibility():
    """Verificar compatibilidade do sistema."""
    print(f"🖥️  Sistema: {platform.system()} {platform.release()}")
    print(f"🏗️  Arquitetura: {platform.machine()}")
    print(f"🐍 Python: {sys.version.split()[0]}")
    print(f"📁 Diretório: {os.getcwd()}")
    
    # Verificações específicas para macOS
    if platform.system() == 'Darwin':
        print("\n🍎 Sistema macOS detectado")
        print("💡 Dicas importantes:")
        print("   - Certifique-se de que o Python tem permissões de acessibilidade")
        print("   - Execute a partir do Terminal nativo (não IDE)")
        print("   - Verifique as configurações de segurança do sistema")
    
    return True

def check_requirements():
    """Verificar se todas as dependências estão instaladas."""
    print("\n🔍 Verificando dependências...")
    
    required_packages = {
        'flet': 'Interface desktop',
        'sqlalchemy': 'Banco de dados',
        'selenium': 'Web scraping',
        'beautifulsoup4': 'Parsing HTML',
        'openpyxl': 'Exportação Excel',
        'pandas': 'Manipulação de dados'
    }
    
    missing_packages = []
    
    for package, description in required_packages.items():
        try:
            if package == 'beautifulsoup4':
                import bs4
            else:
                __import__(package)
            print(f"✅ {package}: OK ({description})")
        except ImportError:
            print(f"❌ {package}: FALTANDO ({description})")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ Pacotes faltando: {', '.join(missing_packages)}")
        print("💡 Para instalar, execute:")
        print("   pip install -r requirements-flet.txt")
        print("   ou")
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    
    print("\n✅ Todas as dependências estão instaladas")
    return True

def setup_environment():
    """Configurar variáveis de ambiente."""
    print("\n🔧 Configurando ambiente...")
    
    env_file = project_root / '.env'
    
    if env_file.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
            print("✅ Variáveis de ambiente carregadas do .env")
        except ImportError:
            print("⚠️  python-dotenv não instalado, usando configurações padrão")
    else:
        print("⚠️  Arquivo .env não encontrado, usando configurações padrão")
        
        # Criar arquivo .env de exemplo se não existir
        env_example = project_root / '.env.flet.example'
        if env_example.exists():
            print("💡 Você pode copiar .env.flet.example para .env e configurar")

def test_flet_basic():
    """Testar funcionalidade básica do Flet."""
    print("\n🧪 Testando Flet...")
    
    try:
        import flet as ft
        
        # Testar criação de componentes básicos
        text = ft.Text("Teste")
        button = ft.ElevatedButton("Teste")
        
        print("✅ Flet: Importação e componentes OK")
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste do Flet: {str(e)}")
        return False

def main():
    """Função principal de inicialização."""
    print_header("FACEBOOK SCRAPER - INICIALIZAÇÃO")
    print(f"🕐 Iniciado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    # Verificações do sistema
    if not check_system_compatibility():
        print("❌ Sistema não compatível")
        sys.exit(1)
    
    # Verificar dependências
    if not check_requirements():
        print("\n❌ Dependências faltando. Instale-as antes de continuar.")
        sys.exit(1)
    
    # Configurar ambiente
    setup_environment()
    
    # Testar Flet
    if not test_flet_basic():
        print("\n❌ Problemas com o Flet detectados")
        print("💡 Execute o diagnóstico: python diagnostico_flet.py")
        sys.exit(1)
    
    print_header("INICIANDO APLICAÇÃO")
    
    # Importar e executar aplicação
    try:
        print("📦 Importando módulos da aplicação...")
        from flet_app.main import main as flet_main
        import flet as ft
        
        print("✅ Módulos importados com sucesso")
        print("\n🚀 INICIANDO INTERFACE FLET...")
        print("⚠️  IMPORTANTE: Uma janela desktop será aberta")
        print("📋 Se a janela não aparecer, verifique as permissões do sistema")
        
        # Aguardar confirmação do usuário
        input("\n🔄 Pressione ENTER para continuar...")
        
        # Executar aplicação
        ft.app(
            target=flet_main,
            view=ft.AppView.FLET_APP,
            port=0,
            web_renderer=ft.WebRenderer.HTML,
            route_url_strategy="hash"
        )
        
        print("\n✅ Aplicação executada com sucesso")
        
    except KeyboardInterrupt:
        print("\n🛑 Aplicação interrompida pelo usuário")
    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO: {str(e)}")
        print("\n📋 Stack trace completo:")
        import traceback
        traceback.print_exc()
        
        print("\n💡 SOLUÇÕES SUGERIDAS:")
        print("   1. Execute o diagnóstico: python diagnostico_flet.py")
        print("   2. Verifique as permissões do sistema")
        print("   3. Tente executar a partir do Terminal nativo")
        print("   4. Reinstale o Flet: pip uninstall flet && pip install flet")
        
        sys.exit(1)
    
    print("\n🏁 Execução finalizada com sucesso.")
    print("="*60)

if __name__ == "__main__":
    main()