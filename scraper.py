import requests
import pandas as pd
from io import StringIO

# 1. 鎖定 Table 17 純數據 CSV 連結
csv_url = "https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/consumer-price-index-australia/latest-release/6401017.csv"

print(f"正在直接下載 Table 17 純數據檔案: {csv_url}")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

response = requests.get(csv_url, headers=headers)
response.encoding = 'utf-8'

# 2. 逐行掃描純文字，避開 ParserError 陷阱
lines = response.text.splitlines()
data_lines = []
start_collecting = False

for line in lines:
    # 只要看到某一行同時包含 Period 和 Weighted average，代表真正的表格從這裡開始！
    if 'Period' in line and 'Weighted average' in line:
        start_collecting = True
    
    if start_collecting:
        data_lines.append(line)

if not data_lines:
    raise Exception("在 CSV 檔案中找不到包含 'Period' 與 'Weighted average' 的數據起始行！")

print(f"🎯 成功剝離表頭雜訊，共擷取到 {len(data_lines)} 行核心數據。")

# 3. 將乾淨的文字行轉回 DataFrame
clean_text = "\n".join(data_lines)
df = pd.read_csv(StringIO(clean_text))

# 清除欄位名稱前後可能存在的隱形空格
df.columns = df.columns.str.strip()

# 自動把時間欄位統一更名為 'Period'
df.rename(columns={df.columns[0]: 'Period'}, inplace=True)

# 4. 精準鎖定目標欄位
target_col = 'Weighted average of eight capital cities'
possible_cols = [col for col in df.columns if 'Weighted average' in str(col)]

if possible_cols:
    target_col = possible_cols[0]
else:
    raise Exception(f"找不到目標欄位！目前的欄位有：{list(df.columns[:3])}")

print(f"成功鎖定數據欄位: {target_col}")

# 5. 建立乾淨的 DataFrame，並丟棄空行
df_clean = df[['Period', target_col]].dropna()

# 6. 清洗資料，只留下正確的季度格式列（例如 2025 September）
df_clean = df_clean[df_clean['Period'].astype(str).str.contains('March|June|September|December', case=False, na=False)]

# 7. 儲存成 CSV
output_file = 'cpi_australia.csv'
df_clean.to_csv(output_file, index=False)
print(f"🎉【恭喜通關】資料已成功抓取，並精準儲存至 {output_file}！")
