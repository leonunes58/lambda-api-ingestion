"""Ingestão do dólar PTAX de venda (Banco Central, API SGS)."""

from __future__ import annotations

from datetime import datetime
from typing import List

from core.base_ingestion import BaseIngestion, Record


class Ingestion(BaseIngestion):
    """A API já responde uma lista de `{"data": "dd/mm/aaaa", "valor": "x.xxxx"}`.

    O extract_records padrão serve; só o transform é sobrescrito para tipar os campos.
    """

    def transform(self, records: List[Record]) -> List[Record]:
        return [
            {
                "data": datetime.strptime(r["data"], "%d/%m/%Y").date().isoformat(),
                "valor": float(r["valor"]),
            }
            for r in records
        ]
