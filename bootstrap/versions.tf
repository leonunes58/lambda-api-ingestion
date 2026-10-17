# Raiz separada, aplicada uma única vez (manualmente) para criar a confiança
# entre o GitHub Actions e a AWS. O pipeline não pode criar a role que ele usa.
terraform {
  required_version = ">= 1.10"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  # Mesmo bucket de state da raiz principal, key diferente.
  # Uso: terraform init -backend-config=../terraform/backend.hcl
  backend "s3" {
    key          = "lambda-api-ingestion/bootstrap.tfstate"
    region       = "us-east-1"
    use_lockfile = true
    encrypt      = true
  }
}
