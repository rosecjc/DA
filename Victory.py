# FinMind 快速測試頁（限前 20 檔熱門股）
import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import os

st.set_page_config(page_title="FinMind 測試工具", layout="centered")

st.title("🧪 FinMind 金鑰測試頁（限 20 檔熱門股）")

FINMIND_TOKEN = st.secrets["FINMIND_TOKEN"] if "FINMIND_TOKEN" in st.secrets else os.getenv("FINMIND_TOKEN")

if not FINMIND_TOKEN:
    st.error("❌ 尚未設定 FINMIND_TOKEN，請至 secrets.toml 或環境變數設定")
    st.stop()

# 常見熱門股票代碼
popular_codes = ['2330', '2303', '2603', '2609', '2615', '2308', '2412', '2454', '2882', '2891', '2379', '3034', '8069', '3661', '2327', '3008', '3017', '2382', '6116', '3481']

start_date = (datetime.today() - timedelta(days=60)).strftime("%Y-%m-%d")
end_date = datetime.today().strftime("%Y-%m-%d")

result = []
progress_bar = st.progress(0)

for i, code in enumerate(popular_codes):
    st.info(f"正在分析第 {i+1}/{len(popular_codes)} 檔：{code}")
    payload = {
        "dataset": "TaiwanStockPrice",
        "data_id": code,
        "start_date": start_date,
        "end_date": end_date
    }
    headers = {"Authorization": f"Bearer {FINMIND_TOKEN}"}
    try:
        res = requests.get("https://api.finmindtrade.com/api/v4/data", params=payload, headers=headers)
        data = res.json()
        if data['status'] != 200 or not data['data']:
            continue
        df = pd.DataFrame(data['data'])
        last_close = df.iloc[-1]['close'] if not df.empty else None
        result.append({"代號": code, "最近收盤價": last_close, "資料筆數": len(df)})
    except:
        continue
    progress_bar.progress((i+1) / len(popular_codes))

progress_bar.empty()

if result:
    df_result = pd.DataFrame(result)
    st.success("✅ 成功擷取以下熱門股資料：")
    st.dataframe(df_result, use_container_width=True)
else:
    st.warning("⚠️ 所有熱門股都無資料，請確認 API 金鑰或連線狀態")
    
