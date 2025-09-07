"""Módulo de casos de uso.

Este módulo centraliza a importação de todos os casos de uso
da aplicação seguindo os padrões da Clean Architecture.
"""

from .create_scraping_task import CreateScrapingTaskUseCase
from .execute_scraping import ExecuteScrapingUseCase
from .export_to_excel import ExportToExcelUseCase

# Exportar todos os use cases
__all__ = [
    'CreateScrapingTaskUseCase',
    'ExecuteScrapingUseCase',
    'ExportToExcelUseCase'
]