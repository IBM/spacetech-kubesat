# create kubesat application tarballs
resource "null_resource" "kubesat_files" {
  depends_on = [null_resource.leaf_swarm, null_resource.gateway_ground, null_resource.cluster_swarm]
  triggers = {
    ground_ids = "${join(",", ibm_compute_vm_instance.ground.*.id)}"
    swarm_ids = "${join(",", ibm_compute_vm_instance.swarm.*.id)}"
  }
  count = (var.deploy_kubesat == true ? 1 : 0)
  provisioner "local-exec" {
    command = "bash ${path.module}/../scripts/pkg-files.sh ${var.ver}"
  }
}

# deploy on ground nodes
resource "null_resource" "kubesat_ground_0" {
  depends_on = [null_resource.leaf_swarm, null_resource.gateway_ground, null_resource.cluster_swarm, null_resource.kubesat_files]
  triggers = {
    ground_ids = "${join(",", ibm_compute_vm_instance.ground.*.id)}"
  }
  count = (var.deploy_kubesat == true ? 1 : 0)

  connection {
    host = ibm_compute_vm_instance.ground[0].ipv4_address
    user = "ground"
    private_key = tls_private_key.tf_ssh_key.private_key_pem
  }

  # copy deployment tar to node
  provisioner "file" {
    source      = "${path.module}/../files/ground_${var.ver}.tgz"
    destination = "/home/ground/ground_${var.ver}.tgz"
  }

  provisioner "file" {
    source      = "${path.module}/../scripts/deploy-ground.sh"
    destination = "/home/ground/scripts/deploy-ground.sh"
  }

  provisioner "remote-exec" {
    inline = [
      "sudo bash /home/ground/scripts/deploy-ground.sh ${var.namespace} ${var.app} ${var.ver} ${var.number_of_iot_sensors} ${var.number_of_ground_stations}"
    ]
  }
}

# deploy on ground nodes
resource "null_resource" "kubesat_ground" {
  depends_on = [null_resource.kubesat_ground_0]
  triggers = {
    ground_ids = "${join(",", ibm_compute_vm_instance.ground.*.id)}"
  }
  count = (var.deploy_kubesat == true ? var.number_of_ground_stations - 1 : 0)

  connection {
    host = ibm_compute_vm_instance.ground[count.index + 1].ipv4_address
    user = "ground"
    private_key = tls_private_key.tf_ssh_key.private_key_pem
  }

  # copy deployment tar to node
  provisioner "file" {
    source      = "${path.module}/../files/ground_${var.ver}.tgz"
    destination = "/home/ground/ground_${var.ver}.tgz"
  }

  provisioner "file" {
    source      = "${path.module}/../scripts/deploy-ground.sh"
    destination = "/home/ground/scripts/deploy-ground.sh"
  }

  provisioner "remote-exec" {
    inline = [
      "sudo bash /home/ground/scripts/deploy-ground.sh ${var.namespace} ${var.app} ${var.ver} ${var.number_of_iot_sensors} ${var.number_of_ground_stations}"
    ]
  }
}

# deploy on swarm nodes
resource "null_resource" "kubesat_swarm" {
  depends_on = [null_resource.kubesat_ground]
  triggers = {
    swarm_ids = "${join(",", ibm_compute_vm_instance.swarm.*.id)}"
  }
  count = (var.deploy_kubesat == true ? var.swarm_size : 0)

  connection {
    host = ibm_compute_vm_instance.swarm[count.index].ipv4_address
    user = "swarm"
    private_key = tls_private_key.tf_ssh_key.private_key_pem
  }

  # copy deployment tar to node
  provisioner "file" {
    source      = "${path.module}/../files/swarm_${var.ver}.tgz"
    destination = "/home/swarm/swarm_${var.ver}.tgz"
  }

  provisioner "file" {
    source      = "${path.module}/../scripts/deploy-swarm.sh"
    destination = "/home/swarm/scripts/deploy-swarm.sh"
  }

  provisioner "remote-exec" {
    inline = [
      "sudo bash /home/swarm/scripts/deploy-swarm.sh ${var.namespace} ${var.app} ${var.ver}"
    ]
  }
}
