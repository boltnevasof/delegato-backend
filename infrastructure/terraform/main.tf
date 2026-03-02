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

  ssh_keys_ids = [var.twc_ssh_key_id]
}

resource "null_resource" "wait_for_ssh" {
  depends_on = [twc_server.agent]

  provisioner "remote-exec" {
    inline = ["echo 'SSH is ready'"]

    connection {
      type        = "ssh"
      host        = twc_server.agent.main_ipv4
      user        = "root"
      private_key = file(var.ssh_private_key_path)
      timeout     = "5m"
    }
  }
}
