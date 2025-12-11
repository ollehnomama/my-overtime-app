import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- 設定檔案儲存路徑 ---
DATA_FILE = "schedule_data.csv"
# --- 設定管理員密碼 (請修改這裡) ---
ADMIN_PASSWORD = "boss"

# --- Aesop 風格客製化 CSS ---
def local_css():
    st.markdown("""
        <style>
        /* 匯入 Google Fonts 中類似 Aesop 的優雅無襯線字體 */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', 'Helvetica Neue', Helvetica, Arial, sans-serif;
            color: #333333;
        }

        /* --- 標題與文字 --- */
        h1, h2, h3 {
            font-weight: 600 !important;
            letter-spacing: -0.5px;
        }
        
        .stMarkdown p {
            font-weight: 300;
            line-height: 1.6;
        }

        /* --- 按鈕 (Button) --- */
        /* 將按鈕改成 Aesop 風格：平面、細黑框、無背景 */
        .stButton > button {
            background-color: transparent !important;
            color: #333333 !important;
            border: 1px solid #333333 !important;
            border-radius: 0px !important; /* 直角 */
            padding: 0.5em 1em !important;
            font-weight: 400 !important;
            transition: all 0.3s ease;
        }
        /* 滑鼠懸停時的效果 */
        .stButton > button:hover {
            background-color: #333333 !important;
            color: #F6F5E8 !important; /* 米色文字 */
            border-color: #333333 !important;
        }
        /* 側邊欄的按鈕稍微不同 */
        [data-testid="stSidebar"] .stButton > button {
             border-color: #666666 !important;
             color: #666666 !important;
        }

        /* --- 輸入框 (Input Fields) --- */
        /* 去掉預設的圓角和陰影，改成極簡風格 */
        .stTextInput > div > div > input,
        .stDateInput > div > div > input,
        .stTimeInput > div > div > input,
        .stSelectbox > div > div > div,
        .stTextArea > div > div > textarea {
            background-color: transparent !important;
            border: 1px solid #CCCCCC !important; /* 淺灰細框 */
            border-radius: 0px !important;
            color: #333333 !important;
        }
        /* 輸入框聚焦時的狀態 */
        .stTextInput > div > div > input:focus,
        .stDateInput > div > div > input:focus,
        .stTimeInput > div > div > input:focus,
        .stSelectbox > div > div > div:focus,
        .stTextArea > div > div > textarea:focus {
            border-color: #333333 !important; /* 聚焦變深框 */
            box-shadow: none !important;
        }
        
        /* --- Expander (展開元件) --- */
        .streamlit-expanderHeader {
            background-color: transparent !important;
            border: 1px solid #CCCCCC !important;
            border-radius: 0px !important;
            color: #333333 !important;
        }
        .streamlit-expanderContent {
            border: 1px solid #CCCCCC !important;
            border-top: none !important;
            border-radius: 0px !important;
            background-color: rgba(255,255,255,0.3) !important;
        }

        /* --- Dataframe 表格 --- */
        /* 讓表格背景透明，融入米色背景，並使用細線條 */
        [data-testid="stDataFrame"] {
            border: 1px solid #CCCCCC;
        }
        [data-testid="stDataFrame"] table {
            background-color: transparent !important;
        }
        [data-testid="stDataFrame"] th {
            background-color: #EAE8D9 !important; /* 表頭稍微深一點的米色 */
            color: #333333 !important;
            font-weight: 600 !important;
            border-bottom: 1px solid #333333 !important;
        }
        [data-testid="stDataFrame"] td {
            color: #333333 !important;
            border-bottom: 1px solid #E0E0E0 !important;
        }

        /* --- 小配件與 Emoji 調整 --- */
        /* 嘗試降低 Emoji 的飽和度，讓它們不要太鮮豔，比較符合 Aesop 的冷靜風格 */
        /* 注意：這在某些瀏覽器可能效果有限 */
        span[role="img"] {
             filter: sepia(0.3) saturate(0.8) !important;
        }
        
        /* 側邊欄樣式微調 */
        [data-testid="stSidebar"] {
            border-right: 1px solid #D0CDBC;
        }

        </style>
        """, unsafe_allow_html=True)

# --- 初始化或讀取資料 ---
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        return pd.DataFrame(columns=[
            "提交時間", "姓名", "類型", "日期",
            "開始時間", "結束時間", "時數", "備註"
        ])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# --- 網站主程式 ---
