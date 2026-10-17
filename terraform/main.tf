locals {
  repo_root       = "${path.module}/.."
  ingestions_root = "${local.repo_root}/ingestions"

  # ["cotacao_dolar/config.yml", "ibge_ipca/config.yml", ...]
  config_files = fileset(local.ingestions_root, "*/config.yml")

  # Map indexado pelo nome da pasta:
  # { cotacao_dolar = { name = "...", api = {...}, ... }, ibge_ipca = {...} }
  ingestions = {
    for f in local.config_files :
    dirname(f) => yamldecode(file("${local.ingestions_root}/${f}"))
  }
}

# Uma instância do module por config.yml. Novo YAML = nova Lambda no próximo apply.
module "ingestion" {
  source   = "./modules/api_ingestion"
  for_each = local.ingestions

  name        = each.key # a pasta é a fonte da verdade (o module a usa para achar o código)
  description = try(each.value.description, "")
  api         = each.value.api
  schedule    = each.value.schedule
  timeout     = try(each.value.timeout, 30)
  memory      = try(each.value.memory, 128)
  source_root = local.repo_root

  # O bucket não vem do YAML: é o bucket raw criado em storage.tf.
  destination = merge(each.value.destination, { bucket = aws_s3_bucket.raw.bucket })
}

# Aviso (não bloqueia) se o `name` do YAML divergir do nome da pasta.
check "name_igual_a_pasta" {
  assert {
    condition = alltrue([for k, v in local.ingestions : try(v.name, k) == k])
    error_message = "name diferente da pasta em: ${join(", ", [
      for k, v in local.ingestions : k if try(v.name, k) != k
    ])}"
  }
}
