"""Testes de contrato: rodam automaticamente para CADA pasta em ingestions/.

Criou uma ingestão nova? Basta rodar `pytest`; ela entra aqui sozinha.

- contrato: config.yml válido e ingestion.py com a classe `Ingestion`
- amostra:  se existir `sample_response.json`, roda o run() completo offline
- ao vivo:  chama a API real (só com `pytest -m live`)
"""

from __future__ import annotations

import importlib
import json
import re
from pathlib import Path
from typing import Any, Dict
from unittest.mock import patch

import pytest
import yaml

from core.base_ingestion import BaseIngestion
from core.s3_writer import PARTITION_FORMATS, S3Writer, build_key
from tests.doubles import FIXED_NOW, URLOPEN_TARGET, FakeS3Client, fake_urlopen

INGESTIONS_DIR = Path(__file__).resolve().parent.parent / "ingestions"
INGESTIONS = sorted(p.parent.name for p in INGESTIONS_DIR.glob("*/config.yml"))

# Limites aceitos no config.yml (o module Terraform aplica as mesmas regras).
NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,39}$")
SCHEDULE_PATTERN = re.compile(r"^(cron|rate)\(.+\)$")
TIMEOUT_RANGE = (3, 300)
MEMORY_RANGE = (128, 1024)
FAKE_BUCKET = "bucket-teste"


def load_config(name: str) -> Dict[str, Any]:
    """Lê o config.yml e simula o que o Terraform faz: injeta o bucket de destino."""
    path = INGESTIONS_DIR / name / "config.yml"
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        pytest.fail(f"{path.relative_to(INGESTIONS_DIR.parent)} está vazio ou não é um mapa YAML (chave: valor)")
    config.setdefault("destination", {})["bucket"] = FAKE_BUCKET
    return config


def load_class(name: str):
    return importlib.import_module(f"ingestions.{name}.ingestion").Ingestion


def make_ingestion(name: str, s3: FakeS3Client) -> BaseIngestion:
    config = load_config(name)
    dest = config["destination"]
    writer = S3Writer(
        bucket=dest["bucket"],
        name=config["name"],
        partition=dest["partition"],
        prefix=dest.get("prefix"),
        client=s3,
        clock=lambda: FIXED_NOW,
    )
    return load_class(name)(config, writer=writer)


def expected_key(name: str) -> str:
    dest = load_config(name)["destination"]
    return build_key(dest.get("prefix") or name, name, dest["partition"], FIXED_NOW)


def test_existe_ao_menos_uma_ingestao():
    assert INGESTIONS, f"nenhum config.yml encontrado em {INGESTIONS_DIR}"


# ----------------------------------------------------------------------
# Contrato
# ----------------------------------------------------------------------
@pytest.mark.parametrize("name", INGESTIONS)
def test_contrato_config(name):
    config = load_config(name)
    erros = []

    if config.get("name") != name:
        erros.append(f"name deve ser igual ao nome da pasta ({name!r}), veio {config.get('name')!r}")
    if not NAME_PATTERN.match(name):
        erros.append("nome da pasta deve ser snake_case minúsculo com até 40 caracteres (vira módulo Python e nome da Lambda)")

    api = config.get("api") or {}
    if not str(api.get("url", "")).startswith("https://"):
        erros.append("api.url é obrigatório e deve começar com https://")
    if api.get("method", "GET").upper() != "GET":
        erros.append("api.method: na Fase 1 só GET é suportado")

    partition = config["destination"].get("partition")
    if partition not in PARTITION_FORMATS:
        erros.append(f"destination.partition deve ser um de {sorted(PARTITION_FORMATS)}, veio {partition!r}")

    if not SCHEDULE_PATTERN.match(str(config.get("schedule", ""))):
        erros.append("schedule é obrigatório no formato cron(...) ou rate(...)")

    for campo, (minimo, maximo) in (("timeout", TIMEOUT_RANGE), ("memory", MEMORY_RANGE)):
        valor = config.get(campo)
        if valor is not None and not (isinstance(valor, int) and minimo <= valor <= maximo):
            erros.append(f"{campo} deve ser inteiro entre {minimo} e {maximo}, veio {valor!r}")

    assert not erros, f"config.yml de {name!r} inválido:\n  - " + "\n  - ".join(erros)


@pytest.mark.parametrize("name", INGESTIONS)
def test_contrato_classe_ingestion(name):
    cls = load_class(name)

    assert issubclass(cls, BaseIngestion), "Ingestion deve herdar de core.base_ingestion.BaseIngestion"
    assert "run" not in vars(cls), "não sobrescreva run(); use os ganchos"
    make_ingestion(name, FakeS3Client())  # o construtor aceita o config.yml sem erro


# ----------------------------------------------------------------------
# Amostra (offline)
# ----------------------------------------------------------------------
@pytest.mark.parametrize("name", INGESTIONS)
def test_amostra_run_completo(name):
    sample = INGESTIONS_DIR / name / "sample_response.json"
    if not sample.exists():
        pytest.skip(f"{name}: crie sample_response.json para testar o fluxo offline")

    payload = json.loads(sample.read_text(encoding="utf-8"))
    s3 = FakeS3Client()
    with patch(URLOPEN_TARGET, fake_urlopen(payload)):
        summary = make_ingestion(name, s3).run()

    assert summary["records"] >= 1
    assert summary["s3_key"] == expected_key(name)
    assert len(s3.calls) == 1
    linhas = s3.calls[0]["Body"].decode("utf-8").splitlines()
    assert len(linhas) == summary["records"]
    assert all(isinstance(json.loads(linha), dict) for linha in linhas)


# ----------------------------------------------------------------------
# Ao vivo (rede real, S3 falso) — `pytest -m live`
# ----------------------------------------------------------------------
@pytest.mark.live
@pytest.mark.parametrize("name", INGESTIONS)
def test_ao_vivo_api_real(name):
    s3 = FakeS3Client()

    summary = make_ingestion(name, s3).run()

    assert summary["records"] >= 1
    assert len(s3.calls) == 1
