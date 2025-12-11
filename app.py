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

# --- CSS ---
def local_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', Helvetica, Arial, sans-serif; color: #333333; }
        h1, h2, h3 { font-weight: 600 !important; letter-spacing: -0.5px; }
        [data-testid="stSidebar"] { border-right: 1px solid #D0CDBC; background-color: #EAE8D9; }
        .stTextInput > div > div > input, .stDateInput > div > div > input, .stTimeInput > div > div > input, 
        .stSelectbox > div > div > div, .stTextArea > div > div > textarea {
            background-color: transparent !important; border: 1px solid #999999 !important; border-radius: 0px !important; color: #333333 !important;
        }
        .stButton > button { background-color: transparent !important; color: #333333 !important; border: 1px solid #333333 !important; border-radius: 0px !important; transition: all 0.3s ease; }
        .stButton > button:hover { background-color: #333333 !important; color: #F6F5E8 !important; }
        div[data-testid="stAlert"] svg { display: none !important; }
        div[data-testid="stAlert"] { background-color: transparent !important; border-radius: 0px !important; }
        [data-testid="stDataFrame"] { border: 1px solid #CCCCCC; }
        [data-testid="stDataFrame"] th { background-color: #E0DED0 !important; color: #333333 !important; }
        [data-testid="stDecoration"] { display: none; }
        div[data-testid="stDialog"] { border-radius: 0px !important; background-color: #F6F5E8 !important; }
        </style>
        """, unsafe_allow_html=True)

# --- 資料讀取 (修復版) ---
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
            
            # 填補空值
            df["審核狀態"] = df["審核狀態"].fillna("待審核")
            df["類型"] = df["類型"].astype(str).str.strip()
            
            # --- 關鍵修正：更寬容的日期讀取 ---
            # 如果日期讀取失敗，不要刪除整行，而是保留原字串，讓我們看看到底發生什麼事
            df["日期_原始"] = df["日期"] # 備份原始資料供檢查
            df["日期"] = pd.to_datetime(df["日期"], errors='coerce')
            
            # 如果日期轉換失敗 (NaT)，我們暫時填入今天的日期，避免資料消失
            # 這樣至少您在後台看得到那筆資料，可以手動刪除重來
            if df["日期"].isna().any():
                df["日期"] = df["日期"].fillna(datetime.today())
                
            df["月份"] = df["日期"].dt.strftime("%Y-%m")
            df = df.reset_index(drop=True)
            return df
        except Exception as e:
            # 如果讀取徹底失敗，顯示錯誤
            st.error(f"資料讀取嚴重錯誤: {e}")
            return pd.DataFrame(columns=columns)
    else:
        return pd.DataFrame(columns=columns)

def save_data(df):
    try:
        # 移除暫存的備份欄位再存檔
        if "日期_原始" in df.columns:
            df = df.drop(columns=["日期_原始"])
        df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
    except Exception as e:
        st.error(f"存檔失敗: {e}")

# --- 彈出視窗 ---
@st.dialog("申請確認")
def success_dialog(name, apply_type, date_str, duration, note):
    st.markdown(f"""
    **✅ 申請成功！**
    
    * **姓名**: {name}
    * **類型**: {apply_type}
    * **日期**: {date_str}
    * **時數**: {duration} 小時
    
    資料已寫入資料庫，請通知管理員。
    """)
    if st.button("我知道了 (關閉)"):
        st.rerun()

# --- 主程式 ---
def main():
    local_css()
    st.set_page_config(page_title="班表管理", page_icon=None)
    
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    st.title("團隊時數管理系統")

    df = load_data()

    # === 員工申請區 ===
    st.markdown("### 員工申請區")
    
    with st.container(border=True):
        st.caption("填寫表單")
        with st.form("application_form", clear_on_submit=True):
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
                        
                        # --- 關鍵修正：存檔前強制把日期轉成字串 ---
                        # 這樣存進 CSV 就是純文字 "2025-12-12"，讀取時絕對不會錯
                        date_str_for_save = date.strftime("%Y-%m-%d")
                        
                        new_row = {
                            "提交時間": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "姓名": name, "類型": apply_type, 
                            "日期": date_str_for_save, # 這裡存純文字
                            "開始時間": start_time.strftime("%H:%M"), "結束時間": end_time.strftime("%H:%M"),
                            "時數": duration, "備註": note, "審核狀態": "待審核", "審核時間": "",
                            "月份": date.strftime("%Y-%m")
                        }
                        
                        # 重新讀取一次最新的 df 再寫入，避免多人同時操作時覆蓋
                        current_df = load_data()
                        current_df = pd.concat([current_df, pd.DataFrame([new_row])], ignore_index=True)
                        save_data(current_df)
                        
                        success_dialog(name, apply_type, date_str_for_save, duration, note)

    st.markdown("---")

    # === 管理後台 ===
    st.sidebar.header("管理員後台")

    if not st.session_state.logged_in:
        input_password = st.sidebar.text_input("輸入密碼", type="password")
        if st.sidebar.button("登入"):
            if input_password == ADMIN_PASSWORD:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.sidebar.error("密碼錯誤")
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
                        
                        # 安全顯示日期
                        try:
                            d_str = row['日期'].strftime('%Y-%m-%d') if isinstance(row['日期'], pd.Timestamp) else str(row['日期'])
                        except:
                            d_str = str(row['日期'])
                            
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
            
            # 安全取得月份列表
            try:
                all_months = sorted(df["月份"].dropna().unique().tolist(), reverse=True)
            except:
                all_months = []
                
            selected_month = st.selectbox("選擇月份", ["全部"] + all_months)
            filtered_df = df if selected_month == "全部" else df[df["月份"] == selected_month]
            
            st.subheader("人員時數統計 (已通過)")
            approved_df = filtered_df[filtered_df["審核狀態"] == "已通過"]
            
            stats = []
            if not approved_df.empty:
                for p in approved_df["姓名"].unique():
                    p_data = approved_df[approved_df["姓名"] == p]
                    # 使用更寬容的包含搜尋
                    ot = p_data[p_data["類型"].str.contains("加班", na=False)]["時數"].sum()
                    comp = p_data[p_data["類型"].str.contains("補休", na=False)]["時數"].sum()
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
                opts = {}
                for i, r in df.sort_values("提交時間", ascending=False).iterrows():
                    # 安全獲取日期字串
                    try:
                        d_show = r['日期'].strftime('%Y-%m-%d') if isinstance(r['日期'], pd.Timestamp) else str(r['日期'])
                    except:
                        d_show = "日期錯誤"
                    opts[f"[{i}] {r['姓名']} {d_show} {r['類型']}"] = i
                
                if opts:
                    sel = st.selectbox("選擇刪除項目", list(opts.keys()))
                    if st.button("確認刪除"):
                        df = df.drop(opts[sel])
                        save_data(df)
                        st.success("已刪除")
                        st.rerun()
                else:
                    st.text("無資料")
                    
            # 5. 除錯專用 (如果資料還是消失，請看這裡)
            with st.expander("🔧 資料庫原始視圖 (除錯用)"):
                st.caption("如果資料有進來，這裡一定看得到。")
                st.dataframe(df)

        else:
            st.info("尚無資料")

if __name__ == "__main__":
    main()
