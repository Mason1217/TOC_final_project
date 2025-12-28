# Scraper Module

1. 整合了 **Tavily API** 進行非同步網路搜尋。
2. 具備自動化的本地快取（Local Cache）與檔案索引管理功能，能有效節省 API 額度並加速重複查詢的回應時間。

##  資料儲存位置 (Evidence Location)

所有的搜尋結果證據（Evidence）與索引檔案會自動儲存於專案根目錄下的 `data/evidence` 資料夾中。

* **儲存路徑**: `project_root/data/evidence/`
* **檔案結構**:
    * `index.json`: 記錄 Query String 與對應檔案名稱的映射表 (Key-Value Map)。
    * `evidence.json`, `evidence1.json`...: 實際存放搜尋結果的 JSON 檔案。

> **注意**: 模組會自動建立此資料夾結構，無需手動建立。

---

## 安裝與設定

1.  **依賴套件**:
    請確保已安裝 `tavily-python`。
    ```bash
    pip install tavily-python
    ```

2.  **API Key 設定**:
    本模組依賴 Tavily API。請在專案根目錄（與 `scraper/` 同層）建立一個名為 `API_KEY.py` 的檔案，內容如下：
    ```python
    # API_KEY.py
    TAVILY_API_KEY = "你的_Tavily_API_Key"
    ```

---

## 模組使用說明

你可以直接從 `scraper` 套件引入主要的 Handler：
```python
from scraper import EvidenceRetrieveHandler, EvidenceFileHandler
```

### 1. EvidenceRetrieveHandler (核心搜尋控制器)
負責管理非同步搜尋任務、執行緒池 (Thread Pool) 以及快取策略。

#### 初始化
```Python
handler = EvidenceRetrieveHandler(max_search_requests=5)
```
`max_search_requests (int)`: 最大併發請求數 (`Default: 5`)。

#### Method : `query`
執行搜尋請求。會根據設定決定讀取快取或發起新的 API 請求。
```Python
result = handler.query(
    query: dict, 
    use_local_TF: bool = False, 
    chunk_count: int = 3, 
    result_count: int = 3, 
    level: str = "basic"
)
```
參數說明:
    `query (dict)`: 必須包含 `"query"` (搜尋關鍵字)。可選欄位包含 `"search_region"`, `"search_duration"`。
    `use_local_TF (bool)`: 是否優先檢查本地快取。若為 `True` 且快取存在，直接回傳檔案 `Handler。`
    `chunk_count (int)`: 每個來源擷取的片段數 (`Default: 3`)。
    `result_count (int)`: API 回傳的最大結果數 (`Default: 3`)。
    `level (str)`: 搜尋深度，可選 `"basic"` 或 `"advanced"`。

回傳值 (Return Types):
    `Future`: 若發起新的 API 請求 (非同步物件)。
    `EvidenceFileHandler`: 若命中本地快取 (同步物件)。
    `None`: 若查詢無效。

#### Method : `shutdown`
關閉執行緒池。
```Python
handler.shutdown(wait=True, cancel_futures=True)
```


### 2. EvidenceFileHandler (檔案存取管理器)
負責證據檔案的讀取、寫入與索引查找。

#### Static Method : `store`
將資料寫入檔案並更新 `index.json`。
```Python
handler = EvidenceFileHandler.store(data: dict)
```
`data`: 必須包含 `"query"` 欄位以建立索引。

#### Static Method : `find_query`
透過 Query String 尋找既有的證據檔案。
```Python
handler = EvidenceFileHandler.find_query(query: str)
```
`回傳`: 若找到回傳 `EvidenceFileHandler` ，否則回傳 `None。`

#### Method : `read`
讀取檔案內容。
```Python
content = handler.read()  # 回傳 dict
```

#### Method : `close`
關閉檔案串流。重要：使用完畢後請務必呼叫。
```Python
handler.close()
```

#### Method : `get_filename`
取得目前開啟的檔案名稱。
```Python
filename = handler.get_filename()
```

---

## 使用範例 (Examples)

### 範例 1: 非同步搜尋 (Async Search)
此範例展示如何批量處理查詢，區分「快取結果」與「API 請求結果」。

```Python
from scraper import EvidenceRetrieveHandler, EvidenceFileHandler
from concurrent.futures import Future

# 定義查詢清單
queries = [
    {
        "search_region": "Taiwan",
        "search_duration": "all_time",
        "query": "台灣 東部 海域 7.0地震"
    },
    {
        "search_region": "US",
        "search_duration": "all_time",
        "query": "馬斯克 最新新聞"
    }
]

# 初始化 Handler
handler = EvidenceRetrieveHandler(max_search_requests=2)
wait_list = []

print("🚀 開始搜尋任務...")

for q in queries:
    print(f"正在處理: {q['query']}")
    
    # 發送查詢 (啟用本地快取)
    result = handler.query(
        query=q, 
        use_local_TF=True, 
        level=EvidenceRetrieveHandler.ADVANCED
    )

    # 情況 A: 命中快取 (直接讀取)
    if isinstance(result, EvidenceFileHandler):
        data = result.read()
        print(f"✅ [快取命中] {data.get('summary', '無摘要')}")
        result.close() # 記得關閉
        continue

    # 情況 B: API 請求中 (加入等待清單)
    if isinstance(result, Future):
        print("⏳ [API 請求中] 已加入排程...")
        wait_list.append(result)

# 等待 API 結果
print(f"\n等待 {len(wait_list)} 個網路請求完成...")
for future in wait_list:
    try:
        data = future.result() # 這裡會阻塞直到完成
        if data:
            print(f"✅ [API 完成] {data.get('summary', '無摘要')}")
    except Exception as e:
        print(f"❌ 發生錯誤: {e}")

handler.shutdown()
```

### 範例 2: 手動檔案操作 (Manual File Operations)
此範例展示如何手動存取證據檔案與測試索引機制。

```Python
from scraper import EvidenceFileHandler

# 1. 手動存檔
data = {
    "query": "測試手動存檔",
    "summary": "這是一筆手動寫入的測試資料。",
    "results": []
}

print("正在寫入檔案...")
handler = EvidenceFileHandler.store(data)
filename = handler.get_filename()
print(f"✅ 檔案已建立: {filename}")
handler.close()

# 2. 透過 Query 找回檔案
target_query = "測試手動存檔"
print(f"\n正在搜尋 Query: {target_query}")

found_handler = EvidenceFileHandler.find_query(target_query)

if found_handler:
    content = found_handler.read()
    print(f"✅ 成功找回檔案！內容摘要: {content.get('summary')}")
    found_handler.close()
else:
    print("❌ 找不到檔案")
```
