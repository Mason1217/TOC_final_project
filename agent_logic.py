import time
from concurrent.futures import Future
from fact_checking.FactChecker import FactChecker
from scraper.EvidenceRetrieveHandler import EvidenceRetrieveHandler
from scraper.EvidenceFileHandler import EvidenceFileHandler

def real_analyze_claims(checker: FactChecker, text: str):
    """
    對接 State 2a: 分析文章
    """
    # 呼叫 FactChecker 分析文章主客觀與擷取論點
    result = checker.analyze_article(text)
    
    # [cite_start]根據 PDF 流程圖：若為主觀，回傳特殊標記 [cite: 9]
    if result.get("is_subjective"):
        return {"is_subjective": True, "reason": result.get("subjectivity_reason")}
    
    return {"is_subjective": False, "claims": result.get("claims", [])}
    # return None # 模擬 API 回傳空值（超時或故障）

def real_fact_check(checker: FactChecker, scraper_handler: EvidenceRetrieveHandler, claims: list, article_context: str):
    """
    對接 State 3a: 搜尋關鍵字 -> 爬蟲搜尋 -> LLM 驗證判定
    """
    final_results = []
    
    for claim in claims:
        # 1. 取得 LLM 生成的搜尋計畫 (內含 "questions" 清單)
        query_plan = checker.generate_search_questions(claim, article_context)
        
        # 2. 修正欄位不對齊：將 "questions" 的第一項 存入 "query"
        if query_plan.get("questions"):
            # 建立一個新的字典來符合 Retriever 的輸入格式
            search_payload = query_plan.copy()
            search_payload["query"] = query_plan["questions"][0] # 抓第一個問題來搜
        else:
            search_payload = {"query": claim} # 備案：直接搜論點本身
            
        # 3. 執行搜尋
        search_result = scraper_handler.query(search_payload, use_local_TF=True)
        
        # 4. 取得證據數據
        evidence_data = None
        if isinstance(search_result, EvidenceFileHandler):
            evidence_data = search_result.read()
            search_result.close()
        elif isinstance(search_result, Future):
            evidence_data = search_result.result()

        # 如果搜尋失敗，則顯示失敗原因
        if not evidence_data:
            evidence_text = "搜尋失敗 (API 無回傳)"
            evidence_url = "#"
        else:
            # 確保讀取到 Tavily 生成的摘要
            evidence_text = evidence_data.get("summary", "搜尋結果無摘要")
            # 取得第一個網頁來源的連結
            results = evidence_data.get("results", [])
            evidence_url = results[0].get("link", "#") if results else "#"

        # 5. 讓 LLM 進行判定
        verification = checker.verify_claim(claim, evidence_text)
        
        final_results.append({
            "claim": claim,
            "fact": verification.get("reason"),
            "url": evidence_url,
            "status": "correct" if verification.get("verdict") == "Correct" else "incorrect"
        })
        
    return final_results