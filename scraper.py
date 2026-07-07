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
# 關鍵修正：ABS 的 Data1 前 9 行是宣告，第 10、11 行是雙層表頭 (header=[0, 1])
df = pd.read_excel(excel_url, sheet_name='Data1', skiprows=9, header=[0, 1])

# 4. 尋找符合條件的欄位
# 我們需要第一層包含 "Weighted average" 且第二層包含 "Index" 的那一欄
target_tuple = None
for col in df.columns:
    top_header = str(col[0])
    sub_header = str(col[1])
    if 'Weighted average' in top_header and 'Index' in sub_header:
        target_tuple = col
        break

if not target_tuple:
    # 預防萬一，如果沒有雙層表頭或文字有微調的備用方案
    possible_cols = [col for col in df.columns if 'Weighted average' in str(col)]
    if possible_cols:
        target_tuple = possible_cols[0]
    else:
        raise Exception(f"依然找不到目標欄位。目前的頂層欄位有：{list(set([c[0] for c in df.columns]))}")

print(f"成功鎖定目標雙層欄位: {target_tuple}")

# 5. 建立乾淨的 DataFrame 
# 第一欄通常是時間 (Period)，我們直接拿 df.columns[0]
period_col = df.columns[0]

df_clean = pd.DataFrame({
    'Period': df[period_col],
    'Weighted_Average_CPI': df[target_tuple]
}).dropna()

# 6. 清洗資料，只留下正確的季度格式列
df_clean = df_clean[df_clean['Period'].astype(str).str.contains('March|June|September|December', case=False, na=False)]

# 7. 儲存成 CSV
output_file = 'cpi_australia.csv'
df_clean.to_csv(output_file, index=False)
print(f"【成功】資料已精準更新並儲存至 {output_file}！")
