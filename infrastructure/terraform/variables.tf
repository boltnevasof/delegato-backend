variable "twc_token" {
  description = "TimeWeb Cloud API token"
  type        = string
  sensitive   = true
}

variable "twc_region" {
  description = "TimeWeb Cloud region"
  type        = string
  default     = "nl-1"
}

variable "twc_ssh_key_id" {
  description = "SSH key ID registered in TimeWeb Cloud"
  type        = string
  sensitive   = true
}

variable "server_name" {
  description = "Name for the VPS instance"
  type        = string
}

variable "preset_id" {
  description = "TimeWeb Cloud server preset (2 vCPU, 4 GB RAM, 50 GB SSD)"
  type        = number
  default     = 1
}

variable "os_name" {
  description = "Operating system name filter"
  type        = string
  default     = "Ubuntu"
}

variable "os_version" {
  description = "Operating system version filter"
  type        = string
  default     = "24.04"
}
