import requests, html2text, datetime, asyncio, sys, os; from playwright.async_api import async_playwright

async def run_task():
    # 1. 抓取数据
    gql, hd = "https://leetcode.cn/graphql", {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type": "application/json",
        "Accept-Language": "zh-CN,zh;q=0.9"
    }
    try:
        s_q = {"query": "query { todayRecord { question { questionTitleSlug } } }"}
        slug = requests.post(gql, json=s_q, headers=hd).json()['data']['todayRecord'][0]['question']['questionTitleSlug']
        d_q = {"query": "query q($s:String!){question(titleSlug:$s){questionFrontendId translatedTitle translatedContent difficulty}}", "variables": {"s": slug}}
        res = requests.post(gql, json=d_q, headers=hd).json()['data']['question']
    except Exception as e: print(f"❌ 数据抓取错误: {e}"); sys.exit(1)

    # 创建文件夹逻辑
    today = datetime.date.today().strftime("%Y-%m-%d")
    folder_path = today
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # 定义文件路径 (全部放在文件夹内)
    p_n, i_n, m_n = f"{today}.pdf", f"{today}.png", f"{today}.md"
    p_path, i_path, m_path = os.path.join(folder_path, p_n), os.path.join(folder_path, i_n), os.path.join(folder_path, m_n)
    
    # 2. 生成极简 PDF 和 图片
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        style = """<style>
            body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;padding:30px;line-height:1.5;color:#1a1a1a;background:white;}
            h1{font-size:22px;margin-bottom:8px;font-weight:600;color:#000;border-bottom:1px solid #ddd;padding-bottom:8px;}
            .meta{font-size:13px;color:#666;margin-bottom:20px;}
            pre{background:#f8f8f8;padding:12px;border-radius:4px;border:1px solid #eee;overflow-x:auto;font-size:13px;}
            code{font-family:Menlo,Monaco,Consolas,monospace;font-size:13px;background:#f3f3f3;padding:2px 4px;border-radius:3px;}
            img{max-width:100%;height:auto;margin:10px 0;}
            table{border-collapse:collapse;width:100%;margin:15px 0;font-size:14px;}
            th,td{border:1px solid #eee;padding:10px;text-align:left;}
            th{background:#fafafa;font-weight:600;}
        </style>"""
        html = f"<html><head><meta charset='UTF-8'>{style}</head><body><h1>{res['questionFrontendId']}. {res['translatedTitle']}</h1><div class='meta'>难度: <b>{res['difficulty']}</b></div><div class='content'>{res['translatedContent']}</div></body></html>"
        
        await page.set_content(html)
        await asyncio.sleep(1) 
        # 写入文件到指定文件夹
        await page.pdf(path=p_path, format="A4", margin={"top":"1.2cm","bottom":"1.2cm","left":"1.2cm","right":"1.2cm"})
        await page.screenshot(path=i_path, full_page=True)
        await browser.close()

    # 3. 生成 Markdown 模板
    md_tpl = f"""# [{res['questionFrontendId']}. {res['translatedTitle']}](https://leetcode.cn/problems/{slug}/)

**{today}**

**题目难度：{res['difficulty']}** 

![题目描述](./{i_n})

---

## 思路 

---

## 代码实现 (C++)
```cpp

```

- 时间复杂度: $O()$
- 空间复杂度: $O()$

---

"""
    with open(m_path, "w", encoding="utf-8") as f: f.write(md_tpl)

    # 4. 更新自动目录 (README.md)
    readme_path = "README.md"
    new_entry = f"| {today} | [{res['questionFrontendId']}. {res['translatedTitle']}](./{folder_path}/{m_n}) | {res['difficulty']} | [PDF](./{folder_path}/{p_n}) |\n"
    
    if not os.path.exists(readme_path):
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write("# LeetCode 每日一题记录\n\n| 日期 | 题目 | 难度 | 附件 |\n| :--- | :--- | :--- | :--- |\n")
    
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.readlines()
    
    # 检查是否已经存在该日期的记录，不存在则追加
    if not any(today in line for line in content):
        with open(readme_path, "a", encoding="utf-8") as f:
            f.write(new_entry)

    print(f"🎉 成功! 所有文件已放入目录: {folder_path}/ 并更新了目录 README.md")

if __name__ == "__main__":
    asyncio.run(run_task())