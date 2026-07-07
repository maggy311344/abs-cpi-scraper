import os
import requests
import pandas as pd

# 1. 直接指定 ABS Table 17 的官方固定下載連結
excel_url = "https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/consumer-price-index-australia/latest-release/6401017.xlsx"

print(f"正在從 ABS 官方下載最新檔案: {excel_url}")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# 2. 讀取官方數據工作表 'Data1'
# 這次我們直接從第 10 行（skiprows=9）讀取，讓 Series ID 直接變成欄位標題
df = pd.read_excel(excel_url, sheet_name='Data1', skiprows=9)

# 清除欄位名稱前後的隱形空格
df.columns = df.columns.str.strip()

# 自動把第一欄（時間軸）更名為 'Period'
df.rename(columns={df.columns[0]: 'Period'}, inplace=True)

# 3. 用 ABS 官方萬年不變的「八大城市加權平均 CPI 指數」專屬代碼進行鎖定
# Table 17 Index Numbers 的代碼就是 A2325846C
target_code = 'A2325846C'

if target_code not in df.columns:
    # 預防萬一如果代碼沒對上，拿最後一欄作為保底
    target_col = df.columns[-1]
    print(f"警告：找不到代碼 {target_code}，改拿最後一欄：{target_col}")
else:
    target_col = target_code
    print(f"🎯 成功鎖定八大城市加權平均 CPI 代碼: {target_code}")

# 4. 建立乾淨的 DataFrame，並丟棄空行與前幾行的文字殘留
df_clean = df[['Period', target_col]].dropna()

# 5. 清洗與格式化時間
# ABS 官方的 Period 讀進來是時間物件，我們把它過濾並格式化
df_clean = df_clean[df_clean['Period'].astype(str).str.contains('March|June|September|December|03|06|09|12', case=False, na=False)]

# 嘗試將時間欄位轉換為漂亮易讀的格式
try:
    df_clean['Period'] = pd.to_datetime(df_clean['Period']).dt.strftime('%Y %B')
except Exception as e:
    df_clean['Period'] = df_clean['Period'].astype(str)

# 重新命名欄位，讓產出的 CSV 漂亮又專業
df_output = pd.DataFrame({
    'Period': df_clean['Period'],
    'Weighted average of eight capital cities': df_clean[target_col]
})

# 6. 儲存成 CSV
output_file = 'cpi_australia.csv'
df_output.to_csv(output_file, index=False)
print(f"🎉【大功告成】最新 CPI 數值已成功抓取，並精準儲存至 {output_file}！")
