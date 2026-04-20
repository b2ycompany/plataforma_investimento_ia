from sqlalchemy import Column, Integer, String, Float, ForeignKey
from database import Base, engine

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    email = Column(String, unique=True, index=True)

class CarteiraVirtual(Base):
    __tablename__ = "carteira_virtual"
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), unique=True)
    saldo_disponivel = Column(Float, default=0.0)

class AtivoComprado(Base):
    __tablename__ = "ativos_comprados"
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    simbolo_ativo = Column(String) # Ex: BTC, PETR4
    quantidade = Column(Float)
    preco_compra = Column(Float)

class HistoricoInvestimento(Base):
    __tablename__ = "historico_investimentos"
    id = Column(Integer, primary_key=True, index=True)
    titulo_noticia = Column(String)
    recomendacao = Column(String)

# Cria todas as tabelas no banco de dados
Base.metadata.create_all(bind=engine)