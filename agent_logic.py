import time

def analyze_claims(text):
    """State 2a: LLM 拆分論述 (模擬耗時)"""
    # 實際開發時，這裡會是 Ollama 的 API 呼叫
    time.sleep(20) 
    return ["114年10月臺南市住宅價格指數為140.25", "大廈價格指數較前期微幅下降0.04%"]

def fact_check_claims(claims):
    """State 3a: 爬蟲 + LLM 驗證 (模擬耗時)"""
    # 實際開發時，這裡會是 Tavily + Ollama
    time.sleep(30) 
    return [{"claim": claims[0], "fact": "正確。數據吻合。", "url": "https://example.com"}]