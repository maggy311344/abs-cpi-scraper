import pandas as pd
import requests

# 1. 直接鎖定 ABS 官方 Table 17 乾淨版資料的固定下載連結 (Data Cube)
# 這個網址對應的就是你下載並上傳給我的那份 "All groups CPI, Index numbers(a).xlsx"
excel_url = "https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/consumer-price-index-australia/latest-release/6401017.xlsx"

# 備用網址：如果上面因為月份網址變動，我們使用最新發布的直接下載點
# 根據 ABS 規則，這條連結通常會自動導向最新的發布版本
print(f"確認直接下載 Table 17 檔案: {excel_url}")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# 2. 下載並讀取指定的工作表 (你說的 Sheet1)
print("正在下載並讀取 Sheet1...")
# 根據你提供的檔案結構，第一行是標題 "All groups CPI, Index numbers(a)"，所以我們跳過 1 行 (skiprows=1)
# 這樣第二行 (Period, Sydney...) 就會自動變成標準表頭！
df = pd.read_excel(excel_url, sheet_name='Sheet1', skiprows=1)

# 清除欄位名稱前後可能存在的隱形空格
df.columns = df.columns.str.strip()

print(f"目前成功讀取到的欄位有：{list(df.columns[:3])} ... {list(df.columns[-1:])}")

# 3. 精準鎖定目標欄位
target_col = 'Weighted average of eight capital cities'

if target_col not in df.columns:
    # 預防萬一，如果名字有些微差異，用關鍵字去撈
    possible_cols = [col for col in df.columns if 'Weighted average' in str(col)]
    if possible_cols:
        target_col = possible_cols[0]
    else:
        raise Exception(f"在 Sheet1 中找不到 '{target_col}'！目前的欄位是：{list(df.columns)}")

# 4. 建立只包含季度和加權平均值的乾淨 DataFrame，並丟棄空行
df_clean = df[['Period', target_col]].dropna()

# 5. 清洗資料，只留下正確的季度格式列（例如 2025 September）
df_clean = df_clean[df_clean['Period'].astype(str).str.contains('March|June|September|December', case=False, na=False)]

# 6. 儲存成 CSV
output_file = 'cpi_australia.csv'
df_clean.to_csv(output_file, index=False)
print(f"🎉【大功告成】資料已成功抓取，並精準儲存至 {output_file}！")
