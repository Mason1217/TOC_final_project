import time
import concurrent.futures
from concurrent.futures import Future
from fact_checking.FactChecker import FactChecker
from scraper.EvidenceRetrieveHandler import EvidenceRetrieveHandler
from scraper.EvidenceFileHandler import EvidenceFileHandler

def real_analyze_claims(checker: FactChecker, text: str):
    """
    對接 State 2a: 分析文章，提取客觀論點
    """
    result = checker.analyze_article(text)
    
    if result is None:
        return None
        
    reason = result.get("subjectivity_reason", "")
    if "無法判定" in reason or "解析錯誤" in reason:
        return None 

    if result.get("is_subjective"):
        return {"is_subjective": True, "reason": reason}
    
    return {"is_subjective": False, "claims": result.get("claims", [])}

def real_fact_check(checker: FactChecker, scraper_handler: EvidenceRetrieveHandler, claims: list, article_context: str):
    """
    對接 State 3a: 採用 Multi-threading 併發處理
    """
    
    def process_single_claim(claim):
        """
        封裝單個論點的查核邏輯
        """
        try:
            # 1. 取得 LLM 生成的搜尋計畫 (包含區域、時間範圍與問題)
            query_plan = checker.generate_search_questions(claim, article_context)
            
            # 2. 檢查是否生成了有效問題。若無則不呼叫 Scraper 直接返回警告。
            questions = query_plan.get("questions")
            if not questions or not isinstance(questions, list) or len(questions) == 0:
                return {
                    "claim": claim,
                    "fact": "⚠️ 該論點無法生成良好搜尋字串，查核終止。",
                    "url": "#",
                    "status": "incorrect"
                }
            
            # 3. 根據先前要求：使用關鍵字生成器優化第一條問題
            # 確保傳給 Tavily 的是精簡的關鍵字而非冗長問題
            keywords = checker.generate_search_keywords(questions[0])
            primary_query = keywords[0] if (keywords and len(keywords) > 0) else questions[0]

            # 4. 組合搜尋 Payload
            search_payload = {
                "query": primary_query,
                "search_region": query_plan.get("search_region", "Taiwan"),
                "search_duration": query_plan.get("search_duration", "all_time")
            }
                
            # 5. 執行搜尋 (此時已確保 query 非 None)
            search_result = scraper_handler.query(
                search_payload, 
                use_local_TF=True, 
                level=EvidenceRetrieveHandler.ADVANCED
            )
            
            # 6. 取得證據數據
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

            # 7. 讓 LLM 進行最後真偽判定
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

    # [cite_start]使用 ThreadPoolExecutor 並發執行 [cite: 2]
    max_workers = min(len(claims), 10) if claims else 1
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        final_results = list(executor.map(process_single_claim, claims))
        
    return final_results