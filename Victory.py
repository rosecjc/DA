# FinMind 快速測試頁
import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import os

st.set_page_config(page_title="FinMind 測試工具", layout="centered")

st.title("🧪 FinMind 金鑰測試頁")

symbol = st.text_input("請輸入股票代號（例如 2330）", value="2330")

FINMIND_TOKEN = st.secrets["FINMIND_TOKEN"] if "FINMIND_TOKEN" in st.secrets else os.getenv("FINMIND_TOKEN")

if not FINMIND_TOKEN:
    st.error("❌ 尚未設定 FINMIND_TOKEN，請至 secrets.toml 或環境變數設定")
    st.stop()

start_date = (datetime.today() - timedelta(days=10)).strftime("%Y-%m-%d")
end_date = datetime.today().strftime("%Y-%m-%d")

payload = {
    "dataset": "TaiwanStockPrice",
    "data_id": symbol,
    "start_date": start_date,
    "end_date": end_date
}
headers = {"Authorization": f"Bearer {FINMIND_TOKEN}"}

res = requests.get("https://api.finmindtrade.com/api/v4/data", params=payload, headers=headers)
try:
    json_data = res.json()
except:
    st.error("❌ 回傳格式錯誤，無法解析 JSON")
    st.stop()

if json_data['status'] != 200:
    st.error(f"❌ FinMind 回傳錯誤：{json_data.get('msg', '未知錯誤')}")
    st.json(json_data)
else:
    df = pd.DataFrame(json_data['data'])
    if df.empty:
        st.warning("⚠️ 呼叫成功但無資料，可能是代號錯誤或無近期資料")
    else:
        st.success("✅ 成功取得資料！以下為近 10 天收盤價：")
        df = df[['date', 'open', 'close']]
        st.dataframe(df.tail(10))
