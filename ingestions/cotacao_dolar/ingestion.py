"""Ingestão da cotação USD/BRL (AwesomeAPI)."""

from __future__ import annotations

from typing import Any, List

from core.base_ingestion import BaseIngestion, Record


class Ingestion(BaseIngestion):
    """A API responde `{"USDBRL": {...}}`; o registro útil está dentro da chave."""

    def extract_records(self, page: Any) -> List[Record]:
        return [page["USDBRL"]]
