"""Configuração do banco de dados para aplicação Flet.

Este módulo configura a conexão com SQLite e define
a sessão do banco de dados para a aplicação.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Base para modelos
Base = declarative_base()

# Configuração do banco de dados
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./facebook_scraper.db')

# Engine do SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=os.getenv('DATABASE_ECHO', 'False').lower() == 'true'
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_database_session():
    """Obter sessão do banco de dados.
    
    Returns:
        Session: Sessão do SQLAlchemy
    """
    db = SessionLocal()
    try:
        return db
    except Exception:
        db.close()
        raise


def init_database():
    """Inicializar banco de dados criando todas as tabelas."""
    Base.metadata.create_all(bind=engine)


def close_database_session(db):
    """Fechar sessão do banco de dados.
    
    Args:
        db: Sessão do banco de dados
    """
    if db:
        db.close()