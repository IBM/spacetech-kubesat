# add each swarm node as leaf to each ground cluster
resource "null_resource" "leaf_ground" {
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

  # copy add-leafnode-acct script to instance
  provisioner "file" {
    source      = "${path.module}/../scripts/add-leafnode-acct.sh"
    destination = "/home/ground/scripts/add-leafnode-acct.sh"
  }

  # update nats conf with leaf accounts
  provisioner "remote-exec" {
    inline = [
      "sudo bash /home/ground/scripts/add-leafnode-acct.sh ${var.namespace} ${join(",", random_password.lf_pass.*.result)} ${join(",", ibm_compute_vm_instance.swarm.*.hostname)}"
    ]
  }
}

# add each ground cluster leaf service endpoint to each swarm node
resource "null_resource" "leaf_swarm" {
  depends_on = [null_resource.leaf_ground]
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

  # copy add-leafnode-acct script to instance
  provisioner "file" {
    source      = "${path.module}/../scripts/add-leafnode-remote.sh"
    destination = "/home/swarm/scripts/add-leafnode-remote.sh"
  }

  # update nats conf with leaf accounts
  provisioner "remote-exec" {
    inline = [
      "sudo bash /home/swarm/scripts/add-leafnode-remote.sh ${var.namespace} ${random_password.lf_pass[count.index].result} ${join(",", ibm_compute_vm_instance.ground.*.ipv4_address_private)}"
    ]
  }
}
