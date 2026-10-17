"""Entrypoint da Lambda: lê a config da env var, instancia a ingestão e chama run()."""

from __future__ import annotations

import json
import os
from typing import Any, Dict

from core.log import get_logger

# No zip, o conteúdo de ingestions/<nome>/ é empacotado como o pacote `ingestion/`.
from ingestion.ingestion import Ingestion

logger = get_logger("handler")


def load_config() -> Dict[str, Any]:
    """Lê a configuração da ingestão enviada pelo Terraform em INGESTION_CONFIG."""
    raw = os.environ.get("INGESTION_CONFIG")
    if not raw:
        raise RuntimeError("variável de ambiente INGESTION_CONFIG não definida")
    return json.loads(raw)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Função chamada pela Lambda (EventBridge Scheduler ou invocação manual)."""
    config = load_config()
    try:
        return Ingestion(config).run()
    except Exception:
        # Loga com stack trace e relança: a invocação fica marcada como erro na Lambda.
        logger.exception("ingestao falhou", extra={"ingestion": config.get("name")})
        raise
