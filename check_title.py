"""检查 httpx 拿到的 HTML 中是否有 <title>。"""
import httpx
from selectolax.parser import HTMLParser

url = "https://support.huaweicloud.com/price-codeartsagent/codeartsagent_billing_0001.html"
resp = httpx.get(url, timeout=15, follow_redirects=True, trust_env=False)
html = resp.text
print(f"HTML 长度：{len(html)}")
print(f"前 500 字符：\n{html[:500]}")
print()

parser = HTMLParser(html)
titles = parser.css("title")
print(f"<title> 标签数：{len(titles)}")
for t in titles:
    print(f"  title: {t.text(strip=True)}")