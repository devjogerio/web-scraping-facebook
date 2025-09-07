"""Configuração de logging para aplicação Flet.

Este módulo configura o sistema de logs da aplicação
com diferentes níveis e formatação adequada.
"""

import os
import logging
from datetime import datetime


def setup_logging(log_level: str = 'INFO') -> None:
    """Configurar sistema de logging.
    
    Args:
        log_level: Nível de log (DEBUG, INFO, WARNING, ERROR)
    """
    # Criar diretório de logs se não existir
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Nome do arquivo de log com timestamp
    log_filename = os.path.join(log_dir, f'flet_app_{datetime.now().strftime("%Y%m%d")}.log')
    
    # Configuração do logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    # Logger específico para a aplicação
    logger = logging.getLogger('flet_app')
    logger.info(f'Sistema de logging configurado - Nível: {log_level}')


def get_logger(name: str) -> logging.Logger:
    """Obter logger configurado.
    
    Args:
        name: Nome do logger
        
    Returns:
        Logger configurado
    """
    return logging.getLogger(f'flet_app.{name}')