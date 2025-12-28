import requests
import json
import re
from typing import Dict, Any, List, Union, Optional

from API_KEY import OLLAMA_API_KEY as KEY

DEBUG = 1
API_URL = "https://api-gateway.netdb.csie.ncku.edu.tw/api/chat"
DEFAULT_MODEL = "gemma3:4b"

class OllamaClient:
    def __init__(
            self,
            api_url: str = API_URL,
            api_key: str = KEY,
            model_name: str = DEFAULT_MODEL,
    ):
        self.api_url = api_url
        self.api_key = api_key
        self.model_name = model_name
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def chat(
            self,
            messages: List[Dict[str, str]],
            json_mode: bool = False,
    ) -> Union[Dict, List, str, None]:
        """
        Returns:
            result: Dict/List if json_mode is True, otherwise, content(str)

        """        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
        }
        
        if json_mode:
            payload["format"] = "json"

        response_data = self.__call_api(self.api_url, payload)
        
        if not response_data:
            return None

        try:
            content = response_data["message"]["content"]
        except KeyError:
            print("錯誤：API 回傳格式不符合預期")
            return None

        if json_mode:
            return self.__parse_json_content(content)
        
        return content

    def __call_api(self, url: str, payload: Dict) -> Optional[Dict]:
        try:
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            result: Dict = response.json()

            if DEBUG:
                content = result.get('message', {}).get('content', '')
                print(f"[DEBUG] Raw Content: {content[:100]}...\n[DEBUG]\n")

            return result
            
        except requests.exceptions.RequestException as e:
            print(f"API Call Error: {e}")
            return None

    def __parse_json_content(self, content: str) -> Union[Dict, List, None]:
        
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # Find find first '{' or '[' and '}' or ']'
        try:
            pattern = r"(\{.*\}|\[.*\])"
            match = re.search(pattern, content, re.DOTALL)
            
            if match:
                json_str = match.group(0)
                return json.loads(json_str)
            else:
                print(f"JSON 解析失敗 (Regex 找不到 JSON 區塊): {content}")
                return None
                
        except (json.JSONDecodeError, Exception) as e:
            print(f"JSON 解析最終失敗: {e}\n原始內容: {content}")
            return None