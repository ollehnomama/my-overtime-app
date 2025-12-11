import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- 設定檔案儲存路徑 ---
DATA_FILE = "schedule_data.csv"

# --- 讀取密碼 ---
if "admin_password" in st.secrets:
    ADMIN_PASSWORD = st.secrets["admin_password"]
else:
    ADMIN_PASSWORD = "boss"

# --- Aesop 風格客製化 CSS (純文字極簡版) ---
def local_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', 'Helvetica Neue', Helvetica, Arial, sans-serif;
            color: #333333;
        }

        h1, h2, h3 { font-weight: 600 !important; letter-spacing: -0.5px; }
        .stMarkdown p { font-weight: 300; line-height: 1.6; }

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

        /* Alert 訊息框風格 - 強制隱藏系統預設圖示 */
        div[data-testid="stAlert"] { 
            background-color: transparent !important; 
            border-radius: 0px !important; 
            padding: 0.5rem 1rem !important;
        }
        /* 隱藏 Alert 裡面的 icon (勾勾或叉叉) */
        div[data-testid="stAlert"] svg {
            display: none !important;
        }

        /* 成功訊息 (Success) */
        div[data-testid="stAlert"]:has(div[aria-label="Success"]) { 
            border: 1px solid #4A5D23 !important; 
            color: #4A5D23 !important; 
        }
        
        /* 錯誤訊息 (Error) */
        div[data-testid="stAlert"]:has(div[aria-label="Error"]) { 
            border: 1px solid #A03C3C !important; 
            color: #A03C3C !important; 
        }

        /* 表格優化 */
        [data-testid="stDataFrame"] { border: 1px solid #CCCCCC; }
        [data-testid="stDataFrame"] th { background-color: #E0DED0 !important; color: #333333 !important; border-bottom: 1px solid #333333 !important; }
        [data-testid="stDataFrame"] td { border-bottom: 1px solid #E0E0E0 !important; color: #333333 !important; }
        [data-testid="stDecoration"] { display: none; }
        </style>
        """, unsafe_allow_html=True)

# --- 資料讀取與處理 ---
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        if "審核狀態" not in df.columns: df["審核狀態"] = "待審核"
        if "審核時間" not in df.columns: df["審核時間"] = ""
        df["審核狀態"] = df["審核狀態"].fillna("待審核")
        df["審核時間"] = df["審核時間"].fillna("")
        
        df["日期"] = pd.to_datetime(df["日期"])
        df["月份"] = df["日期"].dt.strftime("%Y-%m")
        return df
    else:
        return pd.DataFrame(columns=[
            "提交時間", "姓名", "類型", "日期", 
            "開始時間", "結束時間", "時數", "備註", 
            "審核狀態", "審核時間", "月份"
        ])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# --- 主程式 ---
def main():
    local_css()
    # page_icon 設為 None，瀏覽器分頁標籤就不會顯示 emoji
    st.set_page_config(page_title="班表管理", page_icon=None)
    
    st.title("團隊時數管理系統")

    df = load_data()

    # === 區塊 1: 員工申請區 ===
    st.markdown("### 員工申請區")
    with st.expander("點擊展開填寫表單", expanded=True):
        with st.form("application_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("姓名 (請輸入全名)")
                date = st.date_input("日期", datetime.today())
            with col2:
                apply_type = st.selectbox("申請類型", ["加班", "抵班/補休"])
            
            col3, col4 = st.columns(2)
            with col3:
                start_time = st.time_input("開始時間", datetime.strptime("09:00", "%H:%M").time())
            with col4:
                end_time = st.time_input("結束時間", datetime.strptime("18:00", "%H:%M").time())
            
            note = st.text_area("備註 (選填)")
            submitted = st.form_submit_button("送出申請")

            if submitted:
                if name == "":
                    st.error("請輸入姓名！")
                else:
                    start_dt = datetime.combine(date, start_time)
                    end_dt = datetime.combine(date, end_time)
                    if end_dt <= start_dt:
                        st.error("結束時間必須晚於開始時間！")
                    else:
                        duration = (end_dt - start_dt).total_seconds() / 3600
                        duration = round(duration, 1)
                        month_str = date.strftime("%Y-%m")
                        
                        new_data = {
                            "提交時間": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "姓名": name, "類型": apply_type, "日期": date,
                            "開始時間": start_time.strftime("%H:%M"), 
                            "結束時間": end_time.strftime("%H:%M"), 
                            "時數": duration,
                            "備註": note, "審核狀態": "待審核", "審核時間": "",
                            "月份": month_str
                        }
                        df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
                        save_data(df)
                        st.success(f"已送出！狀態：待審核")

    st.markdown("---")

    # === 區塊 2: 管理後台 ===
    st.sidebar.header("管理員登入")
    input_password = st.sidebar.text_input("輸入密碼查看報表", type="password")

    if input_password == ADMIN_PASSWORD:
        st.sidebar.success("身份驗證成功")
        st.header("管理員報表")

        if not df.empty:
            # --- 審核區 ---
            st.subheader("待審核項目")
            pending_df = df[df["審核狀態"] == "待審核"]
            
            if pending_df.empty:
                st.info("目前沒有待審核的項目。")
            else:
                for index, row in pending_df.iterrows():
                    with st.container():
                        c1, c2, c3, c4, c5 = st.columns([1.5, 2, 2, 1, 1])
                        c1.text(f"{row['姓名']}")
                        date_display = row['日期'].strftime('%Y-%m-%d') if isinstance(row['日期'], pd.Timestamp) else row['日期']
                        c2.text(f"{date_display}")
                        c3.text(f"{row['類型']}")
                        c4.text(f"{row['時數']}")
                        if c5.button("通過", key=f"btn_{index}"):
                            df.at[index, "審核狀態"] = "已通過"
                            df.at[index, "審核時間"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                            save_data(df)
                            st.rerun()
                        st.markdown("<hr style='margin: 5px 0; opacity: 0.3;'>", unsafe_allow_html=True)

            st.markdown("---")

            # --- 全域篩選器 ---
            st.subheader("報表篩選")
            all_months = sorted(df["月份"].dropna().unique().tolist(), reverse=True)
            selected_month = st.selectbox("請選擇月份", ["全部"] + all_months)
            
            if selected_month == "全部":
                filtered_df = df
                st.caption("目前顯示：所有時間累計")
            else:
                filtered_df = df[df["月份"] == selected_month]
                st.caption(f"目前顯示：{selected_month} 月份資料")

            # --- 統計區 ---
            st.subheader("人員時數統計 (已通過)")
            approved_df = filtered_df[filtered_df["審核狀態"] == "已通過"]
            summary = approved_df.groupby(['姓名', '類型'])['時數'].sum().unstack(fill_value=0)
            
            for col in ["加班", "抵班/補休"]:
                if col not in summary.columns: summary[col] = 0.0

            summary = summary.rename(columns={"加班": "加班總時數", "抵班/補休": "已抵休時數"})
            summary["小計/餘額"] = summary["加班總時數"] - summary["已抵休時數"]
            
            st.dataframe(
                summary.style.format("{:.1f}")
                .map(lambda x: 'color: #A03C3C' if x < 0 else 'color: #4A5D23', subset=['小計/餘額']),
                use_container_width=True
            )

            # --- 歷史明細 ---
            st.subheader("申請明細列表")
            filter_person = st.selectbox("篩選特定員工", ["全部"] + list(df["姓名"].unique()))
            
            view_df = filtered_df
            if filter_person != "全部":
                view_df = view_df[view_df["姓名"] == filter_person]

            view_df_display = view_df.copy()
            if not view_df_display.empty:
                view_df_display["日期"] = view_df_display["日期"].apply(lambda x: x.strftime('%Y-%m-%d') if isinstance(x, pd.Timestamp) else x)

            st.dataframe(
                view_df_display.sort_values("提交時間", ascending=False)
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
