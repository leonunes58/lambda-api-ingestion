# Entradas do module. Cada ingestão (config.yml) vira uma chamada com estes valores.
# Os blocos `validation` repetem as regras de tests/test_ingestions.py: o pytest pega o
# erro na máquina do dev, o Terraform garante no plan mesmo que os testes sejam pulados.

variable "name" {
  description = "Nome da ingestão (igual ao nome da pasta em ingestions/)."
  type        = string

  validation {
    condition     = can(regex("^[a-z][a-z0-9_]{0,39}$", var.name))
    error_message = "name deve ser snake_case minúsculo, começar com letra e ter até 40 caracteres."
  }
}

variable "description" {
  description = "Descrição curta da ingestão."
  type        = string
  default     = ""
}

variable "api" {
  description = "Configuração da API de origem."
  type = object({
    url    = string
    method = optional(string, "GET")
  })

  validation {
    condition     = startswith(var.api.url, "https://")
    error_message = "api.url deve começar com https://."
  }

  validation {
    condition     = upper(var.api.method) == "GET"
    error_message = "api.method: na Fase 1 só GET é suportado."
  }
}

variable "destination" {
  description = "Destino no S3. prefix é opcional (padrão = name)."
  type = object({
    bucket    = string
    partition = string
    prefix    = optional(string)
  })

  validation {
    condition     = length(var.destination.bucket) > 0
    error_message = "destination.bucket é obrigatório."
  }

  validation {
    condition     = contains(["anomesdia", "anomes"], var.destination.partition)
    error_message = "destination.partition deve ser \"anomesdia\" ou \"anomes\"."
  }
}

variable "schedule" {
  description = "Expressão do EventBridge Scheduler, em UTC: cron(...) ou rate(...)."
  type        = string

  validation {
    condition     = can(regex("^(cron|rate)\\(.+\\)$", var.schedule))
    error_message = "schedule deve estar no formato cron(...) ou rate(...)."
  }
}

variable "timeout" {
  description = "Timeout da Lambda em segundos."
  type        = number
  default     = 30

  validation {
    condition     = var.timeout >= 3 && var.timeout <= 300 && floor(var.timeout) == var.timeout
    error_message = "timeout deve ser inteiro entre 3 e 300 segundos."
  }
}

variable "memory" {
  description = "Memória da Lambda em MB."
  type        = number
  default     = 128

  validation {
    condition     = var.memory >= 128 && var.memory <= 1024 && floor(var.memory) == var.memory
    error_message = "memory deve ser inteiro entre 128 e 1024 MB."
  }
}

variable "source_root" {
  description = "Caminho da raiz do repositório (onde estão handler.py, core/ e ingestions/)."
  type        = string
}

variable "log_retention_days" {
  description = "Dias de retenção do log group no CloudWatch."
  type        = number
  default     = 14
}
