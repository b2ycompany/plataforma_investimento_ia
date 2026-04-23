import feedparser

def analisar_texto_com_ia(texto: str):
    """ Motor IA com suporte a Dólar, Ouro, Petróleo, Imóveis e Cripto. """
    texto_upper = texto.upper()
    
    # 1. Reserva de Valor / Ouro
    if any(palavra in texto_upper for palavra in ["OURO", "GOLD", "RESERVA", "TENSÃO GEOPOLÍTICA"]):
        return {
            "decisao": "COMPRAR", "ativo": "OURO (XAU/USD)", 
            "mensagem": "Busca por segurança devido a incertezas no mercado.",
            "retorno_esperado": "+5.5% a.a. (Segurança)", "tempo_retorno": "Longo Prazo"
        }
    # 2. Câmbio / Dólar
    elif any(palavra in texto_upper for palavra in ["DÓLAR", "CÂMBIO", "FED", "JUROS AMERICANOS"]):
        return {
            "decisao": "COMPRAR", "ativo": "DÓLAR (USD/BRL)", 
            "mensagem": "Fortalecimento da moeda americana frente a emergentes.",
            "retorno_esperado": "+8.0% (Câmbio)", "tempo_retorno": "Curto Prazo"
        }
    # 3. Commodities / Petróleo
    elif any(palavra in texto_upper for palavra in ["PETRÓLEO", "BRENT", "OPEP", "COMBUSTÍVEL", "PETROBRAS"]):
        return {
            "decisao": "COMPRAR", "ativo": "PETR4 (Petróleo)", 
            "mensagem": "Corte na produção ou alta demanda elevando o preço do barril.",
            "retorno_esperado": "+12.5% a.a.", "tempo_retorno": "Médio Prazo"
        }
    # 4. Mercado Imobiliário / FIIs
    elif any(palavra in texto_upper for palavra in ["IMÓVEIS", "IMOBILIÁRIO", "FII", "ALUGUEL", "CONSTRUÇÃO"]):
        return {
            "decisao": "COMPRAR", "ativo": "IFIX (Fundos Imobiliários)", 
            "mensagem": "Setor imobiliário aquecido. Boa janela para renda passiva.",
            "retorno_esperado": "+10.5% a.a. (Isento)", "tempo_retorno": "Longo Prazo"
        }
    # 5. Criptoativos
    elif any(palavra in texto_upper for palavra in ["BITCOIN", "CRIPTO", "BTC", "ETHEREUM", "MOEDA DIGITAL"]):
        return {
            "decisao": "COMPRAR", "ativo": "BTC (Bitcoin)", 
            "mensagem": "Forte fluxo institucional e adoção de tecnologia blockchain.",
            "retorno_esperado": "+40.0% a.a.", "tempo_retorno": "Longo Prazo"
        }
    # 6. Mercado de Ações Geral
    elif any(palavra in texto_upper for palavra in ["BOVESPA", "AÇÕES", "BALANÇO", "LUCRO"]):
        return {
            "decisao": "COMPRAR", "ativo": "IBOVESPA", 
            "mensagem": "Bolsa atrativa com empresas descontadas.",
            "retorno_esperado": "+15.0% a.a.", "tempo_retorno": "Médio Prazo"
        }
    # 7. Cenário de Crise
    elif any(palavra in texto_upper for palavra in ["CRISE", "QUEDA LIVRE", "INFLAÇÃO FORTE", "RECESSÃO"]):
        return {
            "decisao": "VENDER", "ativo": "AÇÕES BRASIL", 
            "mensagem": "Risco macroeconômico severo. Proteger capital em caixa.",
            "retorno_esperado": "Prevenção (-20%)", "tempo_retorno": "Imediato"
        }
    # Neutro
    else:
        return {
            "decisao": "AGUARDAR", "ativo": "NENHUM", 
            "mensagem": "Mercado sem tendência clara. Mantenha posição.",
            "retorno_esperado": "0.0%", "tempo_retorno": "Aguardar"
        }

def buscar_noticias_globais():
    """ Rastreia as principais fontes de economia para varrer todos os setores. """
    canais = [
        "https://g1.globo.com/rss/g1/economia/",
        "http://rss.uol.com.br/feed/economia.xml",
        "https://br.cointelegraph.com/rss"
    ]
    
    todas_noticias = []
    for url in canais:
        try:
            feed = feedparser.parse(url)
            todas_noticias.extend(feed.entries[:3])
        except Exception:
            continue
            
    return todas_noticias