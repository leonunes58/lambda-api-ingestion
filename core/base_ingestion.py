"""Classe base das ingestões, no padrão Template Method.

`run()` define o fluxo fixo; as subclasses (cada `ingestion.py`) sobrescrevem
apenas os ganchos de que precisam. A gravação no S3 é sempre feita aqui.
"""

from __future__ import annotations

import json
import urllib.request
from typing import Any, Dict, Iterable, List, Optional

from core.log import get_logger
from core.s3_writer import S3Writer

Record = Dict[str, Any]

HTTP_TIMEOUT_SECONDS = 10
USER_AGENT = "lambda-api-ingestion/0.1"


class IngestionError(Exception):
    """Erro base das ingestões."""


class EmptyResponseError(IngestionError):
    """A API não retornou nenhum registro."""


class ValidationError(IngestionError):
    """Os registros não passaram na validação."""


class BaseIngestion:
    """Fluxo padrão: authenticate -> fetch_pages -> extract_records -> validate -> transform -> S3."""

    def __init__(self, config: Dict[str, Any], writer: Optional[S3Writer] = None) -> None:
        self.config = config
        self.name: str = config["name"]
        self.api: Dict[str, Any] = config["api"]
        destination = config["destination"]
        self.writer = writer or S3Writer(
            bucket=destination["bucket"],
            name=self.name,
            partition=destination["partition"],
            prefix=destination.get("prefix"),
        )
        self.logger = get_logger(f"ingestion.{self.name}")
        self.headers: Dict[str, str] = {"Accept": "application/json", "User-Agent": USER_AGENT}

    # ------------------------------------------------------------------
    # Método template: NÃO sobrescrever.
    # ------------------------------------------------------------------
    def run(self) -> Dict[str, Any]:
        """Executa a ingestão completa e retorna um resumo."""
        self.logger.info("ingestao iniciada", extra={"ingestion": self.name})

        self.authenticate()

        records: List[Record] = []
        for page in self.fetch_pages():
            records.extend(self.extract_records(page))

        # Regra fixa: sem registros, nada é gravado.
        if not records:
            raise EmptyResponseError(f"[{self.name}] a API não retornou registros")

        self.validate(records)
        records = self.transform(records)
        key = self.writer.write(records)

        summary = {"ingestion": self.name, "records": len(records), "s3_key": key}
        self.logger.info("ingestao concluida", extra=summary)
        return summary

    # ------------------------------------------------------------------
    # Ganchos: implementações padrão simples (Fase 1).
    # ------------------------------------------------------------------
    def authenticate(self) -> None:
        """Prepara credenciais (ex.: preenche `self.headers`). Padrão: sem autenticação."""

    def fetch_pages(self) -> Iterable[Any]:
        """Gera as páginas da API. Padrão: uma única requisição, sem paginação."""
        yield self._request(self.api["url"])

    def extract_records(self, page: Any) -> List[Record]:
        """Extrai a lista de registros de uma página. Padrão: lista vira lista, objeto vira [objeto]."""
        if isinstance(page, list):
            return page
        if isinstance(page, dict):
            return [page]
        raise ValidationError(f"[{self.name}] formato de página inesperado: {type(page).__name__}")

    def validate(self, records: List[Record]) -> None:
        """Valida os registros. Padrão: todo registro deve ser um objeto JSON não vazio."""
        for i, record in enumerate(records):
            if not isinstance(record, dict) or not record:
                raise ValidationError(f"[{self.name}] registro {i} inválido: {record!r}")

    def transform(self, records: List[Record]) -> List[Record]:
        """Transforma os registros antes da gravação. Padrão: sem alteração."""
        return records

    # ------------------------------------------------------------------
    # Utilitários para as subclasses.
    # ------------------------------------------------------------------
    def _request(self, url: str) -> Any:
        """Faz a requisição HTTP e devolve o corpo já decodificado de JSON."""
        method = self.api.get("method", "GET").upper()
        request = urllib.request.Request(url, method=method, headers=self.headers)
        self.logger.info("requisicao http", extra={"method": method, "url": url})
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))
