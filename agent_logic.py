import time

def analyze_claims(text):
    """
    State 2a: LLM 第一次分析，拆分客觀論述
    開發者：LLM 負責人
    """
    time.sleep(2) # 模擬 LLM 運行
    return [
        "114年10月臺南市住宅價格指數為140.25",
        "大廈價格指數較前期微幅下降0.04%"
    ]

def fact_check_claims(claims):
    """
    State 3a: 爬蟲 + LLM 第二次分析，生成事實報告
    開發者：爬蟲 + LLM 負責人整合
    """
    time.sleep(4) # 模擬爬蟲與第二次 LLM 運行
    return [
        {"claim": claims[0], "fact": "事實查核：正確。根據內政部數據...", "url": "https://pip.moi.gov.tw/"},
        {"claim": claims[1], "fact": "事實查核：有誤。實際應為上升 0.01%...", "url": "https://example.com/news"}
    ]