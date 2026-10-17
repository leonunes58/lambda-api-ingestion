variable "github_repository" {
  description = "Repositório no formato dono/nome, único autorizado a assumir as roles."
  type        = string
  default     = "leonunes58/lambda-api-ingestion"
}

variable "deploy_branch" {
  description = "Única branch que pode assumir a role de apply."
  type        = string
  default     = "main"
}
