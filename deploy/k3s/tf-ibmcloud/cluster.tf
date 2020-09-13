# cluster between sats
resource "null_resource" "cluster_swarm" {
  depends_on = [null_resource.gateway_ground]
  triggers = {
    swarm_ids = "${join(",", ibm_compute_vm_instance.swarm.*.id)}"
  }
  count = var.swarm_size

  connection {
    host = ibm_compute_vm_instance.swarm[count.index].ipv4_address
    user = "swarm"
    private_key = tls_private_key.tf_ssh_key.private_key_pem
  }

  provisioner "remote-exec" {
    inline = [
      "sudo bash /home/swarm/scripts/add-cluster-route.sh ${var.namespace} ${join(",", ibm_compute_vm_instance.swarm.*.ipv4_address_private)}"
    ]
  }
}
