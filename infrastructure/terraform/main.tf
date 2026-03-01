data "twc_os" "ubuntu" {
  name    = var.os_name
  version = var.os_version
}

resource "twc_server" "agent" {
  name      = var.server_name
  os_id     = data.twc_os.ubuntu.id
  preset_id = var.preset_id
  region    = var.twc_region

  ssh_keys_ids = [var.twc_ssh_key_id]
}

resource "null_resource" "wait_for_ssh" {
  depends_on = [twc_server.agent]

  provisioner "remote-exec" {
    inline = ["echo 'SSH is ready'"]

    connection {
      type    = "ssh"
      host    = twc_server.agent.main_ipv4
      user    = "root"
      timeout = "5m"
      agent   = false
    }
  }
}
