# Faz a AWS confiar nos tokens que o GitHub Actions emite para cada execução.
# Com isso o pipeline recebe credenciais temporárias (1h) via sts:AssumeRoleWithWebIdentity,
# sem nenhuma chave de acesso guardada nos secrets do GitHub.
# Só pode existir um provider por URL em cada conta.
resource "aws_iam_openid_connect_provider" "github" {
  url            = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]
}

data "aws_caller_identity" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id
  region     = "us-east-1"

  # Nomes usados pela raiz principal (terraform/). As policies só liberam estes recursos.
  resource_prefix = "api-ingestion-"
  state_bucket    = "leo-tfstate-${local.account_id}"
  state_prefix    = "lambda-api-ingestion"
  raw_bucket      = "lambda-api-ingestion-raw-${local.account_id}"

  arn = {
    state_bucket  = "arn:aws:s3:::${local.state_bucket}"
    state_objects = "arn:aws:s3:::${local.state_bucket}/${local.state_prefix}/*"
    state_locks   = "arn:aws:s3:::${local.state_bucket}/${local.state_prefix}/*.tflock"
    raw_bucket    = "arn:aws:s3:::${local.raw_bucket}"
    raw_objects   = "arn:aws:s3:::${local.raw_bucket}/*"
    functions     = "arn:aws:lambda:${local.region}:${local.account_id}:function:${local.resource_prefix}*"
    roles         = "arn:aws:iam::${local.account_id}:role/${local.resource_prefix}*"
    log_groups    = "arn:aws:logs:${local.region}:${local.account_id}:log-group:/aws/lambda/${local.resource_prefix}*"
    schedules     = "arn:aws:scheduler:${local.region}:${local.account_id}:schedule/default/${local.resource_prefix}*"
  }
}
