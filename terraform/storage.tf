data "aws_caller_identity" "current" {}

# Bucket raw de destino de todas as ingestões (cada uma grava no seu prefixo).
# O account ID no nome garante unicidade global sem escrevê-lo no código.
resource "aws_s3_bucket" "raw" {
  bucket        = "lambda-api-ingestion-raw-${data.aws_caller_identity.current.account_id}"
  force_destroy = true # projeto de estudo: o destroy apaga o bucket mesmo com objetos
}

resource "aws_s3_bucket_public_access_block" "raw" {
  bucket = aws_s3_bucket.raw.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
