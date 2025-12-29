from scraper.JsonFileHandler import JsonFileHandler
from pathlib import Path
import os
import json

class EvidenceFileHandler(JsonFileHandler):
    """
    Manages storage and retrieval of evidence data.
    Maintains an index file to map queries to specific evidence files.
    """

    EVIDENCE_DIR = Path(__file__).resolve().parent.parent / "data" / "evidence"
    EVIDENCE_FILE_NAME = "evidence.json"
    INDEX_FILE_NAME = "index.json"

    @classmethod
    def _get_index_path(cls):
        return cls.EVIDENCE_DIR / cls.INDEX_FILE_NAME

    @classmethod
    def _load_index(cls) -> dict:
        """Helper to load the query-to-filename index."""
        index_path = cls._get_index_path()
        if not index_path.exists():
            return {}
        try:
            with open(index_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}

    @classmethod
    def _update_index(cls, query: str, filename: str):
        """Helper to update the index with a new query-filename pair."""
        index = cls._load_index()
        index[query] = filename
        
        if not cls.EVIDENCE_DIR.exists():
            os.makedirs(cls.EVIDENCE_DIR)

        with open(cls._get_index_path(), "w", encoding="utf-8") as f:
            json.dump(index, f, indent=4, ensure_ascii=False)

    @classmethod
    def find_query(cls, query: str) -> 'EvidenceFileHandler | None':
        """
        Search for an existing evidence file for a specific query.
        
        Args:
            query (str): The search query string.
            
        Returns:
            EvidenceFileHandler: Open handler with data if found.
            None: If no cache exists for this query.
        """
        index = cls._load_index()
        filename = index.get(query)

        if filename:
            full_path = cls.EVIDENCE_DIR / filename
            if full_path.exists():
                return EvidenceFileHandler(filename, mode="r")
        
        return None

    @classmethod
    def store(cls, data: dict) -> 'EvidenceFileHandler':
        """
        Store new evidence data and update the index.
        
        Args:
            data (dict): The dictionary containing evidence (must have 'query' key).
            
        Returns:
            EvidenceFileHandler: The handler used to store the file.
        """
        # 使用預設檔名，JsonFileHandler 會自動處理 evidence1, evidence2...
        handler = EvidenceFileHandler(cls.EVIDENCE_FILE_NAME, mode="w")
        handler.write(data)
        
        # 取得實際儲存的檔名
        saved_filename = handler.get_filename()
        
        # 如果資料中有 query，更新索引
        if "query" in data and data["query"]:
            cls._update_index(data["query"], saved_filename)
            
        return handler

    def __init__(self, name: str, mode: str = "r"):
        """Initialize with specific evidence directory."""
        super().__init__(str(self.EVIDENCE_DIR), name, mode)

    def write(self, data: dict):
        """
        Writes evidence data, removing internal fields like file_id before saving.
        """
        store_data = data.copy()
        if "file_id" in store_data:
            del store_data["file_id"]
        super().write(store_data)
