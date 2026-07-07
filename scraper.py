import os
import requests
from bs4 import BeautifulSoup
import pandas as pd

# 1. 定義 ABS CPI 網頁網址
URL = "https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/consumer-price-index-australia/latest-release"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

print("正在解析 ABS 網頁，尋找【All groups CPI, Index numbers(a)】...")
response = requests.get(URL, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')

# 2. 精準尋找符合你上傳檔案名稱的 Excel 下載連結
excel_url = None
for link in soup.find_all('a', href=True):
    href = link['href']
    link_text = link.get_text()
    
    # 只要超連結文字包含 "All groups CPI" 或是 "Index numbers" 且是 xlsx 結尾
    if href.endswith('.xlsx') and ('all groups cpi' in link_text.lower() or 'index numbers' in link_text.lower()):
        if href.startswith('http'):
            excel_url = href
        else:
            excel_url = "https://www.abs.gov.au" + href
        break

# 備用安全機制：如果依照文字找不到，改找包含 "17" 且是 xlsx 的連結
if not excel_url:
    for link in soup.find_all('a', href=True):
        href = link['href']
        if href.endswith('.xlsx') and '17' in href:
            if href.startswith('http'):
                excel_url = href
            else:
                excel_url = "https://www.abs.gov.au" + href
            break

if not excel_url:
    raise Exception("在網頁上找不到對應的 Excel 下載連結！")

print(f"成功鎖定 Excel 連結: {excel_url}")

# 3. 下載並指定讀取 Sheet1
print("正在下載並讀取 Sheet1...")
# 根據你提供的結構，第一行是 "All groups CPI, Index numbers(a)"，跳過 1 行讓 Period 變成表頭
df = pd.read_excel(excel_url, sheet_name='Sheet1', skiprows=1)

# 清除欄位名稱前後的空格
df.columns = df.columns.str.strip()

# 4. 精準鎖定目標欄位
target_col = 'Weighted average of eight capital cities'

if target_col not in df.columns:
    # 備用：如果名稱有極細微文字差異
    possible_cols = [col for col in df.columns if 'Weighted average' in str(col)]
    if possible_cols:
        target_col = possible_cols[0]
    else:
        raise Exception(f"在 Sheet1 中找不到 '{target_col}'！目前的欄位是：{list(df.columns)}")

# 5. 建立乾淨的 DataFrame，並丟棄空行
df_clean = df[['Period', target_col]].dropna()

# 6. 清洗資料，只留下正確的季度格式列
df_clean = df_clean[df_clean['Period'].astype(str).str.contains('March|June|September|December', case=False, na=False)]

# 7. 儲存成 CSV
output_file = 'cpi_australia.csv'
df_clean.to_csv(output_file, index=False)
print(f"🎉【大功告成】資料已成功抓取，並精準儲存至 {output_file}！")
