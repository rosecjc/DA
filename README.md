# 📊 台股隔日沖勝率分析工具（Streamlit + twstock）

這是一個以 Python + Streamlit 打造的視覺化分析小工具，專門用來觀察台股標的的隔日沖漲幅勝率與三日報酬率，並可視覺化出漲幅分布。

---

## 🔧 功能特色

- 支援台股代號（使用 twstock）
- 自訂回測天數、門檻
- 計算隔日/三日報酬、勝率、最大跌幅
- 中文圖表支援（內建中文字體）
- 可直接部署到 [Streamlit Cloud](https://streamlit.io/cloud)

---

## 📁 專案結構

.
├── app.py # 主程式（Overnight Strategy App）
├── fonts/
│ └── NotoSansTC-VariableFont_wght.ttf # 中文字體檔（用於圖表顯示）
├── requirements.txt # 所需套件
└── README.md # 本說明文件


---

## 🔤 中文字型設定（必要）

為確保圖表中文字正常顯示，請從以下位置下載字體檔：

👉 [Noto Sans TC – Google Fonts](https://fonts.google.com/specimen/Noto+Sans+TC)

下載後，請將 `NotoSansTC-VariableFont_wght.ttf` 檔案放入專案資料夾下的 `fonts/` 資料夾中（與 `app.py` 同層）。

程式會自動使用該字體檔：

```python
font_path = "./fonts/NotoSansTC-VariableFont_wght.ttf"
☁️ 部署到 Streamlit Cloud
將本專案 Push 到 GitHub

登入 Streamlit Cloud

點 New app → 選你的 repo → 指定主程式為 app.py

部署後即可使用 🎉

📷 預覽畫面
（你可以貼上 app 實際畫面截圖）
