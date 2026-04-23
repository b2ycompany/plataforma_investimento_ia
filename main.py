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
            {"simbolo": "BTC/USD", "valor": 350000.00, "variacao": "Simulado"},
            {"simbolo": "ETH/USD", "valor": 18500.00, "variacao": "Simulado"}
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
def executar_ordem(usuario_id: int, ativo: str, acao: str, valor_investido: float = 1000.0, db: Session = Depends(get_db)):
    """ 
    Motor de trade atualizado: aceita o valor que o usuário quer investir. 
    Permite frações de ativos (ex: comprar R$ 500 de Bitcoin).
    """
    try:
        carteira = db.query(models.CarteiraVirtual).filter(models.CarteiraVirtual.usuario_id == usuario_id).first()
        if not carteira:
            raise HTTPException(status_code=404, detail="Carteira não encontrada.")
        
        # Tabela de preços base do MVP
        precos_mercado = {
            "PETR4 (Petróleo)": 38.50, "BTC (Bitcoin)": 350000.00, "IBOVESPA": 125000.00, 
            "DÓLAR (USD/BRL)": 5.15, "OURO (XAU/USD)": 350.00, "IFIX (Fundos Imobiliários)": 105.00,
            "ITUB4": 33.20, "MGLU3": 15.30
        }
        
        # Se o ativo não estiver na lista (ex: digitado manualmente), assume R$ 100 base
        preco_unitario = precos_mercado.get(ativo, 100.00) 
        quantidade_fracionada = valor_investido / preco_unitario
        data_atual = datetime.now().strftime("%d/%m %H:%M")
        
        if acao == "COMPRAR":
            if carteira.saldo_disponivel < valor_investido:
                raise HTTPException(status_code=400, detail=f"Saldo insuficiente para operar R$ {valor_investido:.2f}.")
            
            carteira.saldo_disponivel -= valor_investido
            
            # Verifica se já tem o ativo para somar a posição
            ativo_existente = db.query(models.AtivoComprado).filter(models.AtivoComprado.usuario_id == usuario_id, models.AtivoComprado.simbolo_ativo == ativo).first()
            if ativo_existente:
                ativo_existente.quantidade += quantidade_fracionada
                ativo_existente.preco_compra += valor_investido # Acumula o valor total investido neste ativo
            else:
                db.add(models.AtivoComprado(usuario_id=usuario_id, simbolo_ativo=ativo, quantidade=quantidade_fracionada, preco_compra=valor_investido))
            
            db.add(models.TransacaoFinanceira(usuario_id=usuario_id, tipo="COMPRA", ativo=ativo, valor=valor_investido, data_hora=data_atual))
            mensagem = f"Compra de R$ {valor_investido:.2f} em {ativo} executada."
            
        elif acao == "VENDER":
            ativo_existente = db.query(models.AtivoComprado).filter(models.AtivoComprado.usuario_id == usuario_id, models.AtivoComprado.simbolo_ativo == ativo).first()
            if not ativo_existente:
                 raise HTTPException(status_code=400, detail="Você não possui este ativo na carteira.")
            
            # Simulador de lucro variável para dar realismo (entre -2% e +8%)
            multiplicador = random.uniform(0.98, 1.08)
            valor_venda = ativo_existente.preco_compra * multiplicador
            
            carteira.saldo_disponivel += valor_venda
            db.delete(ativo_existente)
            db.add(models.TransacaoFinanceira(usuario_id=usuario_id, tipo="VENDA", ativo=ativo, valor=valor_venda, data_hora=data_atual))
            mensagem = f"Venda executada! Retorno de R$ {valor_venda:.2f}."

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
            "ativos": [{"simbolo": a.simbolo_ativo, "valor": a.preco_compra, "quantidade": a.quantidade} for a in ativos],
            "transacoes": [{"tipo": t.tipo, "ativo": t.ativo, "valor": t.valor, "data": t.data_hora} for t in transacoes],
            "feed_ao_vivo": lista_noticias,
            "indicadores": indicadores
        }
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))