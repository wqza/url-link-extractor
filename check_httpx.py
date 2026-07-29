"""用 httpx 直接拉取页面，检查 HTML 源码中是否含匹配链接。"""
import httpx

url = "https://support.huaweicloud.com/price-codeartsagent/codeartsagent_billing_0001.html"
resp = httpx.get(url, timeout=15, follow_redirects=True, trust_env=False)
print(f"状态码：{resp.status_code}")
print(f"Content-Type：{resp.headers.get('content-type')}")
print(f"HTML 长度：{len(resp.text)}")

# 检查 HTML 源码中是否含 price-codeartsagent 链接
html = resp.text
count = html.count("price-codeartsagent/")
print(f"HTML 源码中 price-codeartsagent/ 出现次数：{count}")

# 检查是否含 .html 链接
import re
html_links = re.findall(r'href="([^"]*price-codeartsagent/[^"]*\.html)"', html)
print(f"HTML 源码中匹配的 .html 链接数：{len(html_links)}")
for link in html_links[:10]:
    print(f"  {link}")