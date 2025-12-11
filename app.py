import streamlit as st
import pandas as pd
from datetime import datetime, date
from streamlit_gsheets import GSheetsConnection # 引入 Google 連線套件

# --- 讀取密碼 ---
if "admin_password" in st.secrets:
    ADMIN_PASSWORD = st.secrets["admin_password"]
else:
    ADMIN_PASSWORD = "boss"

# --- 產生 30 分鐘間隔的時間列表 ---
TIME_OPTIONS = [f"{h:02d}:{m:02d}" for h in range(24) for m in (0, 30)]

# --- Aesop 風格 CSS ---
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
        div[data-testid="stDialog"] { border-radius: 0px !important; background-color: #F6F5E8 !important; }
        [data-testid="stCheckbox"] { display: flex; justify-content: center; }
        </style>
        """, unsafe_allow_html=True)

# --- 資料讀取 (Google Sheets 版) ---
def load_data(conn):
    columns = [
        "提交時間", "姓名", "類型", "日期", 
        "開始時間", "結束時間", "時數", "備註", 
        "審核狀態", "審核時間", "月份"
    ]
    
    try:
        # 從 Google Sheets 的 "Records" 分頁讀取資料
        # ttl=0 代表不快取，每次都抓最新的
        df = conn.read(worksheet="Records", ttl=0)
        
        # 如果是空的或欄位不對，補齊欄位
        for col in columns:
            if col not in df.columns: df[col] = ""
        df = df.fillna("")
        
        # 強制轉換格式 (跟之前一樣的防錯機制)
        df["時數"] = pd.to_numeric(df["時數"], errors='coerce').fillna(0.0)
        df["日期_obj"] = pd.to_datetime(df["日期"], errors='coerce')
        df.loc[df["日期_obj"].isna(), "日期_obj"] = datetime(1900, 1, 1)
        
        df["月份"] = df["日期_obj"].dt.strftime("%Y-%m")
        df.loc[df["月份"] == "1900-01", "月份"] = "未知"
        
        df["類型"] = df["類型"].astype(str).str.strip()
        df["審核狀態"] = df["審核狀態"].replace("", "待審核")
        
        # 確保全部轉為字串儲存，避免 Google Sheets 格式亂跳
        # 除了時數維持數字
        
        return df
    except Exception as e:
        # 如果是第一次建立，可能是空的，回傳空表
        return pd.DataFrame(columns=columns)

# --- 資料存檔 (Google Sheets 版) ---
def save_data(conn, df):
    try:
        df_save = df.copy()
        # 移除暫存欄位
        if "日期_obj" in df_save.columns:
            df_save = df_save.drop(columns=["日期_obj"])
        if "勾選刪除" in df_save.columns:
            df_save = df_save.drop(columns=["勾選刪除"])
            
        # 寫入 Google Sheets 的 "Records" 分頁
        conn.update(worksheet="Records", data=df_save)
        
        # 清除快取，確保下次讀到最新的
        st.cache_data.clear()
    except Exception as e:
        st.error(f"雲端存檔失敗: {e}")

# --- 彈出視窗 ---
@st.dialog("申請確認")
def success_dialog(name, apply_type, date_str, duration, note):
    st.markdown(f"""
    **✅ 申請成功！**
    * **姓名**: {name}
    * **類型**: {apply_type}
    * **日期**: {date_str}
    * **時數**: {duration} 小時
    """)
    
    st.markdown("👇 **點擊右上方複製，貼到群組：**")
    # 修正後的格式
    copy_text = f"今天 {name} 有 {apply_type} {duration}小時\n原因:{note}"
    st.code(copy_text, language=None)
    
    if st.button("關閉視窗"):
        st.rerun()

# --- 主程式 ---
def main():
    local_css()
    st.set_page_config(page_title="班表管理", page_icon=None, layout="wide") 
    
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    # 建立 Google Sheets 連線
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
    except Exception as e:
        st.error("無法連線到 Google Sheets，請檢查 Secrets 設定。")
        st.stop()

    st.title("團隊時數管理系統 (雲端版)")

    # 讀取資料 (傳入 conn 連線物件)
    df = load_data(conn)

    # === 員工申請區 ===
    st.markdown("### 員工申請區")
    with st.container(border=True):
        st.caption("填寫表單")
        with st.form("application_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            name = c1.text_input("姓名 (請輸入全名)")
            input_date = c1.date_input("日期", datetime.today())
            apply_type = c2.selectbox("申請類型", ["加班", "抵班/補休"])
            
            c3, c4 = st.columns(2)
            # 30分鐘選單
            def_start = "09:00" if "09:00" in TIME_OPTIONS else TIME_OPTIONS[0]
            def_end = "18:00" if "18:00" in TIME_OPTIONS else TIME_OPTIONS[-1]
            start_time_str = c3.selectbox("開始時間", TIME_OPTIONS, index=TIME_OPTIONS.index(def_start))
            end_time_str = c4.selectbox("結束時間", TIME_OPTIONS, index=TIME_OPTIONS.index(def_end))
            
            note = st.text_area("備註 (選填)")
            
            submitted = st.form_submit_button("送出申請")

            if submitted:
                if not name:
                    st.error("請輸入姓名")
                else:
                    start_time = datetime.strptime(start_time_str, "%H:%M").time()
                    end_time = datetime.strptime(end_time_str, "%H:%M").time()
                    start_dt = datetime.combine(input_date, start_time)
                    end_dt = datetime.combine(input_date, end_time)
                    
                    if end_dt <= start_dt:
                        st.error("時間錯誤：結束時間必須晚於開始時間")
                    else:
                        duration = round((end_dt - start_dt).total_seconds() / 3600, 1)
                        date_str_save = input_date.strftime("%Y-%m-%d")
                        
                        new_row = {
                            "提交時間": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "姓名": name, 
                            "類型": apply_type, 
                            "日期": date_str_save, 
                            "開始時間": start_time_str,
                            "結束時間": end_time_str,
                            "時數": duration, 
                            "備註": note, 
                            "審核狀態": "待審核", 
                            "審核時間": "",
                            "月份": input_date.strftime("%Y-%m")
                        }
                        
                        # 重新讀取確保最新
                        current_df = load_data(conn)
                        if "日期_obj" in current_df.columns:
                            current_df = current_df.drop(columns=["日期_obj"])
                        
                        new_df = pd.DataFrame([new_row])
                        final_df = pd.concat([current_df, new_df], ignore_index=True)
                        save_data(conn, final_df)
                        
                        success_dialog(name, apply_type, date_str_save, duration, note)

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
            pending_mask = df["審核狀態"].str.contains("待審核", na=False) | (df["審核狀態"] == "")
            pending_df = df[pending_mask]
            
            if pending_df.empty:
                st.info("無待審核項目")
            else:
                for idx, row in pending_df.iterrows():
                    with st.container():
                        c1, c2, c3, c4, c5, c6 = st.columns([1.5, 2, 2, 1, 0.8, 0.8])
                        c1.text(f"{row['姓名']}")
                        c2.text(f"{row['日期']}")
                        c3.text(f"{row['類型']}")
                        try:
                            h_val = float(row['時數'])
                            c4.text(f"{h_val:.1f}")
                        except:
                            c4.text(f"{row['時數']}")
                        
                        if c5.button("通過", key=f"pass_{idx}"):
                            # 這裡要小心 index，因為 pending_df 的 index 是原始 df 的 index
                            # 但我們操作 Google Sheets 需要整張表
                            df.at[idx, "審核狀態"] = "已通過"
                            df.at[idx, "審核時間"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                            save_data(conn, df)
                            st.rerun()
                        if c6.button("刪除", key=f"del_{idx}"):
                            df = df.drop(idx)
                            save_data(conn, df)
                            st.rerun()
                        st.markdown("<hr style='margin: 5px 0; opacity: 0.3;'>", unsafe_allow_html=True)

            st.markdown("---")

            # 2. 統計
            st.subheader("人員時數統計")
            try:
                valid_months = [m for m in df["月份"].unique() if m != "未知" and m != ""]
                all_months = sorted(valid_months, reverse=True)
            except:
                all_months = []
                
            col_filter1, col_filter2 = st.columns(2)
            selected_month = col_filter1.selectbox("選擇月份", ["全部"] + all_months)
            
            if selected_month == "全部":
                stat_source_df = df
            else:
                stat_source_df = df[df["月份"] == selected_month]
            
            stat_source_df = stat_source_df[stat_source_df["審核狀態"] == "已通過"]
            
            stats = []
            if not stat_source_df.empty:
                for p in stat_source_df["姓名"].unique():
                    if not p: continue
                    p_data = stat_source_df[stat_source_df["姓名"] == p]
                    ot = p_data[p_data["類型"].str.contains("加班", na=False)]["時數"].sum()
                    comp = p_data[p_data["類型"].str.contains("補休|抵班", regex=True, na=False)]["時數"].sum()
                    stats.append({"姓名": p, "加班總時數": ot, "已抵休時數": comp, "小計/餘額": ot - comp})
                stat_df = pd.DataFrame(stats)
            else:
                stat_df = pd.DataFrame(columns=["姓名", "加班總時數", "已抵休時數", "小計/餘額"])
            
            st.dataframe(
                stat_df.style.format("{:.1f}", subset=["加班總時數", "已抵休時數", "小計/餘額"])
                .map(lambda x: 'color: #A03C3C' if x < 0 else 'color: #4A5D23', subset=['小計/餘額']),
                use_container_width=True
            )

            st.markdown("---")

            # 3. 批量管理
            st.subheader("管理所有紀錄 (批量刪除)")
            
            with st.expander("🔎 篩選與管理", expanded=True):
                f_col1, f_col2 = st.columns(2)
                all_names = list(df["姓名"].unique())
                filter_names = f_col1.multiselect("篩選人員", all_names, default=all_names)
                
                try:
                    min_date = df["日期_obj"].min().date()
                    max_date = df["日期_obj"].max().date()
                    filter_date_range = f_col2.date_input("篩選日期範圍", (min_date, max_date))
                except:
                    filter_date_range = []

                display_df = df.copy()
                if filter_names:
                    display_df = display_df[display_df["姓名"].isin(filter_names)]
                if isinstance(filter_date_range, tuple) and len(filter_date_range) == 2:
                    start_d, end_d = filter_date_range
                    mask = (display_df["日期_obj"].dt.date >= start_d) & (display_df["日期_obj"].dt.date <= end_d)
                    display_df = display_df[mask]
                
                try:
                    display_df = display_df.sort_values("提交時間", ascending=False)
                except:
                    pass

                display_df.insert(0, "勾選刪除", False)
                show_cols = ["勾選刪除", "姓名", "類型", "日期", "時數", "審核狀態", "備註", "提交時間"]
                
                st.caption(f"共找到 {len(display_df)} 筆資料")
                
                edited_df = st.data_editor(
                    display_df[show_cols],
                    column_config={
                        "勾選刪除": st.column_config.CheckboxColumn("刪除?", default=False),
                        "時數": st.column_config.NumberColumn(format="%.1f")
                    },
                    disabled=["姓名", "類型", "日期", "時數", "審核狀態", "備註", "提交時間"],
                    hide_index=True,
                    use_container_width=True
                )

                rows_to_delete = edited_df[edited_df["勾選刪除"] == True]
                
                if not rows_to_delete.empty:
                    st.warning(f"您已勾選 {len(rows_to_delete)} 筆資料準備刪除。")
                    if st.button("🗑️ 確認刪除勾選的資料", type="primary"):
                        delete_indices = rows_to_delete.index.tolist()
                        df = df.drop(delete_indices)
                        save_data(conn, df)
                        st.success("刪除成功！")
                        st.rerun()

        else:
            st.info("尚無資料 (Google Sheets 是空的)")

if __name__ == "__main__":
    main()
