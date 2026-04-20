import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Carrega as variáveis de ambiente (como a senha do banco de dados do arquivo .env)
load_dotenv()

# Pega o link do banco na nuvem. Se não encontrar, usa o SQLite local de backup
URL_BANCO_DADOS = os.getenv("DATABASE_URL", "sqlite:///./plataforma_ia.db")

# Configuração inteligente do Motor de Banco de Dados
if URL_BANCO_DADOS.startswith("sqlite"):
    engine = create_engine(URL_BANCO_DADOS, connect_args={"check_same_thread": False})
else:
    # Correção de segurança: o SQLAlchemy exige que comece com postgresql:// e não postgres://
    if URL_BANCO_DADOS.startswith("postgres://"):
        URL_BANCO_DADOS = URL_BANCO_DADOS.replace("postgres://", "postgresql://", 1)
        
    # pool_pre_ping=True ajuda a não perder a conexão na nuvem da Vercel
    engine = create_engine(URL_BANCO_DADOS, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()