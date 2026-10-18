import pandas as pd
import requests
from io import StringIO
import os

url = "https://kaijiang.78500.cn/p3/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

print("正在抓取网页数据...")
response = requests.get(url, headers=headers)
# 关键修复：网站是GBK编码，不是UTF-8
response.encoding = 'gbk'

try:
    dfs = pd.read_html(StringIO(response.text))
    df = dfs[0]
    
    # 真正的数据从第2行开始（0和1是表头）
    df = df.iloc[2:].copy()
    
    # 按照你截图里显示的位置，提取：第0列(期号), 第1列(日期), 第3列(开奖号码)
    # 我们将它们重命名
    df = df[[0, 1, 3]]
    df.columns = ['issue', 'date', 'numbers']
    
    # 拆分开奖号码
    df[['d1', 'd2', 'd3']] = df['numbers'].astype(str).str.split(' ', expand=True)
    
    # 只保留这5列
    final_df = df[['issue', 'date', 'd1', 'd2', 'd3']].copy()
    
    # 确保期号是字符串
    final_df['issue'] = final_df['issue'].astype(str)
    
    # 保存
    os.makedirs('data', exist_ok=True)  # 【新增这行】
    final_df.to_csv('data/p3.csv', index=False, encoding='utf-8-sig')
    print(f"\n🎉 成功！共抓取 {len(final_df)} 期数据，已保存到 data/p3.csv")
    print("现在回到浏览器，按一下 R 键刷新页面，就能看到真实数据了！")
    
except Exception as e:
    print(f"\n❌ 抓取失败，错误信息：{e}")
