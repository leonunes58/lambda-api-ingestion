"""Dublês de teste compartilhados: substituem o S3 e o HTTP."""

from __future__ import annotations

import gzip
import io
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

FIXED_NOW = datetime(2026, 10, 17, 12, 0, 0, tzinfo=timezone.utc)
URLOPEN_TARGET = "core.base_ingestion.urllib.request.urlopen"


class FakeS3Client:
    """Substitui o cliente boto3: guarda as chamadas a put_object."""

    def __init__(self) -> None:
        self.calls: List[Dict[str, Any]] = []

    def put_object(self, **kwargs: Any) -> None:
        self.calls.append(kwargs)


class FakeResponse(io.BytesIO):
    """Resposta HTTP mínima: corpo em bytes + headers (BytesIO já é context manager)."""

    def __init__(self, body: bytes, headers: Optional[Dict[str, str]] = None) -> None:
        super().__init__(body)
        self.headers = headers or {}


def fake_urlopen(payload: Any, gzipped: bool = False):
    """Cria um substituto de urllib.request.urlopen que devolve `payload` como JSON."""
    body = json.dumps(payload).encode("utf-8")
    headers = {}
    if gzipped:
        body, headers = gzip.compress(body), {"Content-Encoding": "gzip"}

    def _urlopen(request, timeout):  # mesma assinatura usada em BaseIngestion._request
        return FakeResponse(body, headers)

    return _urlopen
