import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- 設定檔案儲存路徑 ---
DATA_FILE = "schedule_data.csv"
# --- 設定管理員密碼 (改從 Secrets 讀取) ---
ADMIN_PASSWORD = st.secrets["admin_password"]

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
                # 建議這裡可以改成選單，避免打錯字
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
            
            # 用顏色標記：剩餘時數 < 0 顯示紅色 (代表休過頭了)
            st.dataframe(
                summary.style.map(lambda x: 'color: red' if x < 0 else 'color: green', subset=['剩餘可休時數']), 
                use_container_width=True
            )

            # 2. 詳細流水帳
            st.subheader("📋 所有申請明細")
            # 讓管理員可以篩選人名
            filter_person = st.selectbox("篩選特定員工", ["全部"] + list(df["姓名"].unique()))
            
            view_df = df
            if filter_person != "全部":
                view_df = df[df["姓名"] == filter_person]

            st.dataframe(view_df.sort_values("提交時間", ascending=False), use_container_width=True)
            
        else:
            st.info("目前還沒有任何資料。")
            
    elif input_password != "":
        st.sidebar.error("密碼錯誤，無法查看資料。")
    
    # 若沒輸入密碼，下面這一區塊完全不會顯示，達到隱私效果

if __name__ == "__main__":

    main()
