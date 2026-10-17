# Estes ARNs vão para as "variables" do repositório no GitHub (não são segredos).
output "apply_role_arn" {
  description = "Role assumida pelo workflow de apply (push na main)."
  value       = aws_iam_role.apply.arn
}

output "plan_role_arn" {
  description = "Role assumida pelo workflow de plan (pull requests)."
  value       = aws_iam_role.plan.arn
}
