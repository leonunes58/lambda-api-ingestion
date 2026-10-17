terraform {
  required_version = ">= 1.10"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.8"
    }
  }

  # Configuração parcial: o nome do bucket (que contém o account ID) fica em
  # backend.hcl, fora do Git. Uso: terraform init -backend-config=backend.hcl
  backend "s3" {
    key          = "lambda-api-ingestion/terraform.tfstate"
    region       = "us-east-1"
    use_lockfile = true
    encrypt      = true
  }
}
