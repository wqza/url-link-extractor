from url_link_extractor import extract, ExtractRequest

result = extract(ExtractRequest(
    url_prefix="https://support.huaweicloud.com/zh-cn/usermanual-cli/",
    work_dir="./output",
))
print(f"total={result.statistics.total} success={result.statistics.success}")