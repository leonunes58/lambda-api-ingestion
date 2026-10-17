# ----------------------------------------------------------------------
# Permissions: O QUE cada role pode fazer.
# Tudo restrito aos recursos com prefixo `api-ingestion-`, ao bucket raw e
# ao prefixo deste projeto no bucket de state.
# ----------------------------------------------------------------------

# --- apply: cria, altera e destrói a infraestrutura da raiz terraform/ -------
data "aws_iam_policy_document" "apply" {
  statement {
    sid       = "StateList"
    actions   = ["s3:ListBucket"]
    resources = [local.arn.state_bucket]
  }

  statement {
    sid       = "StateReadWrite"
    actions   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
    resources = [local.arn.state_objects]
  }

  statement {
    sid       = "RawBucket"
    actions   = ["s3:*"]
    resources = [local.arn.raw_bucket, local.arn.raw_objects]
  }

  statement {
    sid       = "Lambda"
    actions   = ["lambda:*"]
    resources = [local.arn.functions]
  }

  statement {
    sid = "IamRoles"
    actions = [
      "iam:CreateRole", "iam:DeleteRole", "iam:GetRole", "iam:UpdateRole",
      "iam:UpdateAssumeRolePolicy", "iam:TagRole", "iam:UntagRole",
      "iam:PutRolePolicy", "iam:GetRolePolicy", "iam:DeleteRolePolicy",
      "iam:ListRolePolicies", "iam:ListAttachedRolePolicies", "iam:ListInstanceProfilesForRole",
    ]
    resources = [local.arn.roles]
  }

  statement {
    sid       = "PassRolesToLambdaAndScheduler"
    actions   = ["iam:PassRole"]
    resources = [local.arn.roles]

    condition {
      test     = "StringEquals"
      variable = "iam:PassedToService"
      values   = ["lambda.amazonaws.com", "scheduler.amazonaws.com"]
    }
  }

  statement {
    sid       = "LogGroups"
    actions   = ["logs:*"]
    resources = [local.arn.log_groups, "${local.arn.log_groups}:*"]
  }

  statement {
    sid       = "LogGroupsDescribe" # esta ação não aceita restrição por recurso
    actions   = ["logs:DescribeLogGroups"]
    resources = ["*"]
  }

  statement {
    sid       = "Schedules"
    actions   = ["scheduler:*"]
    resources = [local.arn.schedules]
  }
}

# --- plan: só leitura (exceto o arquivo de lock do state) --------------------
data "aws_iam_policy_document" "plan" {
  statement {
    sid       = "StateList"
    actions   = ["s3:ListBucket"]
    resources = [local.arn.state_bucket]
  }

  statement {
    sid       = "StateRead"
    actions   = ["s3:GetObject"]
    resources = [local.arn.state_objects]
  }

  statement {
    sid       = "StateLock" # use_lockfile grava/apaga <key>.tflock durante o plan
    actions   = ["s3:PutObject", "s3:DeleteObject"]
    resources = [local.arn.state_locks]
  }

  statement {
    sid       = "RawBucketRead"
    actions   = ["s3:GetBucket*", "s3:GetAccelerateConfiguration", "s3:GetLifecycleConfiguration", "s3:GetReplicationConfiguration", "s3:GetEncryptionConfiguration", "s3:ListBucket"]
    resources = [local.arn.raw_bucket]
  }

  statement {
    sid       = "LambdaRead"
    actions   = ["lambda:Get*", "lambda:List*"]
    resources = [local.arn.functions]
  }

  statement {
    sid       = "IamRead"
    actions   = ["iam:GetRole", "iam:GetRolePolicy", "iam:ListRolePolicies", "iam:ListAttachedRolePolicies"]
    resources = [local.arn.roles]
  }

  statement {
    sid       = "LogsRead"
    actions   = ["logs:ListTagsForResource", "logs:ListTagsLogGroup"]
    resources = [local.arn.log_groups, "${local.arn.log_groups}:*"]
  }

  statement {
    sid       = "LogsDescribe"
    actions   = ["logs:DescribeLogGroups"]
    resources = ["*"]
  }

  statement {
    sid       = "SchedulerRead"
    actions   = ["scheduler:GetSchedule", "scheduler:ListTagsForResource"]
    resources = [local.arn.schedules]
  }
}
