import pandas as pd
import requests
from io import StringIO
import os

# 1. 尝试读取本地已有的历史数据
file_path = 'data/p3.csv'
existing_df = None
if os.path.exists(file_path):
    try:
        existing_df = pd.read_csv(file_path, dtype={'issue': str})
        print(f"✅ 发现本地已有 {len(existing_df)} 期数据，将进行增量拼接。")
    except Exception as e:
        print(f"⚠️ 读取本地数据失败，将重新抓取。错误：{e}")

# 2. 抓取最新数据（默认网页提供最近100期）
url = "https://kaijiang.78500.cn/p3/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

print("正在抓取网页最新数据...")
try:
    response = requests.get(url, headers=headers, timeout=10)
    response.encoding = 'gbk'  # 防止乱码
    
    dfs = pd.read_html(StringIO(response.text))
    df = dfs[0]
    
    # 跳过表头，提取数据
    df = df.iloc[2:].copy()
    df = df[[0, 1, 3]]
    df.columns = ['issue', 'date', 'numbers']
    
    # 过滤掉无效行，拆分开奖号码
    df = df[df['issue'].astype(str).str.isdigit()]
    df[['d1', 'd2', 'd3']] = df['numbers'].astype(str).str.split(' ', expand=True)
    df['issue'] = df['issue'].astype(str)
    
    new_df = df[['issue', 'date', 'd1', 'd2', 'd3']]
    print(f"✅ 网页最新抓取到 {len(new_df)} 期。")

    # 3. 合并新旧数据（核心逻辑）
    if existing_df is not None:
        # 把旧数据和新数据拼到一起
        final_df = pd.concat([existing_df, new_df], ignore_index=True)
        # 根据期号去重（防止最新的100期里有之前抓过的），保留最后一次抓的数据
        final_df = final_df.drop_duplicates(subset=['issue'], keep='last')
    else:
        final_df = new_df

    # 4. 按时间顺序（期号）排序，保证从旧到新
    final_df = final_df.sort_values(by='issue').reset_index(drop=True)

    # 5. 保存
    os.makedirs('data', exist_ok=True)
    final_df.to_csv(file_path, index=False, encoding='utf-8-sig')
    
    print(f"\n🎉 增量更新成功！当前共计 {len(final_df)} 期数据。")
    print(f"最新一期为：{final_df.iloc[-1]['issue']}")
    print(f"数据已保存到 {file_path}")

except Exception as e:
    print(f"\n❌ 抓取失败，错误信息：{e}")
    # 【关键修改】：主动抛出异常，让 GitHub Actions 报错变红！
    import sys
    sys.exit(1)
