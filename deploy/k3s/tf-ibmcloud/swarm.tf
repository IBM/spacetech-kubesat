# deploy swarm nodes
resource "ibm_compute_vm_instance" "swarm" {
  depends_on = [ibm_compute_vm_instance.ground]
  count                = var.swarm_size
  hostname             = "${var.namespace}-${var.swarm_hostname}-${count.index}"
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
    "swarm-node",
    "kubesat"
  ]

  ssh_key_ids = [data.ibm_compute_ssh_key.ssh_key_name.id]

  user_metadata = <<EOF
#cloud-config
packages:
  - jq
users:
  - default
  - name: swarm
    groups: [ wheel ]
    sudo: [ "ALL=(ALL) NOPASSWD:ALL" ]
    shell: /bin/bash
    ssh-authorized-keys:
      - ${tls_private_key.tf_ssh_key.public_key_openssh}
write_files:
  - path: /home/swarm/scripts/logger.sh
    permissions: '0755'
    encoding: b64
    content: ${base64encode(file("${path.module}/../scripts/logger.sh"))}
  - path: /home/swarm/scripts/add-cluster-route.sh
    permissions: '0755'
    encoding: b64
    content: ${base64encode(file("${path.module}/../scripts/add-cluster-route.sh"))}
runcmd:
  - chown -R swarm:root /home/swarm
  - chmod -R 0755 /home/swarm

EOF

  connection {
    host = self.ipv4_address
    user = "swarm"
    private_key = tls_private_key.tf_ssh_key.private_key_pem
  }

  # copy container registry script to instance
  provisioner "file" {
    source      = "${path.module}/../scripts/setup-container-registry.sh"
    destination = "/home/swarm/scripts/setup-container-registry.sh"
  }

  # setup container registry
  provisioner "remote-exec" {
    inline = [
      "sudo bash /home/swarm/scripts/setup-container-registry.sh"
    ]
  }

  # copy setup swarm script to instance
  provisioner "file" {
    source      = "${path.module}/../scripts/setup-swarm.sh"
    destination = "/home/swarm/scripts/setup-swarm.sh"
  }

  # deploy nats server on swarm nodes
  provisioner "remote-exec" {
    inline = [
      "sudo bash /home/swarm/scripts/setup-swarm.sh ${var.namespace}"
    ]
  }

  lifecycle {
    create_before_destroy = false
  }
}
