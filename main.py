from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import random
import requests
from datetime import datetime

from database import SessionLocal, engine
import models
import ia_service

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="SaaSIA - Ultimate Investor Terminal")

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

def obter_precos_binance():
    try:
        btc_res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=3).json()
        eth_res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT", timeout=3).json()
        return [
            {"simbolo": "BTC/USD", "valor": float(btc_res["price"]), "variacao": "AO VIVO"},
            {"simbolo": "ETH/USD", "valor": float(eth_res["price"]), "variacao": "AO VIVO"}
        ]
    except Exception:
        return [
            {"simbolo": "BTC/USD", "valor": 64500.00, "variacao": "Simulado"},
            {"simbolo": "ETH/USD", "valor": 3400.00, "variacao": "Simulado"}
        ]

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
        return {"mensagem": "Conta criada!", "usuario_id": novo_usuario.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/depositar")
def depositar(usuario_id: int, valor: float, db: Session = Depends(get_db)):
    try:
        carteira = db.query(models.CarteiraVirtual).filter(models.CarteiraVirtual.usuario_id == usuario_id).first()
        if not carteira:
            raise HTTPException(status_code=404, detail="Carteira não encontrada.")
        
        carteira.saldo_disponivel += valor
        
        # Grava a transação no histórico
        data_atual = datetime.now().strftime("%d/%m %H:%M")
        nova_transacao = models.TransacaoFinanceira(usuario_id=usuario_id, tipo="DEPOSITO", ativo="BRL (PIX)", valor=valor, data_hora=data_atual)
        db.add(nova_transacao)
        
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
        
        precos_mercado = {
            "PETR4 (Petróleo)": 38.50, "BTC (Bitcoin)": 350000.00, "IBOVESPA": 125000.00, 
            "DÓLAR (USD/BRL)": 5.15, "OURO (XAU/USD)": 350.00, "IFIX (Fundos Imobiliários)": 105.00,
            "ITUB4": 33.20, "MGLU3": 15.30
        }
        custo_ativo = precos_mercado.get(ativo, 100.00) 
        data_atual = datetime.now().strftime("%d/%m %H:%M")
        
        if acao == "COMPRAR":
            if carteira.saldo_disponivel < custo_ativo:
                raise HTTPException(status_code=400, detail=f"Saldo insuficiente. {ativo} custa R$ {custo_ativo:.2f}.")
            
            carteira.saldo_disponivel -= custo_ativo
            db.add(models.AtivoComprado(usuario_id=usuario_id, simbolo_ativo=ativo, quantidade=1.0, preco_compra=custo_ativo))
            db.add(models.TransacaoFinanceira(usuario_id=usuario_id, tipo="COMPRA", ativo=ativo, valor=custo_ativo, data_hora=data_atual))
            mensagem = f"Ativo {ativo} integrado ao portfólio."
            
        elif acao == "VENDER":
            ativo_existente = db.query(models.AtivoComprado).filter(models.AtivoComprado.usuario_id == usuario_id, models.AtivoComprado.simbolo_ativo == ativo).first()
            if not ativo_existente:
                 raise HTTPException(status_code=400, detail="Ativo não encontrado na carteira.")
            
            lucro_simulado = ativo_existente.preco_compra * 1.05 
            carteira.saldo_disponivel += lucro_simulado
            db.delete(ativo_existente)
            db.add(models.TransacaoFinanceira(usuario_id=usuario_id, tipo="VENDA", ativo=ativo, valor=lucro_simulado, data_hora=data_atual))
            mensagem = f"Posição liquidada com lucro!"

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
        transacoes = db.query(models.TransacaoFinanceira).filter(models.TransacaoFinanceira.usuario_id == usuario_id).order_by(models.TransacaoFinanceira.id.desc()).limit(8).all()
        
        noticias_ao_vivo = ia_service.buscar_noticias_globais()
        lista_noticias = [{"titulo": n.title, "link": n.link} for n in noticias_ao_vivo]

        cripto_real = obter_precos_binance()

        indicadores = {
            "cripto": cripto_real,
            "commodities": [
                {"simbolo": "OURO (Oz)", "valor": 2350.00 + random.uniform(-10, 10), "variacao": "+0.4%"},
                {"simbolo": "BRENT (Petróleo)", "valor": 85.30 + random.uniform(-1, 1), "variacao": "-0.1%"}
            ],
            "acoes_imoveis": [
                {"simbolo": "IBOVESPA", "valor": 125000.00 + random.randint(-500, 500), "variacao": "+0.8%"},
                {"simbolo": "IFIX (Imóveis)", "valor": 3350.00 + random.randint(-10, 10), "variacao": "+0.2%"}
            ],
            "moedas_taxas": [
                {"simbolo": "USD/BRL", "valor": 5.15 + random.uniform(-0.05, 0.05), "variacao": "-0.2%"},
                {"simbolo": "SELIC", "valor": 10.50, "variacao": "Fixa"}
            ]
        }

        return {
            "nome_usuario": usuario.nome if usuario else "Investidor Master",
            "saldo": carteira.saldo_disponivel if carteira else 0.0,
            "ativos": [{"simbolo": a.simbolo_ativo, "valor": a.preco_compra} for a in ativos],
            "transacoes": [{"tipo": t.tipo, "ativo": t.ativo, "valor": t.valor, "data": t.data_hora} for t in transacoes],
            "feed_ao_vivo": lista_noticias,
            "indicadores": indicadores
        }
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))