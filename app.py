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

# --- Aesop 風格 CSS (純文字極簡版) ---
def local_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', Helvetica, Arial, sans-serif; color: #333333; }
        
        /* 標題與文字 */
        h1, h2, h3 { font-weight: 600 !important; letter-spacing: -0.5px; }
        
        /* 側邊欄 */
        [data-testid="stSidebar"] { border-right: 1px solid #D0CDBC; background-color: #EAE8D9; }
        
        /* 輸入框樣式 */
        .stTextInput > div > div > input, .stDateInput > div > div > input, .stTimeInput > div > div > input, 
        .stSelectbox > div > div > div, .stTextArea > div > div > textarea {
            background-color: transparent !important; 
            border: 1px solid #999999 !important; 
            border-radius: 0px !important; 
            color: #333333 !important;
        }
        
        /* 按鈕樣式 */
        .stButton > button {
            background-color: transparent !important; 
            color: #333333 !important; 
            border: 1px solid #333333 !important; 
            border-radius: 0px !important; 
            transition: all 0.3s ease;
        }
        .stButton > button:hover { background-color: #333333 !important; color: #F6F5E8 !important; }
        
        /* 隱藏系統預設 Alert 圖示 */
        div[data-testid="stAlert"] svg { display: none !important; }
        div[data-testid="stAlert"] { background-color: transparent !important; border-radius: 0px !important; }
        
        /* 表格樣式 */
        [data-testid="stDataFrame"] { border: 1px solid #CCCCCC; }
        [data-testid="stDataFrame"] th { background-color: #E0DED0 !important; color: #333333 !important; }
        [data-testid="stDecoration"] { display: none; }
        
        /* 彈出視窗樣式優化 */
        div[data-testid="stDialog"] { border-radius: 0px !important; background-color: #F6F5E8 !important; }
        </style>
        """, unsafe_allow_html=True)

# --- 資料讀取 ---
def load_data():
    columns = [
        "提交時間", "姓名", "類型", "日期", 
        "開始時間", "結束時間", "時數", "備註", 
        "審核狀態", "審核時間", "月份"
    ]

    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE, encoding='utf-8-sig')
            for col in columns:
                if col not in df.columns: df[col] = ""
            
            # 清洗與轉換
            df["審核狀態"] = df["審核狀態"].fillna("待審核")
            df["類型"] = df["類型"].astype(str).replace({
                "加班 (Overtime)": "加班",
                "抵班/補休 (Comp Time)": "抵班/補休"
            }).str.strip()
            
            df["日期"] = pd.to_datetime(df["日期"], errors='coerce')
            df = df.dropna(subset=["日期"])
            df["月份"] = df["日期"].dt.strftime("%Y-%m")
            df = df.reset_index(drop=True)
            return df
        except Exception:
            return pd.DataFrame(columns=columns)
    else:
        return pd.DataFrame(columns=columns)

def save_data(df):
    df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

# --- 彈出視窗 (Modal) ---
@st.dialog("申請確認")
def success_dialog(name, apply_type, date_str, duration, note):
    st.markdown(f"""
    **申請已送出，請確認以下資訊：**
    
    * **姓名**: {name}
    * **日期**: {date_str}
    * **類型**: {apply_type}
    * **時數**: {duration} 小時
    * **備註**: {note if note else "無"}
    
    請通知管理員進行審核。
    """)
    if st.button("關閉視窗"):
        st.rerun()

# --- 主程式 ---
def main():
    local_css()
    st.set_page_config(page_title="班表管理", page_icon=None)
    
    # 初始化 Session State (用來記住登入狀態)
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    st.title("團隊時數管理系統")

    df = load_data()

    # === 員工申請區 ===
    st.markdown("### 員工申請區")
    
    # 這裡不要用 expander 包住 form，避免狀態重置問題，直接顯示
    with st.container(border=True):
        st.caption("填寫表單")
        with st.form("application_form", clear_on_submit=True): # clear_on_submit 會自動清空欄位
            c1, c2 = st.columns(2)
            name = c1.text_input("姓名 (請輸入全名)")
            date = c1.date_input("日期", datetime.today())
            apply_type = c2.selectbox("申請類型", ["加班", "抵班/補休"])
            c3, c4 = st.columns(2)
            start_time = c3.time_input("開始時間", datetime.strptime("09:00", "%H:%M").time())
            end_time = c4.time_input("結束時間", datetime.strptime("18:00", "%H:%M").time())
            note = st.text_area("備註 (選填)")
            
            submitted = st.form_submit_button("送出申請")

            if submitted:
                if not name:
                    st.error("請輸入姓名")
                else:
                    start_dt = datetime.combine(date, start_time)
                    end_dt = datetime.combine(date, end_time)
                    
                    if end_dt <= start_dt:
                        st.error("結束時間必須晚於開始時間")
                    else:
                        duration = round((end_dt - start_dt).total_seconds() / 3600, 1)
                        new_row = {
                            "提交時間": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "姓名": name, "類型": apply_type, "日期": date,
                            "開始時間": start_time.strftime("%H:%M"), "結束時間": end_time.strftime("%H:%M"),
                            "時數": duration, "備註": note, "審核狀態": "待審核", "審核時間": "",
                            "月份": date.strftime("%Y-%m")
                        }
                        
                        # 存檔
                        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                        save_data(df)
                        
                        # 呼叫彈出視窗 (這會暫停程式直到使用者按關閉)
                        d_str = date.strftime('%Y-%m-%d')
                        success_dialog(name, apply_type, d_str, duration, note)

    st.markdown("---")

    # === 管理後台 (修復登入問題) ===
    st.sidebar.header("管理員後台")

    # 如果還沒登入，顯示輸入框
    if not st.session_state.logged_in:
        input_password = st.sidebar.text_input("輸入密碼", type="password")
        if st.sidebar.button("登入"):
            if input_password == ADMIN_PASSWORD:
                st.session_state.logged_in = True
                st.rerun() # 登入成功後刷新頁面
            else:
                st.sidebar.error("密碼錯誤")
    
    # 如果已經登入，顯示報表
    else:
        if st.sidebar.button("登出"):
            st.session_state.logged_in = False
            st.rerun()

        st.sidebar.success("已登入")
        st.header("管理員報表")

        if not df.empty:
            # 1. 待審核
            st.subheader("待審核項目")
            pending_df = df[df["審核狀態"] == "待審核"]
            
            if pending_df.empty:
                st.info("無待審核項目")
            else:
                for idx, row in pending_df.iterrows():
                    with st.container():
                        c1, c2, c3, c4, c5, c6 = st.columns([1.5, 2, 2, 1, 0.8, 0.8])
                        c1.text(f"{row['姓名']}")
                        d_str = row['日期'].strftime('%Y-%m-%d') if isinstance(row['日期'], pd.Timestamp) else str(row['日期'])
                        c2.text(d_str)
                        c3.text(f"{row['類型']}")
                        c4.text(f"{row['時數']}")
                        
                        if c5.button("通過", key=f"pass_{idx}"):
                            df.at[idx, "審核狀態"] = "已通過"
                            df.at[idx, "審核時間"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                            save_data(df)
                            st.rerun()
                        if c6.button("刪除", key=f"del_{idx}"):
                            df = df.drop(idx)
                            save_data(df)
                            st.rerun()
                        st.markdown("<hr style='margin: 5px 0; opacity: 0.3;'>", unsafe_allow_html=True)

            st.markdown("---")

            # 2. 統計
            st.subheader("報表篩選")
            all_months = sorted(df["月份"].dropna().unique().tolist(), reverse=True)
            selected_month = st.selectbox("選擇月份", ["全部"] + all_months)
            filtered_df = df if selected_month == "全部" else df[df["月份"] == selected_month]
            
            st.subheader("人員時數統計 (已通過)")
            approved_df = filtered_df[filtered_df["審核狀態"] == "已通過"]
            
            stats = []
            if not approved_df.empty:
                for p in approved_df["姓名"].unique():
                    p_data = approved_df[approved_df["姓名"] == p]
                    ot = p_data[p_data["類型"].astype(str).str.contains("加班")]["時數"].sum()
                    comp = p_data[p_data["類型"].astype(str).str.contains("補休")]["時數"].sum()
                    stats.append({"姓名": p, "加班總時數": ot, "已抵休時數": comp, "小計/餘額": ot - comp})
                stat_df = pd.DataFrame(stats)
            else:
                stat_df = pd.DataFrame(columns=["姓名", "加班總時數", "已抵休時數", "小計/餘額"])
            
            st.dataframe(
                stat_df.style.format("{:.1f}", subset=["加班總時數", "已抵休時數", "小計/餘額"])
                .map(lambda x: 'color: #A03C3C' if x < 0 else 'color: #4A5D23', subset=['小計/餘額']),
                use_container_width=True
            )

            # 3. 歷史明細
            st.subheader("申請明細列表")
            filter_person = st.selectbox("篩選員工", ["全部"] + list(df["姓名"].unique()))
            view_df = filtered_df[filtered_df["姓名"] == filter_person] if filter_person != "全部" else filtered_df
            
            view_disp = view_df.copy()
            if not view_disp.empty:
                view_disp["日期"] = view_disp["日期"].apply(lambda x: x.strftime('%Y-%m-%d') if isinstance(x, pd.Timestamp) else str(x))
            
            st.dataframe(
                view_disp.sort_values("提交時間", ascending=False)
                .style.format({"時數": "{:.1f}"})
                .map(lambda v: 'color: #4A5D23; font-weight: bold' if v == '已通過' else 'color: #999999', subset=['審核狀態']),
                use_container_width=True
            )
            
            # 4. 刪除工具
            st.markdown("---")
            with st.expander("🗑️ 刪除歷史資料"):
                opts = {f"[{i}] {r['姓名']} {r['日期']} {r['類型']}": i for i, r in df.sort_values("提交時間", ascending=False).iterrows()}
                if opts:
                    sel = st.selectbox("選擇刪除項目", list(opts.keys()))
                    if st.button("確認刪除"):
                        df = df.drop(opts[sel])
                        save_data(df)
                        st.success("已刪除")
                        st.rerun()
                else:
                    st.text("無資料")

        else:
            st.info("尚無資料")

if __name__ == "__main__":
    main()
