"""ExportFileSpec 结果导出文件常量值对象（spec.md §6.5）。

固化 result.xlsx 全部约束：
- file_name 固定 "result.xlsx"
- column_count 固定 2
- column_1_name 固定 "URL 完整链接"
- column_2_name 固定 "页面标题"
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExportFileSpec:
    """结果导出文件规格（spec.md §6.5）。"""

    file_name: str = "result.xlsx"
    column_count: int = 2
    column_1_name: str = "URL 完整链接"
    column_2_name: str = "页面标题"


EXPORT_FILE_SPEC = ExportFileSpec()
"""模块级单例，全组件共享同一导出文件规格。"""
