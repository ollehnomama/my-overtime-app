import streamlit as st
import pandas as pd
from datetime import datetime, date
from streamlit_gsheets import GSheetsConnection

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
        
        /* 隱藏預設的 sidebar 頂部 padding */
        section[data-testid="stSidebar"] > div { padding-top: 2rem; }
        </style>
        """, unsafe_allow_html=True)

# --- 資料讀取 ---
def load_data(conn):
    # 1. 讀取紀錄
    record_cols = [
        "提交時間", "分店", "姓名", "員工編號", "類型", "日期", 
        "開始時間", "結束時間", "時數", "備註", 
        "審核狀態", "審核時間", "月份"
    ]
    try:
        df = conn.read(worksheet="Records", ttl=0)
        for col in record_cols:
            if col not in df.columns: df[col] = ""
        df = df.fillna("")
        df["時數"] = pd.to_numeric(df["時數"], errors='coerce').fillna(0.0)
        
        df["日期_obj"] = pd.to_datetime(df["日期"], errors='coerce')
        df.loc[df["日期_obj"].isna(), "日期_obj"] = datetime(1900, 1, 1)
        df["月份"] = df["日期_obj"].dt.strftime("%Y-%m")
        df.loc[df["月份"] == "1900-01", "月份"] = "未知"
        
        df["類型"] = df["類型"].astype(str).str.strip()
        df["審核狀態"] = df["審核狀態"].replace("", "待審核")
        
    except:
        df = pd.DataFrame(columns=record_cols)

    # 2. 讀取使用者帳號
    try:
        users_df = conn.read(worksheet="Users", ttl=0)
        users_df = users_df.fillna("")
        # 轉成字串防止數字變成 float
        for col in ["Account", "Password", "Name", "Role", "Store"]:
            if col in users_df.columns:
                users_df[col] = users_df[col].astype(str).str.strip()
    except:
        users_df = pd.DataFrame(columns=["Account", "Password", "Name", "Role", "Store"])

    return df, users_df

# --- 資料存檔 ---
def save_data(conn, df):
    try:
        df_save = df.copy()
        if "日期_obj" in df_save.columns: df_save = df_save.drop(columns=["日期_obj"])
        if "勾選刪除" in df_save.columns: df_save = df_save.drop(columns=["勾選刪除"])
        conn.update(worksheet="Records", data=df_save)
        st.cache_data.clear()
    except Exception as e:
        st.error(f"存檔失敗: {e}")

# --- 彈出視窗 ---
@st.dialog("申請確認")
def success_dialog(name, store, apply_type, date_str, duration, note):
    st.markdown(f"""
    **✅ 申請成功！**
    * **分店**: {store}
    * **姓名**: {name}
    * **類型**: {apply_type}
    * **時數**: {duration} 小時
    """)
    copy_text = f"今天 {name} ({store}) 有 {apply_type} {duration}小時\n原因:{note}"
    st.markdown("👇 **複製文字貼到群組：**")
    st.code(copy_text, language=None)
    if st.button("關閉視窗"):
        st.rerun()

# --- 主程式 ---
def main():
    local_css()
    st.set_page_config(page_title="班表管理系統", page_icon="⏰", layout="wide") 
    
    # Session State 初始化
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.user_id = ""
        st.session_state.user_name = ""
        st.session_state.user_role = ""
        st.session_state.user_store = ""

    # 連線
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df, users_df = load_data(conn)
    except Exception as e:
        st.error("連線失敗，請檢查 secrets 設定。")
        st.stop()

    # === 登入頁面 (如果沒登入，只顯示這個) ===
    if not st.session_state.logged_in:
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.title("🔐 員工登入系統")
            with st.container(border=True):
                with st.form("login_form"):
                    input_acc = st.text_input("員工編號 / 帳號")
                    input_pwd = st.text_input("密碼", type="password")
                    submitted = st.form_submit_button("登入", type="primary")
                    
                    if submitted:
                        # 比對帳號密碼
                        user_record = users_df[
                            (users_df["Account"] == input_acc) & 
                            (users_df["Password"] == input_pwd)
                        ]
                        
                        if not user_record.empty:
                            # 登入成功，寫入 session
                            user = user_record.iloc[0]
                            st.session_state.logged_in = True
                            st.session_state.user_id = user["Account"]
                            # 容錯：如果沒有 Name 欄位，就用 Account 代替
                            st.session_state.user_name = user["Name"] if "Name" in user else user["Account"]
                            st.session_state.user_role = user["Role"]
                            st.session_state.user_store = user["Store"]
                            st.rerun()
                        else:
                            st.error("帳號或密碼錯誤")
        return # 沒登入就結束，不顯示下面內容

    # === 登入後的畫面 (Sidebar 顯示資訊) ===
    with st.sidebar:
        st.title(f"Hi, {st.session_state.user_name}")
        st.caption(f"分店: {st.session_state.user_store}")
        st.caption(f"身份: {st.session_state.user_role}")
        
        if st.button("登出", type="secondary"):
            st.session_state.logged_in = False
            st.rerun()
        st.divider()

    st.title(f"⏰ 團隊時數管理 ({st.session_state.user_store})")

    # === 角色邏輯判斷 ===
    
    # 1. 如果是「員工 (Staff)」，只顯示申請表單
    if st.session_state.user_role == "Staff":
        st.subheader("📝 填寫申請單")
        with st.container(border=True):
            with st.form("staff_form", clear_on_submit=True):
                # 自動鎖定姓名與分店
                c1, c2 = st.columns(2)
                c1.text_input("姓名", value=st.session_state.user_name, disabled=True)
                c2.text_input("分店", value=st.session_state.user_store, disabled=True)
                
                c3, c4 = st.columns(2)
                input_date = c3.date_input("日期", datetime.today())
                apply_type = c4.selectbox("類型", ["加班", "抵班/補休"])
                
                c5, c6 = st.columns(2)
                def_start = "09:00" if "09:00" in TIME_OPTIONS else TIME_OPTIONS[0]
                def_end = "18:00" if "18:00" in TIME_OPTIONS else TIME_OPTIONS[-1]
                start_time_str = c5.selectbox("開始時間", TIME_OPTIONS, index=TIME_OPTIONS.index(def_start))
                end_time_str = c6.selectbox("結束時間", TIME_OPTIONS, index=TIME_OPTIONS.index(def_end))
                
                note = st.text_area("備註")
                
                if st.form_submit_button("送出申請", type="primary"):
                    start_time = datetime.strptime(start_time_str, "%H:%M").time()
                    end_time = datetime.strptime(end_time_str, "%H:%M").time()
                    start_dt = datetime.combine(input_date, start_time)
                    end_dt = datetime.combine(input_date, end_time)
                    
                    if end_dt <= start_dt:
                        st.error("結束時間必須晚於開始時間")
                    else:
                        duration = round((end_dt - start_dt).total_seconds() / 3600, 1)
                        date_str = input_date.strftime("%Y-%m-%d")
                        
                        new_row = {
                            "提交時間": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "分店": st.session_state.user_store,
                            "姓名": st.session_state.user_name,
                            "員工編號": st.session_state.user_id,
                            "類型": apply_type,
                            "日期": date_str,
                            "開始時間": start_time_str,
                            "結束時間": end_time_str,
                            "時數": duration,
                            "備註": note,
                            "審核狀態": "待審核",
                            "審核時間": "",
                            "月份": input_date.strftime("%Y-%m")
                        }
                        
                        curr_df, _ = load_data(conn)
                        if "日期_obj" in curr_df.columns: curr_df = curr_df.drop(columns=["日期_obj"])
                        new_df = pd.DataFrame([new_row])
                        final_df = pd.concat([curr_df, new_df], ignore_index=True)
                        save_data(conn, final_df)
                        
                        success_dialog(st.session_state.user_name, st.session_state.user_store, apply_type, date_str, duration, note)

        # 顯示該員工的個人紀錄
        st.subheader("📋 我的申請紀錄")
        my_records = df[df["員工編號"] == st.session_state.user_id] # 只看自己的
        if not my_records.empty:
            show_cols = ["日期", "類型", "時數", "審核狀態", "備註"]
            st.dataframe(
                my_records[show_cols].sort_values("日期", ascending=False),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("尚無申請紀錄")

    # 2. 如果是「管理者 (Manager/Admin)」，顯示後台
    elif st.session_state.user_role in ["Manager", "Admin"]:
        
        # 篩選資料範圍
        if st.session_state.user_role == "Admin" or st.session_state.user_store == "All":
            view_df = df # 看全部
            st.info("您正在檢視：所有分店資料")
        else:
            view_df = df[df["分店"] == st.session_state.user_store] # 只看自己店
            st.info(f"您正在檢視：{st.session_state.user_store} 資料")

        # --- 待審核 ---
        st.subheader("⚡ 待審核項目")
        pending_mask = view_df["審核狀態"].str.contains("待審核", na=False) | (view_df["審核狀態"] == "")
        pending_df = view_df[pending_mask]
        
        if pending_df.empty:
            st.success("目前沒有待審核項目")
        else:
            for idx, row in pending_df.iterrows():
                with st.container():
                    c1, c2, c3, c4, c5, c6, c7 = st.columns([1, 1, 1.5, 1.5, 1, 0.8, 0.8])
                    c1.text(row['分店'])
                    c2.text(row['姓名'])
                    c3.text(row['日期'])
                    c4.text(row['類型'])
                    c5.text(row['時數'])
                    
                    if c6.button("通過", key=f"p_{idx}"):
                        df.at[idx, "審核狀態"] = "已通過"
                        df.at[idx, "審核時間"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                        save_data(conn, df)
                        st.rerun()
                    if c7.button("退回", key=f"d_{idx}"): # 這裡改成退回/刪除
                        df = df.drop(idx)
                        save_data(conn, df)
                        st.rerun()
                    st.markdown("<hr style='margin: 5px 0; opacity: 0.3;'>", unsafe_allow_html=True)

        st.markdown("---")
        
        # --- 統計報表 ---
        st.subheader("📊 統計報表")
        
        # 月份篩選
        try:
            valid_months = [m for m in view_df["月份"].unique() if m != "未知" and m != ""]
            months = sorted(valid_months, reverse=True)
        except:
            months = []
        sel_month = st.selectbox("月份", ["全部"] + months)
        
        stat_source = view_df if sel_month == "全部" else view_df[view_df["月份"] == sel_month]
        stat_source = stat_source[stat_source["審核狀態"] == "已通過"]
        
        if not stat_source.empty:
            stats = []
            # 依分店 + 姓名 分組統計
            for (store, name), group in stat_source.groupby(["分店", "姓名"]):
                ot = group[group["類型"].str.contains("加班", na=False)]["時數"].sum()
                comp = group[group["類型"].str.contains("補休|抵班", regex=True, na=False)]["時數"].sum()
                stats.append({
                    "分店": store,
                    "姓名": name,
                    "加班總時數": ot,
                    "已抵休時數": comp,
                    "餘額": ot - comp
                })
            st.dataframe(pd.DataFrame(stats).style.format({"加班總時數": "{:.1f}", "已抵休時數": "{:.1f}", "餘額": "{:.1f}"}), use_container_width=True)
        else:
            st.info("尚無核准資料")

        # --- 批量管理 ---
        st.subheader("🛠️ 紀錄管理")
        with st.expander("開啟詳細列表 (可批量刪除)"):
            display_df = view_df.copy()
            # 簡單篩選
            f_name = st.multiselect("篩選姓名", display_df["姓名"].unique())
            if f_name: display_df = display_df[display_df["姓名"].isin(f_name)]
            
            try:
                display_df = display_df.sort_values("提交時間", ascending=False)
            except: pass
            
            display_df.insert(0, "勾選", False)
            cols = ["勾選", "分店", "姓名", "日期", "類型", "時數", "審核狀態", "備註"]
            
            edited = st.data_editor(
                display_df[cols],
                column_config={"勾選": st.column_config.CheckboxColumn("刪除", default=False)},
                disabled=["分店", "姓名", "日期", "類型", "時數", "審核狀態", "備註"],
                hide_index=True,
                use_container_width=True
            )
            
            to_del = edited[edited["勾選"]]
            if not to_del.empty:
                if st.button(f"確認刪除 {len(to_del)} 筆資料", type="primary"):
                    df = df.drop(to_del.index)
                    save_data(conn, df)
                    st.success("刪除成功")
                    st.rerun()

if __name__ == "__main__":
    main()
