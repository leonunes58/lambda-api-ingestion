# Credenciais vêm do ambiente (AWS_PROFILE), nunca do código.
provider "aws" {
  region = "us-east-1"

  # Aplicadas automaticamente a todo recurso que aceita tags, inclusive os do module.
  default_tags {
    tags = {
      Projeto   = "lambda-api-ingestion"
      CriadoPor = "terraform"
    }
  }
}
