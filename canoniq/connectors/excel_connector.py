"""Excel source connector (placeholder; planned v0.2)."""

from __future__ import annotations

from canoniq.connectors._placeholder import PlaceholderConnector


class ExcelConnector(PlaceholderConnector):
    """Samples rows from an .xlsx workbook sheet. Requires ``canoniq[files]``. Planned: v0.2.

    Implementation plan: use openpyxl in read-only mode; ``list_entities`` returns
    sheet names; ``sample`` reads the header row + up to ``limit`` data rows.
    """

    source_type = "excel"
    target_version = "v0.2"
    extra = "files"
