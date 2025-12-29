import streamlit as st
import time
import random
import concurrent.futures

# 引入模組
from fact_checking.OllamaClient import OllamaClient
from fact_checking.FactChecker import FactChecker
from scraper.EvidenceRetrieveHandler import EvidenceRetrieveHandler
from agent_logic import real_analyze_claims, real_fact_check

# --- 1. 設定與初始化 ---
USER_AVATAR = "images/user_icon.png"
AI_AVATAR = "images/ai_icon.png"
USER_AVATAR1 = "images/user_icon1.png"

@st.cache_resource
def init_backend():
    client = OllamaClient()
    checker = FactChecker(client)
    scraper = EvidenceRetrieveHandler(max_search_requests=5)
    return checker, scraper

checker, scraper = init_backend()

# 保持老師名言絕對不更動
TEACHER_QUOTES = [
    {"text": "問他們說：「誒這個上課不是有講？」然後他們就會支支吾吾"},
    {"text": "那個 contain 是 equal的意思，像這邊可能就會考一個是非題"},
    {"text": "下課前十分鐘，網路可能會斷掉"},
    {"text": "今天線上課就上到這邊了（現場拿出考題）"},
    {"text": "整學期的課，可能今天是最有用的"},
    {"text": "人有三急（開始傳加分點名單）"}
]

st.set_page_config(page_title="Fact Mason & Alvin check center", layout="centered")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "processing" not in st.session_state:
    st.session_state.processing = False
if "last_input" not in st.session_state:
    st.session_state.last_input = ""

# --- 2. 強化版執行引擎 (修正 avatar 重疊問題) ---
def run_engine_safe(task_func, args, min_time, loading_type, current_avatar):
    placeholder = st.empty()
    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(task_func, *args)
        while (not future.done()) or (time.time() - start_time < min_time):
            with placeholder.container():
                # 這裡會根據傳入的 current_avatar 顯示
                with st.chat_message("assistant", avatar=current_avatar):
                    if loading_type == "text":
                        st.write("Mason 正在利用 Ollama 拆解論述...")
                        st.caption("🧠 深度運算中...")
                    else:
                        item = random.choice(TEACHER_QUAYES) if 'TEACHER_QUOTES' in locals() else {"text": "載入中..."}
                        # 在老師名言模式，同樣顯示 AI_AVATAR
                        st.warning(random.choice(TEACHER_QUOTES)["text"])
            time.sleep(2.0)
        
        placeholder.empty()
        result = future.result()
        if result is None:
            raise TimeoutError("nckucsie API gate TIMEOUT/ERROR, Please try again。")
        return result

# --- 3. 頁面渲染 ---
st.title("Fact Mason & Alvin check center")

# 側邊欄
with st.sidebar:
    if st.session_state.processing:
        if st.button("🛑 QUIT 🛑", use_container_width=True):
            st.session_state.processing = False
            st.rerun()
    if st.session_state.last_input:
        st.info("📋 last content（you can copy directly）👇：")
        st.code(st.session_state.last_input, language="text")

# 渲染歷史紀錄
for msg in st.session_state.messages:
    avatar = USER_AVATAR if msg["role"] == "user" else AI_AVATAR
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# 輸入框
input_placeholder = "⌛ Loading..." if st.session_state.processing else "請輸入文章或新聞連結..."
if prompt := st.chat_input(input_placeholder, disabled=st.session_state.processing):
    st.session_state.processing = True
    st.session_state.last_input = prompt
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

# --- 4. 核心狀態機邏輯 (移除外部巢狀 chat_message) ---
if st.session_state.processing and st.session_state.messages[-1]["role"] == "user":
    user_input = st.session_state.messages[-1]["content"]
    
    try:
        # 第一階段：Ollama 分析 (使用 USER_AVATAR1)
        analysis_res = run_engine_safe(real_analyze_claims, (checker, user_input), 3.0, "text", USER_AVATAR1)
        
        if analysis_res["is_subjective"]:
            report_md = f"⚠️ **不需查核**：這是一篇主觀內容。\n\n**理由**：{analysis_res['reason']}"
            with st.chat_message("assistant", avatar=AI_AVATAR):
                st.warning(report_md)
            st.session_state.messages.append({"role": "assistant", "content": report_md})
            st.session_state.processing = False
            st.rerun()
        else:
            claims = analysis_res["claims"]
            claims_md = "**📍 擷取到的客觀論點：**\n" + "\n".join([f"- {c}" for c in claims])
            
            # 顯示中間結果 (分析完畢後轉回 AI_AVATAR)
            with st.chat_message("assistant", avatar=AI_AVATAR):
                st.markdown(claims_md)
            
            # 第二階段：事實查核 (使用 AI_AVATAR)
            final_results = run_engine_safe(real_fact_check, (checker, scraper, claims, user_input), 5.0, "teacher", AI_AVATAR)
            
            # 組合最終報告
            report_md = "### 🛡️ 事實查核報告\n\n"
            for item in final_results:
                is_correct = (item["status"] == "correct")
                icon = "✅" if is_correct else "❌"
                color = "green" if is_correct else "red"
                report_md += f"🚩 **論點**：{item['claim']}\n\n"
                report_md += f"🔍 **查核**：{icon} :{color}[{item['fact']}]\n\n"
                if is_correct and item["url"] != "#":
                    report_md += f"🔗 **來源**：[點擊跳轉]({item['url']})\n\n"
                report_md += "---\n\n"
            
            with st.chat_message("assistant", avatar=AI_AVATAR):
                st.markdown(report_md)
            
            st.session_state.messages.append({"role": "assistant", "content": report_md})
            st.session_state.processing = False
            st.rerun()

    except Exception as e:
        error_md = f"❌ **連線異常**：{str(e)}"
        with st.chat_message("assistant", avatar=AI_AVATAR):
            st.error(error_md)
        st.session_state.messages.append({"role": "assistant", "content": error_md})
        st.session_state.processing = False
        st.rerun()