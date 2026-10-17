locals {
  # cotacao_dolar -> api-ingestion-cotacao-dolar
  function_name = "api-ingestion-${replace(var.name, "_", "-")}"
  prefix        = coalesce(var.destination.prefix, var.name)
  ingestion_dir = "${var.source_root}/ingestions/${var.name}"

  # O que o handler.py lê em INGESTION_CONFIG.
  ingestion_config = {
    name        = var.name
    description = var.description
    api         = var.api
    destination = {
      bucket    = var.destination.bucket
      partition = var.destination.partition
      prefix    = local.prefix
    }
  }
}

# Monta o zip da Lambda:
#   handler.py
#   core/*.py
#   ingestion/*.py   <- conteúdo de ingestions/<name>/ (config.yml e sample_response.json ficam de fora)
data "archive_file" "lambda" {
  type        = "zip"
  output_path = "${path.root}/.build/${var.name}.zip"

  source {
    filename = "handler.py"
    content  = file("${var.source_root}/handler.py")
  }

  # `dynamic` gera um bloco `source` para cada arquivo devolvido pelo fileset.
  dynamic "source" {
    for_each = fileset("${var.source_root}/core", "**/*.py")
    content {
      filename = "core/${source.value}"
      content  = file("${var.source_root}/core/${source.value}")
    }
  }

  dynamic "source" {
    for_each = fileset(local.ingestion_dir, "**/*.py")
    content {
      filename = "ingestion/${source.value}"
      content  = file("${local.ingestion_dir}/${source.value}")
    }
  }
}

# Criado pelo Terraform (e não automaticamente pela Lambda) para controlar a retenção
# e para a policy IAM apontar para um ARN conhecido.
resource "aws_cloudwatch_log_group" "this" {
  name              = "/aws/lambda/${local.function_name}"
  retention_in_days = var.log_retention_days
}

resource "aws_lambda_function" "this" {
  function_name = local.function_name
  description   = var.description
  role          = aws_iam_role.lambda.arn

  runtime       = "python3.12"
  architectures = ["arm64"] # Graviton: mais barato e o código não tem dependência nativa
  handler       = "handler.lambda_handler"
  timeout       = var.timeout
  memory_size   = var.memory

  filename         = data.archive_file.lambda.output_path
  source_code_hash = data.archive_file.lambda.output_base64sha256 # muda o código -> novo deploy

  environment {
    variables = {
      INGESTION_CONFIG = jsonencode(local.ingestion_config)
    }
  }

  depends_on = [aws_cloudwatch_log_group.this]
}
