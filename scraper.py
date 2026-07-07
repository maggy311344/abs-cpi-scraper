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
    # 尋找包含 "table_17" 且是 xlsx 的連結
    if "table_17" in href.lower() and href.endswith('.xlsx'):
        # 處理相對路徑或絕對路徑
        if href.startswith('http'):
            excel_url = href
        else:
            excel_url = "https://www.abs.gov.au" + href
        break

if not excel_url:
    raise Exception("找不到 Table 17 的 Excel 下載連結，請檢查網頁結構是否改變！")

print(f"成功找到 Excel 連結: {excel_url}")

# 3. 下載並讀取 Excel (ABS 的資料通常在 'Data1' 工作表)
print("正在下載並解析 Excel 資料...")
# ABS Data downloads 的 Excel 通常第一欄是 Date，接著是各個指標
df = pd.read_excel(excel_url, sheet_name='Data1', skiprows=9) # 通常前幾行是標題，跳過 9 行（視情況調整）

# 重新命名第一欄為 Date
df.rename(columns={df.columns[0]: 'Date'}, inplace=True)

# 4. 篩選 "Weighted average of eight capital cities"
# 我們需要找出欄位名稱中包含這個關鍵字的欄位
target_cols = ['Date'] + [col for col in df.columns if 'Weighted average of eight capital cities' in str(col)]

df_filtered = df[target_cols].dropna(subset=['Date'])

# 5. 格式化 Date 欄位 (將其轉換為 YYYY-MM 格式方便閱讀)
df_filtered['Date'] = pd.to_datetime(df_filtered['Date']).dt.strftime('%Y-%m')

# 6. 儲存成 CSV
output_file = 'cpi_australia.csv'
df_filtered.to_csv(output_file, index=False)
print(f"資料已成功更新並儲存至 {output_file}")
