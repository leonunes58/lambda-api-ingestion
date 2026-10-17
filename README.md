# lambda-api-ingestion

Padrão de Lambdas de ingestão de APIs **dirigido por configuração**, com infraestrutura em Terraform.

> 🚧 Em construção: Fase 1 (MVP).

## Ideia

- Cada ingestão mora em `ingestions/<nome>/`, com um `config.yml` (configuração) e um `ingestion.py` (lógica específica da API).
- O `core/` traz o fluxo padrão (padrão Template Method): `BaseIngestion.run()` é fixo e chama ganchos que podem ser sobrescritos (`authenticate`, `fetch_pages`, `extract_records`, `validate`, `transform`). A gravação no S3 é sempre feita pelo core.
- O Terraform lê todos os `ingestions/*/config.yml` e cria uma Lambda por ingestão (module + `for_each`). **Novo YAML = nova Lambda no próximo `apply`.**

**Regra de design:** escolha entre opções conhecidas vai no YAML; lógica vai no `ingestion.py`.

## Estrutura

```
lambda-api-ingestion/
├── core/                  # fluxo comum (BaseIngestion + gravação no S3)
├── handler.py             # entrypoint da Lambda
├── ingestions/            # uma pasta por ingestão (config.yml + ingestion.py)
├── terraform/             # raiz + module api_ingestion
└── tests/                 # pytest
```
