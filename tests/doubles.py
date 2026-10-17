"""Dublês de teste compartilhados: substituem o S3 e o HTTP."""

from __future__ import annotations

import io
import json
from datetime import datetime, timezone
from typing import Any, Dict, List

FIXED_NOW = datetime(2026, 10, 17, 12, 0, 0, tzinfo=timezone.utc)
URLOPEN_TARGET = "core.base_ingestion.urllib.request.urlopen"


class FakeS3Client:
    """Substitui o cliente boto3: guarda as chamadas a put_object."""

    def __init__(self) -> None:
        self.calls: List[Dict[str, Any]] = []

    def put_object(self, **kwargs: Any) -> None:
        self.calls.append(kwargs)


def fake_urlopen(payload: Any):
    """Cria um substituto de urllib.request.urlopen que devolve `payload` como JSON."""

    def _urlopen(request, timeout):  # mesma assinatura usada em BaseIngestion._request
        return io.BytesIO(json.dumps(payload).encode("utf-8"))  # BytesIO já é context manager

    return _urlopen
