# deploy ground nodes
resource "ibm_compute_vm_instance" "ground" {
  count                = var.number_of_ground_stations
  hostname             = "${var.namespace}-${var.ground_hostname}-${count.index}"
  domain               = var.swarm_domain
  os_reference_code    = "UBUNTU_18_64"
  datacenter           = "dal10"
  network_speed        = 1000
  hourly_billing       = true
  private_network_only = false
  cores                = 4
  memory               = 4096
  disks                = [25]
  local_disk           = false

  tags = [
    var.namespace,
    "ground-node",
    "kubesat"
  ]

  ssh_key_ids = [data.ibm_compute_ssh_key.ssh_key_name.id]

  user_metadata = <<EOF
#cloud-config
packages:
  - jq
users:
  - default
  - name: ground
    groups: [ wheel ]
    sudo: [ "ALL=(ALL) NOPASSWD:ALL" ]
    shell: /bin/bash
    ssh-authorized-keys:
      - ${tls_private_key.tf_ssh_key.public_key_openssh}
write_files:
  - path: /home/ground/scripts/logger.sh
    permissions: '0755'
    encoding: b64
    content: ${base64encode(file("${path.module}/../scripts/logger.sh"))}
runcmd:
  - chown -R ground:root /home/ground
  - chmod -R 0755 /home/ground

EOF

  connection {
    host = self.ipv4_address
    user = "ground"
    private_key = tls_private_key.tf_ssh_key.private_key_pem
  }

  # copy container registry script to instance
  provisioner "file" {
    source      = "${path.module}/../scripts/setup-container-registry.sh"
    destination = "/home/ground/scripts/setup-container-registry.sh"
  }

  # setup container registry
  provisioner "remote-exec" {
    inline = [
      "sudo bash /home/ground/scripts/setup-container-registry.sh"
    ]
  }

  # copy setup ground script to instance
  provisioner "file" {
    source      = "${path.module}/../scripts/setup-ground.sh"
    destination = "/home/ground/scripts/setup-ground.sh"
  }

  # deploy nats cluster on ground nodes
  provisioner "remote-exec" {
    inline = [
      "sudo bash /home/ground/scripts/setup-ground.sh ${var.namespace}"
    ]
  }

  lifecycle {
    create_before_destroy = false
  }
}
