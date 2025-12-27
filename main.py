# from API_KEY import OLLAMA_API_KEY as API_KEY
# print(API_KEY)

import streamlit as st
import time
import random
import os
from agent_logic import analyze_claims, fact_check_claims

# --- 設定與初始化 ---
st.set_page_config(page_title="事實查核 Agent", layout="centered")

# 初始化 Session State
if "messages" not in st.session_state:
    st.session_state.messages = [] # 對話歷史
if "processing" not in st.session_state:
    st.session_state.processing = False # 是否正在處理中 (鎖定 Input 用)

# 模擬老師名言與圖片路徑 (請確保你有這些圖片檔案，或先用文字代替)
TEACHER_QUOTES = [
    "老師：這題考試會考，要注意看！",
    "老師：邏輯要通，程式才會動。",
    "老師：你這個 FSM 畫得不錯喔。",
    "老師：Demo 的時候記得要拜乖乖。"
]

# --- UI 函式 ---

def render_history():
    """渲染對話紀錄"""
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

def animation_loading_1():
    """State 2a: 簡單分析動畫"""
    with st.status("🧠 模型正在拆解文章論述...", expanded=True) as status:
        st.write("正在識別客觀事實...")
        time.sleep(1)
        st.write("正在標記數據與日期...")
        time.sleep(1)
        status.update(label="分析完成！", state="complete", expanded=False)

def animation_loading_2():
    """State 3a: 幽默老師名言動畫"""
    placeholder = st.empty()
    for _ in range(3): # 動畫跑三次切換
        quote = random.choice(TEACHER_QUOTES)
        with placeholder.container():
            st.info("🔍 爬蟲正在全網搜尋證據中...")
            # 如果你有老師的圖片，可以用 st.image("teacher.png", width=100)
            st.warning(f"💡 {quote}")
        time.sleep(1.5)
    placeholder.empty()

# --- 主程式頁面 ---
st.title("🛡️ 事實查核 AI Agent")
st.caption("由專案小組開發的自動化事實查核系統")

# 渲染歷史紀錄 (State 1: Default)
render_history()

# 鎖定機制：如果正在處理，就不顯示 input 或顯示「處理中」
if st.session_state.processing:
    st.info("Agent 正在思考中，請稍候...")
else:
    # State 1: 等待 User Input
    if prompt := st.chat_input("請輸入要查核的文章或新聞連結..."):
        # 開始處理流程
        st.session_state.processing = True
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun() # 立即刷頁以鎖定 input 並顯示新訊息

# 檢查是否需要執行運算邏輯
if st.session_state.processing and st.session_state.messages[-1]["role"] == "user":
    user_input = st.session_state.messages[-1]["content"]
    
    with st.chat_message("assistant"):
        # --- Group 2: Analysis ---
        # State 2a: 動畫 1
        animation_loading_1()
        # 呼叫隊友功能 1
        extracted_claims = analyze_claims(user_input)
        
        # State 2b: 輸出第一次結果
        claims_text = "**抓取到的客觀論述：**\n" + "\n".join([f"- {c}" for c in extracted_claims])
        st.markdown(claims_text)
        
        # --- Group 3: Verification ---
        # State 3a: 動畫 2 (老師圖片與名言)
        animation_loading_2()
        # 呼叫隊友功能 2
        final_results = fact_check_claims(extracted_claims)
        
        # State 3b: 輸出最終結果
        report_md = "### 🛡️ 最終查核報告\n\n"
        for item in final_results:
            report_md += f"📍 **論點**: {item['claim']}\n"
            report_md += f"✅ **事實**: {item['fact']}\n"
            report_md += f"🔗 **來源**: [點擊查看]({item['url']})\n\n---\n"
        
        st.markdown(report_md)
        
        # 將結果存入歷史並解鎖
        st.session_state.messages.append({"role": "assistant", "content": f"{claims_text}\n\n{report_md}"})
        st.session_state.processing = False
        st.rerun() # 再次刷新以解鎖 chat_input