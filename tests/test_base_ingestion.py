"""Testes do fluxo BaseIngestion.run(), da montagem da key e da ingestão cotacao_dolar.

HTTP e S3 são substituídos por dublês: nenhum teste acessa a rede ou a AWS.
"""

from __future__ import annotations

import io
import json
from datetime import datetime, timezone
from typing import Any, Dict, List
from unittest.mock import patch

import pytest

from core.base_ingestion import BaseIngestion, EmptyResponseError, ValidationError
from core.s3_writer import S3Writer, build_key
from ingestions.cotacao_dolar.ingestion import Ingestion as CotacaoDolar

FIXED_NOW = datetime(2026, 10, 17, 12, 0, 0, tzinfo=timezone.utc)


# ----------------------------------------------------------------------
# Dublês e fixtures
# ----------------------------------------------------------------------
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


def make_config(partition: str = "anomesdia", **destination: Any) -> Dict[str, Any]:
    return {
        "name": "teste",
        "api": {"url": "https://api.exemplo.com/dados", "method": "GET"},
        "destination": {"bucket": "bucket-teste", "partition": partition, **destination},
    }


@pytest.fixture
def s3() -> FakeS3Client:
    return FakeS3Client()


def make_writer(config: Dict[str, Any], s3: FakeS3Client) -> S3Writer:
    dest = config["destination"]
    return S3Writer(
        bucket=dest["bucket"],
        name=config["name"],
        partition=dest["partition"],
        prefix=dest.get("prefix"),
        client=s3,
        clock=lambda: FIXED_NOW,
    )


def run_with(ingestion_cls, payload: Any, s3: FakeS3Client, config: Dict[str, Any] = None):
    config = config or make_config()
    ingestion = ingestion_cls(config, writer=make_writer(config, s3))
    with patch("core.base_ingestion.urllib.request.urlopen", fake_urlopen(payload)):
        return ingestion.run()


# ----------------------------------------------------------------------
# Fluxo do run()
# ----------------------------------------------------------------------
def test_run_grava_registros_em_json_lines(s3):
    payload = [{"id": 1}, {"id": 2}]

    summary = run_with(BaseIngestion, payload, s3)

    assert summary == {
        "ingestion": "teste",
        "records": 2,
        "s3_key": "teste/anomesdia=20261017/teste_20261017.json",
    }
    assert len(s3.calls) == 1
    call = s3.calls[0]
    assert call["Bucket"] == "bucket-teste"
    assert call["Key"] == summary["s3_key"]
    lines = call["Body"].decode("utf-8").splitlines()
    assert [json.loads(line) for line in lines] == payload


def test_run_objeto_unico_vira_lista_de_um_registro(s3):
    summary = run_with(BaseIngestion, {"id": 1}, s3)

    assert summary["records"] == 1


def test_run_chama_ganchos_na_ordem(s3):
    chamadas: List[str] = []

    class Rastreada(BaseIngestion):
        def authenticate(self):
            chamadas.append("authenticate")

        def fetch_pages(self):
            chamadas.append("fetch_pages")
            yield from super().fetch_pages()

        def extract_records(self, page):
            chamadas.append("extract_records")
            return super().extract_records(page)

        def validate(self, records):
            chamadas.append("validate")

        def transform(self, records):
            chamadas.append("transform")
            return records

    run_with(Rastreada, [{"id": 1}], s3)

    assert chamadas == ["authenticate", "fetch_pages", "extract_records", "validate", "transform"]


def test_transform_altera_o_que_e_gravado(s3):
    class ComTransform(BaseIngestion):
        def transform(self, records):
            return [{**r, "origem": "api"} for r in records]

    run_with(ComTransform, [{"id": 1}], s3)

    gravado = json.loads(s3.calls[0]["Body"])
    assert gravado == {"id": 1, "origem": "api"}


def test_resposta_vazia_levanta_erro_e_nao_grava(s3):
    with pytest.raises(EmptyResponseError):
        run_with(BaseIngestion, [], s3)

    assert s3.calls == []


def test_validacao_falha_levanta_erro_e_nao_grava(s3):
    with pytest.raises(ValidationError):
        run_with(BaseIngestion, [{"id": 1}, {}], s3)  # registro vazio é inválido

    assert s3.calls == []


def test_validate_sobrescrito_bloqueia_gravacao(s3):
    class ExigeId(BaseIngestion):
        def validate(self, records):
            if any("id" not in r for r in records):
                raise ValidationError("registro sem id")

    with pytest.raises(ValidationError, match="sem id"):
        run_with(ExigeId, [{"nome": "x"}], s3)

    assert s3.calls == []


# ----------------------------------------------------------------------
# Montagem da key no S3
# ----------------------------------------------------------------------
@pytest.mark.parametrize(
    "prefix, partition, esperado",
    [
        ("cotacao_dolar", "anomesdia", "cotacao_dolar/anomesdia=20261017/cotacao_dolar_20261017.json"),
        ("cotacao_dolar", "anomes", "cotacao_dolar/anomes=202610/cotacao_dolar_202610.json"),
        ("raw/cambio/", "anomes", "raw/cambio/anomes=202610/cotacao_dolar_202610.json"),
    ],
)
def test_build_key(prefix, partition, esperado):
    assert build_key(prefix, "cotacao_dolar", partition, FIXED_NOW) == esperado


def test_build_key_particao_invalida():
    with pytest.raises(ValueError, match="partition inválida"):
        build_key("x", "x", "ano", FIXED_NOW)


def test_prefix_padrao_e_o_name(s3):
    summary = run_with(BaseIngestion, [{"id": 1}], s3, make_config(partition="anomes"))

    assert summary["s3_key"] == "teste/anomes=202610/teste_202610.json"


def test_prefix_customizado(s3):
    config = make_config(prefix="raw/outro")

    summary = run_with(BaseIngestion, [{"id": 1}], s3, config)

    assert summary["s3_key"].startswith("raw/outro/anomesdia=20261017/")


# ----------------------------------------------------------------------
# Ingestão de exemplo: cotacao_dolar
# ----------------------------------------------------------------------
RESPOSTA_AWESOMEAPI = {
    "USDBRL": {
        "code": "USD",
        "codein": "BRL",
        "bid": "5.0627",
        "ask": "5.0631",
        "create_date": "2026-10-16 18:01:12",
    }
}


def test_cotacao_extract_records_desembrulha_usdbrl():
    ingestion = CotacaoDolar(make_config(), writer=make_writer(make_config(), FakeS3Client()))

    assert ingestion.extract_records(RESPOSTA_AWESOMEAPI) == [RESPOSTA_AWESOMEAPI["USDBRL"]]


def test_cotacao_run_grava_apenas_o_registro_interno(s3):
    run_with(CotacaoDolar, RESPOSTA_AWESOMEAPI, s3)

    gravado = json.loads(s3.calls[0]["Body"])
    assert gravado["code"] == "USD"
    assert "USDBRL" not in gravado


def test_cotacao_resposta_sem_chave_esperada_falha(s3):
    with pytest.raises(KeyError):
        run_with(CotacaoDolar, {"EURBRL": {}}, s3)

    assert s3.calls == []
