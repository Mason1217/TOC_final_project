import unittest
import shutil
import tempfile
import json
import os
from pathlib import Path

# 引入我們要測試的模組
from scraper.EvidenceFileHandler import EvidenceFileHandler

class TestEvidenceFileHandler(unittest.TestCase):
    
    def setUp(self):
        """
        在每個測試開始前執行：
        建立一個「臨時資料夾」，並把 EvidenceFileHandler 的存檔路徑指向它。
        這樣就不會汙染你原本的 data/evidence 資料夾。
        """
        self.test_dir = tempfile.mkdtemp()
        
        # 保存原始路徑，以免影響其他程式
        self.original_dir = EvidenceFileHandler.EVIDENCE_DIR
        
        # 【關鍵魔法】偷換路徑：強制把存檔位置改到臨時資料夾
        EvidenceFileHandler.EVIDENCE_DIR = Path(self.test_dir)

    def tearDown(self):
        """
        在每個測試結束後執行：
        刪除臨時資料夾，還原環境。
        """
        shutil.rmtree(self.test_dir)
        EvidenceFileHandler.EVIDENCE_DIR = self.original_dir

    def test_1_store_creates_file_and_index(self):
        """測試：存檔後，檔案與 index 是否真的存在"""
        print("\n--- 測試 1: 存檔與索引建立 ---")
        
        data = {
            "query": "測試查詢A",
            "summary": "這是測試內容",
            "results": []
        }

        # 執行存檔
        handler = EvidenceFileHandler.store(data)
        saved_filename = handler.get_filename()
        handler.close()

        # 驗證 1: 證據檔案是否存在
        expected_file_path = Path(self.test_dir) / saved_filename
        self.assertTrue(expected_file_path.exists(), "❌ 證據檔案沒有被建立")
        print(f"✅ 成功建立檔案: {saved_filename}")

        # 驗證 2: index.json 是否存在且內容正確
        index_path = Path(self.test_dir) / "index.json"
        self.assertTrue(index_path.exists(), "❌ index.json 沒有被建立")
        
        with open(index_path, "r", encoding="utf-8") as f:
            index_data = json.load(f)
        
        self.assertEqual(index_data.get("測試查詢A"), saved_filename, "❌ Index 對應錯誤")
        print("✅ Index 索引建立正確")

    def test_2_auto_increment_filename(self):
        """測試：檔名是否會自動遞增 (evidence.json -> evidence1.json)"""
        print("\n--- 測試 2: 檔名自動遞增 ---")

        data1 = {"query": "Q1", "content": "data1"}
        data2 = {"query": "Q2", "content": "data2"}

        # 存第一筆
        h1 = EvidenceFileHandler.store(data1)
        name1 = h1.get_filename()
        h1.close()

        # 存第二筆 (應該要自動變號)
        h2 = EvidenceFileHandler.store(data2)
        name2 = h2.get_filename()
        h2.close()

        print(f"檔案1: {name1}, 檔案2: {name2}")
        self.assertNotEqual(name1, name2, "❌ 檔名重複了，JsonFileHandler 沒有自動變號")
        self.assertTrue(name2.replace(".json", "").endswith("1") or name2 != "evidence.json", "❌ 檔名沒有遞增跡象")
        print("✅ 檔名自動遞增機制正常")

    def test_3_find_query(self):
        """測試：能不能透過 query 找回檔案"""
        print("\n--- 測試 3: 搜尋功能 (Find Query) ---")

        target_query = "馬斯克買推特"
        data = {
            "query": target_query,
            "summary": "這是一筆要被找回的資料"
        }

        # 先存進去
        EvidenceFileHandler.store(data).close()

        # 再找出來
        found_handler = EvidenceFileHandler.find_query(target_query)
        
        self.assertIsNotNone(found_handler, "❌ 找不到剛剛存進去的 Query")
        
        if found_handler:
            read_data = found_handler.read()
            self.assertEqual(read_data["query"], target_query, "❌ 找回來的資料內容不對")
            print(f"✅ 成功找回 Query: {target_query}")
            found_handler.close()

        # 測試找不存在的
        not_found = EvidenceFileHandler.find_query("不存在的Query")
        self.assertIsNone(not_found, "❌ 應該要回傳 None 但卻回傳了東西")
        print("✅ 搜尋不存在的資料正確回傳 None")

if __name__ == '__main__':
    unittest.main()

    