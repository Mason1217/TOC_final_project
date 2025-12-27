# from API_KEY import OLLAMA_API_KEY as API_KEY
# print(API_KEY)

import streamlit as st
import time
import random
import concurrent.futures
from agent_logic import analyze_claims, fact_check_claims

# ==========================================
# 測試與設定區 (你可以隨時調整這裡)
ANIMATION_SWITCH_INTERVAL = 3.0  # 動畫每幾秒切換一次
MOCK_STEP_1_MIN_TIME = 10.0       # Loading 1 最少執行秒數
MOCK_STEP_2_MIN_TIME = 20.0     # Loading 2 最少執行秒數

# 動畫 1 的狀態文字
LOADING_STATES_1 = ["🧠 讀取文章中...", "📝 識別客觀事實...", "🔍 標記數據與日期...", "📊 分析邏輯結構..."]

# 動畫 2 的名言與圖片 (State 3a)
TEACHER_QUOTES = [
    {"text": "老師：這題考試會考，要注意看！", "img": "images/img1.png"},
    {"text": "老師：邏輯要通，程式才會動。", "img": "https://via.placeholder.com/150?text=Teacher_2"},
    {"text": "老師：你這個 FSM 畫得不錯喔。", "img": "https://via.placeholder.com/150?text=Teacher_3"},
    {"text": "老師：Demo 的時候記得要拜乖乖。", "img": "https://via.placeholder.com/150?text=Teacher_4"}
]

# ==========================================
# UI 邏輯與核心引擎
# ==========================================

st.set_page_config(page_title="Factcheck Agent", layout="centered")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "processing" not in st.session_state:
    st.session_state.processing = False

def run_continuous_animation(task_func, task_args, loading_type="text"):
    """
    核心引擎：在背景執行任務，同時在前景持續刷新動畫。
    loading_type: "text" (Loading 1) 或 "teacher" (Loading 2)
    """
    placeholder = st.empty()
    start_time = time.time()
    
    # 使用 ThreadPoolExecutor 在背景執行隊友的函式
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(task_func, task_args)
        
        # 當背景任務尚未完成時，持續循環動畫
        while not future.done():
            with placeholder.container():
                if loading_type == "text":
                    st.info(random.choice(LOADING_STATES_1))
                else:
                    item = random.choice(TEACHER_QUOTES)
                    st.image(item["img"], width=100)
                    st.warning(item["text"])
            time.sleep(ANIMATION_SWITCH_INTERVAL)
        
        # 任務完成，回傳結果
        placeholder.empty()
        return future.result()

# --- 頁面渲染 ---
st.title("🛡️ Fact Mason & Alvin check center")

# 渲染對話紀錄 [cite: 36, 37]
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 輸入區域控管 
if st.session_state.processing:
    # 當正在處理時：鎖定輸入框，並將 placeholder 設為處理中文字
    st.chat_input("⌛ 正在處理中，請稍候...", disabled=True, key="processing_input")
else:
    # 當閒置時：解鎖輸入框，顯示正常提示文字
    if prompt := st.chat_input("請輸入要查核的文章或新聞連結...", key="active_input"):
        st.session_state.processing = True
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()

# 執行狀態機流程
if st.session_state.processing and st.session_state.messages[-1]["role"] == "user":
    user_input = st.session_state.messages[-1]["content"]
    
    with st.chat_message("assistant"):
        # --- State 2a & 2b: Analysis Group ---
        # 啟動持續動畫並執行分析
        extracted_claims = run_continuous_animation(analyze_claims, user_input, loading_type="text")
        
        claims_md = "**📍 擷取到的客觀論點：**\n" + "\n".join([f"- {c}" for c in extracted_claims])
        st.markdown(claims_md)
        
        # --- State 3a & 3b: Verification Group ---
        # 啟動老師名言持續動畫並執行爬蟲驗證
        final_results = run_continuous_animation(fact_check_claims, extracted_claims, loading_type="teacher")
        
        report_md = "### 🛡️ 事實查核報告\n\n"
        for item in final_results:
            report_md += f"🚩 **論點**: {item['claim']}\n"
            report_md += f"🔍 **查核**: {item['fact']}\n"
            report_md += f"🔗 **來源**: [點擊跳轉]({item['url']})\n\n---\n"
        
        st.markdown(report_md)
        
        # 存入 Session 並解除鎖定 
        st.session_state.messages.append({"role": "assistant", "content": f"{claims_md}\n\n{report_md}"})
        st.session_state.processing = False
        st.rerun()