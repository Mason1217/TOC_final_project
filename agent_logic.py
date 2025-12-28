import time

def analyze_claims(text):
    """State 2a: LLM 拆分論述 (模擬)"""
    time.sleep(2) 
    # 回傳多筆資料
    return [
        "114年10月臺南市住宅價格指數為140.25",
        "大廈價格指數較前期微幅下降0.04%",
        "台南市交易量前期微幅增加10.69%" # 增加一筆測試錯誤
    ]

def fact_check_claims(claims):
    """State 3a: 爬蟲 + LLM 驗證 (模擬)"""
    time.sleep(5) 
    results = []
    for i, claim in enumerate(claims):
        # 模擬：偶數項正確，奇數項錯誤
        if i % 2 == 0:
            results.append({
                "claim": claim,
                "fact": "查核結果：正確。與官方數據吻合。",
                "url": "https://example.com/correct",
                "status": "correct" # 新增狀態欄位
            })
        else:
            results.append({
                "claim": claim,
                "fact": "查核結果：有誤。實際數據應為 2.69%。",
                "url": "https://example.com/error",
                "status": "incorrect" # 新增狀態欄位
            })
    return results # 確保回傳完整清單