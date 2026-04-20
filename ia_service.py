import feedparser

def analisar_texto_com_ia(texto: str):
    """ Regras da IA focadas no mercado brasileiro e criptomoedas em BRL. """
    texto_upper = texto.upper()
    
    if any(palavra in texto_upper for palavra in ["PETROBRAS", "PETRÓLEO", "ALTA", "LUCRO", "DIVIDENDOS", "MERCADO", "BOVESPA"]):
        return {"decisao": "COMPRAR", "ativo": "PETR4", "mensagem": "Cenário positivo. Oportunidade de alta captada no mercado nacional."}
    elif any(palavra in texto_upper for palavra in ["BITCOIN", "CRIPTO", "BTC", "ETHEREUM", "MOEDA DIGITAL"]):
        return {"decisao": "COMPRAR", "ativo": "BTC", "mensagem": "Adoção forte de ativos digitais. Recomendação de entrada."}
    elif any(palavra in texto_upper for palavra in ["QUEDA", "CRISE", "INFLAÇÃO", "JUROS", "RECESSÃO", "SELIC", "DÓLAR"]):
        return {"decisao": "VENDER", "ativo": "IBOVESPA", "mensagem": "Risco macroeconômico detectado. Proteger capital."}
    else:
        return {"decisao": "AGUARDAR", "ativo": "NENHUM", "mensagem": "Mercado lateralizado. Aguarde novas movimentações."}

def buscar_noticias_globais():
    """ Rastreia feeds oficiais Brasileiros (100% em Português) """
    # Tentativa 1: G1 Economia
    url_feed = "https://g1.globo.com/rss/g1/economia/"
    feed = feedparser.parse(url_feed)
    
    # Se o G1 estiver fora do ar, usa o UOL Economia como plano B
    if not feed.entries:
        url_feed = "http://rss.uol.com.br/feed/economia.xml"
        feed = feedparser.parse(url_feed)
        
    return feed.entries[:6] # Traz as 6 notícias mais recentes e quentes