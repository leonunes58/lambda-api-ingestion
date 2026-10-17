# Um module declara os providers de que precisa, mas NÃO os configura
# (região, credenciais): isso é responsabilidade da raiz que o chama.
terraform {
  required_version = ">= 1.10"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 6.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = ">= 2.4"
    }
  }
}
