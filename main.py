from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import random

from database import SessionLocal, engine
import models
import ia_service

# Força a criação das tabelas
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="SaaSIA - Premium Terminal")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
def carregar_plataforma():
    return FileResponse("index.html")

@app.post("/criar-conta")
def criar_conta(nome: str, email: str, db: Session = Depends(get_db)):
    try:
        if db.query(models.Usuario).filter(models.Usuario.email == email).first():
            raise HTTPException(status_code=400, detail="Email já cadastrado.")
        novo_usuario = models.Usuario(nome=nome, email=email)
        db.add(novo_usuario)
        db.commit()
        db.refresh(novo_usuario)
        nova_carteira = models.CarteiraVirtual(usuario_id=novo_usuario.id, saldo_disponivel=0.0)
        db.add(nova_carteira)
        db.commit()
        return {"mensagem": "Conta criada com sucesso!", "usuario_id": novo_usuario.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/depositar")
def depositar(usuario_id: int, valor: float, db: Session = Depends(get_db)):
    try:
        carteira = db.query(models.CarteiraVirtual).filter(models.CarteiraVirtual.usuario_id == usuario_id).first()
        if not carteira:
            raise HTTPException(status_code=404, detail="Carteira não encontrada.")
        carteira.saldo_disponivel += valor
        db.commit()
        return {"mensagem": "Depósito concluído", "saldo_atual": carteira.saldo_disponivel}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/solicitar-analise-ia")
def analisar_mercado_ia(usuario_id: int, db: Session = Depends(get_db)):
    try:
        noticias = ia_service.buscar_noticias_globais()
        recomendacoes = []

        for noticia in noticias:
            analise = ia_service.analisar_texto_com_ia(noticia.title)
            
            # Formata a string para caber no banco de dados existente sem quebrar a tabela
            resumo_db = f"{analise['decisao']} | {analise['mensagem']}"
            db.add(models.HistoricoInvestimento(titulo_noticia=noticia.title, recomendacao=resumo_db))
            
            if analise["decisao"] != "AGUARDAR":
                recomendacoes.append({
                    "ativo": analise["ativo"],
                    "decisao": analise["decisao"],
                    "motivo": analise["mensagem"],
                    "noticia_base": noticia.title,
                    "retorno_esperado": analise["retorno_esperado"],
                    "tempo_retorno": analise["tempo_retorno"]
                })

        db.commit()
        return {"mensagem": "Análise concluída", "sugestoes": recomendacoes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/executar-ordem")
def executar_ordem(usuario_id: int, ativo: str, acao: str, db: Session = Depends(get_db)):
    try:
        carteira = db.query(models.CarteiraVirtual).filter(models.CarteiraVirtual.usuario_id == usuario_id).first()
        if not carteira:
            raise HTTPException(status_code=404, detail="Carteira não encontrada.")
        
        precos_mercado = {"PETR4": 38.50, "BTC": 350000.00, "IBOVESPA": 125000.00, "MGLU3": 15.30, "ITUB4": 33.20}
        custo_ativo = precos_mercado.get(ativo, 100.00) 
        
        if acao == "COMPRAR":
            if carteira.saldo_disponivel < custo_ativo:
                raise HTTPException(status_code=400, detail=f"Saldo insuficiente. {ativo} custa R$ {custo_ativo:.2f}.")
            
            carteira.saldo_disponivel -= custo_ativo
            novo_ativo = models.AtivoComprado(
                usuario_id=usuario_id, 
                simbolo_ativo=ativo, 
                quantidade=1.0, 
                preco_compra=custo_ativo
            )
            db.add(novo_ativo)
            mensagem = f"Ordem executada! {ativo} adicionado."
            
        elif acao == "VENDER":
            ativo_existente = db.query(models.AtivoComprado).filter(models.AtivoComprado.usuario_id == usuario_id, models.AtivoComprado.simbolo_ativo == ativo).first()
            if not ativo_existente:
                 raise HTTPException(status_code=400, detail="Ativo não encontrado na sua carteira.")
            
            lucro_simulado = ativo_existente.preco_compra * 1.05 
            carteira.saldo_disponivel += lucro_simulado
            db.delete(ativo_existente)
            mensagem = f"Ordem de VENDA executada com lucro!"

        db.commit()
        return {"mensagem": mensagem, "saldo_atual": carteira.saldo_disponivel}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dados-painel")
def obter_dados_painel(usuario_id: int = 1, db: Session = Depends(get_db)):
    try:
        usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
        carteira = db.query(models.CarteiraVirtual).filter(models.CarteiraVirtual.usuario_id == usuario_id).first()
        ativos = db.query(models.AtivoComprado).filter(models.AtivoComprado.usuario_id == usuario_id).all()
        
        # O backend vai buscar as notícias em TEMPO REAL sempre que o painel abrir
        noticias_ao_vivo = ia_service.buscar_noticias_globais()
        lista_noticias = [{"titulo": n.title, "link": n.link} for n in noticias_ao_vivo]

        indicadores = {
            "cripto": [
                {"simbolo": "BTC/BRL", "valor": 350000.00 + random.randint(-1000, 1000), "variacao": "+1.5%"},
                {"simbolo": "ETH/BRL", "valor": 18500.00 + random.randint(-100, 100), "variacao": "-0.3%"}
            ],
            "acoes": [
                {"simbolo": "IBOVESPA", "valor": 125000.00 + random.randint(-500, 500), "variacao": "+0.8%"},
                {"simbolo": "USD/BRL", "valor": 5.15 + random.uniform(-0.05, 0.05), "variacao": "-0.2%"}
            ],
            "renda_fixa": [
                {"nome": "Taxa Selic", "valor": "10.50% a.a."},
                {"nome": "CDI", "valor": "10.40% a.a."}
            ]
        }

        return {
            "nome_usuario": usuario.nome if usuario else "Investidor VIP",
            "saldo": carteira.saldo_disponivel if carteira else 0.0,
            "ativos": [{"simbolo": a.simbolo_ativo, "valor": a.preco_compra} for a in ativos],
            "feed_ao_vivo": lista_noticias,
            "indicadores": indicadores
        }
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))