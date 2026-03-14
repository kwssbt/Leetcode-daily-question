import requests
import datetime
import asyncio
import sys
import os
from playwright.async_api import async_playwright

async def run_task():
    print("🚀 开始抓取 LeetCode 每日一题...")
    
    # 1. 抓取数据
    gql_url = "https://leetcode.cn/graphql"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", 
        "Content-Type": "application/json", 
        "Accept-Language": "zh-CN"
    }
    
    try:
        # 获取今日题目的 slug
        slug_query = {"query": "query { todayRecord { question { questionTitleSlug } } }"}
        slug_res = requests.post(gql_url, json=slug_query, headers=headers).json()
        slug = slug_res['data']['todayRecord'][0]['question']['questionTitleSlug']
        
        # 获取题目的详细信息
        detail_query = {
            "query": "query q($s:String!){question(titleSlug:$s){questionFrontendId translatedTitle translatedContent difficulty}}", 
            "variables": {"s": slug}
        }
        res = requests.post(gql_url, json=detail_query, headers=headers).json()['data']['question']
    except Exception as e: 
        print(f"❌ 数据抓取错误: {e}")
        sys.exit(1)

    # 2. 文件夹与路径逻辑
    today = datetime.date.today().strftime("%Y-%m-%d")
    folder_path = today
    
    if not os.path.exists(folder_path): 
        os.makedirs(folder_path)

    pdf_name = f"{today}.pdf"
    img_name = f"{today}.png"
    md_name = f"{today}.md"
    
    pdf_path = os.path.join(folder_path, pdf_name)
    img_path = os.path.join(folder_path, img_name)
    md_path = os.path.join(folder_path, md_name)
    
    # 3. 使用 Playwright 生成文档
    print(f"📄 正在生成文档至目录: {folder_path}/ ...")
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        style = """<style>
            body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;padding:30px;line-height:1.6;color:#1a1a1a;background:white;}
            h1{font-size:22px;margin-bottom:8px;font-weight:600;color:#000;border-bottom:1px solid #ddd;padding-bottom:8px;}
            .meta{font-size:13px;color:#666;margin-bottom:20px;}
            pre{background:#f8f8f8;padding:12px;border-radius:4px;border:1px solid #eee;overflow-x:auto;font-size:13px;}
            code{font-family:Menlo,Monaco,Consolas,monospace;font-size:13px;background:#f3f3f3;padding:2px 4px;border-radius:3px;}
            img{max-width:100%;height:auto;margin:10px 0;}
            table{border-collapse:collapse;width:100%;margin:15px 0;font-size:14px;}
            th,td{border:1px solid #eee;padding:10px;text-align:left;}
            th{background:#fafafa;font-weight:600;}
        </style>"""
        
        html_content = f"""
        <html>
        <head><meta charset='UTF-8'>{style}</head>
        <body>
            <h1>{res['questionFrontendId']}. {res['translatedTitle']}</h1>
            <div class='meta'>难度: <b>{res['difficulty']}</b></div>
            <div>{res['translatedContent']}</div>
        </body>
        </html>
        """
        
        await page.set_content(html_content)
        await asyncio.sleep(1) 
        
        await page.pdf(path=pdf_path, format="A4", margin={"top":"1.2cm","bottom":"1.2cm","left":"1.2cm","right":"1.2cm"})
        await page.screenshot(path=img_path, full_page=True)
        await browser.close()

    # 4. 生成 Markdown 笔记模板
    md_tpl = f"""# [{res['questionFrontendId']}. {res['translatedTitle']}](https://leetcode.cn/problems/{slug}/)

**{today}**

**题面难度：{res['difficulty']}** 

[查看PDF题面](./{img_name})

---

## 


---

## 代码实现 (C++)
```cpp

```

- 时间复杂度: $O()$
- 空间复杂度: $O()$

---

"""
    if not os.path.exists(md_path):
        with open(md_path, "w", encoding="utf-8") as f: 
            f.write(md_tpl)

    # 5. 更新 README.md (最新日期排在最上面，且表头仅保留一份)
    print("📝 正在更新 README.md (优化表格结构)...")
    readme_path = "README.md"
    header = "# LeetCode 每日一题记录\n\n| 日期 | 题目 | 难度 | 附件 |\n| :--- | :--- | :--- | :--- |\n"
    new_entry = f"| {today} | [{res['questionFrontendId']}. {res['translatedTitle']}](./{folder_path}/{md_name}) | {res['difficulty']} | [PDF](./{folder_path}/{pdf_name}) |"
    
    existing_rows = []
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            # 1. 如果今天已经记录过了，直接退出，防止 Actions 报错或重复插入
            if any(today in line for line in lines):
                print(f"✅ 今日题目 {today} 已经存在于目录中。")
                return
            
            # 2. 核心修复：只保留真正包含日期的数据行
            # 我们过滤掉标题、空行、以及包含 "日期" 或 "---" 的表头行
            for line in lines:
                line = line.strip()
                if line.startswith("|") and "日期" not in line and ":---" not in line:
                    existing_rows.append(line)

    # 3. 将新行置顶，重新组合
    all_rows = [new_entry] + existing_rows
    
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(header)
        for row in all_rows:
            f.write(row + "\n")
            
    print(f"🎉 目录已重构，表头已精简，最新题目已置顶。")

if __name__ == "__main__":
    asyncio.run(run_task())