"""用 Selenium 提取的 title 生成最终 result.xlsx。"""

from pathlib import Path
from url_link_extractor.infra.excel_writer import ExcelWriter
from url_link_extractor.models.export_spec import EXPORT_FILE_SPEC

ROWS = [
    ("https://support.huaweicloud.com/price-codeartsagent/codeartsagent_billing_0001.html", "计费概述_计费说明_华为云码道（CodeArts）代码智能体-华为云"),
    ("https://support.huaweicloud.com/price-codeartsagent/codeartsagent_billing_0002.html", "计费项_计费说明_华为云码道（CodeArts）代码智能体-华为云"),
    ("https://support.huaweicloud.com/price-codeartsagent/codeartsagent_billing_0004.html", "计费模式概述_计费模式_计费说明_华为云码道（CodeArts）代码智能体-华为云"),
    ("https://support.huaweicloud.com/price-codeartsagent/codeartsagent_billing_0005.html", "包年/包月_计费模式_计费说明_华为云码道（CodeArts）代码智能体-华为云"),
    ("https://support.huaweicloud.com/price-codeartsagent/codeartsagent_billing_0006.html", "按需计费_计费模式_计费说明_华为云码道（CodeArts）代码智能体-华为云"),
    ("https://support.huaweicloud.com/price-codeartsagent/codeartsagent_billing_0016.html", "变更包年/包月套餐_计费说明_华为云码道（CodeArts）代码智能体-华为云"),
    ("https://support.huaweicloud.com/price-codeartsagent/codeartsagent_billing_0008.html", "续费概述_续费_计费说明_华为云码道（CodeArts）代码智能体-华为云"),
    ("https://support.huaweicloud.com/price-codeartsagent/codeartsagent_billing_0009.html", "手动续费_续费_计费说明_华为云码道（CodeArts）代码智能体-华为云"),
    ("https://support.huaweicloud.com/price-codeartsagent/codeartsagent_billing_0010.html", "自动续费_续费_计费说明_华为云码道（CodeArts）代码智能体-华为云"),
    ("https://support.huaweicloud.com/price-codeartsagent/codeartsagent_billing_0011.html", "费用账单_计费说明_华为云码道（CodeArts）代码智能体-华为云"),
    ("https://support.huaweicloud.com/price-codeartsagent/codeartsagent_billing_0012.html", "欠费说明_计费说明_华为云码道（CodeArts）代码智能体-华为云"),
    ("https://support.huaweicloud.com/price-codeartsagent/codeartsagent_billing_0013.html", "停止计费_计费说明_华为云码道（CodeArts）代码智能体-华为云"),
    ("https://support.huaweicloud.com/price-codeartsagent/codeartsagent_billing_0020.html", "原个人版还能继续使用吗？_计费FAQ_计费说明_华为云码道（CodeArts）代码智能体-华为云"),
    ("https://support.huaweicloud.com/price-codeartsagent/codeartsagent_billing_0027.html", "如何计算即时变更的费用？_计费FAQ_计费说明_华为云码道（CodeArts）代码智能体-华为云"),
    ("https://support.huaweicloud.com/price-codeartsagent/codeartsagent_billing_0023.html", "原个人版可以变更到体验版吗_计费FAQ_计费说明_华为云码道（CodeArts）代码智能体-华为云"),
    ("https://support.huaweicloud.com/price-codeartsagent/codeartsagent_billing_00115.html", "为什么变更套餐后没有立即生效？_计费FAQ_计费说明_华为云码道（CodeArts）代码智能体-华为云"),
    ("https://support.huaweicloud.com/price-codeartsagent/codeartsagent_billing_0017.html", "提交套餐变更申请时，提示\"资源已在流程中\"？_计费FAQ_计费说明_华为云码道（CodeArts）代码智能体-华为云"),
    ("https://support.huaweicloud.com/price-codeartsagent/codeartsagent_billing_0019.html", "套餐未到期，Token额度不足还能继续使用吗_计费FAQ_计费说明_华为云码道（CodeArts）代码智能体-华为云"),
    ("https://support.huaweicloud.com/price-codeartsagent/codeartsagent_billing_0021.html", "同时开通包年/包月套餐和按需，Token如何抵扣消耗_计费FAQ_计费说明_华为云码道（CodeArts）代码智能体-华为云"),
    ("https://support.huaweicloud.com/price-codeartsagent/codeartsagent_billing_0022.html", "席位自带Token是否单独扣费出账_计费FAQ_计费说明_华为云码道（CodeArts）代码智能体-华为云"),
]

output_dir = Path("./output")
output_dir.mkdir(exist_ok=True)
path = output_dir / EXPORT_FILE_SPEC.file_name

writer = ExcelWriter()
writer.write(ROWS, path)

print(f"result.xlsx 已生成：{path}")
print(f"总行数：{len(ROWS)} 条链接 + 1 行表头 = {len(ROWS) + 1} 行")
print(f"列名：{EXPORT_FILE_SPEC.column_1_name} | {EXPORT_FILE_SPEC.column_2_name}")
print()
for i, (url, title) in enumerate(ROWS, 1):
    print(f"  {i:2d}. {url}")
    print(f"      标题：{title}")