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
        slug_query = {"query": "query { todayRecord { question { questionTitleSlug } } }"}
        slug_res = requests.post(gql_url, json=slug_query, headers=headers).json()
        slug = slug_res['data']['todayRecord'][0]['question']['questionTitleSlug']
        
        detail_query = {
            "query": "query q($s:String!){question(titleSlug:$s){questionFrontendId translatedTitle translatedContent difficulty}}", 
            "variables": {"s": slug}
        }
        res = requests.post(gql_url, json=detail_query, headers=headers).json()['data']['question']
    except Exception as e: 
        print(f"❌ 数据抓取错误: {e}")
        sys.exit(1)

    # 2. 文件夹与路径逻辑 (修复为北京时间 UTC+8)
    tz_bj = datetime.timezone(datetime.timedelta(hours=8))
    today = datetime.datetime.now(tz_bj).strftime("%Y-%m-%d")
    year = today[:4]
    month = today[5:7]
    
    # 构建嵌套文件夹路径: YYYY/MM/YYYY-MM-DD
    folder_path = os.path.join(year, month, today)
    # 使用 exist_ok=True 避免由于目录已存在导致报错
    os.makedirs(folder_path, exist_ok=True)

    pdf_name, img_name, md_name = f"{today}.pdf", f"{today}.png", f"{today}.md"
    pdf_path = os.path.join(folder_path, pdf_name)
    img_path = os.path.join(folder_path, img_name)
    md_path = os.path.join(folder_path, md_name)
    
    # 3. 使用 Playwright 生成文档 (加入备选字体族)
    print(f"📄 正在生成文档至目录: {folder_path}/ ...")
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # 样式中显式指定中文字体族
        style = """<style>
            body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,"PingFang SC","Hiragino Sans GB","Microsoft YaHei","Noto Sans CJK SC",sans-serif;padding:30px;line-height:1.6;color:#1a1a1a;background:white;}
            h1{font-size:22px;margin-bottom:8px;font-weight:600;color:#000;border-bottom:1px solid #ddd;padding-bottom:8px;}
            .meta{font-size:13px;color:#666;margin-bottom:20px;}
            pre{background:#f8f8f8;padding:12px;border-radius:4px;border:1px solid #eee;overflow-x:auto;font-size:13px;}
            code{font-family:Menlo,Monaco,Consolas,monospace;font-size:13px;background:#f3f3f3;padding:2px 4px;border-radius:3px;}
            img{max-width:100%;height:auto;margin:10px 0;}
            table{border-collapse:collapse;width:100%;margin:15px 0;font-size:14px;}
            th,td{border:1px solid #eee;padding:10px;text-align:left;}
            th{background:#fafafa;font-weight:600;}
        </style>"""
        
        html_content = f"<html><head><meta charset='UTF-8'>{style}</head><body><h1>{res['questionFrontendId']}. {res['translatedTitle']}</h1><div class='meta'>难度: <b>{res['difficulty']}</b></div><div>{res['translatedContent']}</div></body></html>"
        
        await page.set_content(html_content)
        await asyncio.sleep(2) # 稍微延长等待时间确保字体加载
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

[每日一题记录](https://github.com/kwssbt/Leetcode-daily-question)

"""
    if not os.path.exists(md_path):
        with open(md_path, "w", encoding="utf-8") as f: 
            f.write(md_tpl)

    "\n"# 5. 更新 README.md (按年月分类动态生成)
    print("📝 正在更新 README.md (按年月分类重构)...")
    readme_path = "README.md"
    
    # 提取历史记录
    records = {}
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # 识别有效的表格数据行
                if line.startswith("|") and "日期" not in line and ":---" not in line:
                    parts = line.split("|")
                    if len(parts) > 2:
                        date_key = parts[1].strip()
                        # 💡 关键修复：自动把 Windows 风格的反斜杠 \ 替换为 Markdown 支持的正斜杠 /
                        records[date_key] = line.replace("\\", "/")

    # 💡 关键修复：专门构建一个用于网页链接的路径，强制使用正斜杠 /
    url_folder_path = f"{year}/{month}/{today}"
    
    # 写入今日新数据 (使用 url_folder_path)
    new_entry = f"| {today} | [{res['questionFrontendId']}. {res['translatedTitle']}](./{url_folder_path}/{md_name}) | {res['difficulty']} | [PDF](./{url_folder_path}/{pdf_name}) |"
    records[today] = new_entry

    # 将所有日期降序排列
    sorted_dates = sorted(records.keys(), reverse=True)

    # 重新生成带层级的 README.md
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("# LeetCode 每日一题记录\n\n")
        
        current_year = ""
        current_month = ""
        
        for d in sorted_dates:
            y, m, _ = d.split("-")
            
            # 跨年时，生成二级标题
            if y != current_year:
                current_year = y
                f.write(f"## {current_year}年\n\n")
                current_month = "" # 强制跨月逻辑触发
                
            # 跨月时，生成三级标题和表头
            if m != current_month:
                current_month = m
                f.write(f"### {current_month}月\n\n")
                f.write("| 日期 | 题目 | 难度 | 附件 |\n")
                f.write("| :--- | :--- | :--- | :--- |\n")
                
            # 写入题目数据行
            f.write(records[d] + "\n")
            
    print(f"🎉 目录已按年月分类重构完毕，最新题目已置顶，历史链接修复完成。")

if __name__ == "__main__":
    asyncio.run(run_task())