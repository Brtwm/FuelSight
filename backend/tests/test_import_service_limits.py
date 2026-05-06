from __future__ import annotations

import pytest

from app.core.config import Settings
from app.services.import_service import ImportService


def test_csv_import_rejects_more_than_configured_rows(tmp_path) -> None:  # noqa: ANN001
    service = ImportService(
        session=None,  # type: ignore[arg-type]
        settings=Settings(import_max_rows=1, model_artifacts_dir=str(tmp_path)),
    )
    file_bytes = (
        b"date,product_code,volume_liters,revenue_rub,avg_retail_price_rub\n"
        b"2026-03-01,AI_95,1000,58000,58\n"
        b"2026-03-02,AI_95,1100,63800,58\n"
    )

    with pytest.raises(ValueError, match="Файл содержит больше 1 строк"):
        service._read_rows(file_name="sales.csv", file_bytes=file_bytes)  # noqa: SLF001
