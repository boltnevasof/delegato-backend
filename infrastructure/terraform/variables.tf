variable "twc_token" {
  description = "TimeWeb Cloud API token"
  type        = string
  sensitive   = true
}

variable "availability_zone" {
  description = "TimeWeb Cloud availability zone (spb-1, msk-1, ams-1, fra-1, etc.)"
  type        = string
  default     = "ams-1"
}

variable "twc_ssh_key_id" {
  description = "SSH key ID registered in TimeWeb Cloud"
  type        = number
  sensitive   = true
}

variable "ssh_private_key_path" {
  description = "Path to SSH private key for remote-exec provisioner"
  type        = string
  default     = "~/.ssh/id_ed25519"
}

variable "server_name" {
  description = "Name for the VPS instance"
  type        = string
}

variable "preset_cpu" {
  description = "Number of CPU cores for the server preset"
  type        = number
  default     = 2
}

variable "preset_ram" {
  description = "RAM in MB for the server preset (must be divisible by 1024)"
  type        = number
  default     = 4096
}

variable "os_name" {
  description = "Operating system name filter"
  type        = string
  default     = "ubuntu"
}

variable "os_version" {
  description = "Operating system version filter"
  type        = string
  default     = "24.04"
}
