"""Módulo de serviços.

Este módulo centraliza a importação de todos os serviços
da aplicação seguindo os padrões da Clean Architecture.
"""

from .scraping_service import ScrapingService
from .excel_service import ExcelService

# Exportar todos os serviços
__all__ = [
    'ScrapingService',
    'ExcelService'
]