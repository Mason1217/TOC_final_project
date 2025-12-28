import json
import datetime
from typing import List, Dict, Any

from .OllamaClient import OllamaClient

class FactChecker:
    def __init__(self, client: OllamaClient):
        self.client = client

    def analyze_article(
            self,
            article_text: str
    ) -> Dict[str, Any]:
        """
        Analyzes the given article, returns \n
        (1) Whether the article is subjective or objective.\n
        (2) Extract claims found in the given article.

        Args:
            article_text(str): article's content

        Returns:
            analysis(dict):
                {\n
                    **"is_subjective"**(bool)       : True/False\n
                    **"subjectivity_reason"**(str)  : "..."\n
                    **"claims"**(List[str])         : ["claim_1", "claim_2", ...]\n
                    **error"**(str)                 : if LLM's response unexpected\n
                }
        
        """
        system_prompt = """
        你是一個專業的新聞查核員。請分析使用者的文章，執行以下任務：
        1. 判斷文章整體是「主觀 (Subjective)」還是「客觀 (Objective)」。
        2. 提取文章中所有包含具體事實（如數據、事件、人物行為、時間地點）的「陳述句」。
        3. 忽略個人感受、形容詞或模糊的預測。

        【重要指令】：
        1. 如果文章是中文，JSON 內的所有文字內容（reasoning, questions）必須嚴格使用「繁體中文」回答。

        請回傳 JSON 格式：
        {
            "is_subjective": True/False,
            "subjectivity_reason": "判斷理由",
            "claims": [
                "完整的陳述句1",
                "完整的陳述句2"
            ]
        }
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"文章內容：\n{article_text}"}
        ]

        raw_result = self.client.chat(messages, json_mode=True)
        cleaned_result = self.__validate_analysis_res(raw_result)

        return cleaned_result

    def generate_search_keywords(
            self,
            claim: str,
    ) -> List[str]:
        """
        針對單一陳述句，生成搜尋關鍵字

        Args:
            claim(str):

        Returns:
            keyword_list(List):
                ["關鍵字組合1", "關鍵字組合2", "關鍵字組合3"]
        
        """
        system_prompt = """
        你是一個搜尋引擎專家 (SEO Expert)。
        請針對使用者提供的「陳述句」，生成 3 組適合 Google 搜尋的關鍵字。
        目標是找到能驗證該陳述句真偽的新聞或資料。

        請回傳 JSON 格式：
        {
            "keywords": ["關鍵字組合1", "關鍵字組合2", "關鍵字組合3"]
        }
        """

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"需要驗證的陳述句：{claim}"}
        ]

        result = self.client.chat(messages, json_mode=True)
        
        if result and "keywords" in result:
            return result["keywords"]
        return []

    def generate_search_questions(
            self,
            claim: str,
            article_context: str,
    ) -> Dict[str, Any]:
        """
        生成查詢字典 (example as below)

        Args:
            claim(str):
            article_context(str): 原始文章內容

        Returns:
            search_dict(Dict):
                {\n
                    **"search_duration"**: "all_time" | "last_year" | "last_month,\n
                    **"search_region"**: "Taiwan"(str),\n
                    **"questions"**: [q1(str), q2(str), ...],\n
                }
            
        """
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")

        system_prompt = f"""
        你是一個頂尖的 Google 搜尋引擎優化 (SEO) 專家。
        你的任務是將使用者提供的「陳述句 (Claim)」，轉換為最能找到真相的「搜尋字串 (Search Queries)」。
        
        現在時間是 {current_date}。
        陳述句背景：
        ---
        {article_context[:800]}...
        ---

        【轉換規則】：
        1. **拒絕指令句**：絕對不要使用「搜尋...」、「查找...」、「確認...」這些冗詞。
        2. **關鍵字化**：提取陳述句中的「實體 (Entity)」(人名、地名、專有名詞) 加上「屬性」。
        3. **口語短問句**：直接模擬一般人在 Google 搜尋框打入的問題。
        4. **語言**：JSON 內容必須嚴格使用「繁體中文」。
        
        【範例】：
        Input Claim: "台積電 2023 年營收創下歷史新高，突破 2 兆元。"
        Bad Output: ["請搜尋台積電去年的財報", "確認台積電營收是否突破 2 兆"] (太長、包含指令)
        Good Output: ["台積電 2023 營收", "台積電 2023 財報 2兆", "台積電 營收歷史新高 真實性"]

        Input Claim: "伊萊雯在影集中死掉了。"
        Good Output: ["怪奇物語 伊萊雯 結局", "Eleven Stranger Things death scene", "伊萊雯 死亡 第幾季"]

        請回傳 JSON 格式：
        {{
            "reasoning": "簡短說明搜尋策略",
            "search_region": "Taiwan" 或 "Global" 或 "US",
            "search_duration": "all_time" 或 "last_year" 或 "last_month",
            "questions": [
                "關鍵字組合 1",
                "關鍵字組合 2",
                "口語短問句 1",
                "口語短問句 2"
            ]
        }}
        """

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"需要驗證的陳述句：{claim}"}
        ]

        raw_result = self.client.chat(messages, json_mode=True)
        cleaned_result = self.__validate_search_questions(raw_result)
        
        return cleaned_result

    def verify_claim(
            self,
            claim: str,
            search_evidence: str,
    ) -> Dict[str, Any]:
        """
        判斷與原始文章的關聯性 (驗證真偽)

        Args:
            claim(str):
            search_evidence(str):

        Returns:
            result(Dict[str, Any]):
                {\n
                    **"verdict"**           : "Correct" | "Incorrect" | "Unverifiable",\n
                    **"confidence_score"**  : 0-10,\n
                    **"reason"**            : "請引用證據說明判定理由"\n
                }

        """
        system_prompt = """
        你是一個公正的法官。
        請比對「原始主張」與「搜尋到的證據」，判斷主張的真實性。

        注意：「搜尋證據」可能是一段總結摘要，也可能是原始文章中與搜尋相近的部份。
        請綜合所有證據內容來進行判斷。如果證據不足以支持或反駁，請標記為 Unverifiable。

        請回傳 JSON 格式：
        {
            "verdict": "Correct" | "Incorrect" | "Unverifiable",
            "confidence_score": 0-10,
            "reason": "請引用證據說明判定理由"
        }
        """
        
        user_content = f"""
        【原始主張】：{claim}
        【搜尋證據】：{search_evidence}
        """

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]

        raw_result = self.client.chat(messages, json_mode=True)
        cleaned_result = self.__validate_verify_res(raw_result)
        
        return cleaned_result

    def __validate_analysis_res(
            self,
            result: Any,
    ) -> Dict[str, Any]:
        
        safe_output = {
            "is_subjective": True,
            "subjectivity_reason": "無法判定 (解析錯誤)",
            "claims": [],
            "error": None
        }

        if not result or not isinstance(result, dict):
            safe_output["error"] = "LLM_NO_RESPONSE_OR_INVALID_FORMAT"
            return safe_output
        
        raw_is_sub = result.get("is_subjective", True)
        if isinstance(raw_is_sub, str):
            safe_output["is_subjective"] = raw_is_sub.lower() in ["true", "yes"]
        else:
            safe_output["is_subjective"] = bool(raw_is_sub)

        safe_output["subjectivity_reason"] = str(result.get("subjectivity_reason", "未提供理由"))

        raw_claims = result.get("claims", [])
        if isinstance(raw_claims, list):
            safe_output["claims"] = [
                str(c) for c in raw_claims \
                if isinstance(c, (str, int, float))
            ]
        else:
            safe_output["claims"] = []

        return safe_output

    def __validate_verify_res(
            self,
            result: Any,
    ) -> Dict[str, Any]:
        
        safe_output = {
            "verdict": "Unverifiable",
            "confidence_score": 0,
            "reason": "LLM 回傳格式錯誤或無法解析",
            "error": None
        }

        if not result or not isinstance(result, dict):
            safe_output["error"] = "LLM_NO_RESPONSE_OR_INVALID_FORMAT"
            return safe_output

        raw_verdict = result.get("verdict", "Unverifiable")

        VALID_VERDICTS = {"Correct", "Incorrect", "Unverifiable"}
        POSSIBLE_CORRECT = ["True", "Yes", "Supported"]
        POSSIBLE_INCORRECT = ["False", "No", "Refuted"]
        
        if isinstance(raw_verdict, str):
            cleaned_verdict = raw_verdict.strip().title()
            
            if cleaned_verdict in VALID_VERDICTS:
                safe_output["verdict"] = cleaned_verdict
            else:
                if cleaned_verdict in POSSIBLE_CORRECT:
                    safe_output["verdict"] = "Correct"
                elif cleaned_verdict in POSSIBLE_INCORRECT:
                    safe_output["verdict"] = "Incorrect"
                else:
                    safe_output["verdict"] = "Unverifiable"
        else:
            safe_output["verdict"] = "Unverifiable"

        raw_score = result.get("confidence_score", 0)
        try:
            score = int(raw_score)
            safe_output["confidence_score"] = max(0, min(10, score))
        except (ValueError, TypeError):
            safe_output["confidence_score"] = 0

        safe_output["reason"] = str(result.get("reason", "未提供理由"))

        return safe_output
    
    def __validate_search_questions(self, result: Any) -> Dict[str, Any]:

        safe_output = {
            "reasoning": "未提供理由",
            "search_region": "Global",
            "search_duration": "all_time",
            "questions": [],
            "error": None
        }

        if not result or not isinstance(result, dict):
            safe_output["error"] = "LLM_NO_RESPONSE"
            return safe_output

        safe_output["reasoning"] = str(result.get("reasoning", "LLM 未回傳理由"))
        safe_output["search_region"] = str(result.get("search_region", "Global"))
        safe_output["search_duration"] = str(result.get("search_duration", "all_time"))

        raw_questions = result.get("questions", [])
        if isinstance(raw_questions, list):
            safe_output["questions"] = [str(q) for q in raw_questions if isinstance(q, str)]
        else:
            if isinstance(raw_questions, str):
                safe_output["questions"] = [raw_questions]
            else:
                safe_output["questions"] = []

        if not safe_output["questions"]:
            safe_output["error"] = "No questions generated"

        return safe_output