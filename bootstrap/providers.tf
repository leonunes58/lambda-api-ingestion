provider "aws" {
  region = "us-east-1"

  default_tags {
    tags = {
      Projeto   = "lambda-api-ingestion"
      CriadoPor = "terraform"
      Camada    = "bootstrap"
    }
  }
}
