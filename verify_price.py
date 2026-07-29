from url_link_extractor import extract, ExtractRequest

result = extract(ExtractRequest(
    url_prefix="https://support.huaweicloud.com/price-codeartsagent/",
    entry_urls=["https://support.huaweicloud.com/price-codeartsagent/"],
    work_dir="./output",
    concurrency=10,
))

print(f"任务 ID：{result.task_id}")
print(f"统计：total={result.statistics.total}  success={result.statistics.success}  "
      f"no_title={result.statistics.no_title}  failed={result.statistics.failed}")
print(f"导出路径：{result.export_path}")
print(f"异常报告数：{len(result.errors)}")
print()

for i, record in enumerate(result.result_set):
    title_display = record.title or "(缺失)"
    print(f"[{record.status.value:8s}] {record.url}")
    print(f"            标题：{title_display}")

if result.errors:
    print(f"\n异常报告（前 20 条）：")
    for err in result.errors[:20]:
        print(f"  [{err.error_code.value}] {err.url}  |  {err.detail[:80] if err.detail else ''}")