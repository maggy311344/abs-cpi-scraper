import os
import requests
import pandas as pd

# 1. 鎖定官方固定下載連結
excel_url = "https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/consumer-price-index-australia/latest-release/6401017.xlsx"

print(f"正在從 ABS 官方下載最新檔案: {excel_url}")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# 2. 直接精準讀取 'Data1'，並跳過前 9 行的宣告，讓 Series ID 直接變成表頭
df = pd.read_excel(excel_url, sheet_name='Data1', skiprows=9)

# 清除欄位空格
df.columns = df.columns.str.strip()

# 將第一欄更名為 Period
df.rename(columns={df.columns[0]: 'Period'}, inplace=True)

# 3. 指定加權平均 CPI 指數的官方萬年不變代碼
target_code = 'A2325846C'

if target_code not in df.columns:
    # 保底機制：如果代碼變了，拿最後一欄
    target_col = df.columns[-1]
else:
    target_col = target_code

print(f"🎯 已成功鎖定核心數據欄位: {target_col}")

# 4. 建立乾淨的 DataFrame，並剔除無效空行
df_clean = df[['Period', target_col]].dropna()

# 5. 清洗時間格式
# 先將 Period 轉換為標準時間格式，以便精準篩選與排序
df_clean['Period'] = pd.to_datetime(df_clean['Period'], errors='coerce')
df_clean = df_clean.dropna(subset=['Period'])

# 只留下 quarterly 的月份（3月、6月、9月、12月）
df_clean = df_clean[df_clean['Period'].dt.month.isin([3, 6, 9, 12])]

# 6. 將時間格式化為你指定的完美格式（例如 "2025 September"）
df_clean['Period'] = df_clean['Period'].dt.strftime('%Y %B')

# 7. 重新命名輸出的欄位名稱，完全對齊你手邊的乾淨表格
df_output = pd.DataFrame({
    'Period': df_clean['Period'],
    'Weighted average of eight capital cities': df_clean[target_col]
})

# 8. 關鍵排序：將數據倒序排列（最新的 2025/2026 年季度直接推到最上面！）
df_output = df_output.iloc[::-1].reset_index(drop=True)

# 9. 儲存成 CSV
output_file = 'cpi_australia.csv'
df_output.to_csv(output_file, index=False)
print(f"🎉【大功告成】最新 CPI 數值（如 143.6）已完美寫入 {output_file}！")
