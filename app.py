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

# --- Aesop 風格客製化 CSS ---
def local_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', Helvetica, Arial, sans-serif; color: #333333; }
        h1, h2, h3 { font-weight: 600 !important; letter-spacing: -0.5px; }
        .stMarkdown p { font-weight: 300; line-height: 1.6; }
        [data-testid="stSidebar"] { border-right: 1px solid #D0CDBC; background-color: #EAE8D9; }
        .stTextInput > div > div > input, .stDateInput > div > div > input, .stTimeInput > div > div > input, 
        .stSelectbox > div > div > div, .stTextArea > div > div > textarea {
            background-color: transparent !important; border: 1px solid #999999 !important; border-radius: 0px !important; color: #333333 !important;
        }
        .stButton > button {
            background-color: transparent !important; color: #333333 !important; border: 1px solid #333333 !important; border-radius: 0px !important; transition: all 0.3s ease;
        }
        .stButton > button:hover { background-color: #333333 !important; color: #F6F5E8 !important; }
        div[data-testid="stAlert"] { background-color: transparent !important; border-radius: 0px !important; }
        div[data-testid="stAlert"] svg { display: none !important; }
        div[data-testid="stAlert"]:has(div[aria-label="Success"]) { border: 1px solid #4A5D23 !important; color: #4A5D23 !important; }
        div[data-testid="stAlert"]:has(div[aria-label="Error"]) { border: 1px solid #A03C3C !important; color: #A03C3C !important; }
        [data-testid="stDataFrame"] { border: 1px solid #CCCCCC; }
        [data-testid="stDataFrame"] th { background-color: #E0DED0 !important; color: #333333 !important; }
        [data-testid="stDataFrame"] td { border-bottom: 1px solid #E0E0E0 !important; color: #333333 !important; }
        [data-testid="stDecoration"] { display: none; }
        </style>
        """, unsafe_allow_html=True)

# --- 資料讀取 (加入 utf-8-sig 與 重置索引) ---
def load_data():
    columns = [
        "提交時間", "姓名", "類型", "日期", 
        "開始時間", "結束時間", "時數", "備註", 
        "審核狀態", "審核時間", "月份"
    ]

    if os.path.exists(DATA_FILE):
        try:
            # 關鍵修正 1: 使用 utf-8-sig 編碼讀取，避免中文亂碼
            df = pd.read_csv(DATA_FILE, encoding='utf-8-sig')
            
            # 補齊欄位
            for col in columns:
                if col not in df.columns:
                    df[col] = ""

            # 確保欄位皆為字串，避免錯誤
            df["審核狀態"] = df["審核狀態"].fillna("待審核")
            df["審核時間"] = df["審核時間"].fillna("")
            
            # 修正舊資料名稱
            df["類型"] = df["類型"].astype(str).replace({
                "加班 (Overtime)": "加班",
                "抵班/補休 (Comp Time)": "抵班/補休"
            }).str.strip()

            # 處理日期
            df["日期"] = pd.to_datetime(df["日期"], errors='coerce')
            df = df.dropna(subset=["日期"])
            df["月份"] = df["日期"].dt.strftime("%Y-%m")
            
            # 關鍵修正 2: 重置索引，確保按鈕操作時不會對應錯行
            df = df.reset_index(drop=True)
            
            return df
        except Exception:
            return pd.DataFrame(columns=columns)
    else:
        return pd.DataFrame(columns=columns)

def save_data(df):
    # 關鍵修正 3: 存檔時也使用 utf-8-sig
    df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

# --- 主程式 ---
def main():
    local_css()
    st.set_page_config(page_title="班表管理", page_icon=None)
    st.title("團隊時數管理系統")

    df = load_data()

    # === 員工申請區 ===
    st.markdown("### 員工申請區")
    with st.expander("點擊展開填寫表單", expanded=True):
        with st.form("application_form"):
            c1, c2 = st.columns(2)
            name = c1.text_input("姓名 (請輸入全名)")
            date = c1.date_input("日期", datetime.today())
            apply_type = c2.selectbox("申請類型", ["加班", "抵班/補休"])
            c3, c4 = st.columns(2)
            start_time = c3.time_input("開始時間", datetime.strptime("09:00", "%H:%M").time())
            end_time = c4.time_input("結束時間", datetime.strptime("18:00", "%H:%M").time())
            note = st.text_area("備註 (選填)")
            
            if st.form_submit_button("送出申請"):
                if not name:
                    st.error("請輸入姓名！")
                else:
                    start_dt = datetime.combine(date, start_time)
                    end_dt = datetime.combine(date, end_time)
                    if end_dt <= start_dt:
                        st.error("時間錯誤！")
                    else:
                        duration = round((end_dt - start_dt).total_seconds() / 3600, 1)
                        new_row = {
                            "提交時間": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "姓名": name, "類型": apply_type, "日期": date,
                            "開始時間": start_time.strftime("%H:%M"), "結束時間": end_time.strftime("%H:%M"),
                            "時數": duration, "備註": note, "審核狀態": "待審核", "審核時間": "",
                            "月份": date.strftime("%Y-%m")
                        }
                        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                        save_data(df)
                        st.success("已送出！請通知管理員審核。")
                        st.rerun()

    st.markdown("---")

    # === 管理後台 ===
    st.sidebar.header("管理員登入")
    input_password = st.sidebar.text_input("輸入密碼", type="password")

    if input_password == ADMIN_PASSWORD:
        st.sidebar.success("身份驗證成功")
        st.header("管理員報表")

        if not df.empty:
            # --- 待審核區 ---
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
                        
                        # 按鈕使用 row 的 index (因為經過 reset_index，這是安全的)
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

            # --- 統計報表 ---
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
                    # 強制轉字串再搜尋，避免型別錯誤
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

            # --- 歷史明細 ---
            st.subheader("申請明細列表")
            filter_person = st.selectbox("篩選員工", ["全部"] + list(df["姓名"].unique()))
            view_df = filtered_df[filtered_df["姓名"] == filter_person] if filter_person != "全部" else filtered_df
            
            # 顯示處理
            view_display = view_df.copy()
            if not view_display.empty:
                view_display["日期"] = view_display["日期"].apply(lambda x: x.strftime('%Y-%m-%d') if isinstance(x, pd.Timestamp) else str(x))
                
            st.dataframe(
                view_display.sort_values("提交時間", ascending=False)
                .style.format({"時數": "{:.1f}"})
                .map(lambda v: 'color: #4A5D23; font-weight: bold' if v == '已通過' else 'color: #999999', subset=['審核狀態']),
                use_container_width=True
            )

            # --- 刪除功能 ---
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
            
            st.markdown("---")
            # --- 診斷區 (新功能) ---
            with st.expander("🔧 原始資料診斷 (若資料異常請看這)"):
                st.caption("這是資料庫目前最原始的樣子，如果上面表格沒顯示，但這裡有，代表是篩選器或計算邏輯的問題。")
                st.dataframe(df)

        else:
            st.info("尚無資料")
    elif input_password:
        st.sidebar.error("密碼錯誤")

if __name__ == "__main__":
    main()