def main():
    # 套用 Aesop 風格 CSS
    local_css()
    
    # 注意：page_icon 在這裡設定後，瀏覽器分頁上的圖示很難透過 CSS 改顏色
    # 但頁面內的 Emoji 會被 CSS 濾鏡影響變暗
    st.set_page_config(page_title="班表管理系統", page_icon="⏰")
    
    st.title("⏰ 團隊時數管理系統")

    # 讀取資料
    df = load_data()

    # --- 區塊 1: 所有人都可以看到的「申請區」 ---
    st.markdown("### 📝 員工申請區")
    with st.expander("點擊展開填寫表單", expanded=True):
        with st.form("application_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("姓名 (請輸入全名)")
                date = st.date_input("日期", datetime.today())
            with col2:
                apply_type = st.selectbox("申請類型", ["加班 (Overtime)", "抵班/補休 (Comp Time)"])
            
            col3, col4 = st.columns(2)
            with col3:
                start_time = st.time_input("開始時間", datetime.strptime("09:00", "%H:%M").time())
            with col4:
                end_time = st.time_input("結束時間", datetime.strptime("18:00", "%H:%M").time())
            
            note = st.text_area("備註 (選填)")
            
            # 這個按鈕現在會是 Aesop 風格的細黑框按鈕
            submitted = st.form_submit_button("送出申請")

            if submitted:
                if name == "":
                    st.error("❌ 請輸入姓名！")
                else:
                    # 計算時數
                    start_dt = datetime.combine(date, start_time)
                    end_dt = datetime.combine(date, end_time)
                    
                    if end_dt <= start_dt:
                        st.error("❌ 結束時間必須晚於開始時間！")
                    else:
                        duration = (end_dt - start_dt).total_seconds() / 3600
                        duration = round(duration, 1)
                        
                        new_data = {
                            "提交時間": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "姓名": name,
                            "類型": apply_type,
                            "日期": date,
                            "開始時間": start_time,
                            "結束時間": end_time,
                            "時數": duration,
                            "備註": note
                        }
                        df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
                        save_data(df)
                        st.success(f"✅ 已送出！{name} {apply_type} {duration} 小時")

    st.markdown("---")

    # --- 區塊 2: 只有老闆能看到的「管理後台」 ---
    
    # 在側邊欄做一個登入框
    st.sidebar.header("🔐 管理員登入")
    input_password = st.sidebar.text_input("輸入密碼查看報表", type="password")

    if input_password == ADMIN_PASSWORD:
        st.sidebar.success("身份驗證成功！")
        
        st.header("📊 管理員報表 (僅您可見)")
        
        if not df.empty:
            # 1. 餘額統計表
            st.subheader("👥 人員時數餘額")
            summary = df.groupby(['姓名', '類型'])['時數'].sum().unstack(fill_value=0)
            
            # 防呆：確保欄位存在
            for col in ["加班 (Overtime)", "抵班/補休 (Comp Time)"]:
                if col not in summary.columns:
                    summary[col] = 0.0

            summary = summary.rename(columns={
                "加班 (Overtime)": "加班總時數",
                "抵班/補休 (Comp Time)": "已抵休時數"
            })
            summary["剩餘可休時數"] = summary["加班總時數"] - summary["已抵休時數"]
            
            # 用顏色標記：剩餘時數 < 0 顯示紅色
            # 表格現在也會融入米色背景
            st.dataframe(
                summary.style
                .format("{:.1f}") 
                .map(lambda x: 'color: #D9534F' if x < 0 else 'color: #5CB85C', subset=['剩餘可休時數']), # 調整了一下紅綠色使其稍微柔和一點
                use_container_width=True
            )

            # 2. 詳細流水帳
            st.subheader("📋 所有申請明細")
            filter_person = st.selectbox("篩選特定員工", ["全部"] + list(df["姓名"].unique()))
            
            view_df = df
            if filter_person != "全部":
                view_df = df[df["姓名"] == filter_person]

            st.dataframe(
                view_df.sort_values("提交時間", ascending=False).style.format({"時數": "{:.1f}"}), 
                use_container_width=True
            )
            
        else:
            st.info("目前還沒有任何資料。")
            
    elif input_password != "":
        st.sidebar.error("密碼錯誤，無法查看資料。")

if __name__ == "__main__":
    main()
