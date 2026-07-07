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

# 3. 下載並讀取 Excel 資料 (這次不跳行讀取，保留前幾行的文字標題)
print("正在下載並解析 Excel 資料...")
df = pd.read_excel(excel_url, sheet_name='Data1')

# 4. 尋找含有 "Weighted average" 文字的那一行作為標題
header_row_index = None
target_col_name = None

# 掃描前 15 行，找出哪一行包含了我們要的關鍵字
for i in range(min(15, len(df))):
    row_values = df.iloc[i].astype(str).tolist()
    for val in row_values:
        if 'Weighted average' in val:
            header_row_index = i
            break
    if header_row_index is not None:
        break

if header_row_index is not None:
    print(f"成功在第 {header_row_index + 1} 行找到文字表頭！正在重構表格...")
    # 將那一行設為新的欄位名稱
    df.columns = df.iloc[header_row_index]
    # 把表頭之前和那一行本身的雜訊刪除，只留下後面的數據
    df = df.iloc[header_row_index + 1:].reset_index(drop=True)
else:
    # 如果真的沒找到，就嘗試拿第一行（對應你上傳的 CSV 結構）
    df.columns = df.iloc[0]
    df = df[1:].reset_index(drop=True)

# 重新命名第一欄為 Period
df.rename(columns={df.columns[0]: 'Period'}, inplace=True)

# 5. 精準篩選我們需要的兩欄
target_col = 'Weighted average of eight capital cities'
possible_cols = [col for col in df.columns if 'Weighted average' in str(col)]

if possible_cols:
    target_col = possible_cols[0]
else:
    raise Exception(f"重構後依舊找不到對應欄位，目前的欄位有：{list(df.columns[:3])}")

# 建立乾淨的 DataFrame
df_clean = df[['Period', target_col]].dropna()

# 6. 清洗資料，只留下正確的季度格式列 (例如 2025 September)
df_clean = df_clean[df_clean['Period'].astype(str).str.contains('March|June|September|December', case=False, na=False)]

# 7. 儲存成 CSV
output_file = 'cpi_australia.csv'
df_clean.to_csv(output_file, index=False)
print(f"【成功】資料已精準更新並儲存至 {output_file}！")
