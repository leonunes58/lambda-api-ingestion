# EventBridge Scheduler: dispara a Lambda no cron do config.yml.
# O Scheduler precisa de uma role própria com permissão de invocar a função.

data "aws_caller_identity" "current" {}

data "aws_iam_policy_document" "scheduler_assume" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["scheduler.amazonaws.com"]
    }

    # Proteção contra "confused deputy": só schedules desta conta podem assumir a role.
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

resource "aws_iam_role" "scheduler" {
  name               = "${local.function_name}-sched"
  assume_role_policy = data.aws_iam_policy_document.scheduler_assume.json
}

data "aws_iam_policy_document" "scheduler_permissions" {
  statement {
    actions   = ["lambda:InvokeFunction"]
    resources = [aws_lambda_function.this.arn]
  }
}

resource "aws_iam_role_policy" "scheduler" {
  name   = "invoke-lambda"
  role   = aws_iam_role.scheduler.id
  policy = data.aws_iam_policy_document.scheduler_permissions.json
}

resource "aws_scheduler_schedule" "this" {
  name                         = local.function_name
  description                  = var.description
  schedule_expression          = var.schedule
  schedule_expression_timezone = "UTC"

  flexible_time_window {
    mode = "OFF" # dispara no horário exato
  }

  target {
    arn      = aws_lambda_function.this.arn
    role_arn = aws_iam_role.scheduler.arn
  }
}
