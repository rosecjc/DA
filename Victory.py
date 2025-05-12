# 分析工具（使用 FinMind 來源）
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import requests
import os

st.set_page_config(page_title="隔日沖勝率工具（FinMind 版）", layout="wide")

FINMIND_TOKEN = st.secrets["FINMIND_TOKEN"] if "FINMIND_TOKEN" in st.secrets else os.getenv("FINMIND_TOKEN")

headers = {"Authorization": f"Bearer {FINMIND_TOKEN}"}

@st.cache_data
def fetch_finmind_data(stock_id, start_date, end_date):
    url = "https://api.finmindtrade.com/api/v4/data"
    payload = {
        "dataset": "TaiwanStockPrice",
        "data_id": stock_id,
        "start_date": start_date,
        "end_date": end_date,
    }
    res = requests.get(url, params=payload, headers=headers)
    data = res.json()
    if data['status'] != 200 or len(data['data']) == 0:
        return pd.DataFrame()
    df = pd.DataFrame(data['data'])
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    return df[['open', 'close']].dropna()

@st.cache_data
def analyze_stock(df, threshold):
    df['Next_Open'] = df['open'].shift(-1)
    df['Day3_Close'] = df['close'].shift(-2)
    df['Overnight_Change'] = ((df['Next_Open'] - df['close']) / df['close']) * 100
    df['ThreeDay_Change'] = ((df['Day3_Close'] - df['close']) / df['close']) * 100
    df['Win'] = df['Overnight_Change'] >= threshold
    df['ThreeDay_Win'] = df['ThreeDay_Change'] >= 2.5
    return df.dropna()

st.title("📊 台股隔日沖勝率工具（FinMind 版）")
symbol = st.text_input("請輸入股票代碼（例如：2330）", value="2330")
days_back = st.slider("回測天數：", 30, 300, 180, 10)
threshold = st.slider("隔日漲幅門檻（%）", 0.5, 5.0, 1.5, 0.1)

if symbol:
    end_date = datetime.today().strftime("%Y-%m-%d")
    start_date = (datetime.today() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    raw_df = fetch_finmind_data(symbol, start_date, end_date)
    if raw_df.empty:
        st.error("❌ 無法取得資料，請檢查代碼或 API Token 是否設定正確")
        st.stop()

    df = analyze_stock(raw_df, threshold)
    total = len(df)
    win_count = df['Win'].sum()
    three_day_count = df['ThreeDay_Win'].sum()

    st.metric("隔日沖勝率（%.1f%%↑）" % threshold, f"{win_count / total * 100:.2f}%")
    st.metric("三日沖勝率（2.5%↑）", f"{three_day_count / total * 100:.2f}%")

    st.caption(f"樣本數：{total} 筆 | 隔日勝出次數：{win_count} 次 | 三日勝出次數：{three_day_count} 次")

    st.subheader("📋 勝率統計表（最近 20 筆）")
    display_df = df[['close', 'Next_Open', 'Day3_Close', 'Overnight_Change', 'ThreeDay_Change', 'Win', 'ThreeDay_Win']].tail(20)
    display_df.index.name = '日期'
    display_df.reset_index(inplace=True)
    display_df = display_df.rename(columns={
        'close': '收盤價',
        'Next_Open': '隔日開盤',
        'Day3_Close': '第三日收盤',
        'Overnight_Change': '隔日漲幅%',
        'ThreeDay_Change': '三日漲幅%',
        'Win': f'隔日是否 ≥ {threshold}%',
        'ThreeDay_Win': '三日是否 ≥ 2.5%'
    })
    st.dataframe(display_df.round(2), use_container_width=True, height=800)
    
