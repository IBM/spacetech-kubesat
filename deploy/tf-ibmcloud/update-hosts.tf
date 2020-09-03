locals {
  hostnames = "${concat(ibm_compute_vm_instance.ground.*.hostname, ibm_compute_vm_instance.swarm.*.hostname)}"
  private_ips = "${concat(ibm_compute_vm_instance.ground.*.ipv4_address_private, ibm_compute_vm_instance.swarm.*.ipv4_address_private)}"
  public_ips = "${concat(ibm_compute_vm_instance.ground.*.ipv4_address, ibm_compute_vm_instance.swarm.*.ipv4_address)}"
}

# update hosts file on ground nodes
resource "null_resource" "ground_hosts" {
  depends_on = [ibm_compute_vm_instance.swarm]
  triggers = {
    ground_ids = "${join(",", ibm_compute_vm_instance.ground.*.id)}"
    swarm_ids = "${join(",", ibm_compute_vm_instance.swarm.*.id)}"
  }
  count = var.number_of_ground_stations

  connection {
    host = ibm_compute_vm_instance.ground[count.index].ipv4_address
    user = "ground"
    private_key = tls_private_key.tf_ssh_key.private_key_pem
  }

  # copy update hosts script to instance
  provisioner "file" {
    source      = "${path.module}/../scripts/regen-hosts.sh"
    destination = "/home/ground/scripts/regen-hosts.sh"
  }

  # update /etc/hosts
  provisioner "remote-exec" {
    inline = [
      "sudo bash /home/ground/scripts/regen-hosts.sh ${join(",", local.hostnames)} ${join(",", local.private_ips)} ${join(",", local.public_ips)}"
    ]
  }
}

# update hosts file on swarm nodes
resource "null_resource" "swarm_hosts" {
  depends_on = [ibm_compute_vm_instance.swarm]
  triggers = {
    ground_ids = "${join(",", ibm_compute_vm_instance.ground.*.id)}"
    swarm_ids = "${join(",", ibm_compute_vm_instance.swarm.*.id)}"
  }
  count = var.swarm_size

  connection {
    host = ibm_compute_vm_instance.swarm[count.index].ipv4_address
    user = "swarm"
    private_key = tls_private_key.tf_ssh_key.private_key_pem
  }

  # copy update hosts script to instance
  provisioner "file" {
    source      = "${path.module}/../scripts/regen-hosts.sh"
    destination = "/home/swarm/scripts/regen-hosts.sh"
  }

  # update /etc/hosts
  provisioner "remote-exec" {
    inline = [
      "sudo bash /home/swarm/scripts/regen-hosts.sh ${join(",", local.hostnames)} ${join(",", local.private_ips)} ${join(",", local.public_ips)}"
    ]
  }
}
