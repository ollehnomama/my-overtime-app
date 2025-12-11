import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- 設定檔案儲存路徑 ---
DATA_FILE = "schedule_data.csv"

# --- 讀取密碼 (優先讀取金庫 Secrets，若無則用預設值方便測試) ---
# 舊寫法有防呆，會導致誤會。改成下面這樣，強制讀取金庫：
if "admin_password" in st.secrets:
    ADMIN_PASSWORD = st.secrets["admin_password"]
else:
    st.error("🚨 錯誤：找不到密碼設定！請檢查 Secrets 裡的變數名稱是否為 admin_password")
    st.stop() # 停止執行，避免用錯誤密碼繼續跑

# --- Aesop 風格客製化 CSS ---
def local_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', 'Helvetica Neue', Helvetica, Arial, sans-serif;
            color: #333333;
        }

        /* 標題與文字 */
        h1, h2, h3 { font-weight: 600 !important; letter-spacing: -0.5px; }
        .stMarkdown p { font-weight: 300; line-height: 1.6; }

        /* 側邊欄與輸入框優化 */
        [data-testid="stSidebar"] { border-right: 1px solid #D0CDBC; background-color: #EAE8D9; }
        
        /* 輸入框去背、細線條 */
        .stTextInput > div > div > input,
        .stDateInput > div > div > input,
        .stTimeInput > div > div > input,
        .stSelectbox > div > div > div,
        .stTextArea > div > div > textarea {
            background-color: transparent !important;
            border: 1px solid #999999 !important;
            border-radius: 0px !important;
            color: #333333 !important;
        }

        /* 按鈕 Aesop 風格 */
        .stButton > button {
            background-color: transparent !important;
            color: #333333 !important;
            border: 1px solid #333333 !important;
            border-radius: 0px !important;
            padding: 0.4em 1em !important;
            transition: all 0.3s ease;
        }
        .stButton > button:hover {
            background-color: #333333 !important;
            color: #F6F5E8 !important;
            border-color: #333333 !important;
        }

        /* Alert 訊息框風格 (成功=深綠, 失敗=深紅) */
        div[data-testid="stAlert"] { background-color: transparent !important; border-radius: 0px !important; }
        
        div[data-testid="stAlert"]:has(div[aria-label="Success"]) { 
            border: 1px solid #4A5D23 !important; color: #4A5D23 !important; 
        }
        div[data-testid="stAlert"]:has(div[aria-label="Success"]) svg { fill: #4A5D23 !important; }
        
        div[data-testid="stAlert"]:has(div[aria-label="Error"]) { 
            border: 1px solid #A03C3C !important; color: #A03C3C !important; 
        }
        div[data-testid="stAlert"]:has(div[aria-label="Error"]) svg { fill: #A03C3C !important; }

        /* 表格優化 */
        [data-testid="stDataFrame"] { border: 1px solid #CCCCCC; }
        [data-testid="stDataFrame"] th { background-color: #E0DED0 !important; color: #333333 !important; border-bottom: 1px solid #333333 !important; }
        [data-testid="stDataFrame"] td { border-bottom: 1px solid #E0E0E0 !important; color: #333333 !important; }
        
        /* 隱藏預設裝飾 */
        [data-testid="stDecoration"] { display: none; }
        </style>
        """, unsafe_allow_html=True)

# --- 資料讀取與處理 ---
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        # 自動補齊新欄位 (防呆)
        if "審核狀態" not in df.columns: df["審核狀態"] = "待審核"
        if "審核時間" not in df.columns: df["審核時間"] = ""
        df["審核狀態"] = df["審核狀態"].fillna("待審核")
        df["審核時間"] = df["審核時間"].fillna("")
        return df
    else:
        return pd.DataFrame(columns=[
            "提交時間", "姓名", "類型", "日期", 
            "開始時間", "結束時間", "時數", "備註", 
            "審核狀態", "審核時間"
        ])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# --- 主程式 ---
def main():
    local_css()
    st.set_page_config(page_title="班表管理", page_icon="⏰")
    
    st.title("⏰ 團隊時數管理系統")

    df = load_data()

    # === 區塊 1: 員工申請 ===
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
            submitted = st.form_submit_button("送出申請")

            if submitted:
                if name == "":
                    st.error("❌ 請輸入姓名！")
                else:
                    start_dt = datetime.combine(date, start_time)
                    end_dt = datetime.combine(date, end_time)
                    if end_dt <= start_dt:
                        st.error("❌ 結束時間必須晚於開始時間！")
                    else:
                        duration = (end_dt - start_dt).total_seconds() / 3600
                        duration = round(duration, 1)
                        
                        new_data = {
                            "提交時間": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "姓名": name, "類型": apply_type, "日期": date,
                            "開始時間": start_time, "結束時間": end_time, "時數": duration,
                            "備註": note, "審核狀態": "待審核", "審核時間": ""
                        }
                        df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
                        save_data(df)
                        st.success(f"✅ 已送出！狀態：待審核")

    st.markdown("---")

    # === 區塊 2: 管理後台 ===
    st.sidebar.header("🔐 管理員登入")
    input_password = st.sidebar.text_input("輸入密碼查看報表", type="password")

    if input_password == ADMIN_PASSWORD:
        st.sidebar.success("身份驗證成功")
        st.header("📊 管理員報表")

        if not df.empty:
            # --- 審核區 ---
            st.subheader("⚡ 待審核項目")
            pending_df = df[df["審核狀態"] == "待審核"]
            
            if pending_df.empty:
                st.info("目前沒有待審核的項目。")
            else:
                for index, row in pending_df.iterrows():
                    with st.container():
                        c1, c2, c3, c4, c5 = st.columns([1.5, 2, 2, 1, 1])
                        c1.text(f"👤 {row['姓名']}")
                        c2.text(f"📅 {row['日期']}")
                        c3.text(f"{row['類型']}")
                        c4.text(f"⏳ {row['時數']}")
                        # 審核按鈕
                        if c5.button("通過", key=f"btn_{index}"):
                            df.at[index, "審核狀態"] = "已通過"
                            df.at[index, "審核時間"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                            save_data(df)
                            st.rerun()
                        st.markdown("<hr style='margin: 5px 0; opacity: 0.3;'>", unsafe_allow_html=True)

            st.markdown("---")

            # --- 統計區 (只算已通過) ---
            st.subheader("👥 人員時數餘額 (僅計算已通過)")
            approved_df = df[df["審核狀態"] == "已通過"]
            summary = approved_df.groupby(['姓名', '類型'])['時數'].sum().unstack(fill_value=0)
            
            for col in ["加班 (Overtime)", "抵班/補休 (Comp Time)"]:
                if col not in summary.columns: summary[col] = 0.0

            summary = summary.rename(columns={"加班 (Overtime)": "加班總時數", "抵班/補休 (Comp Time)": "已抵休時數"})
            summary["剩餘可休時數"] = summary["加班總時數"] - summary["已抵休時數"]
            
            st.dataframe(
                summary.style.format("{:.1f}")
                .map(lambda x: 'color: #A03C3C' if x < 0 else 'color: #4A5D23', subset=['剩餘可休時數']),
                use_container_width=True
            )

            # --- 歷史明細 ---
            st.subheader("📋 所有申請明細")
            filter_person = st.selectbox("篩選特定員工", ["全部"] + list(df["姓名"].unique()))
            view_df = df[df["姓名"] == filter_person] if filter_person != "全部" else df

            st.dataframe(
                view_df.sort_values("提交時間", ascending=False)
                .style.format({"時數": "{:.1f}"})
                .map(lambda v: 'color: #4A5D23; font-weight: bold' if v == '已通過' else 'color: #999999', subset=['審核狀態']),
                use_container_width=True
            )
        else:
            st.info("尚無資料。")
    elif input_password != "":
        st.sidebar.error("密碼錯誤")

if __name__ == "__main__":
    main()

