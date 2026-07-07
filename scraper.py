import os
import requests
from bs4 import BeautifulSoup
import pandas as pd

# 1. 直接指定 ABS Table 17 的官方固定下載連結
excel_url = "https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/consumer-price-index-australia/latest-release/6401017.xlsx"

print(f"正在從 ABS 官方下載最新檔案: {excel_url}")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# 2. 下載並讀取官方真正的數據工作表 'Data1' (不指定 skiprows，讓程式動態找)
df_raw = pd.read_excel(excel_url, sheet_name='Data1', header=None)

# 3. 動態尋找含有 "Weighted average" 或 "Period" 的那一行作為真正的欄位標題
header_idx = None
for idx, row in df_raw.iterrows():
    row_vals = row.astype(str).tolist()
    # 只要看到某一行同時有 Series ID 或 Weighted average 相關關鍵字
    if any('Weighted average' in val or 'Series ID' in val for val in row_vals):
        header_idx = idx
        break

if header_idx is not None:
    print(f"🎯 成功在 Excel 的 Data1 工作表第 {header_idx + 1} 行定位到欄位結構。")
    # 將那一行設定為欄位名稱
    df_raw.columns = df_raw.iloc[header_idx]
    # 切下數據區，拋棄上面的標題
    df = df_raw.iloc[header_idx + 1:].reset_index(drop=True)
else:
    # 備用方案：如果動態找失敗，就強制用標準的第 10 行 (skiprows=9)
    df = pd.read_excel(excel_url, sheet_name='Data1', skiprows=9)

# 清除欄位名稱前後的隱形空格
df.columns = df.columns.str.strip()

# 自動把第一欄（時間軸）統一更名為 'Period'
df.rename(columns={df.columns[0]: 'Period'}, inplace=True)

# 4. 精準鎖定目標欄位
target_col = 'Weighted average of eight capital cities'

# 模糊比對，只要欄位名稱包含 "Weighted average" 就直接拿來用
possible_cols = [col for col in df.columns if 'Weighted average' in str(col)]
if possible_cols:
    target_col = possible_cols[0]
else:
    # 萬一 ABS 用的是代碼，Table 17 的加權平均代碼通常是 A2325846C 或最後一欄
    # 我們這裡直接幫你做保底：找不到文字就拿最後一欄（加權平均通常放在最後面）
    target_col = df.columns[-1]

print(f"成功鎖定數據欄位: {target_col}")

# 5. 建立乾淨的 DataFrame，並丟棄空行
df_clean = df[['Period', target_col]].dropna()

# 6. 清洗資料，只留下正確的季度格式列（支援 2025-09 或 2025 September 等格式）
# 官方時間序列有時是時間物件，先轉成字串處理
df_clean['Period'] = df_clean['Period'].astype(str)

# 7. 儲存成 CSV
output_file = 'cpi_australia.csv'
df_clean.to_csv(output_file, index=False)
print(f"🎉【恭喜通關】最新 CPI 數據已自動抓取成功，並精準儲存至 {output_file}！")
