import feedparser

def analisar_texto_com_ia(texto: str):
    """ Regras da IA focadas no mercado brasileiro, criptomoedas e setores macroeconômicos. """
    texto_upper = texto.upper()
    
    # Setor de Energia / Commodities
    if any(palavra in texto_upper for palavra in ["PETROBRAS", "PETRÓLEO", "COMMODITIES", "DIVIDENDOS"]):
        return {
            "decisao": "COMPRAR", "ativo": "PETR4", 
            "mensagem": "Alta demanda de energia e previsão de bons dividendos.",
            "retorno_esperado": "+14.5% a.a.", "tempo_retorno": "Médio Prazo (6 a 12 meses)"
        }
    # Setor Cripto / Ativos Digitais
    elif any(palavra in texto_upper for palavra in ["BITCOIN", "CRIPTO", "BTC", "ETHEREUM", "MOEDA DIGITAL"]):
        return {
            "decisao": "COMPRAR", "ativo": "BTC", 
            "mensagem": "Quebra de resistência técnica e forte adoção institucional.",
            "retorno_esperado": "+35.0% a.a.", "tempo_retorno": "Longo Prazo (1 a 3 anos)"
        }
    # Setor de Varejo / Consumo
    elif any(palavra in texto_upper for palavra in ["VAREJO", "CONSUMO", "MAGALU", "MERCADO LIVRE", "VENDAS"]):
        return {
            "decisao": "COMPRAR", "ativo": "MGLU3", 
            "mensagem": "Setor de varejo apresentando recuperação nas vendas sazonais.",
            "retorno_esperado": "+8.2% a.a.", "tempo_retorno": "Curto Prazo (3 a 6 meses)"
        }
    # Setor Financeiro / Bancos
    elif any(palavra in texto_upper for palavra in ["BANCO", "JUROS", "SELIC", "CRÉDITO", "ITAU", "BRADESCO"]):
        return {
            "decisao": "COMPRAR", "ativo": "ITUB4", 
            "mensagem": "Margens financeiras fortes devido à manutenção das taxas de juros.",
            "retorno_esperado": "+11.0% a.a.", "tempo_retorno": "Médio Prazo (12 meses)"
        }
    # Cenário de Risco Extremo
    elif any(palavra in texto_upper for palavra in ["QUEDA LIVRE", "CRASH", "RECESSÃO GLOBAL", "GUERRA"]):
        return {
            "decisao": "VENDER", "ativo": "IBOVESPA", 
            "mensagem": "Risco macroeconômico severo detectado. Proteger capital imediatamente.",
            "retorno_esperado": "Prevenção de Perda (-20%)", "tempo_retorno": "Imediato"
        }
    # Cenário Neutro
    else:
        return {
            "decisao": "AGUARDAR", "ativo": "NENHUM", 
            "mensagem": "Mercado lateralizado. Aguarde confirmação de tendência.",
            "retorno_esperado": "0.0%", "tempo_retorno": "Aguardar"
        }

def buscar_noticias_globais():
    """ Rastreia feeds oficiais Brasileiros (G1 e UOL) """
    url_feed = "https://g1.globo.com/rss/g1/economia/"
    feed = feedparser.parse(url_feed)
    
    if not feed.entries:
        url_feed = "http://rss.uol.com.br/feed/economia.xml"
        feed = feedparser.parse(url_feed)
        
    return feed.entries[:8] # Traz as 8 notícias mais quentes