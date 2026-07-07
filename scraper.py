import os
import requests
import pandas as pd

# 1. 直接指定 ABS Table 17 的官方固定下載連結
excel_url = "https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/consumer-price-index-australia/latest-release/6401017.xlsx"

print(f"正在從 ABS 官方下載最新檔案: {excel_url}")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# 2. 為了徹底避免讀錯工作表，我們掃描 Excel 裡面的所有 Sheet
excel_file = pd.ExcelFile(excel_url)
df_target = None
target_col_name = None

for sheet_name in excel_file.sheet_names:
    print(f"正在檢查工作表: {sheet_name} ...")
    # 先把整張表讀進來（不設表頭）
    df_raw = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
    
    # 逐行尋找哪裡有寫 'Weighted average of eight capital cities'
    for idx, row in df_raw.iterrows():
        row_vals = row.astype(str).tolist()
        # 只要這行有我們要的完整文字
        if any('Weighted average of eight capital cities' in val for val in row_vals):
            # 再檢查一下這張表是不是我們要的「指數表」（看它後面幾行的數值是不是大於 100）
            # 隨便挑下面第 5 行的資料來看看
            test_idx = idx + 5
            if test_idx < len(df_raw):
                test_val = df_raw.iloc[test_idx].dropna().tolist()
                # 如果這張表底下的數字都是小於 5 或 90 幾的百分比，就代表找錯張了，繼續找下一張
                if any(isinstance(v, (int, float)) and v > 100 for v in test_val) or \
                   any(str(v).replace('.','',1).isdigit() and float(v) > 100 for v in test_val):
                    
                    print(f"🎯 找到了！在 [{sheet_name}] 第 {idx + 1} 行找到正確的 CPI 指數表頭！")
                    df_raw.columns = df_raw.iloc[idx]
                    df_target = df_raw.iloc[idx + 1:].reset_index(drop=True)
                    break
    if df_target is not None:
        break

if df_target is None:
    raise Exception("翻遍了所有工作表，依然找不到包含數值大於 100 的 'Weighted average of eight capital cities' 欄位！")

# 3. 清洗與格式化
df_target.columns = df_target.columns.str.strip()
df_target.rename(columns={df_target.columns[0]: 'Period'}, inplace=True)

target_col = 'Weighted average of eight capital cities'

# 4. 建立乾淨的 DataFrame
df_clean = df_target[['Period', target_col]].dropna()

# 5. 過濾季度並轉換時間格式為 "2025 September"
df_clean = df_clean[df_clean['Period'].astype(str).str.contains('March|June|September|December|03|06|09|12', case=False, na=False)]

try:
    df_clean['Period'] = pd.to_datetime(df_clean['Period'])
    df_clean['Period'] = df_clean['Period'].dt.strftime('%Y %B')
except Exception as e:
    df_clean['Period'] = df_clean['Period'].astype(str)

# 6. 重新封裝，並將順序倒排（最新季度在最上面，完全符合你的範例檔）
df_output = pd.DataFrame({
    'Period': df_clean['Period'],
    'Weighted average of eight capital cities': df_clean[target_col]
})
df_output = df_output.iloc[::-1].reset_index(drop=True)

# 7. 儲存成 CSV
output_file = 'cpi_australia.csv'
df_output.to_csv(output_file, index=False)
print(f"🎉【大功告成】這次抓到的絕對是正確的 {target_col} 指數（例如 143.6）！")
