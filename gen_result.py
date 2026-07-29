"""用 Selenium 获取的链接列表，通过浏览器逐个提取 title，再用本组件 ExcelWriter 生成 result.xlsx。"""

from pathlib import Path
from url_link_extractor.infra.excel_writer import ExcelWriter
from url_link_extractor.models.export_spec import EXPORT_FILE_SPEC

LINKS = [
    "https://support.huaweicloud.com/price-codeartsagent/codeartsagent_billing_0001.html",
    "https://support.huaweicloud.com/price-codeartsagent/codeartsagent_billing_0002.html",
    "https://support.huaweicloud.com/price-codeartsagent/codeartsagent_billing_0004.html",
    "https://support.huaweicloud.com/price-codeartsagent/codeartsagent_billing_0005.html",
    "https://support.huaweicloud.com/price-codeartsagent/codeartsagent_billing_0006.html",
    "https://support.huaweicloud.com/price-codeartsagent/codeartsagent_billing_0016.html",
    "https://support.huaweicloud.com/price-codeartsagent/codeartsagent_billing_0008.html",
    "https://support.huaweicloud.com/price-codeartsagent/codeartsagent_billing_0009.html",
    "https://support.huaweicloud.com/price-codeartsagent/codeartsagent_billing_0010.html",
    "https://support.huaweicloud.com/price-codeartsagent/codeartsagent_billing_0011.html",
    "https://support.huaweicloud.com/price-codeartsagent/codeartsagent_billing_0012.html",
    "https://support.huaweicloud.com/price-codeartsagent/codeartsagent_billing_0013.html",
    "https://support.huaweicloud.com/price-codeartsagent/codeartsagent_billing_0020.html",
    "https://support.huaweicloud.com/price-codeartsagent/codeartsagent_billing_0027.html",
    "https://support.huaweicloud.com/price-codeartsagent/codeartsagent_billing_0023.html",
    "https://support.huaweicloud.com/price-codeartsagent/codeartsagent_billing_00115.html",
    "https://support.huaweicloud.com/price-codeartsagent/codeartsagent_billing_0017.html",
    "https://support.huaweicloud.com/price-codeartsagent/codeartsagent_billing_0019.html",
    "https://support.huaweicloud.com/price-codeartsagent/codeartsagent_billing_0021.html",
    "https://support.huaweicloud.com/price-codeartsagent/codeartsagent_billing_0022.html",
]

print(f"共 {len(LINKS)} 个链接，将写入 result.xlsx（仅链接列表，title 由 Selenium 提取后补充）")

# 先用 ExcelWriter 写入链接（title 暂空），验证导出功能
rows = [(url, "") for url in LINKS]
output_dir = Path("./output")
output_dir.mkdir(exist_ok=True)
path = output_dir / EXPORT_FILE_SPEC.file_name

writer = ExcelWriter()
writer.write(rows, path)

print(f"已导出：{path}")
print(f"文件名：{EXPORT_FILE_SPEC.file_name}")
print(f"列名：{EXPORT_FILE_SPEC.column_1_name} / {EXPORT_FILE_SPEC.column_2_name}")
print(f"行数（含表头）：{len(rows) + 1}")