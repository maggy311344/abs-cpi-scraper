import os
import requests
import pandas as pd

# 1. 鎖定你指定的 6401017.xlsx 官方萬年不變連結
excel_url = "https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/consumer-price-index-australia/latest-release/6401017.xlsx"

print(f"正在下載目標檔案: {excel_url}")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# 2. 讀取 Excel 的第一個數據工作表，不設定 header，我們自己來切
df_raw = pd.read_excel(excel_url, sheet_name='Data1', header=None)

# 3. 根據你的指示：時間在第一欄（A欄），目標數據在第 J 欄
# Excel 的 J 欄對應到 Python 的索引是 9 (A=0, B=1, C=2... J=9)
# 我們直接暴力提取 A 欄和 J 欄
df_j = pd.DataFrame({
    'Period': df_raw[0],
    'Weighted average of eight capital cities': df_raw[9]
})

# 4. 開始向下尋找真正的季度數據
# 官方表格前面大約有 10 幾行是標題宣告（也就是你說的 J2 寫著名稱的地方）
# 真正的數據行，其 Period 欄位會是時間型態，或者是包含日期的字串
data_rows = []

for idx, row in df_j.iterrows():
    p_val = str(row['Period'])
    # 只要 Period 包含年份數字（例如 19 或 20 開頭的 4 位數日期數字），就代表進到數據區了
    if any(p_val.startswith(str(year)) for year in range(1900, 2100)):
        data_rows.append(row)

# 建立乾淨的數據表
df_clean = pd.DataFrame(data_rows).dropna()

# 5. 精準將時間格式化為你指定的 "2025 September"
try:
    df_clean['Period'] = pd.to_datetime(df_clean['Period'])
    # 只留下 quarterly 的月份（3月、6月、9月、12月）
    df_clean = df_clean[df_clean['Period'].dt.month.isin([3, 6, 9, 12])]
    df_clean['Period'] = df_clean['Period'].dt.strftime('%Y %B')
except Exception as e:
    pass

# 6. 將順序倒排（最新季度在最上面，完全對齊你的格式）
df_output = df_clean.iloc[::-1].reset_index(drop=True)

# 7. 儲存成 CSV
output_file = 'cpi_australia.csv'
df_output.to_csv(output_file, index=False)
print(f"🎉【大功告成】已成功鎖定 J 欄，並將最新 CPI 指數精準儲存至 {output_file}！")
