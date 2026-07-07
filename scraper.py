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

# 3. 讀取 Excel 檔案的所有工作表
print("正在下載並掃描 Excel 所有工作表...")
excel_file = pd.ExcelFile(excel_url)

df_target = None
target_col = 'Weighted average of eight capital cities'

# 逐一檢查每一個工作表，直到找到含有目標欄位的那張表
for sheet_name in excel_file.sheet_names:
    # 先不管表頭，整張表直接讀進來
    df_sheet = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
    
    # 一行一行掃描，看看有沒有哪一行包含了 "Weighted average of eight capital cities"
    for idx, row in df_sheet.iterrows():
        row_str = row.astype(str).tolist()
        if any(target_col in val for val in row_str):
            print(f"🎯 找到了！在工作表 [{sheet_name}] 的第 {idx + 1} 行發現目標數據結構。")
            
            # 將那一行設定為欄位名稱
            df_sheet.columns = df_sheet.iloc[idx]
            # 切下數據區（拋棄上面的廢話標題）
            df_target = df_sheet.iloc[idx + 1:].reset_index(drop=True)
            break
            
    if df_target is not None:
        break

if df_target is None:
    raise Exception("翻遍了整份 Excel 依舊找不到 'Weighted average of eight capital cities' 的文字欄位！")

# 4. 清洗與重構表格
# 自動把第一欄（不管它叫 Period 還是 Date）統一更名為 'Period'
df_target.rename(columns={df_target.columns[0]: 'Period'}, inplace=True)

# 精準剔除欄位名稱前後的隱形空格
df_target.columns = df_target.columns.str.strip()

# 建立只包含季度和加權平均值的乾淨 DataFrame
df_clean = df_target[['Period', target_col]].dropna()

# 5. 清洗季度資料（只留下 March, June, September, December 結尾的資料列）
df_clean = df_clean[df_clean['Period'].astype(str).str.contains('March|June|September|December', case=False, na=False)]

# 6. 儲存成 CSV
output_file = 'cpi_australia.csv'
df_clean.to_csv(output_file, index=False)
print(f"【大功告成】資料已成功更新並儲存至 {output_file}！")
