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
        </style>
        """, unsafe_allow_html=True)

# --- 資料讀取 (絕對顯示版) ---
def load_data():
    columns = [
        "提交時間", "姓名", "類型", "日期", 
        "開始時間", "結束時間", "時數", "備註", 
        "審核狀態", "審核時間", "月份"
    ]

    if os.path.exists(DATA_FILE):
        try:
            # 1. 全部當作字串讀取，避免 Pandas 猜錯型別導致資料遺失
            df = pd.read_csv(DATA_FILE, encoding='utf-8-sig', dtype=str)
            
            # 2. 補齊欄位
            for col in columns:
                if col not in df.columns: df[col] = ""
            
            # 3. 填補空值 (顯示為空字串，而不是消失)
            df = df.fillna("")
            
            # 4. 強制轉換「時數」為數字 (計算用)
            # errors='coerce' 會把無法轉成數字的變成 0，但行不會消失
            df["時數"] = pd.to_numeric(df["時數"], errors='coerce').fillna(0.0)
            
            # 5. 處理日期 (只為了排序和月份篩選，不影響原始顯示)
            # 建立一個臨時的日期物件欄位用來排序
            df["日期_obj"] = pd.to_datetime(df["日期"], errors='coerce')
            
            # 如果日期爛掉了，補一個預設值讓我們找得到它
            df.loc[df["日期_obj"].isna(), "日期_obj"] = datetime(1900, 1, 1)
            
            # 產生月份 (如果日期爛掉，月份設為 "未知")
            df["月份"] = df["日期_obj"].dt.strftime("%Y-%m")
            df.loc[df["月份"] == "1900-01", "月份"] = "未知/錯誤"

            # 6. 整理文字
            df["類型"] = df["類型"].astype(str).str.strip()
            df["審核狀態"] = df["審核狀態"].replace("", "待審核")

            # ⚠️ 絕對不執行 dropna()，保留所有資料
            
            return df
        except Exception as e:
            st.error(f"資料讀取錯誤: {e}")
            return pd.DataFrame(columns=columns)
    else:
        return pd.DataFrame(columns=columns)

def save_data(df):
    try:
        # 存檔前移除我們剛剛產生的臨時欄位
        df_save = df.copy()
        if "日期_obj" in df_save.columns:
            df_save = df_save.drop(columns=["日期_obj"])
        df_save.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
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
    """)
    if st.button("關閉"):
        st.rerun()

# --- 主程式 ---
def main():
    local_css()
    st.set_page_config(page_title="班表管理", page_icon=None)
    
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    st.title("團隊時數管理系統")

    # 讀取資料
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
                        st.error("時間錯誤")
                    else:
                        duration = round((end_dt - start_dt).total_seconds() / 3600, 1)
                        date_str_save = date.strftime("%Y-%m-%d")
                        
                        new_row = {
                            "提交時間": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "姓名": name, 
                            "類型": apply_type, 
                            "日期": date_str_save, 
                            "開始時間": start_time.strftime("%H:%M"), 
                            "結束時間": end_time.strftime("%H:%M"),
                            "時數": duration, 
                            "備註": note, 
                            "審核狀態": "待審核", 
                            "審核時間": "",
                            "月份": date.strftime("%Y-%m")
                        }
                        
                        # 重新讀取最新的 df 再寫入
                        current_df = load_data()
                        # 轉成 DataFrame 並合併
                        new_df = pd.DataFrame([new_row])
                        
                        # 確保 columns 一致 (避免 append warning)
                        if not current_df.empty and "日期_obj" in current_df.columns:
                             current_df = current_df.drop(columns=["日期_obj"])

                        final_df = pd.concat([current_df, new_df], ignore_index=True)
                        save_data(final_df)
                        
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
            # 1. 待審核區
            st.subheader("待審核項目")
            # 寬鬆篩選：只要狀態包含 "待審核" 或者 是空的，都顯示出來
            pending_mask = df["審核狀態"].str.contains("待審核", na=False) | (df["審核狀態"] == "")
            pending_df = df[pending_mask]
            
            if pending_df.empty:
                st.info("無待審核項目")
            else:
                for idx, row in pending_df.iterrows():
                    with st.container():
                        c1, c2, c3, c4, c5, c6 = st.columns([1.5, 2, 2, 1, 0.8, 0.8])
                        c1.text(f"{row['姓名']}")
                        c2.text(f"{row['日期']}") # 直接顯示原始文字，不轉換格式以免報錯
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

            # 2. 統計報表
            st.subheader("報表篩選")
            try:
                # 只取有意義的月份
                valid_months = [m for m in df["月份"].unique() if m != "未知/錯誤" and m != ""]
                all_months = sorted(valid_months, reverse=True)
            except:
                all_months = []
                
            selected_month = st.selectbox("選擇月份", ["全部"] + all_months)
            
            # 篩選邏輯
            if selected_month == "全部":
                filtered_df = df
            else:
                filtered_df = df[df["月份"] == selected_month]
            
            st.subheader("人員時數統計 (已通過)")
            approved_df = filtered_df[filtered_df["審核狀態"] == "已通過"]
            
            stats = []
            if not approved_df.empty:
                for p in approved_df["姓名"].unique():
                    if not p: continue # 跳過空白名字
                    p_data = approved_df[approved_df["姓名"] == p]
                    
                    # 寬鬆匹配：只要類型文字裡面有 "加班" 就算
                    ot = p_data[p_data["類型"].str.contains("加班", na=False)]["時數"].sum()
                    # 寬鬆匹配：只要類型文字裡面有 "補休" 或 "抵班" 就算
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

            # 3. 歷史明細
            st.subheader("申請明細列表")
            # 排除空白名字
            unique_names = [n for n in df["姓名"].unique() if n]
            filter_person = st.selectbox("篩選員工", ["全部"] + list(unique_names))
            
            view_df = filtered_df
            if filter_person != "全部":
                view_df = view_df[view_df["姓名"] == filter_person]
            
            # 顯示時排序
            try:
                view_df = view_df.sort_values("提交時間", ascending=False)
            except:
                pass # 如果時間格式爛掉就不排序，直接顯示
                
            # 只顯示需要的欄位，且不進行複雜格式化以免報錯
            display_cols = ["提交時間", "姓名", "類型", "日期", "開始時間", "結束時間", "時數", "備註", "審核狀態"]
            # 確保欄位存在
            final_cols = [c for c in display_cols if c in view_df.columns]
            
            st.dataframe(
                view_df[final_cols].style.map(lambda v: 'color: #4A5D23; font-weight: bold' if v == '已通過' else 'color: #999999', subset=['審核狀態']),
                use_container_width=True
            )

            # 4. 刪除工具
            st.markdown("---")
            with st.expander("🗑️ 刪除歷史資料"):
                opts = {}
                for i, r in df.sort_values("提交時間", ascending=False).iterrows():
                    opts[f"[{i}] {r['姓名']} {r['日期']} {r['類型']}"] = i
                
                if opts:
                    sel = st.selectbox("選擇刪除項目", list(opts.keys()))
                    if st.button("確認刪除"):
                        df = df.drop(opts[sel])
                        save_data(df)
                        st.success("已刪除")
                        st.rerun()
                else:
                    st.text("無資料")
                    
            # 5. 除錯區
            with st.expander("🔧 資料庫原始視圖 (如果上面沒顯示，這裡一定有)"):
                st.write(df)

        else:
            st.info("尚無資料")

if __name__ == "__main__":
    main()
