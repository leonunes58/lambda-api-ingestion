"""Ingestão de agregados do IBGE (API SIDRA v3)."""

from __future__ import annotations

from typing import Any, List, Optional

from core.base_ingestion import BaseIngestion, Record

# O IBGE usa símbolos no lugar de valores ausentes ou sigilosos.
SIMBOLOS_SEM_VALOR = {"-", "..", "...", "X"}


class Ingestion(BaseIngestion):
    """Achata variável > resultado > série > período em um registro por linha."""

    def extract_records(self, page: Any) -> List[Record]:
        records: List[Record] = []
        for variavel in page:
            for resultado in variavel["resultados"]:
                for serie in resultado["series"]:
                    localidade = serie["localidade"]
                    for periodo, valor in serie["serie"].items():
                        records.append({
                            "variavel_id": variavel["id"],
                            "variavel": variavel["variavel"],
                            "unidade": variavel["unidade"],
                            "classificacoes": resultado["classificacoes"],
                            "localidade_id": localidade["id"],
                            "localidade": localidade["nome"],
                            "nivel": localidade["nivel"]["id"],
                            "periodo": periodo,
                            "valor": valor,
                        })
        return records

    def transform(self, records: List[Record]) -> List[Record]:
            return [{**r, "valor": self._to_float(r["valor"])} for r in records]

    @staticmethod
    def _to_float(valor: Optional[str]) -> Optional[float]:
        if valor is None or valor in SIMBOLOS_SEM_VALOR:
            return None
        return float(valor)