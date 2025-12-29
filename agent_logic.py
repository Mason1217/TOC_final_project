import time
import concurrent.futures
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
    
    # 關鍵修正：若 API 超時導致回傳 None 或解析出錯，不應判定為主觀
    if result is None:
        return None
        
    reason = result.get("subjectivity_reason", "")
    if "無法判定" in reason or "解析錯誤" in reason:
        return None # 讓 main.py 進入 except 區塊顯示連線異常

    # 根據流程圖：若為主觀，回傳標記
    if result.get("is_subjective"):
        return {"is_subjective": True, "reason": reason}
    
    return {"is_subjective": False, "claims": result.get("claims", [])}

def real_fact_check(checker: FactChecker, scraper_handler: EvidenceRetrieveHandler, claims: list, article_context: str):
    """
    對接 State 3a: 採用 Multi-threading 併發處理多個論點查核
    """
    
    def process_single_claim(claim):
        """
        封裝單個論點的查核邏輯，供執行緒池調用
        """
        try:
            # 1. 取得 LLM 生成的搜尋計畫
            query_plan = checker.generate_search_questions(claim, article_context)
            
            # 2. 修正欄位不對齊
            if query_plan.get("questions"):
                search_payload = query_plan.copy()
                search_payload["query"] = query_plan["questions"][0]
            else:
                search_payload = {"query": claim}
                
            # 3. 執行搜尋 (內含快取機制)
            search_result = scraper_handler.query(search_payload, use_local_TF=True, level=EvidenceRetrieveHandler.ADVANCED)
            
            # 4. 取得證據數據
            evidence_data = None
            if isinstance(search_result, EvidenceFileHandler):
                evidence_data = search_result.read()
                search_result.close()
            elif isinstance(search_result, Future):
                evidence_data = search_result.result()

            if not evidence_data:
                evidence_text = "搜尋失敗 (API 無回傳)"
                evidence_url = "#"
            else:
                evidence_text = evidence_data.get("summary", "搜尋結果無摘要")
                results = evidence_data.get("results", [])
                evidence_url = results[0].get("link", "#") if results else "#"

            # 5. 讓 LLM 進行判定
            verification = checker.verify_claim(claim, evidence_text)
            
            return {
                "claim": claim,
                "fact": verification.get("reason"),
                "url": evidence_url,
                "status": "correct" if verification.get("verdict") == "Correct" else "incorrect"
            }
        except Exception as e:
            # 單個論點出錯時的備案，避免毀掉整個報告
            return {
                "claim": claim,
                "fact": f"查核過程發生錯誤：{str(e)}",
                "url": "#",
                "status": "incorrect"
            }

    # 使用 ThreadPoolExecutor 同時處理所有論點 [cite: 2]
    final_results = []
    # 根據論點數量動態決定 worker 數，上限為 10
    max_workers = min(len(claims), 10) if claims else 1
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 使用 map 確保回傳結果順序與輸入的 claims 一致
        final_results = list(executor.map(process_single_claim, claims))
        
    return final_results