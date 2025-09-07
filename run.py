#!/usr/bin/env python3
"""Arquivo principal para executar a aplicação Flask."""

import os
import sys
from pathlib import Path

# Adicionar diretório raiz ao path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app import create_app
from app.config.logging_config import setup_logging


def main():
    """Função principal para executar a aplicação."""
    # Criar aplicação
    app = create_app()
    
    # Configurar sistema de logs
    try:
        logging_config = setup_logging(app)
        print("✓ Sistema de logs configurado")
    except Exception as e:
        print(f"⚠ Aviso ao configurar logs: {e}")
    
    print("✓ Aplicação inicializada com sucesso")
    
    # Obter configurações do servidor
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    print(f"\n🚀 Iniciando aplicação Facebook Scraper")
    print(f"📍 URL: http://{host}:{port}")
    print(f"🔧 Modo: {'Desenvolvimento' if debug else 'Produção'}")
    print(f"📊 Banco: {app.config.get('SQLALCHEMY_DATABASE_URI', 'N/A')}")
    print(f"📝 Logs: logs/")
    print("\n" + "="*50)
    
    try:
        # Executar aplicação
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n\n🛑 Aplicação interrompida pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro ao executar aplicação: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()