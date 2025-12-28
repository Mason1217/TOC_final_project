import json
from fact_checking import OllamaClient, FactChecker

# 設定輸出檔案名稱
OUTPUT_FILE = "fact_check_output.json"

def main():
    client = OllamaClient()
    checker = FactChecker(client)

    # 讀取文章 (建議加上 encoding='utf-8' 以防編碼錯誤)
    try:
        with open("article.txt", 'r', encoding='utf-8') as f:
            article_text = f.read()
    except FileNotFoundError:
        print("找不到 article.txt，請確認檔案位置。")
        return

    # 準備一個字典來存放最終結果
    final_output = {
        "article_content": article_text, # 選擇性：保留原始文章以便對照
        "analysis_result": {},
        "claims_processing": [] 
    }

    print("--- 1. 開始分析文章 ---")
    # 1. 先分析文章
    analysis_result = checker.analyze_article(article_text)
    
    # 將分析結果存入 output
    final_output["analysis_result"] = analysis_result
    print(f"分析完成，找到 {len(analysis_result.get('claims', []))} 個陳述句。\n")

    # 2. 針對每個 Claim 生成搜尋關鍵字
    claims = analysis_result.get("claims", [])
    
    print("--- 2. 開始生成搜尋策略 ---")
    for i, claim in enumerate(claims):
        print(f"正在處理第 {i+1}/{len(claims)} 個陳述句...")
        
        # 呼叫生成函式
        search_plan = checker.generate_search_questions(claim, article_context=article_text)
        
        # 將「陳述句」與「搜尋計畫」綁定在一起存入列表
        claim_data = {
            "claim_id": i + 1,
            "claim_text": claim,
            "search_plan": search_plan
        }
        final_output["claims_processing"].append(claim_data)

    # 3. 寫入 JSON 檔案
    print(f"\n--- 3. 正在寫入檔案: {OUTPUT_FILE} ---")
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            # ensure_ascii=False 是關鍵，讓中文能正常顯示
            # indent=4 讓格式縮排漂亮易讀
            json.dump(final_output, f, ensure_ascii=False, indent=4)
        print("寫入成功！")
    except Exception as e:
        print(f"寫入檔案失敗: {e}")

if __name__ == "__main__":
    main()