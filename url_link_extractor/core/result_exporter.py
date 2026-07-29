"""ResultExporter result.xlsx 导出（spec.md §5.3.1/§5.3.3、设计 §2.2.2-5）。

约束：
- 文件名固定 result.xlsx
- 标题缺失写空字符串
- 行顺序与 result_set 一致
- 导出失败为软失败，返回 EXPORT_WRITE_ERROR，不抛异常
"""

from __future__ import annotations

from pathlib import Path

from ..infra.excel_writer import ExcelWriter
from ..models.enums import ErrorCode
from ..models.export_spec import EXPORT_FILE_SPEC
from ..models.result import ErrorReportItem, ExportOutcome, LinkTitleRecord


class ExcelResultExporter:
    """Excel 结果导出器。"""

    def __init__(self, writer: ExcelWriter | None = None) -> None:
        self._writer = writer or ExcelWriter()

    def export(
        self, result_set: list[LinkTitleRecord], work_dir: Path | str | None = None
    ) -> ExportOutcome:
        """导出结果集到 result.xlsx。

        - 成功返回 ExportOutcome(file_path=..., error=None)
        - 失败返回 ExportOutcome(file_path=None, error=EXPORT_WRITE_ERROR)，不抛异常
        """
        work_dir_path = Path(work_dir) if work_dir is not None else Path.cwd()
        path = work_dir_path / EXPORT_FILE_SPEC.file_name

        rows = [(record.url, record.title or "") for record in result_set]

        try:
            self._writer.write(rows, path)
            return ExportOutcome(file_path=str(path), error=None)
        except Exception as exc:
            return ExportOutcome(
                file_path=None,
                error=ErrorReportItem(
                    url=str(path),
                    error_code=ErrorCode.EXPORT_WRITE_ERROR,
                    detail=str(exc),
                ),
            )
