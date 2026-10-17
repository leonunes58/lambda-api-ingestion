"""Gravação dos registros no S3, particionada por data (estilo Hive)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from core.log import get_logger

logger = get_logger(__name__)


def build_key(prefix: str, now: datetime) -> str:
    """Monta `<prefix>/ano=YYYY/mes=MM/dia=DD/<timestamp_utc>.json`."""
    return (
        f"{prefix.strip('/')}/"
        f"ano={now:%Y}/mes={now:%m}/dia={now:%d}/"
        f"{now:%Y%m%dT%H%M%SZ}.json"
    )


def to_json_lines(records: List[Dict[str, Any]]) -> bytes:
    """Serializa um registro por linha (JSON Lines), formato que Athena/Glue leem direto."""
    return "\n".join(json.dumps(r, ensure_ascii=False) for r in records).encode("utf-8")


class S3Writer:
    """Grava uma lista de registros como um único objeto JSON no S3."""

    def __init__(
        self,
        bucket: str,
        prefix: str,
        client: Optional[Any] = None,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> None:
        self.bucket = bucket
        self.prefix = prefix
        self._client = client
        self._clock = clock

    @property
    def client(self) -> Any:
        # Import tardio: boto3 já existe no runtime da Lambda, mas não é exigido nos testes.
        if self._client is None:
            import boto3

            self._client = boto3.client("s3")
        return self._client

    def write(self, records: List[Dict[str, Any]]) -> str:
        """Grava os registros e retorna a key do objeto criado."""
        key = build_key(self.prefix, self._clock())
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=to_json_lines(records),
            ContentType="application/json",
        )
        logger.info("objeto gravado no S3", extra={"bucket": self.bucket, "key": key, "records": len(records)})
        return key
