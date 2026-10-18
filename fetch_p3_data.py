import pandas as pd
import requests
import os

file_path = 'data/p3.csv'
existing_df = None

# 1. 读取本地已有数据（用于增量拼接）
if os.path.exists(file_path):
    try:
        existing_df = pd.read_csv(file_path, dtype={'issue': str})
        print(f"✅ 发现本地已有 {len(existing_df)} 期数据，将进行增量拼接。")
    except Exception as e:
        print(f"⚠️ 读取本地数据失败，将重新抓取。错误：{e}")

# 2. 请求体彩官方 API 接口 (gameNo=35 代表排列三)
url = "https://webapi.sporttery.cn/gateway/lottery/getHistoryPageListV1.qry?gameNo=35&provinceId=0&pageSize=100&isVerify=1&pageNo=1"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.sporttery.cn/",
    "Origin": "https://www.sporttery.cn",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9"
}

print("正在通过官方 API 抓取最新数据...")
try:
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    
    json_data = response.json()
    data_list = json_data['value']['list']
    
    records = []
    for item in data_list:
        issue = str(item['lotteryDrawNum'])
        date = item['lotteryDrawTime']
        numbers = item['lotteryDrawResult'] # 格式如 "1 2 3"
        
        parts = numbers.split()
        if len(parts) == 3:
            records.append({
                'issue': issue,
                'date': date,
                'd1': parts[0],
                'd2': parts[1],
                'd3': parts[2]
            })
            
    new_df = pd.DataFrame(records)
    print(f"✅ 官方 API 最新抓取到 {len(new_df)} 期。")

    # 4. 合并新旧数据
    if existing_df is not None:
        final_df = pd.concat([existing_df, new_df], ignore_index=True)
        final_df = final_df.drop_duplicates(subset=['issue'], keep='last')
    else:
        final_df = new_df

    final_df = final_df.sort_values(by='issue').reset_index(drop=True)

    # 5. 保存
    os.makedirs('data', exist_ok=True)
    final_df.to_csv(file_path, index=False, encoding='utf-8-sig')
    
    print(f"\n🎉 增量更新成功！当前共计 {len(final_df)} 期数据。")
    print(f"最新一期为：{final_df.iloc[-1]['issue']}")

except Exception as e:
    print(f"\n❌ 抓取失败，错误信息：{e}")
    import sys
    sys.exit(1)