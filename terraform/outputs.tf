output "raw_bucket" {
  description = "Bucket raw de destino."
  value       = aws_s3_bucket.raw.bucket
}

output "ingestions" {
  description = "Recursos criados por ingestão."
  value = {
    for name, m in module.ingestion : name => {
      function_name  = m.function_name
      log_group      = m.log_group_name
      schedule       = m.schedule_name
      s3_destination = m.s3_destination
    }
  }
}
