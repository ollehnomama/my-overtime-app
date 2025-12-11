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

        div[data-testid="stAlert"] { 
            background-color: transparent !important; 
            border-radius: 0px !important; 
            padding: 0.5rem 1rem !important;
        }
        div[data-testid="stAlert"] svg { display: none !important; }

        div[data-testid="stAlert"]:has(div[aria-label="Success"]) { 
            border: 1px solid #4A5D23 !important; color: #4A5D23 !important; 
        }
        div[data-testid="stAlert"]:has(div[aria-label="Error"]) { 
            border: 1px solid #A03C3C !important; color: #A03C3C !important; 
        }

        [data-testid="stDataFrame"] { border: 1px solid #CCCCCC; }
        [data-testid="stDataFrame"] th { background-color: #E0DED0 !important; color: #333333 !important; border-bottom: 1px solid #333333 !important; }
        [data-testid="stDataFrame"] td { border-bottom: 1px solid #E0E0E0 !important; color: #333333 !important; }
        [data-testid="stDecoration"] { display: none; }
        </style>
        """, unsafe_allow_html=True)

# --- 資料讀取與處理 (已加入防錯機制) ---
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            
            # 補齊欄位
            if "審核狀態" not in df.columns: df["審核狀態"] = "待審核"
            if "審核時間" not in df.columns: df["審核時間"] = ""
            df["審核狀態"] = df["審核狀態"].fillna("待審核")
            df["審核時間"] = df["審核時間"].fillna("")

            # --- 關鍵修正：加入 errors='coerce' ---
            # 這會把讀不懂的怪日期轉成 NaT (空值)，而不是讓程式崩潰
            df["日期"] = pd.to_datetime(df["日期"], errors='coerce')
            
            # 刪除日期轉換失敗的壞資料行
            df = df.dropna(subset=["日期"])
            
            # 產生月份欄位
            df["月份"] = df["日期"].dt.strftime("%Y-%m")
            
            return df
            
        except Exception as e:
            # 萬一 CSV 檔案壞得太徹底，直接回傳空表格，避免網站掛掉
            return pd.DataFrame(columns=[
                "提交時間", "姓名", "類型", "日期", 
                "開始時間", "結束時間", "時數", "備註", 
                "審核狀態", "審核時間", "月份"
            ])
    else:
