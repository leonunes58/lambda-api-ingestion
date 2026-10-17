"""Logging estruturado em JSON simples (uma linha por evento)."""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone

# Atributos que todo LogRecord já tem; o que sobrar veio do `extra=` e vira campo do JSON.
_RESERVED = set(vars(logging.makeLogRecord({}))) | {"message", "asctime"}


class JsonFormatter(logging.Formatter):
    """Formata cada registro como um objeto JSON."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        payload.update({k: v for k, v in vars(record).items() if k not in _RESERVED})
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def get_logger(name: str) -> logging.Logger:
    """Retorna um logger que escreve JSON no stdout (capturado pelo CloudWatch)."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        # Evita duplicar a linha no handler que o runtime da Lambda instala no root logger.
        logger.propagate = False
    return logger
