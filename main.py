from API_KEY import OLLAMA_API_KEY as API_KEY
print(API_KEY)

import streamlit as st
import random
import time
from agent_logic import analyze_content, search_and_verify

# 優先讀取環境變數 (Zeabur 用)，若無則讀取本地 API_KEY.py
try:
    from API_KEY import OLLAMA_API_KEY, TAVILY_API_KEY
except ImportError:
    OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not TAVILY_API_KEY:
    st.error("找不到 API Key，請檢查環境變數或 API_KEY.py 檔案")


# kt quotation 
TEACHER_QUOTES = ["老師名言：這題考試會考！", "老師名言：邏輯要通，程式才會動。", "老師名言：Demo 不要緊張。"]

st.set_page_config(page_title="事實查核 Agent", page_icon="🛡️")
st.title("🛡️ 事實查核 AI Agent")

# 初始化對話紀錄 [cite: 3, 4]
if "messages" not in st.session_state:
    st.session_state.messages = []

# 顯示歷史訊息
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


def loading_animation():
    """模擬二次元遊戲隨機跳出名言 [cite: 12]"""
    placeholder = st.empty()
    for _ in range(4): # 隨機跳動 4 次
        quote = random.choice(TEACHER_QUOTES)
        placeholder.info(f"🔍 搜尋中...\n\n> **{quote}**")
        time.sleep(1.5)
    placeholder.empty()


if prompt := st.chat_input("請輸入文章或新聞連結..."):
    # 狀態 1: 使用者輸入 [cite: 4, 5]
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # 狀態 2: 判斷主客觀 (Loading 1) [cite: 6, 7]
        with st.spinner("LLM 正在分析內容主客觀性..."):
            res = analyze_content(prompt)

        if res["status"] == "subjective":
            response = "這是一篇主觀心得或抒情文，無需啟動事實查核。 [cite: 9]"
            st.write(response)
        else:
            # 狀態 3: 執行搜尋與名言動畫 (Loading 2) [cite: 12, 13, 15]
            loading_animation()
            
            # 狀態 4: 驗證與合成 [cite: 17, 19]
            evidence = search_and_verify(res["keywords"])
            
            # 狀態 5: 格式化輸出 [cite: 20, 21]
            response = "### 🛡️ 事實查核報告\n\n"
            for item in evidence:
                response += f"📍 **論點**: {item['claim']}\n"
                response += f"✅ **事實**: {item['fact']}\n"
                response += f"🔗 **來源**: [點擊查看]({item['url']})\n\n---\n\n"
            st.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})