data "twc_os" "ubuntu" {
  name    = var.os_name
  version = var.os_version
}

data "twc_presets" "server" {
  availability_zone = var.availability_zone
  cpu               = var.preset_cpu
  ram               = var.preset_ram
}

resource "twc_server" "agent" {
  name              = var.server_name
  os_id             = data.twc_os.ubuntu.id
  preset_id         = data.twc_presets.server.id
  availability_zone = var.availability_zone
  bandwidth         = 1000

  ssh_keys_ids = [var.twc_ssh_key_id]
}

resource "twc_server_ip" "agent_ipv4" {
  source_server_id = twc_server.agent.id
  type             = "ipv4"
}
