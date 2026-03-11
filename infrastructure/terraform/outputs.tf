output "server_ip" {
  description = "Public IPv4 address of the provisioned server"
  value       = twc_server_ip.agent_ipv4.ip
}

output "server_id" {
  description = "TimeWeb Cloud server ID (provider_id)"
  value       = tostring(twc_server.agent.id)
}
