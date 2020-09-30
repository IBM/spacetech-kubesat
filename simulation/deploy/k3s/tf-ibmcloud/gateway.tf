# super cluster ground stations
resource "null_resource" "gateway_ground" {
  depends_on = [null_resource.leaf_swarm]
  triggers = {
    ground_ids = "${join(",", ibm_compute_vm_instance.ground.*.id)}"
  }
  count = (var.number_of_ground_stations > 1 ? var.number_of_ground_stations : 0)

  connection {
    host = ibm_compute_vm_instance.ground[count.index].ipv4_address
    user = "ground"
    private_key = tls_private_key.tf_ssh_key.private_key_pem
  }

  # copy add-leafnode-acct script to instance
  provisioner "file" {
    source      = "${path.module}/../scripts/add-gateways.sh"
    destination = "/home/ground/scripts/add-gateways.sh"
  }

  # update nats conf with leaf accounts
  provisioner "remote-exec" {
    inline = [
      "sudo bash /home/ground/scripts/add-gateways.sh ${var.namespace} ${join(",", ibm_compute_vm_instance.ground.*.hostname)} ${join(",", ibm_compute_vm_instance.ground.*.ipv4_address_private)}"
    ]
  }
}
