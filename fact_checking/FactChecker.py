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
                    **"search_duration"**: [YYYY/MM/DD(str), YYYY/MM/DD(str)],\n
                    **"search_region"**: "Taiwan"(str),\n
                    **"questions"**: [q1(str), q2(str), ...],\n
                }
            
        """
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")

        system_prompt = f"""
        你是一個高階搜尋策略專家。現在時間是 {current_date}。
        使用者的目標是驗證一句「陳述句」的真偽。
        該陳述句來自於一篇文章，背景資訊如下：
        ---
        {article_context[:1000]}... (只取前1000字以節省 token)
        ---
        
        請根據陳述句的內容與文章背景，制定最佳的搜尋策略。
        
        【重要指令】：
        1. 如果文章是中文，JSON 內的所有文字內容（reasoning, questions）必須嚴格使用「繁體中文」回答。
        2. 如果文章明顯是虛構故事，搜尋方向應為「確認該劇情是否真實存在於該作品中」。

        請回傳 JSON 格式：
        {{
            "reasoning": "請簡短說明為何選擇此搜尋地區與時間範圍（例如：這是一部80年代背景的美劇，或者是最近發生的台灣新聞）",
            "search_region": "Taiwan" 或 "Global" 或 "US",
            "search_duration": "all_time" (適合歷史/劇情/舊聞) 或 "last_year" (適合近期新聞) 或 "last_month",
            "questions": [
                "搜尋問句1",
                "搜尋問句2",
                "搜尋問句3"
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