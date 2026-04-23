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
    # Tenta buscar os top 4 criptoativos para dar o "Efeito Binance"
    try:
        btc = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=3).json()
        eth = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT", timeout=3).json()
        sol = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=SOLUSDT", timeout=3).json()
        bnb = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BNBUSDT", timeout=3).json()
        
        return [
            {"simbolo": "BTC/USD", "valor": float(btc["price"]), "variacao": "AO VIVO"},
            {"simbolo": "ETH/USD", "valor": float(eth["price"]), "variacao": "AO VIVO"},
            {"simbolo": "SOL/USD", "valor": float(sol["price"]), "variacao": "AO VIVO"},
            {"simbolo": "BNB/USD", "valor": float(bnb["price"]), "variacao": "AO VIVO"}
        ]
    except Exception:
        return [
            {"simbolo": "BTC/USD", "valor": 350000.00, "variacao": "Simulado"},
            {"simbolo": "ETH/USD", "valor": 18500.00, "variacao": "Simulado"}
        ]

@app.get("/", response_class=HTMLResponse)
def carregar_plataforma():
    return FileResponse("index.html")

@app.post("/depositar")
def depositar(usuario_id: int, valor: float, db: Session = Depends(get_db)):
    try:
        carteira = db.query(models.CarteiraVirtual).filter(models.CarteiraVirtual.usuario_id == usuario_id).first()
        if not carteira:
            # Auto-cria a carteira se não existir no banco da nuvem
            novo_usuario = models.Usuario(id=usuario_id, nome="Investidor", email="admin@saasia.com")
            db.add(novo_usuario)
            carteira = models.CarteiraVirtual(usuario_id=usuario_id, saldo_disponivel=0.0)
            db.add(carteira)
            db.commit()
            
        carteira.saldo_disponivel += valor
        data_atual = datetime.now().strftime("%d/%m %H:%M")
        db.add(models.TransacaoFinanceira(usuario_id=usuario_id, tipo="DEPOSITO", ativo="BRL (PIX)", valor=valor, data_hora=data_atual))
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
            if analise["decisao"] != "AGUARDAR":
                recomendacoes.append({
                    "ativo": analise["ativo"], "decisao": analise["decisao"],
                    "motivo": analise["mensagem"], "retorno_esperado": analise["retorno_esperado"],
                    "tempo_retorno": analise["tempo_retorno"]
                })
        return {"sugestoes": recomendacoes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/executar-ordem")
def executar_ordem(usuario_id: int, ativo: str, acao: str, valor_investido: float = 1000.0, db: Session = Depends(get_db)):
    try:
        carteira = db.query(models.CarteiraVirtual).filter(models.CarteiraVirtual.usuario_id == usuario_id).first()
        if not carteira: raise HTTPException(status_code=404, detail="Carteira não encontrada.")
        
        # O SUPER CATÁLOGO DE ATIVOS SIMULADOS
        precos_mercado = {
            # Criptomoedas
            "BTC (Bitcoin)": 350000.00, "ETH (Ethereum)": 18500.00, "SOL (Solana)": 850.00, "BNB (Binance Coin)": 3200.00,
            # B3 - Blue Chips
            "PETR4 (Petrobras)": 38.50, "VALE3 (Vale)": 62.10, "ITUB4 (Itaú)": 33.20, "BBDC4 (Bradesco)": 14.80,
            # B3 - Varejo e Tech
            "MGLU3 (Magalu)": 15.30, "WEGE3 (WEG)": 38.90, "RENT3 (Localiza)": 55.40,
            # Imobiliário (FIIs)
            "HGLG11 (Logística)": 165.00, "MXRF11 (Papel)": 10.50, "KNRI11 (Lajes)": 158.20,
            # Commodities & Moedas
            "OURO (XAU/USD)": 350.00, "DÓLAR (USD/BRL)": 5.15, "EURO (EUR/BRL)": 5.45,
            # Índices
            "IBOVESPA": 125000.00, "S&P 500 (EUA)": 26500.00
        }
        
        preco_unitario = precos_mercado.get(ativo, 100.00) 
        quantidade_fracionada = valor_investido / preco_unitario
        data_atual = datetime.now().strftime("%d/%m %H:%M")
        
        if acao == "COMPRAR":
            if carteira.saldo_disponivel < valor_investido:
                raise HTTPException(status_code=400, detail=f"Saldo insuficiente.")
            carteira.saldo_disponivel -= valor_investido
            
            ativo_existente = db.query(models.AtivoComprado).filter(models.AtivoComprado.usuario_id == usuario_id, models.AtivoComprado.simbolo_ativo == ativo).first()
            if ativo_existente:
                ativo_existente.quantidade += quantidade_fracionada
                ativo_existente.preco_compra += valor_investido
            else:
                db.add(models.AtivoComprado(usuario_id=usuario_id, simbolo_ativo=ativo, quantidade=quantidade_fracionada, preco_compra=valor_investido))
            
            db.add(models.TransacaoFinanceira(usuario_id=usuario_id, tipo="COMPRA", ativo=ativo, valor=valor_investido, data_hora=data_atual))
            mensagem = f"Compra de R$ {valor_investido:.2f} executada."
            
        elif acao == "VENDER":
            ativo_existente = db.query(models.AtivoComprado).filter(models.AtivoComprado.usuario_id == usuario_id, models.AtivoComprado.simbolo_ativo == ativo).first()
            if not ativo_existente: raise HTTPException(status_code=400, detail="Ativo não encontrado na carteira.")
            
            # Simulador de oscilação realista do mercado
            multiplicador = random.uniform(0.95, 1.15)
            valor_venda = ativo_existente.preco_compra * multiplicador
            
            carteira.saldo_disponivel += valor_venda
            db.delete(ativo_existente)
            db.add(models.TransacaoFinanceira(usuario_id=usuario_id, tipo="VENDA", ativo=ativo, valor=valor_venda, data_hora=data_atual))
            mensagem = f"Venda executada. Liquidação: R$ {valor_venda:.2f}."

        db.commit()
        return {"mensagem": mensagem}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dados-painel")
def obter_dados_painel(usuario_id: int = 1, db: Session = Depends(get_db)):
    try:
        carteira = db.query(models.CarteiraVirtual).filter(models.CarteiraVirtual.usuario_id == usuario_id).first()
        ativos = db.query(models.AtivoComprado).filter(models.AtivoComprado.usuario_id == usuario_id).all()
        transacoes = db.query(models.TransacaoFinanceira).filter(models.TransacaoFinanceira.usuario_id == usuario_id).order_by(models.TransacaoFinanceira.id.desc()).limit(8).all()
        
        noticias_ao_vivo = ia_service.buscar_noticias_globais()
        
        return {
            "nome_usuario": "Investidor VIP",
            "saldo": carteira.saldo_disponivel if carteira else 0.0,
            "ativos": [{"simbolo": a.simbolo_ativo, "valor": a.preco_compra, "quantidade": a.quantidade} for a in ativos],
            "transacoes": [{"tipo": t.tipo, "ativo": t.ativo, "valor": t.valor, "data": t.data_hora} for t in transacoes],
            "feed_ao_vivo": [{"titulo": n.title} for n in noticias_ao_vivo],
            "indicadores": { "cripto": obter_precos_binance() }
        }
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))