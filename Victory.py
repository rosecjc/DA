# 分析工具（twstock 為主 + TSE法人與收盤價補充）
import matplotlib
from matplotlib import font_manager
import matplotlib.pyplot as plt
import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import twstock

# 字體設定
font_path = "./fonts/NotoSansTC-VariableFont_wght.ttf"
font_prop = font_manager.FontProperties(fname=font_path)
plt.rcParams['font.family'] = font_prop.get_name()
plt.rcParams['axes.unicode_minus'] = False

st.set_page_config(page_title="隔日沖勝率工具", layout="wide")

# 取得今日法人買賣資訊
@st.cache_data
def fetch_tse_institution_data(stock_id):
    today = datetime.today().strftime("%Y%m%d")
    url = f"https://www.twse.com.tw/fund/T86?response=json&date={today}&selectType=ALL&_=1683631540000"
    res = requests.get(url)
    if res.status_code != 200:
        return None
    data = res.json()
    for entry in data.get("data", []):
        if entry[0] == stock_id:
            return {
                "外資買賣超": entry[4],
                "投信買賣超": entry[7],
                "自營商買賣超": entry[10]
            }
    return None

# 取得今日收盤價
@st.cache_data
def fetch_tse_closing_price(stock_id):
    today = datetime.today().strftime("%Y%m%d")
    url = f"https://www.twse.com.tw/exchangeReport/MI_INDEX?response=json&date={today}&type=ALL"
    res = requests.get(url)
    if res.status_code != 200:
        return None
    data = res.json()
    for entry in data.get("data9", []):
        if entry[0].strip() == stock_id:
            return entry[8]  # 收盤價
    return None

# 建立資料清單（你提供的股票）
custom_codes = [
    '2330', '2303', '2603', '2609', '2615', '2308', '2412', '2454', '2882', '2891',
    '2379', '3034', '8069', '3661', '2327', '3008', '3017', '2382', '6116', '3481',
    '1101', '1216', '2105', '2301', '3045', '3702', '4904', '3231', '1314', '1303',
    '1301', '1102', '1103', '1210', '1215', '1227', '1231', '1304', '1305', '1310',
    '1312', '1321', '1323', '1325', '1402', '1409', '1410', '1413', '1417', '1434',
    '1437', '1439', '1440', '1444', '1447', '1453', '1455', '1457', '1463', '1470',
    '1477', '1503', '1504', '1513', '1514', '1515', '1517', '1522', '1524', '1525',
    '1536', '1537', '1539', '1540', '1558', '1582', '1603', '1604', '1605', '1608',
    '1609', '1611', '1612', '1614', '1615', '1616', '1701', '1702', '1707', '1708',
    '1709', '1710', '1711', '1712', '1713', '1714', '1717', '1720', '1721'
]
st.title("📊 精選台股資訊（含法人買賣＋即時收盤）")

rows = []
for code in custom_codes:
    name = twstock.codes.get(code, {}).get('name', code)
    price = fetch_tse_closing_price(code)
    inst = fetch_tse_institution_data(code)
    row = {
        "股票代號": code,
        "股票名稱": name,
        "今日收盤價": price if price else "-",
        "外資買賣超": inst["外資買賣超"] if inst else "-",
        "投信買賣超": inst["投信買賣超"] if inst else "-",
        "自營商買賣超": inst["自營商買賣超"] if inst else "-"
    }
    rows.append(row)

st.dataframe(pd.DataFrame(rows), use_container_width=True)

st.caption("📌 數據來源：台灣證券交易所 TSE")

# 加入個股分析搜尋功能
st.subheader("🔍 個股分析")
symbol = st.text_input("請輸入股票代號（例如 2330）")
if symbol:
    stock = twstock.Stock(symbol)
    df = pd.DataFrame([{ 'date': d.date, 'open': d.open, 'close': d.close } for d in stock.fetch_31()])
    df.set_index('date', inplace=True)
    df['Next_Open'] = df['open'].shift(-1)
    df['Day3_Close'] = df['close'].shift(-2)
    df['Overnight_Change'] = ((df['Next_Open'] - df['close']) / df['close']) * 100
    df['ThreeDay_Change'] = ((df['Day3_Close'] - df['close']) / df['close']) * 100
    df['Win'] = df['Overnight_Change'] >= 1.5
    df['ThreeDay_Win'] = df['ThreeDay_Change'] >= 2.5
    valid_rows = df.dropna(subset=['Next_Open', 'Day3_Close'])
    total = len(valid_rows)
    if total > 0:
        win_rate = round(valid_rows['Win'].mean() * 100, 1)
        three_day_rate = round(valid_rows['ThreeDay_Win'].mean() * 100, 1)
        st.metric("隔日沖勝率（1.5%↑）", f"{win_rate}%")
        st.metric("三日沖勝率（2.5%↑）", f"{three_day_rate}%")
        st.dataframe(valid_rows[['close', 'Next_Open', 'Day3_Close', 'Overnight_Change', 'ThreeDay_Change', 'Win', 'ThreeDay_Win']].tail(20).round(2), use_container_width=True)
    else:
        st.warning("此股票近 30 日無足夠資料進行分析。")
