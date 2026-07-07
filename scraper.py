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
# 關鍵修正：指定讀取 'Data1' 工作表，並跳過前 9 行（ABS 標準時間序列格式的表頭宣告）
df = pd.read_excel(excel_url, sheet_name='Data1', skiprows=9)

# 重新命名第一欄為 Period (時間欄位)
df.rename(columns={df.columns[0]: 'Period'}, inplace=True)

# 4. 精準篩選我們需要的兩欄
target_col = 'Weighted average of eight capital cities'

# 預防萬一欄位名稱前後有空格，先用關鍵字搜尋包含 "Weighted average" 的欄位
possible_cols = [col for col in df.columns if 'Weighted average' in str(col)]

if possible_cols:
    target_col = possible_cols[0]
else:
    raise Exception(f"在 Data1 中依舊找不到對應的欄位！目前的欄位有：{list(df.columns[:3])} 等...")

# 重新建立一個乾淨的 DataFrame，只留下季度和加權平均值
df_clean = df[['Period', target_col]].dropna()

# 5. 清洗資料，只留下正確的季度格式列
df_clean = df_clean[df_clean['Period'].astype(str).str.contains('March|June|September|December', case=False, na=False)]

# 6. 儲存成 CSV
output_file = 'cpi_australia.csv'
df_clean.to_csv(output_file, index=False)
print(f"【成功】資料已精準更新並儲存至 {output_file}！")
