from scraper import EvidenceRetrieveHandler, EvidenceFileHandler
from concurrent.futures import Future


querys = [
    {
    "search_region": "Taiwan",
    "search_duration": "last_year",
    "query": "台灣 東部 海域 7.0地震"
    }, 
    {
    "search_region": "Taiwan",
    "search_duration": "last_month",
    "query": "7.0地震 震央 距離"
    }, 
    {
    "search_region": "US",
    "search_duration": "all_time",
    "query": "是否在《怪奇物語》小說或漫畫中明確描述威爾拜爾斯騎車返家途中神秘失蹤的事件發生地點為印第安納州霍金斯鎮？"
    }, 
    # {
    # "search_duration": "all_time",
    # "query": "在《怪奇物語》第一季中，警長哈普的調查過程，以及他如何發現屍體是假造的，是否被詳細描述？"
    # }, 
    # {
    # "search_region": "US",
    # "search_duration": "all_time",
    # "query": "在《怪奇物語》第一季和第二季的劇情中，威爾被帶入『上下顛倒世界』的具體描述為何？是否有詳細的場景或事件記錄"
    # }, 
    # {
    # "search_region": "US",
    # "search_duration": "all_time",
    # "query": "在《怪奇物語》第一季中，伊萊雯是否與麥克、達斯汀和盧卡斯結盟？"
    # }, 
    # {
    # "search_region": "US",
    # "search_duration": "all_time",
    # "query": "在《怪奇物語》第一季中，伊萊雯如何被描述為無意間打開異界之門？"
    # }, 
    # {
    # "search_region": "US",
    # "search_duration": "all_time",
    # "query": "確認《怪奇物語》第一季的劇情中，威爾和伊萊雯在發揮全力後，是否同時消失，並留下未解之謎的描述？"
    # }, 
    # {
    # "search_region": "US",
    # "search_duration": "all_time",
    # "query": "搜尋相關影評或論壇討論，看看是否有提到1984年霍金斯出現新同學麥克絲的設定。"
    # }, 
]

evidenceRetrieveHandler = EvidenceRetrieveHandler(2)

wait_list = list()
for query in querys:
    print(f"Querying: {query['query']}")
    handler = evidenceRetrieveHandler.query(
        query=query, 
        use_local_TF=False, 
        level=EvidenceRetrieveHandler.BASIC
    )

    if isinstance(handler, EvidenceFileHandler):
        print(handler.read().get("summary", "No Summary"))
        handler.close()
        continue

    if isinstance(handler, Future):
        wait_list.append(handler)
        print("handler is Future")


print(f"Waiting for {len(wait_list)} futures to complete...")
for future in wait_list:
    result = future.result()
    print(result.get("summary", "No Summary"))
