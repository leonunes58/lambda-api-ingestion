output "function_name" {
  description = "Nome da Lambda."
  value       = aws_lambda_function.this.function_name
}

output "function_arn" {
  description = "ARN da Lambda."
  value       = aws_lambda_function.this.arn
}

output "log_group_name" {
  description = "Log group no CloudWatch."
  value       = aws_cloudwatch_log_group.this.name
}

output "schedule_name" {
  description = "Nome do schedule no EventBridge Scheduler."
  value       = aws_scheduler_schedule.this.name
}

output "s3_destination" {
  description = "Onde a ingestão grava os dados."
  value       = "s3://${var.destination.bucket}/${local.prefix}/"
}
