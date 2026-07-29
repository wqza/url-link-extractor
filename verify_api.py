"""方式三验证：Python API 实际调用。"""

from url_link_extractor import extract, ExtractRequest

print("=" * 60)
print("开始验证：URL 链接标题提取组件")
print("=" * 60)

request = ExtractRequest(
    url_prefix="https://support.huaweicloud.com/intl/zh-cn/usermanual-cli/",
    work_dir="./output",
)

print(f"请求前缀：{request.url_prefix}")
print("正在执行提取（需真实网络访问）...")
print()

result = extract(request)

print("=" * 60)
print(f"任务 ID：{result.task_id}")
print(f"统计：total={result.statistics.total}  success={result.statistics.success}  "
      f"no_title={result.statistics.no_title}  failed={result.statistics.failed}")
print(f"导出路径：{result.export_path}")
print(f"异常报告数：{len(result.errors)}")
print(f"告警数：{len(result.warnings)}")
print("=" * 60)

print("\n结果集（前 20 条）：")
for i, record in enumerate(result.result_set[:20]):
    title_display = record.title or "(缺失)"
    print(f"  [{record.status.value:8s}] {record.url}")
    print(f"            标题：{title_display}")

if len(result.result_set) > 20:
    print(f"  ... 还有 {len(result.result_set) - 20} 条")

if result.errors:
    print(f"\n异常报告（前 10 条）：")
    for err in result.errors[:10]:
        print(f"  [{err.error_code.value}] {err.url}")
        if err.detail:
            print(f"    detail: {err.detail[:100]}")

if result.warnings:
    print(f"\n告警：")
    for w in result.warnings:
        print(f"  [{w.error_code.value}] {w.detail}")

print("\n验证完成。")