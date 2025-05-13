# 個股分析頁：使用 FinMind API 顯示趨勢圖、勝率、基本面
import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="個股分析 - 勝率工具", layout="wide")

FINMIND_TOKEN = st.secrets["FINMIND_TOKEN"]
API_URL = "https://api.finmindtrade.com/api/v4/data"

# --- 使用者輸入股票代號 ---
st.title("🔍 個股分析")
symbol = st.text_input("請輸入台股股票代號（例如：2330）", value="2330")

# --- 抓取歷史價格資料 ---
@st.cache_data
def get_price_data(stock_id):
    today = datetime.today()
    start_date = (today - timedelta(days=180)).strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")
    params = {
        "dataset": "TaiwanStockPrice",
        "data_id": stock_id,
        "start_date": start_date,
        "end_date": end_date
    }
    headers = {"Authorization": f"Bearer {FINMIND_TOKEN}"}
    res = requests.get(API_URL, params=params, headers=headers)
    data = res.json()
    if data['status'] != 200 or len(data['data']) == 0:
        return None
    return pd.DataFrame(data['data'])

# --- 抓取 EPS ---
@st.cache_data

def get_eps_data(stock_id):
    params = {
        "dataset": "TaiwanStockFinancialStatements",
        "data_id": stock_id
    }
    headers = {"Authorization": f"Bearer {FINMIND_TOKEN}"}
    res = requests.get(API_URL, params=params, headers=headers)
    data = res.json()
    return pd.DataFrame(data['data']) if data['status'] == 200 else None

# --- 抓取配息資訊 ---
@st.cache_data

def get_dividend_data(stock_id):
    params = {
        "dataset": "TaiwanStockDividend",
        "data_id": stock_id
    }
    headers = {"Authorization": f"Bearer {FINMIND_TOKEN}"}
    res = requests.get(API_URL, params=params, headers=headers)
    data = res.json()
    return pd.DataFrame(data['data']) if data['status'] == 200 else None

if symbol:
    df_price = get_price_data(symbol)
    if df_price is not None:
        df_price['date'] = pd.to_datetime(df_price['date'])
        df_price.set_index('date', inplace=True)
        df_price['Next_Open'] = df_price['open'].shift(-1)
        df_price['Day3_Close'] = df_price['close'].shift(-2)
        df_price['Overnight_Change'] = ((df_price['Next_Open'] - df_price['close']) / df_price['close']) * 100
        df_price['ThreeDay_Change'] = ((df_price['Day3_Close'] - df_price['close']) / df_price['close']) * 100
        df_price['Win'] = df_price['Overnight_Change'] >= 1.5
        df_price['ThreeDay_Win'] = df_price['ThreeDay_Change'] >= 2.5
        valid = df_price.dropna(subset=['Next_Open', 'Day3_Close'])

        st.subheader("📈 股價趨勢圖")
        st.line_chart(df_price[['close', 'Next_Open']])

        st.subheader("📊 勝率統計")
        win_rate = round(valid['Win'].mean() * 100, 1)
        three_rate = round(valid['ThreeDay_Win'].mean() * 100, 1)
        st.metric("隔日沖勝率（1.5%↑）", f"{win_rate}%")
        st.metric("三日沖勝率（2.5%↑）", f"{three_rate}%")

        st.dataframe(valid.rename(columns={
            'close': '收盤價',
            'Next_Open': '次日開盤價',
            'Day3_Close': '第3日收盤價',
            'Overnight_Change': '隔日漲跌幅(%)',
            'ThreeDay_Change': '三日漲跌幅(%)',
            'Win': '隔日勝',
            'ThreeDay_Win': '三日勝'
        })[['收盤價', '次日開盤價', '第3日收盤價', '隔日漲跌幅(%)', '三日漲跌幅(%)', '隔日勝', '三日勝']].tail(20).round(2), use_container_width=True)

        st.subheader("📑 基本面資訊")
        df_eps = get_eps_data(symbol)
        df_div = get_dividend_data(symbol)

        if df_eps is not None and not df_eps.empty:
            latest_eps = df_eps[df_eps['type'] == 'Q4'].sort_values('date').iloc[-1]  # 取年度 EPS
            st.metric("每股盈餘 EPS", latest_eps.get('EPS', '無資料'))
        else:
            st.metric("每股盈餘 EPS", "無資料")

        if df_div is not None and not df_div.empty:
            latest_div = df_div.sort_values('date').iloc[-1]
            st.metric("殖利率 (%)", latest_div.get('DividendYield', '無資料'))
            st.metric("現金股利 (元)", latest_div.get('CashEarningsDistribution', '無資料'))
        else:
            st.metric("殖利率 (%)", "無資料")
            st.metric("現金股利 (元)", "無資料")
            st.write("查無基本面資料")
    else:
        st.error("❌ 查無股價資料，請確認代碼或 API token")


# 多檔勝率排行推薦頁（使用 FinMind API）
import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="勝率排行推薦", layout="wide")

FINMIND_TOKEN = st.secrets["FINMIND_TOKEN"]
API_URL = "https://api.finmindtrade.com/api/v4/data"

st.title("📊 多檔勝率排行推薦")

@st.cache_data

def get_price_data(stock_id, days=180):
    today = datetime.today()
    start_date = (today - timedelta(days=days)).strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")
    params = {
        "dataset": "TaiwanStockPrice",
        "data_id": stock_id,
        "start_date": start_date,
        "end_date": end_date
    }
    headers = {"Authorization": f"Bearer {FINMIND_TOKEN}"}
    res = requests.get(API_URL, params=params, headers=headers)
    data = res.json()
    if data['status'] != 200 or not data['data']:
        return None
    df = pd.DataFrame(data['data'])
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    df['Next_Open'] = df['open'].shift(-1)
    df['Day3_Close'] = df['close'].shift(-2)
    df['Overnight_Change'] = ((df['Next_Open'] - df['close']) / df['close']) * 100
    df['ThreeDay_Change'] = ((df['Day3_Close'] - df['close']) / df['close']) * 100
    df['Win'] = df['Overnight_Change'] >= 1.5
    df['ThreeDay_Win'] = df['ThreeDay_Change'] >= 2.5
    return df.dropna(subset=['Next_Open', 'Day3_Close'])

# 📌 可以自行擴增此清單
target_stocks = ['2330', '2303', '2603', '2882', '2317', '2408', '3008', '1301', '1101', '2891']

ranking = []
progress = st.progress(0.0, text="🔍 正在分析勝率...")

for i, symbol in enumerate(target_stocks):
    df = get_price_data(symbol)
    if df is not None and len(df) >= 20:
        win_rate = round(df['Win'].mean() * 100, 1)
        three_rate = round(df['ThreeDay_Win'].mean() * 100, 1)
        avg_return = round(df['Overnight_Change'].mean(), 2)
        ranking.append({
            "股票代號": symbol,
            "隔日勝率": f"{win_rate}%",
            "三日勝率": f"{three_rate}%",
            "平均隔日漲幅": f"{avg_return}%",
            "樣本數": len(df)
        })
    progress.progress((i + 1) / len(target_stocks))

progress.empty()

if ranking:
    df_rank = pd.DataFrame(ranking)
    df_rank = df_rank.sort_values(by="隔日勝率", key=lambda x: x.str.replace('%','').astype(float), ascending=False)
    st.success("✅ 分析完成！以下為推薦股票勝率排行：")
    st.dataframe(df_rank, use_container_width=True)
else:
    st.warning("⚠️ 無法取得足夠資料進行排行分析。")



