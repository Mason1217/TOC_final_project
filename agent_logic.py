import time

def analyze_content(text):
    """狀態 2: 判斷主客觀與生成關鍵字 [cite: 6, 7, 10]"""
    time.sleep(2) # 模擬 LLM 思考時間
    if "我覺得" in text or "好漂亮" in text:
        return {"status": "subjective", "keywords": []}
    return {"status": "objective", "keywords": ["2024 奧運 獎牌榜"]}

def search_and_verify(keywords):
    """狀態 3 & 4: 搜尋與驗證 [cite: 12, 17]"""
    # 這裡會用到 Tavily API [cite: 14, 24]
    time.sleep(5) # 模擬爬蟲長時間運作
    return [
        {"claim": "台灣獲得 2 面金牌", "fact": "事實查核：正確", "url": "https://example.com/news1"},
        {"claim": "總排名第一", "fact": "事實查核：錯誤，實際為第 XX 名", "url": "https://example.com/news2"}
    ]