import os
import requests
from bs4 import BeautifulSoup
import pandas as pd

# 1. 定義 ABS CPI 網頁網址
URL = "https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/consumer-price-index-australia/latest-release"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

print("正在解析 ABS 網頁...")
response = requests.get(URL, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')

# 2. 尋找 Table 17 的 Excel 下載連結
excel_url = None
for link in soup.find_all('a', href=True):
    href = link['href']
    link_text = link.get_text().lower()
    
    # 只要網址結尾是 xlsx，且超連結文字或網址包含 "17" 
    if href.endswith('.xlsx') and ('17' in href or '17' in link_text):
        if href.startswith('http'):
            excel_url = href
        else:
            excel_url = "https://www.abs.gov.au" + href
        break

if not excel_url:
    raise Exception("找不到 Table 17，請檢查網頁結構是否改變！")

print(f"成功找到 Excel 連結: {excel_url}")

# 3. 下載並讀取 Excel 資料
print("正在下載並解析 Excel 資料...")
# 根據你提供的檔案結構，ABS 資料在讀取時，第一行通常是表頭 "All groups CPI, Index numbers(a)"
# 我們直接讀取，並將真正的欄位行（第二行）設為 header，或者利用 pandas 調整
df = pd.read_excel(excel_url, sheet_name=0, skiprows=1)

# 如果發現第一欄叫做 'Period' 或 'Date'，我們統一處理
if df.columns[0] != 'Period' and 'Period' in df.iloc[0].values:
    # 有時候前幾行有雜訊，自動修正為以 Period 為標題的那一行
    df.columns = df.iloc[0]
    df = df[1:]

# 4. 精準篩選我們需要的兩欄：Period 與 Weighted average of eight capital cities
target_col = 'Weighted average of eight capital cities'

if target_col not in df.columns:
    # 預防萬一欄位有名稱微調，用關鍵字搜尋
    possible_cols = [col for col in df.columns if 'Weighted average' in str(col)]
    if possible_cols:
        target_col = possible_cols[0]
    else:
        raise Exception(f"找不到對應的 {target_col} 欄位！目前的欄位有：{list(df.columns)}")

# 重新建立一個乾淨的 DataFrame，只留下季度和加權平均值
df_clean = df[['Period', target_col]].dropna()

# 5. 清洗與排序資料（讓最新的季度排在最下面或最上面，依你喜好，預設依時間順序）
# 移除可能不小心中招的表格結尾附註（例如包含文字 "(a)" 的列）
df_clean = df_clean[df_clean['Period'].astype(str).str.contains('March|June|September|December', case=False, na=False)]

# 6. 儲存成 CSV
output_file = 'cpi_australia.csv'
df_clean.to_csv(output_file, index=False)
print(f"【成功】資料已精準更新並儲存至 {output_file}！")
