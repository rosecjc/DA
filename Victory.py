# 分析工具：使用 FinMind API
import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="分析工具", layout="wide")

FINMIND_TOKEN = st.secrets["FINMIND_TOKEN"]
API_URL = "https://api.finmindtrade.com/api/v4/data"

# --- 抓取資料工具函式 ---
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

@st.cache_data
def get_eps_data(stock_id):
    params = {"dataset": "TaiwanStockFinancialStatements", "data_id": stock_id}
    headers = {"Authorization": f"Bearer {FINMIND_TOKEN}"}
    res = requests.get(API_URL, params=params, headers=headers)
    data = res.json()
    return pd.DataFrame(data['data']) if data['status'] == 200 else None

@st.cache_data
def get_dividend_data(stock_id):
    params = {"dataset": "TaiwanStockDividend", "data_id": stock_id}
    headers = {"Authorization": f"Bearer {FINMIND_TOKEN}"}
    res = requests.get(API_URL, params=params, headers=headers)
    data = res.json()
    return pd.DataFrame(data['data']) if data['status'] == 200 else None

# --- 頁面切換 ---
page = st.sidebar.radio("📁 功能選單", ["🔍 個股分析", "📊 勝率排行", "🧪 勝率模擬器"])

if page == "🔍 個股分析":
    st.title("🔍 個股分析")
    st.caption(f"資料分析時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    symbol = st.text_input("請輸入台股股票代號（例如：2330）", value="2330")
    df_price = get_price_data(symbol)
    if df_price is not None:
        st.subheader("📈 股價趨勢圖")
        st.line_chart(df_price[['close', 'Next_Open']])

        st.subheader("📊 勝率統計")
        win_rate = round(df_price['Win'].mean() * 100, 1)
        three_rate = round(df_price['ThreeDay_Win'].mean() * 100, 1)
        st.metric("隔日沖勝率（1.5%↑）", f"{win_rate}%")
        st.metric("三日沖勝率（2.5%↑）", f"{three_rate}%")

        df_price['日期'] = df_price.index.date
        df_display = df_price.rename(columns={
            'close': '收盤價',
            'Next_Open': '次日開盤價',
            'Day3_Close': '第3日收盤價',
            'Overnight_Change': '隔日漲跌幅(%)',
            'ThreeDay_Change': '三日漲跌幅(%)',
            'Win': '隔日勝',
            'ThreeDay_Win': '三日勝'
        })[['日期', '收盤價', '次日開盤價', '第3日收盤價', '隔日漲跌幅(%)', '三日漲跌幅(%)', '隔日勝', '三日勝']].sort_index(ascending=False).round(2)
        st.dataframe(df_display.tail(20), use_container_width=True)

        st.subheader("📑 基本面資訊")

        df_eps = get_eps_data(symbol)
        df_div = get_dividend_data(symbol)

        col1, col2, col3 = st.columns(3)

        with col1:
            if df_eps is not None and not df_eps.empty:
                latest_eps_all = df_eps[df_eps['type'] == 'Q4'].sort_values('date', ascending=False)
                latest_eps = latest_eps_all.iloc[0] if not latest_eps_all.empty else {}
                st.metric("每股盈餘 EPS（稅後純益）", latest_eps.get('EPS', '無資料'))
            else:
                st.metric("每股盈餘 EPS（稅後純益）", "無資料")

        with col2:
            if df_div is not None and not df_div.empty:
                latest_div = df_div.sort_values('date').iloc[-1]
                st.metric("殖利率 (%)（衡量投資回報）", latest_div.get('DividendYield', '無資料'))
            else:
                st.metric("殖利率 (%)（衡量投資回報）", "無資料")

        with col3:
            if df_div is not None and not df_div.empty:
                latest_div = df_div.sort_values('date').iloc[-1]
                st.metric("現金股利 (元)（每股發放總額）", latest_div.get('CashEarningsDistribution', '無資料'))
            else:
                st.metric("現金股利 (元)（每股發放總額）", "無資料")
    else:
        st.error("❌ 查無股價資料，請確認代碼或 API token")

elif page == "📊 勝率排行":
    st.title("📊 多檔勝率排行推薦")
    st.caption(f"資料分析時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    target_stocks = [
        ('2330', '台積電'), ('2317', '鴻海'), ('2303', '聯電'), ('2412', '中華電'),
        ('2882', '國泰金'), ('2881', '富邦金'), ('2886', '兆豐金'), ('2891', '中信金'),
        ('2892', '第一金'), ('5880', '合庫金'), ('2603', '長榮'), ('2609', '陽明'),
        ('2615', '萬海'), ('3034', '聯詠'), ('2454', '聯發科'), ('2308', '台達電'),
        ('2408', '南亞科'), ('2377', '微星'), ('3008', '大立光'), ('3017', '奇鋐'),
        ('6415', '矽力*-KY'), ('8046', '南電'), ('2327', '國巨'), ('3702', '大聯大'),
        ('2379', '瑞昱'), ('2382', '廣達'), ('2385', '群光'), ('3006', '晶豪科'),
        ('2345', '智邦'), ('3014', '聯陽'), ('6669', '緯穎'), ('4961', '天鈺'),
        ('2605', '新興'), ('5608', '四維航'), ('2618', '長榮航'), ('2634', '漢翔'),
        ('6223', '旺矽'), ('3680', '家登'), ('6147', '頎邦'), ('3035', '智原'),
        ('3228', '金麗科'), ('2354', '鴻準'), ('3675', '德微'), ('6552', '易華電'),
        ('6488', '環球晶'), ('3707', '漢磊'), ('2301', '光寶科'), ('2344', '華邦電'),
        ('4966', '譜瑞-KY'), ('2347', '聯強'), ('5243', '乙盛-KY'), ('2383', '台光電'),
        ('1589', '永冠-KY'), ('3016', '嘉晶'), ('3037', '欣興'), ('3481', '群創'),
        ('2409', '友達'), ('8105', '凌巨'), ('2476', '鉅祥'), ('2610', '華航'),
        ('5871', '中租-KY'), ('1605', '華新'), ('2002', '中鋼'), ('2027', '大成鋼'),
        ('9958', '世紀鋼'), ('2105', '正新'), ('2201', '裕隆'), ('2207', '和泰車'),
        ('1513', '中興電'), ('1519', '華城'), ('1536', '和大'), ('3706', '神達'),
        ('3045', '台灣大'), ('4904', '遠傳'), ('4906', '正文'), ('4958', '臻鼎-KY'),
        ('5269', '祥碩'), ('6182', '合晶'), ('3231', '緯創'), ('8210', '勤誠'),
        ('8099', '大世科'), ('3010', '華立'), ('4746', '台耀'), ('5274', '信驊'),
        ('4107', '邦特'), ('4736', '泰博'), ('6531', '愛普*'), ('6485', '點序'),
        ('3529', '力旺'), ('3686', '達能'), ('6278', '台表科'), ('8936', '國統'),
        ('8996', '高力'), ('8454', '富邦媒'), ('2204', '中華'), ('2607', '榮運'),
        ('3701', '大眾控'), ('9933', '中鼎'), ('1476', '儒鴻'), ('9910', '豐泰')
    ]
    ranking = []
    progress = st.progress(0.0, text="🔍 正在分析勝率...")

    for i, (symbol, name) in enumerate(target_stocks):
        df = get_price_data(symbol)
        if df is not None and len(df) >= 20:
            win_rate = round(df['Win'].mean() * 100, 1)
            three_rate = round(df['ThreeDay_Win'].mean() * 100, 1)
            avg_return = round(df['Overnight_Change'].mean(), 2)
            ranking.append({
                "股票代號": symbol,
                "公司名稱": name,
                "隔日勝率": f"{win_rate}%",
                "三日勝率": f"{three_rate}%",
                "平均隔日漲幅": f"{avg_return}%",
                "樣本數": len(df),
                "下單日": datetime.today().strftime('%Y-%m-%d'),
                "三日持有": f"{(datetime.today() + timedelta(days=1)).strftime('%m/%d')}、{(datetime.today() + timedelta(days=2)).strftime('%m/%d')}、{(datetime.today() + timedelta(days=3)).strftime('%m/%d')}"
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

elif page == "🧪 勝率模擬器":
    st.title("🧪 勝率模擬器")
    st.caption(f"資料分析時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    symbol = st.text_input("請輸入股票代號進行模擬分析", value="2330")
    threshold = st.slider("漲幅門檻 %（若達此漲幅視為成功）", min_value=0.5, max_value=5.0, step=0.1, value=1.5)
    df = get_price_data(symbol)
    if df is not None:
        df['CustomWin'] = df['Overnight_Change'] >= threshold
        win_rate = round(df['CustomWin'].mean() * 100, 1)
        avg_return = round(df['Overnight_Change'].mean(), 2)
        st.metric("模擬勝率", f"{win_rate}%")
        st.metric("平均報酬率", f"{avg_return}%")
        df_display = df[['close', 'Next_Open', 'Overnight_Change', 'CustomWin']].copy()
        df_display['date'] = df_display.index.date
        df_display = df_display.sort_index(ascending=False)
        df_display = df_display.rename(columns={
            'close': '收盤價',
            'Next_Open': '次日開盤',
            'Overnight_Change': '隔日漲跌幅(%)',
            'CustomWin': f'是否達 {threshold}%',
            'date': '日期'
        })
        st.dataframe(df_display[['日期', '收盤價', '次日開盤', '隔日漲跌幅(%)', f'是否達 {threshold}%']].round(2), use_container_width=True)
    else:
        st.warning("查無資料，請確認代碼")



