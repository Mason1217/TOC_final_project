# from API_KEY import TAVILY_API_KEY as API_KEY
import os # 改從環境變數讀取(for Zeabur)
API_KEY = os.getenv("TAVILY_API_KEY")

from tavily import TavilyClient
import re
from typing import Any, Dict, List, Optional
from scraper.JsonFileHandler import JsonFileHandler

class Retriever():
    """
    Wrapper for the Tavily API to perform web searches and parse results.
    """

    BASIC = "basic"
    ADVANCED = "advanced"
    DEFAULT_COUNTRY = None  # not specified
    DEFAULT_TOPIC = "general"
    IGNORE_TIME_DURATION = "all_time"

    def __init__(self):
        self.__client = TavilyClient(api_key=API_KEY)

    def retrieve(self, query: dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Executes a search query and returns parsed results with a list of sources.
        """
        if "query" not in query or not query["query"]:
            return None
        
        start_date = None
        end_date = None
        if "search_duration" in query and \
            query["search_duration"] != self.IGNORE_TIME_DURATION and \
            isinstance(query["search_duration"], list) and \
            len(query["search_duration"]) == 2:

            start_date = query["search_duration"][0]
            end_date = query["search_duration"][1]

        try:
            response = self.__client.search(
                query=query["query"],
                include_answer=True, 
                search_depth=query.get("level", self.BASIC), 
                include_raw_content=True, 
                chunks_per_source=query.get("chunk_count", 3), 
                max_results=query.get("result_count", 3), 
                country=self.__parse_country(query.get("search_region", None)), 
                start_date=start_date, 
                end_date=end_date, 
                topic=self.__topic_check(query.get("topic", self.DEFAULT_TOPIC)), 
                include_usage=True
            )
        except Exception as e:
            print(f"❌ Tavily Search Error: {e}")
            return None
        
        # with JsonFileHandler(".", "raw_evidence.json", "w") as ha:
        #     ha.write(response)

        # --- Parsing Response ---
        output = dict()
        output["summary"] = response.get("answer", "")
        output["query"] = response.get("query", query["query"])
        output["response_time"] = response.get("response_time", 0.0)
        output["usage"] = response.get("usage", dict())
        
        raw_results = response.get("results", [])
        cleaned_results = []

        if isinstance(raw_results, list):
            for res in raw_results:
                raw_text = res.get("raw_content", "")
                content_with_chunks = res.get("content", "")

                item = {
                    "title": res.get("title", ""),
                    "link": res.get("url", ""),
                    "article": raw_text,
                    "chunks": self.__split_content(content_with_chunks),
                    "score": res.get("score", 0.0)
                }
                cleaned_results.append(item)
        
        output["results"] = cleaned_results

        return output
    
    def __parse_country(self, country: Optional[str]) -> str:
        if not country:
            return self.DEFAULT_COUNTRY
        country_map = {
            "US": "united states",
            "UK": "united kingdom", 
            "Global": None
        }
        return country_map.get(country, country.lower())

    def __topic_check(self, topic: str) -> str:
        if topic.lower() in ("general", "news", "finance"):
            return topic.lower()
        return self.DEFAULT_TOPIC
        
    def __split_content(self, content: str) -> List[str]:
        """
        Parses the content string to extract chunks based on Tavily's format.
        Format: '<chunk 1> content... <chunk 2> content...'
        """
        if not content:
            return []

        # 1. 檢查是否包含 chunk 標籤
        if "<chunk 1>" in content:
            # 使用 Regex 切割
            # Pattern 解釋: <chunk \d+> 會匹配 <chunk 1>, <chunk 2>...
            parts = re.split(r'<chunk \d+>', content)
            
            # 過濾掉空字串並去除頭尾空白
            chunks = [p.strip() for p in parts if p.strip()]
            return chunks
        
        # 2. 如果沒有標籤 (Basic 模式或是短文)，直接回傳整段當作一個 chunk
        return [content.strip()]