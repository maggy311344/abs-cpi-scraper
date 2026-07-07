import os
import requests
from bs4 import BeautifulSoup
import pandas as pd

# 1. 定義 ABS CPI 網頁網址
URL = "https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/consumer-price-index-australia/latest-release"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

print("正在解析 ABS 網頁，尋找 Excel 下載連結...")
response = requests.get(URL, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')

# 2. 自動尋找 Table 17 的 Excel 連結
excel_url = None
for link in soup.find_all('a', href=True):
    href = link['href']
    link_text = link.get_text().lower()
    
    if href.endswith('.xlsx') and ('17' in href or 'all groups cpi' in link_text or 'index numbers' in link_text):
        if href.startswith('http'):
            excel_url = href
        else:
            excel_url = "https://www.abs.gov.au" + href
        break

if not excel_url:
    raise Exception("在網頁上找不到任何對應的 Excel 下載連結！")

print(f"成功鎖定 Excel 連結: {excel_url}")

# 3. 終極修正：直接讀取「第一個工作表」(sheet_name=0)，完全不管它叫 Sheet1 還是 Data1！
print("正在下載並讀取第一個工作表...")
df = pd.read_excel(excel_url, sheet_name=0)

# 4. 尋找含有 'Period' 或 'Weighted average' 的那一行作為真正的欄位標題
header_idx = None
for idx, row in df.iterrows():
    row_vals = row.astype(str).tolist()
    # 只要看到某一行同時有任何城市或關鍵字，就認定它是欄位列
    if any('Weighted average' in val or 'Period' in val for val in row_vals):
        header_idx = idx
        break

if header_idx is not None:
    print(f"🎯 成功定位欄位結構，位於 Excel 的第 {header_idx + 1} 行。")
    df.columns = df.iloc[header_idx]
    df = df.iloc[header_idx + 1:].reset_index(drop=True)
else:
    # 萬一真的沒找到，就強制用第二行當標題 (對應 skiprows=1 的邏輯)
    df.columns = df.iloc[0]
    df = df[1:].reset_index(drop=True)

# 清除欄位名稱前後的空格
df.columns = df.columns.str.strip()

# 自動把時間欄位統一更名為 'Period'
df.rename(columns={df.columns[0]: 'Period'}, inplace=True)

# 5. 精準鎖定目標欄位
target_col = 'Weighted average of eight capital cities'

# 模糊比對，只要欄位名稱包含 "Weighted average" 就直接拿來用
possible_cols = [col for col in df.columns if 'Weighted average' in str(col)]
if possible_cols:
    target_col = possible_cols[0]
else:
    raise Exception(f"找不到目標欄位！目前的欄位有：{list(df.columns[:3])}")

print(f"成功鎖定數據欄位: {target_col}")

# 6. 建立乾淨的 DataFrame，並丟棄空行
df_clean = df[['Period', target_col]].dropna()

# 7. 清洗資料，只留下正確的季度格式列
df_clean = df_clean[df_clean['Period'].astype(str).str.contains('March|June|September|December', case=False, na=False)]

# 8. 儲存成 CSV
output_file = 'cpi_australia.csv'
df_clean.to_csv(output_file, index=False)
print(f"🎉【大功告成】資料已成功抓取，並精準儲存至 {output_file}！")
