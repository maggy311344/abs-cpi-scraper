import pandas as pd
import requests

# 1. 直接鎖定 ABS 最底層、最純粹的 Table 17 CSV 數據流連結
# 這個連結繞過了所有網頁按鈕與 Index 頁的干擾，直達數據核心
csv_url = "https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/consumer-price-index-australia/latest-release/6401017.csv"

print(f"正在直接下載 Table 17 純數據檔案: {csv_url}")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# 2. 使用 requests 下載並用 pandas 讀取 CSV
response = requests.get(csv_url, headers=headers)
response.encoding = 'utf-8'

# 將下載下來的文字轉成 DataFrame
# 根據你上傳的檔案：第一行是 "All groups CPI..."，所以 skiprows=1 讓第二行直接變表頭
from io import StringIO
df = pd.read_csv(StringIO(response.text), skiprows=1)

# 清除欄位名稱前後可能存在的隱形空格
df.columns = df.columns.str.strip()

# 自動把時間欄位統一更名為 'Period'
df.rename(columns={df.columns[0]: 'Period'}, inplace=True)

print(f"成功讀取！目前的欄位有：{list(df.columns[:3])} ... 等")

# 3. 精準鎖定目標欄位
target_col = 'Weighted average of eight capital cities'

# 模糊比對，確保萬無一失
possible_cols = [col for col in df.columns if 'Weighted average' in str(col)]
if possible_cols:
    target_col = possible_cols[0]
else:
    raise Exception(f"找不到目標欄位！目前的欄位有：{list(df.columns[:3])}")

print(f"🎯 成功鎖定目標數據欄位: {target_col}")

# 4. 建立乾淨的 DataFrame，並丟棄空行
df_clean = df[['Period', target_col]].dropna()

# 5. 清洗資料，只留下正確的季度格式列（例如 2025 September）
df_clean = df_clean[df_clean['Period'].astype(str).str.contains('March|June|September|December', case=False, na=False)]

# 6. 儲存成 CSV
output_file = 'cpi_australia.csv'
df_clean.to_csv(output_file, index=False)
print(f"🎉【大功告成】純數據已成功下載，並精準儲存至 {output_file}！")
