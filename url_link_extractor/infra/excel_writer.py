"""ExcelWriter openpyxl 封装（spec.md §6.5、§5.3.1 规则 5-9）。

约束：
- 文件名固定 result.xlsx，表头取自 EXPORT_FILE_SPEC
- 两列：URL 完整链接 / 页面标题
- 覆盖写语义（不追加合并）
- 空结果集仅写表头
- 标题缺失写空字符串
- 工作目录不可写或磁盘不足抛 ExcelWriteError
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from openpyxl import Workbook

from ..exceptions import ExcelWriteError
from ..models.export_spec import EXPORT_FILE_SPEC


class ExcelWriter:
    """openpyxl Excel 写入器。"""

    def write(self, rows: list[tuple[str, str]], path: Path) -> None:
        """将 rows 写入 Excel 文件。

        - 首行表头取自 EXPORT_FILE_SPEC
        - 标题缺失应为空字符串（调用方负责转换）
        - 覆盖写：直接新建 Workbook 后 save
        """
        path = Path(path)
        work_dir = path.parent

        # 校验工作目录可写
        if not work_dir.exists():
            try:
                work_dir.mkdir(parents=True, exist_ok=True)
            except Exception as exc:
                raise ExcelWriteError(f"工作目录创建失败：{work_dir} ({exc})") from exc

        if not os.access(str(work_dir), os.W_OK):
            raise ExcelWriteError(f"工作目录不可写：{work_dir}")

        # 校验磁盘空间（至少 1MB 可用）
        try:
            usage = shutil.disk_usage(str(work_dir))
            if usage.free < 1024 * 1024:
                raise ExcelWriteError(f"磁盘空间不足：{work_dir} 剩余 {usage.free} 字节")
        except ExcelWriteError:
            raise
        except Exception:
            pass

        # 新建 Workbook，覆盖写语义
        wb = Workbook()
        ws = wb.active
        ws.title = "结果"
        ws.append([EXPORT_FILE_SPEC.column_1_name, EXPORT_FILE_SPEC.column_2_name])
        for url, title in rows:
            ws.append([url, title if title is not None else ""])

        try:
            wb.save(str(path))
        except Exception as exc:
            raise ExcelWriteError(f"Excel 保存失败：{path} ({exc})") from exc
